"""
Groq LLM client — 1 key drives all 3 agents via different system prompts.
"""
import json
import os
from dataclasses import dataclass
from string import Template
from dotenv import load_dotenv
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_client = Groq(api_key=os.environ["GROQ_API_KEY"])


@dataclass
class AgentDecision:
    action: str
    token_in: str = ""
    token_out: str = ""
    amount: float = 0
    pool_id: str = ""
    confidence: float = 0
    reasoning: str = ""
    raw_response: str = ""
    expected_profit_pct: float = 0
    market_implied_pct: float = 0
    your_estimate_pct: float = 0
    outcome: int = 0


AGENT_PROMPTS = {
    "yield": Template("""You are a DeFi yield optimizer. Output EXACTLY one JSON object, no other text.

Valid actions: "swap", "stake", "unstake", "compound", "hold"
All fields are REQUIRED in the JSON: action, token_in, token_out, amount, pool_id, confidence, reasoning

Example valid response:
{"action":"swap","token_in":"SUI","token_out":"USDC","amount":50,"pool_id":"0xabc","confidence":0.85,"reasoning":"8.2 percent APR vs current 6.5 percent — 1.7 percent edge"}

Rules:
- Only act if APR differential exceeds 2 percentage points
- Prefer pools with TVL over 100K USD
- Max single pool allocation: 50 percent of capital

$state"""),

    "trader": Template("""You are an algorithmic trader. Output EXACTLY one JSON object, no other text.

Valid actions: "swap", "hold"
All fields REQUIRED: action, token_in, token_out, amount, pool_id, confidence, expected_profit_pct, reasoning

Example valid response:
{"action":"swap","token_in":"SUI","token_out":"USDC","amount":30,"pool_id":"0xabc","confidence":0.72,"expected_profit_pct":0.8,"reasoning":"0.8 percent arbitrage between pools after 0.3 percent fee"}

Rules:
- Only trade if profit after 0.3 percent fee exceeds 0.5 percent
- Max position: $max_position SUI
- Stop at $stop_loss percent loss

$state"""),

    "prediction": Template("""You are a prediction market analyst. Output EXACTLY one JSON object, no other text.

Valid actions: "bet", "claim", "hold"
All fields REQUIRED: action, market_id, outcome (integer 0 or 1), amount, confidence, market_implied_pct, your_estimate_pct, reasoning

Example valid response:
{"action":"bet","market_id":"0xpred1","outcome":0,"amount":8,"confidence":0.65,"market_implied_pct":42,"your_estimate_pct":48,"reasoning":"Market implies 42 percent, our model estimates 48 percent — 6 percent edge"}

Rules:
- Only bet if your estimate exceeds market-implied by at least 5 percentage points
- Max bet: $max_bet SUI per market
- Use Kelly criterion for position sizing

$state""")
}


def decide(agent_type: str, state: str, **kwargs) -> AgentDecision:
    prompt_template = AGENT_PROMPTS[agent_type]
    system_prompt = prompt_template.substitute(state=state, **kwargs)

    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Output the JSON object now."},
        ],
        max_tokens=512,
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    for prefix in ["```json", "```"]:
        if raw.startswith(prefix):
            raw = raw[len(prefix):].strip()
    for suffix in ["```"]:
        if raw.endswith(suffix):
            raw = raw[:-len(suffix)].strip()

    brace_start = raw.find("{")
    brace_end = raw.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        raw = raw[brace_start:brace_end + 1]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return AgentDecision(
            action="hold", reasoning=f"JSON parse failed: {raw[:100]}",
            raw_response=raw,
        )

    if not isinstance(data, dict):
        return AgentDecision(
            action="hold", reasoning=f"non-dict response: {raw[:100]}",
            raw_response=raw,
        )

    return AgentDecision(
        action=data.get("action", "hold"),
        token_in=data.get("token_in", ""),
        token_out=data.get("token_out", ""),
        amount=float(data.get("amount", 0)),
        pool_id=data.get("pool_id", ""),
        confidence=float(data.get("confidence", 0)),
        reasoning=data.get("reasoning", ""),
        raw_response=raw,
        expected_profit_pct=float(data.get("expected_profit_pct", 0)),
        market_implied_pct=float(data.get("market_implied_pct", 0)),
        your_estimate_pct=float(data.get("your_estimate_pct", 0)),
        outcome=int(data.get("outcome", 0)),
    )

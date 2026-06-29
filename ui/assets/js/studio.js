const lenis = new Lenis({
    duration: 1.3,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    direction: 'vertical',
    gestureDirection: 'vertical',
    smooth: true,
    mouseMultiplier: 1,
    smoothTouch: false,
    touchMultiplier: 2,
    infinite: false,
})
function raf(time) {
    lenis.raf(time)
    requestAnimationFrame(raf)
}
requestAnimationFrame(raf)

function page4Animation() {
    var elemC = document.querySelector("#elem-container")
    var fixed = document.querySelector("#fixed-image")

    elemC.addEventListener("mouseenter", function () {
        fixed.style.display = "block"
    });

    elemC.addEventListener("mouseleave", function () {
        fixed.style.display = "none"
    });

    elemC.addEventListener("mousemove", function (dets) {
        gsap.to(fixed, {
            x: dets.x,
            y: dets.y,
            duration: 0.4,
            ease: "power3.out"
        });
    });

    var elems = document.querySelectorAll(".elem")
    elems.forEach(function (e) {
        e.addEventListener("mouseenter", function () {
            var image = e.getAttribute("data-image")
            fixed.style.backgroundImage = `url(${image})`
        })
    })
}

function swiperAnimation() {
    var swiper = new Swiper(".mySwiper", {
        slidesPerView: "auto",
        spaceBetween: 50,
        freeMode: true,
        grabCursor: true,
    });
}

var loader = document.querySelector("#loader")
setTimeout(function () {
    loader.style.top = "-100%"
}, 4000)

function responsiveMenu() {
    var menu = document.querySelector("#menu");
    var full = document.querySelector("#full-scr");

    var flag = 0;

    menu.addEventListener("click", function () {
        if (flag == 0) {
            full.style.top = 0;
            flag = 1;
        }
        else {
            full.style.top = "-100%";
            flag = 0;
        }
    })
}

responsiveMenu()
swiperAnimation()
page4Animation()

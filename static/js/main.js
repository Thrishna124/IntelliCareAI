const nav = document.querySelector(".navbar");

if (nav) {
    window.addEventListener("scroll", () => {
        nav.classList.toggle("shadow", window.scrollY > 50);
    });
}
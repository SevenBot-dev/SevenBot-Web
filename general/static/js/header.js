menuOpener = document.getElementById("header-menu-opener")
menuOpenerAnimating = false
menuOpener.addEventListener("click", () => {
    if (menuOpenerAnimating) { return }
    menuOpenerAnimating = true
    menuOpener.setAttribute("open", Boolean(menuOpener.getAttribute("open") != "true").toString())

    if (menuOpener.getAttribute("open") == "true") {
        menuOpener.animate({
            "transform": ["rotateX(0deg)", "rotateX(180deg)"]

        }, { duration: 100, fill: "forwards" })
        e3 = document.getElementById(`header-menu`)
        e3.style.display = "block"
    } else {
        menuOpener.animate({
            "transform": ["rotateX(180deg)", "rotateX(0deg)"]

        }, { duration: 100, fill: "forwards" })
        e3 = document.getElementById(`header-menu`)
        e3.style.display = "none"
    }
    menuOpenerAnimating = false
})
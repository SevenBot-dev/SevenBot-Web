console.debug("%cLoaded: header.js", "color:#5865f2")
menuOpener = document.getElementById("header-menu-opener")
menuOpenerOpen = document.getElementById("header-menu-opener-svg-open")
menuOpenerClose = document.getElementById("header-menu-opener-svg-close")
sideBar = document.querySelector("aside")
menuOpenerAnimating = false
menuOpener.addEventListener("click", () => {
  if (menuOpenerAnimating) {
    return
  }
  menuOpenerAnimating = true
  menuOpener.setAttribute("open", Boolean(menuOpener.getAttribute("open") != "true").toString())

  if (menuOpener.getAttribute("open") == "true") {
    menuOpenerOpen.animate({
      opacity: [1, 0]
    }, {
      duration: 100,
      fill: "forwards"
    })
    menuOpenerClose.animate({
      opacity: [0, 1]
    }, {
      duration: 100,
      fill: "forwards"
    })
    sideBar.style.display = "block"
  } else {
    menuOpenerOpen.animate({
      opacity: [0, 1]
    }, {
      duration: 100,
      fill: "forwards"
    })
    menuOpenerClose.animate({
      opacity: [1, 0]
    }, {
      duration: 100,
      fill: "forwards"
    })
    sideBar.style.display = "none"
  }
  menuOpenerAnimating = false
})
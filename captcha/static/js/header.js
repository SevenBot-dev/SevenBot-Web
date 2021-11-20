menuOpener = document.getElementById("header-menu-opener")
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
    e3 = document.getElementById(`header-menu`)
    e3.style.display = "block"
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
    e3 = document.getElementById(`header-menu`)
    e3.style.display = "none"
  }
  menuOpenerAnimating = false
})
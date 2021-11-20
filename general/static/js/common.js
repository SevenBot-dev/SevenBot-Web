console.debug("%cLoaded: common.js", "color:#5865f2")

function showTooltip(text, target) {
  r = target.getClientRects()[0]
  console.log(r, r.x + r.width / 2)
  tooltip = document.querySelector(".tooltip")
  tooltip.style.left = `${Math.floor(r.x + r.width / 2)}px`
  tooltip.style.top = `${Math.floor(window.scrollY + r.top)}px`
  document.querySelector(".tooltip .tooltip-main div").innerHTML = text
  tooltipOp = document.querySelector(".tooltip .tooltip-opacity")
  tooltip.style.display = "block"
  tooltipOp.animate({
    opacity: [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
  }, {
    duration: 1200,
    fill: "forwards"
  }).finished.then(() => {
    tooltip.style.display = "none"
  })
}


if (document.cookie.replace(/(?:(?:^|.*;\s*)google-show\s*\=\s*([^;]*).*$)|^.*$/, "$1") !== "true") {
  document.getElementById("google-alert").style.display = "block"
  document.cookie = "google-show=true; expires=Fri, 31 Dec 9999 23:59:59 GMT";
}
if (location.search.includes("tk-redirect")) {
  document.getElementById("tk-alert").style.display = "block"
}

setTimeout(() => {
  Array.from(document.getElementsByClassName("alert")).forEach((alert) => {
    alert.style.display = "none"
  })
}, 5000)
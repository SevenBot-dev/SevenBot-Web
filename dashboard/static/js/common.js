console.debug("%cLoaded: common.js", "color:#5865f2")

function showTooltip(text, target, color, length) {
    length = length || 1000
    r = target.getClientRects()[0]
    let template = document.getElementById("tooltip-template")
    let tooltip = template.content.cloneNode(true).firstElementChild
    tooltip.style.zIndex = 9999 + document.querySelectorAll(".tooltip").length
    tooltip.style.left = `${Math.floor(r.x+r.width/2)}px`
    tooltip.style.top = `${Math.floor(window.scrollY+r.top)}px`
    tooltip.querySelector(".tooltip-main div").innerHTML = text.replace(/\n/g, "<br>")
    let tooltipOp = tooltip.querySelector(".tooltip-opacity")
    tooltip.style.display = "block"
    tooltipOp.style.setProperty("--tooltip-bg-color", "var(--tooltip-bg-" + color + ")")
    tooltipOp.style.setProperty("--tooltip-text-color", "var(--tooltip-text-" + color + ")")
    document.getElementById("content").appendChild(tooltip)
    tooltipOp.animate({
        opacity: [0, 1]
    }, {
        duration: 100,
        fill: "forwards"
    })
    tooltipOp.animate({
        opacity: [1, 0]
    }, {
        duration: 100,
        fill: "forwards",
        delay: length + 100,
    }).finished.then(() => {
        tooltip.remove()
    })

}


if (document.cookie.replace(/(?:(?:^|.*;\s*)google-show\s*\=\s*([^;]*).*$)|^.*$/, "$1") !== "true") {
    document.getElementById("google-alert").style.display = "block"
    document.cookie = "google-show=true; expires=Fri, 31 Dec 9999 23:59:59 GMT";
}
if (location.search.includes("tk-redirect")) {
    document.getElementById("tk-alert").style.display = "block"
}
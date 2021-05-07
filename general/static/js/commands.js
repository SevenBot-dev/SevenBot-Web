function copyCommand(elem) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText("sb#" + elem.innerText.trim())
        showTooltip("コピーした！", elem)
    }
}

function copyLink(elem) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText("https://sevenbot.jp/commands#" + elem.innerText.trim().replace(" ", "-"))
        showTooltip("コピーした！", elem)
    }
}
Array.from(document.getElementsByClassName("more")).forEach(e => {
    e.addEventListener("click", () => {
        e.setAttribute("open", e.getAttribute("open") != "true")
        if (e.getAttribute("open") == "true") {
            e.animate({
                "transform": ["rotate(0deg)", "rotate(45deg)"]

            }, 100, { fills: "both" }).ready.then(() => {
                e.style.transform = "rotate(45deg)"
            })
        } else {
            e.animate({
                "transform": ["rotate(45deg)", "rotate(0deg)"]

            }, 100, { fill: "both" }).ready.then(() => {
                e.style.transform = "rotate(0deg)"
            })
        }
        d = e.parentElement.querySelector("span.datail")
        d.style.display = e.getAttribute("open") == "true" ? "inline" : "none"
    })
})
ary = []
Array.from(document.getElementsByClassName("has-parent")).forEach(e => {
    ary.push(e.getAttribute("parent"))
})

function btnOpener() {
    this.setAttribute("open", Boolean(this.getAttribute("open") != "true").toString())
    e2 = this.querySelector("td svg")

    if (this.getAttribute("open") == "true") {
        e2.animate({
            "transform": ["rotateX(0deg)", "rotateX(180deg)"]

        }, 100, {}).ready.then(() => {
            e2.style.transform = "rotateX(180deg)"
        })
        Array.from(document.querySelectorAll(`tr[parent="${this.getAttribute("for")}"]`)).forEach(e => {
            e.style.display = "table-row"
        })
    } else {
        e2.animate({
            "transform": ["rotateX(180deg)", "rotateX(0deg)"]

        }, 100, {}).ready.then(() => {
            e2.style.transform = "rotateX(0deg)"
        })
        Array.from(document.querySelectorAll(`tr[parent="${this.getAttribute("for")}"]`)).forEach(e3 => {
            e3.style.display = "none"
            if (e3.classList.contains("expand-tr")) {
                e3.setAttribute("open", "false")
                e3.querySelector("td svg").style.transform = "rotateX(0deg)"
                Array.from(document.querySelectorAll(`tr[parent="${e3.getAttribute("for")}"]`)).forEach(e5 => {
                    e5.style.display = "none"
                })
            }
        })
    }

}
ary = ary.filter((x, i, self) => self.indexOf(x) === i)
Array.from(document.querySelectorAll("tbody tr")).forEach(e => {
    if (ary.includes(e.getAttribute("name"))) {
        expandTr = document.createElement("tr");
        expandBtn = document.createElement("td");
        expandBtn.setAttribute("colspan", "4")
        expandBtn.innerHTML = '<svg width="18" height="10" viewBox="-2 -2 34 18"><polyline points="0,0 16,16 32,0" stroke="#72767d" fill="none" stroke-width="1"></polyline></svg>'
        expandTr.appendChild(expandBtn)
        expandTr.setAttribute("class", "expand-tr")
        if (e.getAttribute("parent")) {
            expandTr.setAttribute("parent", e.getAttribute("parent"))
            expandTr.setAttribute("class", "expand-tr has-parent")
        }
        expandTr.setAttribute("for", e.getAttribute("name"))
        e.parentElement.insertBefore(expandTr, e.nextSibling);
        expandTr.addEventListener("click", btnOpener)
    }
})

function scrollToHash() {
    if (location.hash != "#") {
        if (location.hash.startsWith("#category-")) {
            cn = location.hash.slice(10)
            elem = document.querySelector(`.category[category=${cn}]`)
            if (document.querySelector(`.pinged`)) {
                document.querySelector(`.pinged`).classList.remove("pinged")
            }
            if (!elem) { return }
            window.scrollTo(0, elem.getBoundingClientRect().top + window.scrollY - 192)
            return
        }
        if (!location.hash.slice(1)) { return }
        elem = document.querySelector(`[name=${location.hash.slice(1)}]`)
        if (document.querySelector(`.pinged`)) {
            document.querySelector(`.pinged`).classList.remove("pinged")
        }
        if (!elem) { return }

        function openParent(elm) {
            if (elm.getAttribute("parent")) {
                tr = document.querySelector(`.expand-tr[for=${elm.getAttribute("parent")}]`)
                tr.click()
                openParent(tr)
            }
        }
        openParent(elem)
        window.scrollTo(0, elem.getBoundingClientRect().top + window.scrollY - 192)
        elem.classList.add("pinged")
        if (elem.querySelector(".more")) {
            elem.querySelector(".more").click()
        }


    }
}
window.addEventListener("hashchange", scrollToHash)
scrollToHash()
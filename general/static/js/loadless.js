var isJumping = false
var pageCaches = {}
var aHistory = [location.pathname]
menuOpener = document.getElementById("header-menu-opener")

function pretendJump() {
  for (e of document.getElementsByTagName("a")) {
    if (e.getAttribute("target") != "blank" && e.getAttribute("href").match(/^\/(?:[^\/]|$)/)) {
      e.addEventListener("click", onAClick)
    }
  }
}

function escapeRegex(string) {
  return string.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
}

function runScript() {
  for (script of document.querySelectorAll("block[block-name='main'] script, head script")) {
    if (document.head.innerHTML.match(new RegExp(`<!-- reload-area -->[\\s\\S]*${escapeRegex(script.outerHTML)}`))) {
      tmpScript = document.createElement("script")
      for (a of script.attributes) {
        tmpScript.setAttribute(a.name, a.value)
      }
      tmpScript.appendChild(document.createTextNode(script.innerHTML))
      script.parentElement.replaceChild(tmpScript, script)
    }
  }
}

function makeCacheObject(target) {
  headBlock = target.head.innerHTML.match(/<!-- block head -->([\s\S]*)<!-- endblock head -->/)[1]
  title = target.querySelector("head title").innerHTML
  body = target.querySelector("block[block-name='main']").innerHTML
  return {
    title,
    headBlock,
    body,
  }
}

function onAClick(event) {
  event.preventDefault();
  if (isJumping) {
    return
  }
  isJumping = true
  aHistory.push(location.pathname)
  href = this.getAttribute("href")
  jumpURL(href)

}
async function jumpURL(href) {
  console.debug("%cJumping to " + href, "color:#0067e0")
  // console.debug(pageCaches[href])
  if (!pageCaches[href]) {

    mainBlocker = document.getElementById("main-blocker")
    mainBlocker.style.display = "block"
    mainBlocker.style.pointerEvents = "auto"
    mainBlocker.animate({
      opacity: [0, 0.4]
    }, {
      duration: 200,
      easing: "ease-in-out",
      fill: "forwards"
    })

    console.debug("Fetch and cacheing")
    response = await fetch(href, {
      method: "GET"
    })
    txt = await response.text()
    dom = (new DOMParser).parseFromString(txt, "text/html")

    singleheadBlock = txt.match(/<!-- block singlehead -->([\s\S]*)<!-- endblock singlehead -->/)[1]
    pageCaches[href] = makeCacheObject(dom)
    mainBlocker.style.pointerEvents = "none"
    mainBlocker.animate({
      opacity: [0.4, 0]
    }, {
      duration: 200,
      easing: "ease-in-out",
      fill: "forwards"
    }).finished.then(() => {
      mainBlocker.style.display = "none"
    })
  } else {
    console.debug("Loading cache")
    title = pageCaches[href].title
    headBlock = pageCaches[href].headBlock
    body = pageCaches[href].body
    singleheadBlock = ""
  }
  console.debug("Replacing")
  document.querySelector("head title").innerHTML = title
  document.querySelector("head").innerHTML = document.querySelector("head").innerHTML.replace(
    /<!-- block head -->([\s\S]*)<!-- endblock head -->/,
    `<!-- block head -->${headBlock}<!-- tmpblock -->$1<!-- endtmpblock --><!-- endblock head -->`
  )
  document.querySelector("head").innerHTML = document.querySelector("head").innerHTML.replace(
    /<!-- block singlehead -->[\s\S]*<!-- endblock singlehead -->/,
    `<!-- block singlehead -->${singleheadBlock}<!-- endblock singlehead -->`)
  promisies = [];
  [...document.querySelectorAll("head link[rel=stylesheet]")].forEach(e => {
    if (!e.sheet) {
      promisies.push(new Promise(resolve => {
        e.addEventListener("load", resolve)
      }))
    }
  })
  await Promise.all(promisies)
  document.querySelector("block[block-name='main']").innerHTML = body

  console.debug("Running script")
  runScript()
  history.pushState(null, title, href)
  isJumping = false
  pretendJump()
  if (menuOpener.getAttribute("open") === "true") {
    menuOpener.click()
  }
  setTimeout(() => {
    document.querySelector("head").innerHTML = document.querySelector("head").innerHTML.replace(
      /<!-- tmpblock -->([\s\S]*)<!-- endtmpblock -->/,
      ``
    )
  }, 0)

  console.debug("%cDone", "color:#3ba55c")
}

function onPopState(state) {
  href = aHistory.pop()
  jumpURL(href)
}
window.addEventListener("popstate", onPopState)
pretendJump()

pageCaches[location.pathname] = makeCacheObject(document)
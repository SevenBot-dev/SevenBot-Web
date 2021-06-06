console.debug("%cLoaded: manage.js", "color:#5865f2")
flaskData = JSON.parse(document.getElementById("flask-passer").getAttribute("content"))
async function autoreply(){
    uri = `/api/${flaskData.guild.id}/settings`
    console.debug("Fetching " + uri)
    resp = await fetch(uri, { headers: { "authorization": document.cookie.match(/ token=(.+?);/)[1] } })
    if (resp.status === 403) {
        location.href = "/"
    }
    console.debug("Fetched")
    data = await resp.json()
    template = document.getElementById("autoreply-template")
    arTable = document.querySelector("#autoreply-table tbody")
    console.debug("Adding elements")
    for ([ari, [arb, arr]] of Object.entries(data.autoreply)) {
        newContent = template.content.cloneNode(true)
        newContent.querySelector(".autoreply-id span").innerHTML = ari
        newContent.querySelector(".autoreply-target textarea").value = arb
        newContent.querySelector(".autoreply-reply textarea").value = arr
        arTable.appendChild(newContent)
    }
}
async function main() {
    console.debug("%cLoading autoreply", "color:#0067e0")
    await autoreply()
    console.debug("%cDone", "color:#3ba55c")
    document.getElementById("loading").style.display = "none"
    document.getElementById("main").style.display = "block"
}

main().then(() => { })
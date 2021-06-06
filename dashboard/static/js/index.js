console.debug("%cLoaded: index.js", "color:#5865f2")
async function showGuilds() {
    console.debug("Fetching /api/servers")
    resp = await fetch("/api/servers", {
        headers: { "authorization": document.cookie.match(/ token=(.+?);/)[1] }
    })
    console.debug("Fetched")
    data = await resp.json()
    template = document.getElementById("server-list-content-template")
    serverList = document.getElementById("server-list-container")
    console.debug("Adding elements")
    for (server of data.manage) {
        newContent = template.content.cloneNode(true)
        newContent.querySelector(".server-list-name").innerHTML = server.name
        newContent.querySelector(".server-list-icon").src = (server.icon == null ? `https://cdn.discordapp.com/embed/avatars/${parseInt(server.id) % 6}.png` : `https://cdn.discordapp.com/icons/${server.id}/${server.icon}.${server.features.includes("ANIMATED_ICON") && server.icon.startsWith("a_") ? "gif" : "webp"}`)
        newContent.querySelector(".server-list-move a").href = "/manage/" + server.id
        newContent.querySelector(".server-list-invite").remove()
        serverList.appendChild(newContent)
    }
    for (server of data.invite) {
        newContent = template.content.cloneNode(true)
        newContent.querySelector(".server-list-name").innerHTML = server.name
        newContent.querySelector(".server-list-icon").src = (server.icon == null ? `https://cdn.discordapp.com/embed/avatars/${parseInt(server.id) % 6}.png` : `https://cdn.discordapp.com/icons/${server.id}/${server.icon}.${server.features.includes("ANIMATED_ICON") && server.icon.startsWith("a_") ? "gif" : "webp"}`)
        newContent.querySelector(".server-list-invite a").href = "/invite?guild_id=" + server.id
        newContent.querySelector(".server-list-move").remove()
        serverList.appendChild(newContent)
    }
    [...Array(data.manage.length + data.invite.length)].map(() => {
        serverList.innerHTML += `<div class="server-list-dummy"></div>`
    })
    document.getElementById("server-list-loading").style.display = "none"
}

function main() {
    if (document.getElementById("server-list-container")) {
        console.debug("%cShowing guild list", "color:#0067e0")
        showGuilds().then(() => { })
        console.debug("%cDone", "color:#3ba55c")
    }
}

main()
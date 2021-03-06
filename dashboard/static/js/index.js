console.debug("%cLoaded: index.js", "color:#5865f2")
async function showGuilds() {
  console.debug("Fetching /api/servers")
  resp = await fetch("/api/servers", {
    headers: {
      "authorization": document.cookie.match(/(?: |^)token=(.+?);/)[1]
    }
  })
  if (resp.status === 401) {
    document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    location.href = "/"
    return
  }
  console.debug("Fetched")
  data = await resp.text()
  data = JSON.parse(data)
  template = document.getElementById("server-list-content-template")
  serverList = document.getElementById("server-list-container")
  console.debug("Adding elements")
  for (server of data.manage) {
    newContent = template.content.cloneNode(true)
    newContent.querySelector(".server-list-name").innerHTML = server.name
    newContent.querySelector(".server-list-icon").src = (
      server.icon == null ?
      `https://cdn.discordapp.com/embed/avatars/${parseInt(server.id) % 6}.png?size=512` :
      `https://cdn.discordapp.com/icons/${server.id}/${server.icon}.${server.features.includes("ANIMATED_ICON") && server.icon.startsWith("a_") ? "gif" : "webp"}?size=512`)
    newContent.querySelector(".server-list-move a").href = "/manage/" + server.id
    newContent.querySelector(".server-list-invite").remove()
    serverList.insertBefore(newContent, serverList.childNodes[serverList.childNodes.length - 2])
  }
  for (server of data.invite) {
    newContent = template.content.cloneNode(true)
    newContent.querySelector(".server-list-name").innerHTML = server.name
    newContent.querySelector(".server-list-icon").src = (
      server.icon == null ?
      `https://cdn.discordapp.com/embed/avatars/${parseInt(server.id) % 6}.png?size=512` :
      `https://cdn.discordapp.com/icons/${server.id}/${server.icon}.${server.features.includes("ANIMATED_ICON") && server.icon.startsWith("a_") ? "gif" : "webp"}?size=512`)
    newContent.querySelector(".server-list-invite a").href = "/invite?guild_id=" + server.id
    newContent.querySelector(".server-list-move").remove()
    serverList.insertBefore(newContent, serverList.childNodes[serverList.childNodes.length - 2])
  }
  [...Array(data.manage.length + data.invite.length)].map(() => {
    serverList.innerHTML += `<div class="server-list-dummy"></div>`
  })
  document.getElementById("server-list-loading").style.display = "none"
  document.getElementById("server-list-container").style.display = "flex"
}

function main() {
  if (document.getElementById("server-list-container")) {
    console.debug("%cShowing guild list", "color:#0067e0")
    showGuilds().then(() => {})
    console.debug("%cDone", "color:#3ba55c")
  }
}

main()
flaskData = JSON.parse(document.getElementById("flask-passer").getAttribute("content"))

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
async function fetchGuildData() {
  id = flaskData.guild.id
  uri = `/api/guilds/${id}/settings`
  console.debug("%cFetching settings", "color:#5865f2")
  while (true) {
    resp = await fetch(uri, {
      headers: {
        "authorization": document.cookie.match(/ token=(.+?);/)[1]
      }
    })
    respJson = await resp.json()
    if (resp.status === 403 || resp.status === 401) {
      location.href = "/"
      return
    }
    if (resp.status === 200) {
      break
    }
    if (resp.status === 429) {
      await sleep(respJson.retry_after * 1000)
      continue
    }
  }
  console.debug("Fetched")
  return respJson
}

saveButton = document.querySelector("#save-container > .save-button")
if (saveButton) {
  saveButton.addEventListener("click", async function() {
    return save.bind(this)()
  })
}

fetchGuildData().then(async data => {
  await main(data)
})
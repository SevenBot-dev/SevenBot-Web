console.debug("%cLoaded: manage.js", "color:#5865f2")
arTemplate = document.getElementById("autoreply-template")
arTable = document.querySelector("#autoreply-table tbody")
arAddButton = document.getElementById("autoreply-add")

/**
 * ランダムな16進数を生成する。
 * @param {Integer} length 長さ。
 */
function genHex(length) {
  let hex = ""
  for (let i = 0; i < length; i++) {
    hex += Math.floor(Math.random() * 16).toString(16)
  }
  return hex
}
/**
 * 自動返信のUIを作成する。
 * @param {Object} data サーバーのデータ
 */
async function autoreply(data) {
  arAddButton.addEventListener("click", async () => {
    hex = genHex(8)
    while ([...arTable.querySelectorAll(`.autoreply_id span`)].filter(span => span.innerHTML == hex).length != 0) {
      hex = genHex(8)
    }
    addAutoreply(hex, "", "")
  })
  console.debug("Adding elements")
  if (Object.keys(data.autoreply).length == 0) {
    arTable.innerHTML = `
    <tr id="autoreply-add-message">
      <td colspan="4">
        自動返信はありません。下のボタンから追加してください。
      </td>
    </tr>
    `
  } else {
    for ([ari, [arb, arr]] of Object.entries(data.autoreply)) {
      addAutoreply(ari, arb, arr)
    }
  }
}
/**
 * 自動返信のテーブルに行を追加する。
 * @param {String} ari 自動返信のID
 * @param {String} arb 自動返信の条件
 * @param {String} arr 自動返信の内容
 */
function addAutoreply(ari, arb, arr) {
  newContent = arTemplate.content.cloneNode(true)
  newContent.querySelector(".autoreply-id span").innerHTML = ari
  newContent.querySelector(".autoreply-target textarea").value = arb
  newContent.querySelector(".autoreply-reply textarea").value = arr
  newContent.querySelector(".autoreply-delete").addEventListener("click", async function() {
    this.parentElement.remove()
    if (arTable.querySelectorAll("tr").length == 0) {
      arTable.innerHTML = `
      <tr id="autoreply-add-message">
        <td colspan="4">
          自動返信はありません。下のボタンから追加してください。
        </td>
      </tr>
      `
    }
  })
  if (document.getElementById("autoreply-add-message")) {
    document.getElementById("autoreply-add-message").remove()
  }
  arTable.appendChild(newContent)
}

async function main(data) {
  console.debug("%cLoading autoreply", "color:#0067e0")
  await autoreply(data)
  console.debug("%cDone", "color:#3ba55c")
  document.getElementById("loading").style.display = "none"
  document.getElementById("main").style.display = "block"
}

async function save() {
  if (this.classList.contains("disabled")) {
    showTooltip("現在クールダウン中です。", this, "white", 1000)
    return
  }
  console.debug("%cSaving autoreply", "color:#0067e0")
  rowData = [...arTable.querySelectorAll("tr")].map(tr => {
    return [
      tr.querySelector(".autoreply-id span").innerHTML,
      [
        tr.querySelector(".autoreply-target textarea").value,
        tr.querySelector(".autoreply-reply textarea").value
      ]
    ]
  })
  this.classList.add("disabled")
  resp = await fetch(`/api/guilds/${flaskData.guild.id}/settings/autoreply`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "authorization": document.cookie.match(/ token=(.+?);/)[1]
    },
    body: JSON.stringify({
      data: rowData
    })
  })
  resp_json = await resp.json()
  showTooltip(resp_json.message, this, (resp.ok ? "green" : "red"))
  setTimeout(() => {
      this.classList.remove("disabled")
    },
    resp_json.code === "ratelimited" ? resp_json.retry_after * 1000 : 5000)
  if (resp_json.code === "invalid_data") {
    arTable.querySelectorAll(".table-error").forEach(e => {
      e.classList.remove("table-error")
    })
    arTable.querySelectorAll(".autoreply-id span").forEach(e => {
      if (resp_json.failures[e.innerHTML]) {
        for (fail of resp_json.failures[e.innerHTML]) {
          e.parentElement.parentElement.classList.add("table-error-bg")
          targetColumn = e.parentElement.parentElement.querySelector(`.autoreply-${fail[1]}`)
          targetColumn.classList.add("table-error")
          showTooltip(fail[2], targetColumn, "red", 3000)
        }
      }
    })

  }
}
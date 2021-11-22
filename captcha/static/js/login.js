target = document.getElementsByClassName('h-captcha')[0]

async function checked(records) {
  response = await fetch("/check", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    redirect: 'follow',
    body: JSON.stringify({
      token: document.getElementsByClassName('h-captcha')[0].childNodes[0].attributes.getNamedItem("data-hcaptcha-response").value,
      id: (new URL(document.location)).searchParams.get("id")
    })
  })
  responseData = await response.json()
  if (response.status == 200 && responseData["success"]) {
    location.href = "/success"
  }
}
document.getElementById("not-working").addEventListener("click", checked)
ptarget = document.getElementsByClassName('h-captcha')[0]
pobserver = new MutationObserver(records => {
  target = document.getElementsByClassName('h-captcha')[0].childNodes[0]
  observer = new MutationObserver(checked)
  config = {
    attributes: true,
    attributeFilter: ['data-hcaptcha-response']
  }
  observer.observe(target, config)
  pobserver.disconnect()
})
pconfig = {
  childList: true
}
pobserver.observe(ptarget, pconfig)
target = document.getElementsByClassName('h-captcha')[0]

async function checked(records) {
    const response = await fetch("https://captcha.sevenbot.jp/check", {
        method: 'POST',
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer',
        body: JSON.stringify({
            token: document.getElementsByClassName('h-captcha')[0].childNodes[0].attributes.getNamedItem("data-hcaptcha-response").value,
            sessionid: (new URL(document.location)).searchParams.get("id")
        })
    })
    if (response.status == 200) {
        if (response.json()["success"]) {
            location.href = "https://captcha.sevenbot.jp/success"
        }
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
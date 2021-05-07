target = document.getElementsByClassName('h-captcha')[0]

function checked(records) {
    if (document.getElementsByClassName('h-captcha')[0].childNodes[0].attributes.getNamedItem("data-hcaptcha-response").nodeValue != "") {
        xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function(e) {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    if (JSON.parse(xhr.response)["success"]) {
                        location.href = "https://captcha.sevenbot.jp/success"
                    }
                }
            }
        }
        xhr.open('POST', "https://captcha.sevenbot.jp/check?token=" + document.getElementsByClassName('h-captcha')[0].childNodes[0].attributes.getNamedItem("data-hcaptcha-response").value + "&sessionid=" + (new URL(document.location)).searchParams.get("id"))
        xhr.send();
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
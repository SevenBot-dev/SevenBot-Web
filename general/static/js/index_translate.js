var language = (window.navigator.languages && window.navigator.languages[0]) ||
  window.navigator.language ||
  window.navigator.userLanguage ||
  window.navigator.browserLanguage;


if (language != "ja") {
  window.addEventListener("load", () => {
    const TRANSLATES = {
      ".top-features:nth-child(2) .top-features-content .top-features-title": "Tired of changing your keyboard?",
      ".top-features:nth-child(2) .top-features-content .top-features-desc": 'Are you tired of typing "!", "?", and ":"?' + "<br>" +
        'Prefix of this bot is "#" and ".", so you don`t have to change your keyboard!' + "<br>" +
        '(No matter your server have some channels named "#help"; you can use ".")' + "<br>" +
        '<span class="light">(Keyboard by: <a href="https://twitter.com/cat-atto" target="blank">AttoCat(@cat_atto)</a>)</span>',

      ".top-features:nth-child(3) .top-features-content .top-features-title": "Want a strange greets?",
      ".top-features:nth-child(3) .top-features-content .top-features-desc": 'Do you want to make bot greet with strange words?' + "<br>" +
        'YOU can make your original greets!' + "<br>" +
        'Of course, you don`t have to use it for only greets(Like: Message like "Please do these:").' + "<br>" +
        '<span class="light">(This image is from: <a href="https://discord.gg/M2VcGerSKn" target="blank">🐢超 雑談鯖</a>)</span>',

      ".top-features:nth-child(4) .top-features-content .top-features-title": "Want to tell reason of your afk?",
      ".top-features:nth-child(4) .top-features-content .top-features-desc": 'Do you want to tell reason of your afk?' + "<br>" +
        'You can tell your reason of your afk!' + "<br>" +
        'And you can see place where you got pinged!',

      "#top-invite div h1": 'Did you get intersted?',
      "#top-invite div a": 'Invite from here!',
    }
    for ([key, value] of Object.entries(TRANSLATES)) {
      try {
        document.querySelector(key).innerHTML = value
      } catch {}
    }
  })
}
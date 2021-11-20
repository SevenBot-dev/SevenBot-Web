const ANIME_LENGTH = 500

var lefts = Array.from(document.getElementsByClassName('--slideleft'));
var ups = Array.from(document.getElementsByClassName('--slideup'));
var rights = Array.from(document.getElementsByClassName('--slideright'));
var fades = Array.from(document.getElementsByClassName('--fade'));
window.addEventListener("load", function() {

  lefts = Array.from(document.getElementsByClassName('--slideleft'));
  ups = Array.from(document.getElementsByClassName('--slideup'));
  rights = Array.from(document.getElementsByClassName('--slideright'));
  fades = Array.from(document.getElementsByClassName('--fade'));

  function in_window(e) {
    rc = e.getBoundingClientRect();
    return window.scrollY < (rc.top) && (rc.top) < window.scrollY + window.innerHeight;
  }
  var CheckVisibility = function() {

    var bottom = document.documentElement.scrollTop + document.documentElement.clientHeight;

    function do_slide(l) {
      return (in_window(l) || l.classList.contains("--onload")) && !l.classList.contains("--animated");
    };
    lefts.forEach(function(l) {
      if (do_slide(l)) {
        l.classList.add('--animated');
        l.animate({
          transform: ["translateX(-100%)", "translateX(0%)"]
        }, {
          duration: ANIME_LENGTH,
          easing: "ease-out",
          fill: "forwards"
        });
      }
    });
    ups.forEach(function(l) {


      if (do_slide(l)) {
        l.classList.add('--animated');
        l.animate({
          transform: ["translateY(100%)", "translateY(0%)"],
          opacity: [0, 1]
        }, {
          duration: ANIME_LENGTH,
          easing: "ease-out",
          fill: "forwards"
        });
      }
    });
    rights.forEach(function(l) {

      if (do_slide(l)) {
        l.classList.add('--animated');
        l.animate({
          transform: ["translateX(100%)", "translateX(0%)"]
        }, {
          duration: ANIME_LENGTH,
          easing: "ease-out",
          fill: "forwards"
        });
      }
    });
    fades.forEach(function(l) {

      if (do_slide(l)) {
        l.classList.add('--animated');

        l.animate({
          opacity: [0, 1]
        }, {
          duration: ANIME_LENGTH,
          easing: "ease-out",
          fill: "forwards"
        });
      }
    });
  };



  window.setTimeout(CheckVisibility, 0);
  document.addEventListener("scroll", CheckVisibility);

  lefts.forEach(function(l) {
    l.style.transform = "translateX(-100%)";
  });
  rights.forEach(function(l) {
    l.style.transform = "translateX(100%)";
  });
  ups.forEach(function(l) {
    l.style.transform = "translateY(100%)";
  });
  fades.forEach(function(l) {
    l.style.opacity = 0;

  });
});
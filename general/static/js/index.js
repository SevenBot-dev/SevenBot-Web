function noScroll() {

    document.addEventListener("mousewheel", scrollControl, { passive: false });
    document.body.style.overflowY = "hidden";
    document.addEventListener("touchmove", scrollControl, { passive: false });
}

function returnScroll() {

    document.removeEventListener("mousewheel", scrollControl, { passive: false });
    document.body.style.overflowY = "visible";
    document.removeEventListener('touchmove', scrollControl, { passive: false });
}


function scrollControl(event) {
    event.preventDefault();
}


if (document.cookie.replace(/(?:(?:^|.*;\s*)animated\s*\=\s*([^;]*).*$)|^.*$/, "$1") === "true") {
    si = document.getElementById("sb-img");
    si.setAttribute("style", "mask-image: linear-gradient(0deg, rgba(0, 0, 0, 0) 0%, rgb(255, 255, 255) 25%, rgb(255, 255, 255) 100%);")
    si.setAttribute("style", "-webkit-mask-image: linear-gradient(0deg, rgba(0, 0, 0, 0) 0%, rgb(255, 255, 255) 25%, rgb(255, 255, 255) 100%);")
    returnScroll()
} else {
    noScroll();
    document.cookie = "animated=true; expires=Fri, 31 Dec 9999 23:59:59 GMT";

    window.scrollTo(0, 0);
    sc = document.getElementById("scroll-sign");


    sc.style.opacity = 0;
    setTimeout(function() {
        returnScroll();
        sc.animate({
            opacity: [0, 1]
        }, { duration: 1000, easing: "ease-out", fill: "both" }).finished.then(() => { sc.style.opacity = 1 });
        si = document.getElementById("sb-img");

        i = 0
        anime = setInterval(() => {
            // console.log(si, i)
            i += 0.1
            si.setAttribute("style", "mask-image: linear-gradient(0deg, rgba(0, 0, 0, 0) 0%, rgb(255, 255, 255) " + i + "%, rgb(255, 255, 255) 100%);")
            si.setAttribute("style", "-webkit-mask-image: linear-gradient(0deg, rgba(0, 0, 0, 0) 0%, rgb(255, 255, 255) " + i + "%, rgb(255, 255, 255) 100%);")
            if (i > 25) {
                clearInterval(anime)
            }
        }, 4)


    }, 3000);
    // sc.addEventListener("click",function(){
    // window.scrollTo(0,window.innerHeight,{
    // behavior: "smooth"
    // });
    // 		
    // });}
}
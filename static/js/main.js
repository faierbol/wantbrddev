$(function() {
    $('.match').matchHeight();
});

// sticky header
function init() {
    window.addEventListener('scroll', function(e){
        var distanceY = window.pageYOffset || document.documentElement.scrollTop,
            shrinkOn = 100,
            header = document.querySelector("header#main");
        if (distanceY > shrinkOn) {
            classie.add(header,"shrink");
        } else {
            if (classie.has(header,"shrink")) {
                classie.remove(header,"shrink");
            }
        }
    });
}
window.onload = init();


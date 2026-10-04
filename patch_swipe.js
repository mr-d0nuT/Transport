const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

const swipeCode = `
/* --- SWIPE GESTURES & HAPTIC FEEDBACK --- */
document.addEventListener('touchstart', handleTouchStart, false);
document.addEventListener('touchmove', handleTouchMove, false);
document.addEventListener('touchend', handleTouchEnd, false);

let xDown = null;
let yDown = null;
let swipeTarget = null;

function handleTouchStart(evt) {
    const firstTouch = evt.touches[0];
    xDown = firstTouch.clientX;
    yDown = firstTouch.clientY;
    
    // Only target arrival rows or journey cards
    const el = evt.target.closest('.arr-row, .jcard');
    if (el) swipeTarget = el;
    else swipeTarget = null;
}

function handleTouchMove(evt) {
    if (!xDown || !yDown || !swipeTarget) return;

    let xUp = evt.touches[0].clientX;
    let yUp = evt.touches[0].clientY;
    let xDiff = xDown - xUp;
    let yDiff = yDown - yUp;

    if (Math.abs(xDiff) > Math.abs(yDiff) && Math.abs(xDiff) > 50) { // Horizontal swipe
        evt.preventDefault();
        swipeTarget.style.transform = \`translateX(\${-xDiff}px)\`;
    }
}

function handleTouchEnd(evt) {
    if (!xDown || !swipeTarget) return;
    
    let xUp = evt.changedTouches[0].clientX;
    let xDiff = xDown - xUp;
    
    if (xDiff > 100) {
        // Swipe left
        if (navigator.vibrate) navigator.vibrate(10);
        swipeTarget.style.transition = 'transform 0.3s ease';
        swipeTarget.style.transform = 'translateX(-100%)';
        setTimeout(() => {
            if (swipeTarget) swipeTarget.style.display = 'none';
        }, 300);
        showTripAlert("Línea ocultada temporalmente");
    } else if (xDiff < -100) {
        // Swipe right
        if (navigator.vibrate) navigator.vibrate(10);
        swipeTarget.style.transition = 'transform 0.3s ease';
        swipeTarget.style.transform = 'translateX(0)';
        showTripAlert("Alarma configurada. Te avisaremos en breve.");
    } else {
        // Cancel swipe
        swipeTarget.style.transition = 'transform 0.3s ease';
        swipeTarget.style.transform = 'translateX(0)';
    }
    
    // reset
    xDown = null;
    yDown = null;
    swipeTarget = null;
}
`;

app += '\n' + swipeCode;
fs.writeFileSync('app.js', app);

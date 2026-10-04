// Bottom sheet drag logic
document.addEventListener('DOMContentLoaded', () => {
    const sheet = document.getElementById('bottomSheet');
    const dragHandle = sheet.querySelector('.sheet-drag-handle');
    const sheetContent = sheet.querySelector('.sheet-content');
    
    // Set base height to 85vh so it can be dragged up
    sheet.style.height = '85vh';
    
    // States (in pixels from the top of the sheet to its resting point)
    // 0 = fully expanded (85vh)
    // mid = partially expanded (e.g. 50vh visible)
    // min = collapsed (only search bar visible, e.g. 15vh visible)
    let state = 'mid'; 
    let currentY = 0;
    let startY = 0;
    let initialTranslateY = 0;
    
    const getViewportHeight = () => window.innerHeight;
    
    const updateSnapPoints = () => {
        const vh = getViewportHeight();
        const sheetH = vh * 0.85; // 85vh
        return {
            max: 0,                           // Fully expanded
            mid: sheetH - (vh * 0.45),        // 45vh visible
            min: sheetH - 120                 // ~120px visible (just search bar & handle)
        };
    };
    
    const isDesktop = () => window.matchMedia("(min-width: 700px)").matches;

    const setY = (y, animate) => {
        if (isDesktop()) { sheet.style.transform = ''; return; }
        sheet.style.transition = animate ? 'transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1)' : 'none';
        sheet.style.transform = `translateY(${y}px)`;
        currentY = y;
    };
    
    // Initialize
    if (!isDesktop()) setY(updateSnapPoints().mid, false);
    
    // Handle Touch & Mouse
    let isDragging = false;
    
    const onStart = (e) => {
        if (isDesktop()) return;
        const isHandle = e.target.closest?.('.sheet-drag-handle');
        if (!isHandle && sheetContent.scrollTop > 0) return;
        
        isDragging = true;
        startY = e.touches ? e.touches[0].clientY : e.clientY;
        initialTranslateY = currentY;
        sheet.style.transition = 'none';
    };
    
    const onMove = (e) => {
        if (!isDragging || isDesktop()) return;
        
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        const dy = clientY - startY;
        
        if (!e.target.closest?.('.sheet-drag-handle') && dy > 0 && sheetContent.scrollTop > 0) {
            isDragging = false;
            return;
        }
        if (!e.target.closest?.('.sheet-drag-handle') && dy < 0 && initialTranslateY <= updateSnapPoints().max) {
            isDragging = false;
            return;
        }
        
        if (isDragging && e.cancelable) {
            e.preventDefault(); 
        }
        
        let newY = initialTranslateY + dy;
        const snaps = updateSnapPoints();
        
        if (newY < snaps.max) newY = snaps.max - (snaps.max - newY) * 0.2;
        if (newY > snaps.min) newY = snaps.min + (newY - snaps.min) * 0.2;
        
        setY(newY, false);
    };
    
    const onEnd = (e) => {
        if (!isDragging || isDesktop()) return;
        isDragging = false;
        
        const snaps = updateSnapPoints();
        const dy = currentY - initialTranslateY;
        
        let targetY = currentY;
        if (dy < -30) {
            if (initialTranslateY === snaps.min) targetY = snaps.mid;
            else targetY = snaps.max;
        } else if (dy > 30) {
            if (initialTranslateY === snaps.max) targetY = snaps.mid;
            else targetY = snaps.min;
        } else {
            const distMax = Math.abs(currentY - snaps.max);
            const distMid = Math.abs(currentY - snaps.mid);
            const distMin = Math.abs(currentY - snaps.min);
            if (distMax < distMid && distMax < distMin) targetY = snaps.max;
            else if (distMid < distMin) targetY = snaps.mid;
            else targetY = snaps.min;
        }
        
        setY(targetY, true);
    };
    
    sheet.addEventListener('touchstart', onStart, { passive: true });
    sheet.addEventListener('touchmove', onMove, { passive: false });
    sheet.addEventListener('touchend', onEnd);
    
    sheet.addEventListener('mousedown', onStart);
    window.addEventListener('mousemove', onMove, { passive: false });
    window.addEventListener('mouseup', onEnd);
    
    window.addEventListener('resize', () => {
        if (isDesktop()) { sheet.style.transform = ''; sheet.style.height = ''; }
        else { sheet.style.height = '85vh'; setY(updateSnapPoints().mid, false); }
    });
});

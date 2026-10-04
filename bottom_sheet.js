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
    
    const setY = (y, animate) => {
        sheet.style.transition = animate ? 'transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1)' : 'none';
        sheet.style.transform = `translateY(${y}px)`;
        currentY = y;
    };
    
    // Initialize
    setY(updateSnapPoints().mid, false);
    
    // Handle Touch
    let isDragging = false;
    
    const onTouchStart = (e) => {
        // Only allow dragging from the handle OR if we are dragging down and at scrollTop 0
        const isHandle = e.target.closest?.('.sheet-drag-handle');
        if (!isHandle && sheetContent.scrollTop > 0) return;
        
        isDragging = true;
        startY = e.touches[0].clientY;
        initialTranslateY = currentY;
        sheet.style.transition = 'none';
    };
    
    const onTouchMove = (e) => {
        if (!isDragging) return;
        
        const dy = e.touches[0].clientY - startY;
        
        // If dragging down from content but not at top, ignore
        if (!e.target.closest?.('.sheet-drag-handle') && dy > 0 && sheetContent.scrollTop > 0) {
            isDragging = false;
            return;
        }
        // If dragging up from content and sheet is fully expanded, let it scroll
        if (!e.target.closest?.('.sheet-drag-handle') && dy < 0 && initialTranslateY <= updateSnapPoints().max) {
            isDragging = false;
            return;
        }
        
        // Prevent scrolling content while dragging sheet
        if (isDragging && e.cancelable) {
            e.preventDefault(); 
        }
        
        let newY = initialTranslateY + dy;
        const snaps = updateSnapPoints();
        
        // Resist going above max or below min
        if (newY < snaps.max) newY = snaps.max - (snaps.max - newY) * 0.2; // Rubber band effect
        if (newY > snaps.min) newY = snaps.min + (newY - snaps.min) * 0.2;
        
        setY(newY, false);
    };
    
    const onTouchEnd = (e) => {
        if (!isDragging) return;
        isDragging = false;
        
        const snaps = updateSnapPoints();
        const dy = currentY - initialTranslateY;
        
        // Determine closest snap point based on direction and distance
        let targetY = currentY;
        
        if (dy < -30) {
            // Dragged up
            if (initialTranslateY === snaps.min) targetY = snaps.mid;
            else targetY = snaps.max;
        } else if (dy > 30) {
            // Dragged down
            if (initialTranslateY === snaps.max) targetY = snaps.mid;
            else targetY = snaps.min;
        } else {
            // Snap to closest
            const distMax = Math.abs(currentY - snaps.max);
            const distMid = Math.abs(currentY - snaps.mid);
            const distMin = Math.abs(currentY - snaps.min);
            
            if (distMax < distMid && distMax < distMin) targetY = snaps.max;
            else if (distMid < distMin) targetY = snaps.mid;
            else targetY = snaps.min;
        }
        
        setY(targetY, true);
    };
    
    sheet.addEventListener('touchstart', onTouchStart, { passive: true });
    sheet.addEventListener('touchmove', onTouchMove, { passive: false });
    sheet.addEventListener('touchend', onTouchEnd);
});

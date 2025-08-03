// Direct scroll functions that will be called from inline HTML attributes
function scrollToBottom() {
    console.log('scrollToBottom function called');
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
    return false; // Prevent default behavior
}

function scrollToTop() {
    console.log('scrollToTop function called');
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
    return false; // Prevent default behavior
}

// Make functions available globally
window.scrollToBottom = scrollToBottom;
window.scrollToTop = scrollToTop;

// For backward compatibility - attach listeners via JavaScript as well
document.addEventListener('DOMContentLoaded', function() {
    console.log('Attaching click handlers to scroll buttons');
    
    const scrollToBottomBtn = document.getElementById('scroll-to-bottom');
    const scrollToTopBtn = document.getElementById('scroll-to-top');
    
    if (scrollToBottomBtn) {
        console.log('Bottom button found, attaching event');
        scrollToBottomBtn.onclick = function(e) {
            e.preventDefault();
            scrollToBottom();
            return false;
        };
    }
    
    if (scrollToTopBtn) {
        console.log('Top button found, attaching event');
        scrollToTopBtn.onclick = function(e) {
            e.preventDefault();
            scrollToTop();
            return false;
        };
    }
});

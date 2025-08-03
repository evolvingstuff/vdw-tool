/**
 * LightSPA - Lightweight Single Page Application for Hugo sites
 * 
 * A minimal SPA implementation that handles client-side navigation while preserving
 * state (search, scroll position) and maintaining browser history.
 * 
 * Features:
 * - Client-side navigation without page reloads
 * - Preserves search index and state between pages
 * - Maintains browser history and scroll positions
 * - Handles internal/external links appropriately
 * - Efficient content caching in history state
 * 
 * Usage:
 * 1. Add role="main" to your main content area:
 *    <main role="main">{{ .Content }}</main>
 * 
 * 2. Add data-spa-nav to navigation regions (optional):
 *    <nav data-spa-nav>...</nav>
 * 
 * 3. Initialize LightSPA:
 *    const spa = new LightSPA({
 *      mainContentSelector: 'main[role="main"]',  // Content area selector
 *      navigationSelector: '[data-spa-nav]'       // Navigation area selector
 *    });
 * 
 * Events:
 * - 'spaContentUpdated': Fired after content updates, with detail: { url, pushState }
 * 
 * State Management:
 * - Each state includes: url, title, content, scrollPosition, index
 * - Content is cached to avoid refetching
 * - Scroll positions are preserved during back/forward navigation
 */
class LightSPA {
    constructor(config = {}) {
        // Default configuration
        this.config = {
            mainContentSelector: 'main[role="main"]',
            navigationSelector: '[data-spa-nav]',
            ...config
        };

        // Store bound handler for proper removal
        this.boundHandleClick = this.handleClick.bind(this);
        this.init();
    }

    /**
     * Initialize the SPA
     * Sets up event listeners and saves initial state
     */
    init() {
        // Store references to key DOM elements
        this.mainContent = document.querySelector(this.config.mainContentSelector);
        this.navigationElements = document.querySelectorAll(this.config.navigationSelector);
        this.searchResults = document.getElementById('search-results');

        if (!this.mainContent) {
            console.warn('LightSPA: Main content element not found');
            return;
        }

        // Handle initial state and back/forward navigation
        window.addEventListener('popstate', (e) => this.handlePopState(e));

        // Handle all internal link clicks
        document.addEventListener('click', this.boundHandleClick);

        // Save initial state with a flag indicating it's the SPA session start
        const initialState = {
            url: window.location.href,
            title: document.title,
            content: this.mainContent.innerHTML,
            scrollPosition: { x: window.scrollX, y: window.scrollY },
            isInitialState: true,
            index: 0
        };
        console.log('Saving initial state:', initialState);
        history.replaceState(initialState, document.title, window.location.href);
        this.currentIndex = 0;
    }

    initializeEventListeners() {
        // Only handle search results since document handler covers everything else
        if (this.searchResults && !this.searchResults.dataset.spaInitialized) {
            this.searchResults.dataset.spaInitialized = 'true';
        }
    }

    /**
     * Handle internal link clicks
     * @param {Event} e - The click event
     */
    async handleClick(e) {
        const link = e.target.closest('a');
        if (!link) return;

        // Skip SPA navigation for links with data-no-spa attribute
        if (link.hasAttribute('data-no-spa')) {
            return;
        }
        
        // Skip SPA navigation for non-HTML resources (PDFs, images, etc.)
        const href = link.getAttribute('href');
        const fileExtension = href.split('.').pop().toLowerCase();
        const nonHtmlExtensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'];
        
        if (this.isInternalLink(link)) {
            // Non-HTML file links should open in a new tab
            if (nonHtmlExtensions.includes(fileExtension)) {
                // Set target="_blank" and security attributes
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                return; // Let the browser handle the click naturally
            }
            
            e.preventDefault();
            await this.navigateTo(link.href);
        } else {
            // Ensure external links open in new tab
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
        }
    }

    /**
     * Determines if a link points to a page on the same domain
     * @param {HTMLAnchorElement} link - The link element to check
     * @returns {boolean} True if the link's host matches the current page's host
     */
    isInternalLink(link) {
        return link.host === window.location.host;
    }

    /**
     * Navigate to a new URL using AJAX
     * @param {string} url - The URL to navigate to
     */
    async navigateTo(url, pushState = true) {
        console.log('navigateTo: Check point 1')
        // Prevent duplicate navigation to the same URL
        if (url === window.location.href && !pushState) {
            console.log('Preventing duplicate navigation to:', url);
            return;
        }
        console.log('check point 2')

        console.log('[navigateTo] Starting navigation to:', url, 'pushState:', pushState);
        
        // Check for URL fixer function - FAIL EXPLICITLY if missing
        if (typeof window.fixUrl !== 'function') {
            const errorMsg = 'CRITICAL ERROR: window.fixUrl function not found. ' +
                'Check that tiki-redirects.js is loaded before lightspa.js or navigation will fail.';
            console.error(errorMsg);
            
            // Display error to user and stop navigation
            const mainContent = document.querySelector('[role="main"]');
            if (mainContent) {
                const errorDiv = document.createElement('div');
                errorDiv.style.color = 'red';
                errorDiv.style.padding = '20px';
                errorDiv.style.margin = '20px';
                errorDiv.style.border = '2px solid red';
                errorDiv.innerHTML = `<h2>Navigation Error</h2><p>${errorMsg}</p>`;
                mainContent.prepend(errorDiv);
            }
            
            throw new Error(errorMsg);
        }
        
        // Fix URL before navigation
        const originalUrl = url;
        const fixedUrl = window.fixUrl(url);
        console.log('[navigateTo] fixUrl returned:', fixedUrl, 'original was:', url);
        if (fixedUrl !== url) {
            console.log('[navigateTo] URL was modified by fixUrl');
            url = fixedUrl;
        }

        console.log('[navigateTo] Final URL for navigation:', url, 'original was:', originalUrl);
        console.log('[navigateTo] pushState:', pushState, 'currentIndex:', this.currentIndex);
        
        // Extract hash fragment if present
        const urlObj = new URL(url);
        const hash = urlObj.hash;
        
        try {
            // Show loading state
            this.mainContent.style.opacity = '0.5';
            
            // Fetch new page content
            const response = await fetch(url);
            
            // Handle 404 errors by opening 404.html in a new tab
            if (response.status === 404) {
                console.log('404 error encountered, opening 404.html in new tab');
                
                // Open 404.html in a new tab while preserving current SPA state
                window.open(window.location.origin + '/404.html', '_blank');
                
                // Return SPA to normal state but keep the URL in history
                this.mainContent.style.opacity = '1';
                
                // Can optionally add a small message in the current view
                this.mainContent.innerHTML += '<div style="margin-top: 20px; text-align: center;"><p>The requested page was not found. A 404 page has been opened in a new tab.</p></div>';
                
                return;
            }
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const html = await response.text();

            // Create a temporary element to parse the HTML
            const doc = new DOMParser().parseFromString(html, 'text/html');
            const newContent = doc.querySelector(this.config.mainContentSelector);

            if (!newContent) {
                throw new Error('Could not find main content in new page');
            }

            // Update the page
            this.mainContent.innerHTML = newContent.innerHTML;
            document.title = doc.title;

            // Update browser history
            if (pushState) {
                const state = {
                    url: url,
                    title: document.title,
                    content: this.mainContent.innerHTML,
                    scrollPosition: { x: 0, y: 0 }, // Reset scroll for new pages
                    index: ++this.currentIndex
                };
                console.log('Pushing new state:', state);
                history.pushState(state, document.title, url);
                
                // Only scroll to top if there's no hash
                if (!hash) {
                    window.scrollTo(0, 0); // Scroll to top for new pages
                }
            }

            // Restore opacity
            this.mainContent.style.opacity = '1';

            // Re-initialize only our SPA event listeners
            this.initializeEventListeners();
            
            // Handle hash navigation after content is loaded
            if (hash) {
                // Try to find the element with the ID from the hash
                const hashElement = document.getElementById(hash.substring(1));
                if (hashElement) {
                    // Use a slight delay to ensure content is fully rendered
                    setTimeout(() => {
                        hashElement.scrollIntoView({ behavior: 'smooth' });
                    }, 100);
                } else {
                    console.warn(`Element with ID ${hash.substring(1)} not found`);
                }
            }

            // Dispatch a custom event for content update
            const event = new CustomEvent('spaContentUpdated', {
                detail: { url, pushState }
            });
            document.dispatchEvent(event);
        } catch (error) {
            console.error('Navigation failed:', error);
            
            // For any error (including network errors), show the 404 page in a new tab
            console.log('Error during navigation, opening 404.html in new tab');
            window.open(window.location.origin + '/404.html', '_blank');
            
            // Return SPA to normal state
            this.mainContent.style.opacity = '1';
            
            // Add a small message in the current view
            this.mainContent.innerHTML += '<div style="margin-top: 20px; text-align: center;"><p>The requested page could not be loaded. A 404 page has been opened in a new tab.</p></div>';
        }
    }

    /**
     * Handle browser back/forward navigation
     */
    async handlePopState(event) {
        console.log('PopState event:', event.state);
        
        // If no state, use current URL
        if (!event.state) {
            console.log('No state, using current URL:', window.location.href);
            await this.navigateTo(window.location.href, false);
            return;
        }

        // Update our current index
        this.currentIndex = event.state.index;
        console.log('Updated index to:', this.currentIndex);
        
        // Update content directly from state if available
        if (event.state.content) {
            document.title = event.state.title;
            this.mainContent.innerHTML = event.state.content;
            
            // Restore scroll position if available
            if (event.state.scrollPosition) {
                console.log('Restoring scroll position:', event.state.scrollPosition);
                window.scrollTo(event.state.scrollPosition.x, event.state.scrollPosition.y);
            }
            return;
        }

        // Otherwise fetch the page
        console.log('Fetching content for:', event.state.url);
        await this.navigateTo(event.state.url, false);
    }

    // Helper to get initial state
    getInitialState() {
        return {
            url: window.location.href,
            title: document.title,
            content: this.mainContent.innerHTML,
            scrollPosition: { x: window.scrollX, y: window.scrollY },
            isInitialState: true,
            index: 0
        };
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LightSPA;
} else {
    // Make available globally when not in module environment
    window.LightSPA = LightSPA;
}

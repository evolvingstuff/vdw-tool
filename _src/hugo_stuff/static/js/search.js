/**
 * Search functionality for Hugo site using Pagefind
 * Handles search initialization, execution, and results display
 */

class Search {
    constructor(config = {}) {
        this.config = {
            searchInputId: 'search-input',
            searchResultsPanelId: 'search-results-panel',
            searchResultsListId: 'search-results-list',
            searchStatusId: 'search-status',
            ...config
        };
        
        // Reference to key DOM elements
        this.searchInput = document.getElementById(this.config.searchInputId);
        this.searchStatus = document.getElementById(this.config.searchStatusId);
        
        // Create search UI elements if they don't exist
        this.createSearchUI();
        
        // State tracking
        this.pagefindInitialized = false;
        this.isResultsPanelVisible = false;
        
        // Disable search until Pagefind is initialized
        if (this.searchInput) {
            this.searchInput.disabled = true;
            this.searchInput.placeholder = 'Loading search...';
        }
        
        if (this.searchStatus) {
            this.searchStatus.textContent = 'Initializing search...';
            this.searchStatus.style.display = 'block';
        }
        
        // Make the search instance available globally for module script to access
        window.searchInstance = this;
        
        // Initialize event listeners
        this.initializeEventListeners();
        
        console.log('Search instance created, waiting for Pagefind initialization');
    }
    
    /**
     * Create search UI elements if they don't exist
     */
    createSearchUI() {
        // Check if search results panel exists
        this.resultsPanel = document.getElementById(this.config.searchResultsPanelId);
        
        if (!this.resultsPanel) {
            console.log('Creating search results panel elements');
            
            // Create the panel
            this.resultsPanel = document.createElement('div');
            this.resultsPanel.id = this.config.searchResultsPanelId;
            this.resultsPanel.className = 'search-results-panel';
            
            // Add a header to the panel with "Search Results" text
            const resultsHeader = document.createElement('div');
            resultsHeader.className = 'results-header';
            resultsHeader.textContent = 'Search Results';
            this.resultsPanel.appendChild(resultsHeader);
            
            // Add results list container
            this.searchResultsList = document.createElement('ul');
            this.searchResultsList.id = this.config.searchResultsListId;
            this.searchResultsList.className = 'results-list';
            
            // Add close button
            const closeButton = document.createElement('button');
            closeButton.className = 'search-results-close';
            closeButton.textContent = '×';
            closeButton.setAttribute('aria-label', 'Close search results');
            closeButton.onclick = () => this.hideSearchResults();
            
            // Assemble the panel
            this.resultsPanel.appendChild(closeButton);
            this.resultsPanel.appendChild(this.searchResultsList);
            
            document.body.appendChild(this.resultsPanel);
            console.log('Search results panel added to DOM');
        } else {
            // Get the existing results list
            console.log('Found existing search results panel');
            this.searchResultsList = document.getElementById(this.config.searchResultsListId);
            
            if (!this.searchResultsList) {
                console.warn('Results list not found inside panel - creating it');
                this.searchResultsList = document.createElement('ul');
                this.searchResultsList.id = this.config.searchResultsListId;
                this.searchResultsList.className = 'results-list';
                this.resultsPanel.appendChild(this.searchResultsList);
            }
        }
        
        // Add debug info to DOM elements for easier inspection
        if (this.resultsPanel) {
            this.resultsPanel.setAttribute('data-initialized', 'true');
        }
        if (this.searchResultsList) {
            this.searchResultsList.setAttribute('data-initialized', 'true');
        }
        
        // Set initial visibility
        if (this.resultsPanel) {
            this.resultsPanel.style.display = 'none';
            this.isResultsPanelVisible = false;
            console.log('Initialized search results panel, initially hidden');
        }
    }

    /**
     * Called by the module script once Pagefind is loaded and initialized
     */
    initializePagefind(pagefindInstance) {
        if (!pagefindInstance) {
            throw new Error('Invalid Pagefind instance provided to initializePagefind');
        }
        
        console.log('Pagefind instance received in search.js');
        this.pagefind = pagefindInstance;
        this.pagefindInitialized = true;
        
        // Enable search now that Pagefind is ready
        if (this.searchInput) {
            this.searchInput.disabled = false;
            this.searchInput.placeholder = 'Search...';
        }
        
        if (this.searchStatus) {
            this.searchStatus.textContent = '';
            this.searchStatus.style.display = 'none';
        }
    }

    /**
     * Handle initialization errors in a consistent way
     */
    handleInitError(message) {
        console.error('Search initialization error:', message);
        if (this.searchStatus) {
            this.searchStatus.textContent = `Search unavailable: ${message}`;
            this.searchStatus.style.display = 'block';
        }
        if (this.searchInput) {
            this.searchInput.disabled = true;
            this.searchInput.placeholder = 'Search unavailable';
        }
    }
    
    /**
     * Show an error message in the search results
     */
    showError(message) {
        console.error('Search error:', message);
        
        if (this.searchResultsList) {
            // Clear existing results
            this.searchResultsList.innerHTML = '';
            
            const errorElement = document.createElement('li');
            errorElement.className = 'search-error';
            errorElement.textContent = message;
            errorElement.style.color = 'red';
            this.searchResultsList.appendChild(errorElement);
            
            // Show the panel
            this.showSearchResults();
        }
    }

    /**
     * Handle search input changes
     */
    handleSearch() {
        const query = this.searchInput.value.trim();
        
        // Show suggestions regardless of query length
        if (typeof getSuggestions === 'function') {
            this.showSuggestions(query);
        }
        
        // Only perform actual search if we have 2+ characters
        if (!query || query.length < 2) {
            this.hideSearchResults();
            return;
        }
        
        // Clear previous results
        if (this.searchResultsList) {
            this.searchResultsList.innerHTML = '';
        }
        
        // Always attempt the search - we'll handle initialization issues in performPagefindSearch
        this.performPagefindSearch(query);
    }
    
    /**
     * Simple method to show suggestions
     */
    showSuggestions(query) {
        const suggestions = getSuggestions(query);
        if (!suggestions || !suggestions.length) {
            this.hideSuggestions();
            return;
        }
        
        // Find or create suggestions container
        let suggestionsContainer = document.querySelector('.search-suggestions');
        if (!suggestionsContainer) {
            suggestionsContainer = document.createElement('div');
            suggestionsContainer.className = 'search-suggestions';
            document.body.appendChild(suggestionsContainer);
        }
        
        // Clear and fill with new suggestions
        suggestionsContainer.innerHTML = '';
        
        // Store reference to "this" for use in event handlers
        const self = this;
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion';
            item.textContent = suggestion;
            
            // Use addEventListener instead of onclick property
            item.addEventListener('click', function() {
                // Instead of replacing search input, append the suggestion
                const currentText = self.searchInput.value.trim();
                const terms = currentText.split(/\s+/);
                
                // If we have a partial term at the end, replace just that term
                if (currentText.endsWith(' ')) {
                    // If the current text ends with a space, just append the suggestion
                    self.searchInput.value = currentText + suggestion;
                } else if (terms.length >= 1) {
                    // Replace the last partial term with the selected suggestion
                    terms[terms.length - 1] = suggestion;
                    self.searchInput.value = terms.join(' ');
                } else {
                    // If there's nothing, just use the suggestion
                    self.searchInput.value = suggestion;
                }
                
                // Add a space after the suggestion to prepare for the next word
                self.searchInput.value += ' ';
                
                // Mark this suggestion as used to prevent future repetition
                if (typeof markSuggestionAsUsed === 'function') {
                    markSuggestionAsUsed(suggestion);
                }
                
                self.handleSearch();
                self.hideSuggestions();
                
                // Focus on the search input after selection
                self.searchInput.focus();
            });
            
            suggestionsContainer.appendChild(item);
        });
        
        // Show suggestions
        suggestionsContainer.style.display = 'block';
    }
    
    /**
     * Hide suggestions
     */
    hideSuggestions() {
        const suggestionsContainer = document.querySelector('.search-suggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }

    /**
     * Perform a search using Pagefind and display results
     */
    async performPagefindSearch(query) {
        console.log(`Performing Pagefind search for: "${query}"`);
        
        try {
            if (!window.pagefind) {
                throw new Error('Pagefind global object not available');
            }
            
            // Pagefind is available in the global scope even if our instance isn't initialized
            // This happens because window.pagefind is set by the ES module before our class is notified
            const pagefindToUse = this.pagefindInitialized ? this.pagefind : window.pagefind;
            
            const searchResults = await pagefindToUse.search(query);
            
            if (!searchResults) {
                throw new Error('Invalid search results from Pagefind');
            }
            
            console.log(`Pagefind found ${searchResults.results ? searchResults.results.length : 0} results`);
            
            if (!searchResults.results || searchResults.results.length === 0) {
                this.displayResults([]);
                return;
            }
            
            // Process the results to get full details
            const processPromises = searchResults.results.map(async (result) => {
                try {
                    return await result.data();
                } catch (error) {
                    console.error('Error processing Pagefind result:', error);
                    return null;
                }
            });
            
            // Wait for all results to be processed
            const processedResults = await Promise.all(processPromises);
            
            // Filter out any null results and display them
            const validResults = processedResults.filter(result => result !== null);
            console.log(`Successfully processed ${validResults.length} out of ${searchResults.results.length} results`);
            
            // Debug the structure of the first result
            if (validResults.length > 0) {
                console.log('First result structure:', Object.keys(validResults[0]));
            }
            
            this.displayResults(validResults);
            
        } catch (error) {
            console.error('Pagefind search error:', error);
            this.showError(`Search failed: ${error.message}`);
        }
    }

    /**
     * Display search results in the results panel
     */
    displayResults(results) {
        console.log(`Displaying ${results ? results.length : 0} search results`);
        
        // Check if we have the search results list element
        if (!this.searchResultsList) {
            console.error('Search results list element not found');
            // Try to recreate the UI
            this.createSearchUI();
            if (!this.searchResultsList) {
                console.error('Failed to create search results list');
                return;
            }
        }
    
        // Clear existing results
        this.searchResultsList.innerHTML = '';
    
        if (!results || results.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No results found';
            li.className = 'no-results';
            this.searchResultsList.appendChild(li);
            this.showSearchResults();
            return;
        }
        
        // Debug: let's see what's in the results
        console.log('First search result data:', JSON.stringify(results[0]).substring(0, 200) + '...');
        
        // Add results to the DOM
        results.forEach((data, index) => {
            console.log(`Processing result #${index + 1}`);
            
            if (!data || !data.url) {
                console.warn(`Result #${index + 1} is missing required data:`, data);
                return; // Skip invalid result
            }
            
            const li = document.createElement('li');
            const a = document.createElement('a');
            
            // Use URL and title from Pagefind results
            a.href = data.url;
            
            // Make sure we have a title, use URL as fallback
            let title = 'Untitled Page';
            if (data.meta && data.meta.title) {
                title = data.meta.title;
            } else if (data.title) {
                title = data.title;
            }
            a.textContent = title;
            
            // Add click handler to clear search when a result is clicked
            a.addEventListener('click', () => {
                // Use setTimeout to allow the navigation to start before clearing
                setTimeout(() => this.clearSearch(), 0);
            });
            
            li.appendChild(a);
            
            // Add excerpt if available
            if (data.excerpt) {
                const excerptDiv = document.createElement('div');
                excerptDiv.className = 'search-result-excerpt';
                excerptDiv.innerHTML = data.excerpt;
                li.appendChild(excerptDiv);
            }
            
            // Add to results list
            this.searchResultsList.appendChild(li);
            console.log(`Added result #${index + 1} to DOM: "${title.substring(0, 30)}..."`);
        });
        
        // Add a "Search powered by Pagefind" attribution at the bottom
        const attribution = document.createElement('li');
        attribution.className = 'search-attribution';
        attribution.textContent = 'Search powered by Pagefind';
        this.searchResultsList.appendChild(attribution);
        
        // Show the results panel
        this.showSearchResults();
        console.log('Results rendered and panel shown');
    }
    
    /**
     * Show the search results panel
     */
    showSearchResults() {
        if (this.resultsPanel) {
            console.log('Showing search results panel');
            this.resultsPanel.style.display = 'block';
            this.isResultsPanelVisible = true;
        } else {
            console.error('Cannot show results panel - element not found');
            // Try to recreate the panel as a fallback
            this.createSearchUI();
            if (this.resultsPanel) {
                this.resultsPanel.style.display = 'block';
                this.isResultsPanelVisible = true;
            }
        }
    }
    
    /**
     * Hide the search results panel
     */
    hideSearchResults() {
        if (this.resultsPanel) {
            this.resultsPanel.style.display = 'none';
            this.isResultsPanelVisible = false;
        }
    }
    
    /**
     * Clear search input and hide results
     */
    clearSearch() {
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        this.hideSearchResults();
        this.hideSuggestions(); // Also hide suggestions when clearing search
        
        // Reset used suggestions tracking when search is cleared
        if (typeof resetUsedSuggestions === 'function') {
            resetUsedSuggestions();
        }
    }

    /**
     * Set up all event listeners
     */
    initializeEventListeners() {
        // Search input handler
        if (this.searchInput) {
            // Handle input changes
            this.searchInput.addEventListener('input', () => {
                this.handleSearch();
            });
            
            // Show suggestions on focus
            this.searchInput.addEventListener('focus', () => {
                if (typeof getSuggestions === 'function') {
                    this.showSuggestions(this.searchInput.value.trim());
                }
            });
            
            // Handle Enter key
            this.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSearch();
                }
            });
        }
        
        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isResultsPanelVisible && 
                !e.target.closest('.search-container') && 
                !e.target.closest('.search-results-panel')) {
                this.hideSearchResults();
            }

            // Also hide suggestions when clicking outside
            if (!e.target.closest('.search-container') && 
                !e.target.closest('.search-suggestions')) {
                this.hideSuggestions();
            }
        });
        
        // Add ESC key handler to close search results
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isResultsPanelVisible) {
                this.hideSearchResults();
                if (this.searchInput) this.searchInput.blur();
            }
        });
    }
}

// Create search instance when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.search = new Search();
});
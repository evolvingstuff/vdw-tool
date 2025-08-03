// Global variable to store cooccurrences data - loaded once
let cooccurrencesData = null;
let displayToInternalMap = {}; // Map from display format to internal format
let internalToDisplayMap = {}; // Map from internal format to display format
let allTagsForCompletion = []; // Store all unique tags for completion (in display format)
let loadingPromise = null;
let usedSuggestions = new Set(); // Track suggestions that have already been used

// Function to load cooccurrences data
function loadCooccurrencesData() {
    if (loadingPromise) {
        return loadingPromise; // Return existing promise if already loading
    }
    
    loadingPromise = fetch('/js/cooccurrences.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load cooccurrences data: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Store original data
            cooccurrencesData = data;
            
            // Build mapping between internal and display formats
            buildTagMappings(data);
            
            console.log("Cooccurrences data loaded and mapping built successfully");
            return data;
        })
        .catch(error => {
            console.error("Error loading cooccurrences data:", error);
            // Reset the promise so we can try again later
            loadingPromise = null;
            throw error;
        });
    
    return loadingPromise;
}

// Build mapping between internal (#tag_with_underscores) and display formats (tag with spaces)
function buildTagMappings(data) {
    displayToInternalMap = {};
    internalToDisplayMap = {};
    const uniqueTagsSet = new Set();
    
    // Process each key in the original data
    for (const key in data) {
        if (data.hasOwnProperty(key)) {
            // Get display format: remove # and replace _ with spaces
            const displayFormat = key.replace(/^#/, '').replace(/_/g, ' ');
            
            // Store mappings
            displayToInternalMap[displayFormat] = key;
            internalToDisplayMap[key] = displayFormat;
            
            // Add to unique tags set
            uniqueTagsSet.add(displayFormat);
            
            // Process values: remove # and replace _ with spaces for each item
            data[key].forEach(value => {
                const valueDisplayFormat = value.replace(/^#/, '').replace(/_/g, ' ');
                displayToInternalMap[valueDisplayFormat] = value;
                internalToDisplayMap[value] = valueDisplayFormat;
                uniqueTagsSet.add(valueDisplayFormat);
            });
        }
    }
    
    // Convert to array and sort
    allTagsForCompletion = Array.from(uniqueTagsSet).sort();
}

// Track a suggestion as used (in display format)
function markSuggestionAsUsed(suggestion) {
    if (suggestion && suggestion.trim()) {
        usedSuggestions.add(suggestion.toLowerCase().trim());
    }
}

// Check if a suggestion has been used (in display format)
function hasBeenSuggested(suggestion) {
    return usedSuggestions.has(suggestion.toLowerCase().trim());
}

// Reset used suggestions tracking
function resetUsedSuggestions() {
    usedSuggestions.clear();
}

// Convert display format to internal format
function displayToInternal(displayTag) {
    return displayToInternalMap[displayTag] || null;
}

// Convert internal format to display format
function internalToDisplay(internalTag) {
    return internalToDisplayMap[internalTag] || null;
}

// Load cooccurrences data when the script runs
loadCooccurrencesData();

function getSuggestions(searchString) {
    // If no search string provided, return empty array
    if (!searchString || searchString.trim() === '') {
        return [];
    }
    
    // If cooccurrences data not loaded yet, return basic suggestions
    if (!cooccurrencesData) {
        console.log("Cooccurrences data not loaded yet, returning basic suggestions");
        return [
            'cancer',
            'diabetes',
            'pregnancy',
            'vitamin d'
        ].filter(suggestion => !hasBeenSuggested(suggestion));
    }
    
    // Parse the search string into terms (in display format)
    const terms = searchString.split(/\s+/).filter(term => term.trim() !== '');
    
    // Update used suggestions based on current search string
    terms.forEach(term => {
        if (term.trim()) {
            markSuggestionAsUsed(term);
        }
    });
    
    // Check if we're completing a word or suggesting a new tag
    const lastTerm = terms[terms.length - 1];
    const isCompletingWord = lastTerm && lastTerm.trim() !== '';
    
    if (isCompletingWord) {
        // If completing a word, get completion suggestions
        return getWordCompletionSuggestions(lastTerm);
    } else {
        // We have a trailing space, so the last term is complete
        // Get tag suggestions based on completed terms
        const completedTerms = terms.filter(term => term.trim() !== '');
        
        // If no valid search terms found, return empty array
        if (completedTerms.length === 0) {
            return [];
        }
        
        return getTagSuggestions(completedTerms);
    }
}

// Match partial input against full tag display names
// e.g. "skin can" should match "skin cancer"
function findMatchingTags(partialInput) {
    // If empty input, return empty array
    if (!partialInput || partialInput.trim() === '') {
        return [];
    }
    
    // Normalize input for comparison
    const normalizedInput = partialInput.toLowerCase();
    
    // Look for tags that match the partial input
    const matches = allTagsForCompletion.filter(tag => {
        // First check if the tag starts with the exact input
        if (tag.toLowerCase().startsWith(normalizedInput)) {
            return true;
        }
        
        // Next, check if this could be a multi-word tag match
        // Create a regex pattern that allows spaces between characters
        // For example, "skin can" would match "skin cancer"
        const words = normalizedInput.split(/\s+/);
        if (words.length > 1) {
            // Create pattern like "^skin.*can"
            const pattern = words.map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('.*');
            const regex = new RegExp('^' + pattern, 'i');
            return regex.test(tag);
        }
        
        return false;
    });
    
    return matches.filter(match => !hasBeenSuggested(match));
}

// Get word completion suggestions
function getWordCompletionSuggestions(partialWord) {
    if (!partialWord || partialWord.trim() === '') {
        return [];
    }
    
    // Find tags that match the partial input
    const matches = findMatchingTags(partialWord);
    
    // Filter out exact match and used suggestions
    const filteredMatches = matches.filter(match => 
        match.toLowerCase() !== partialWord.toLowerCase() && 
        !hasBeenSuggested(match)
    );
    
    // Limit results to avoid overwhelming the UI
    return filteredMatches.slice(0, 20);
}

// Get tag suggestions based on search terms (in display format)
function getTagSuggestions(searchTerms) {
    // If no terms or data not loaded, return empty array
    if (searchTerms.length === 0 || !cooccurrencesData) {
        return [];
    }
    
    // Create a normalized version of the search terms for matching
    const normalizedSearchTerms = searchTerms.map(term => term.toLowerCase());
    
    // Mark all search terms as used
    searchTerms.forEach(term => markSuggestionAsUsed(term));
    
    // Try to find internal tag format for each display term
    const matchedInternalTags = [];
    
    // First, try to find exact matches for each term
    for (const term of searchTerms) {
        // Look for exact match
        const displayFormat = findMatchingTags(term)[0];
        if (displayFormat) {
            const internalTag = displayToInternal(displayFormat);
            if (internalTag) {
                matchedInternalTags.push(internalTag);
            }
        }
    }
    
    // If we have matched tags, get suggestions
    if (matchedInternalTags.length > 0) {
        // Start with suggestions from the first matched tag
        let suggestionsSet = new Set();
        let isFirst = true;
        
        for (const internalTag of matchedInternalTags) {
            const cooccurringTags = cooccurrencesData[internalTag] || [];
            
            if (isFirst) {
                // For first tag, add all co-occurring tags
                cooccurringTags.forEach(tag => suggestionsSet.add(tag));
                isFirst = false;
            } else {
                // For subsequent tags, find intersection
                const currentSet = new Set(cooccurringTags);
                suggestionsSet = new Set(
                    [...suggestionsSet].filter(tag => currentSet.has(tag))
                );
            }
        }
        
        // Convert internal suggestions to display format
        const displaySuggestions = [...suggestionsSet]
            .map(internalTag => internalToDisplay(internalTag))
            .filter(tag => tag !== null);
        
        // Filter out terms already in the search and any that have been used before
        return displaySuggestions.filter(suggestion => 
            !normalizedSearchTerms.includes(suggestion.toLowerCase()) && 
            !hasBeenSuggested(suggestion)
        );
    }
    
    // If no exact matches found, try matching against the last term
    const lastTerm = searchTerms[searchTerms.length - 1];
    const matchingTags = findMatchingTags(lastTerm);
    
    if (matchingTags.length > 0) {
        // Get the internal tag for the first match
        const internalTag = displayToInternal(matchingTags[0]);
        
        if (internalTag && cooccurrencesData[internalTag]) {
            // Get co-occurring tags in display format
            const suggestions = cooccurrencesData[internalTag]
                .map(tag => internalToDisplay(tag))
                .filter(tag => tag !== null);
                
            // Filter out terms already in the search and any that have been used before
            return suggestions.filter(suggestion => 
                !normalizedSearchTerms.includes(suggestion.toLowerCase()) && 
                !hasBeenSuggested(suggestion)
            );
        }
    }
    
    // If no matches found at all, return empty array
    return [];
}
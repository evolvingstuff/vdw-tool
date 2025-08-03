/**
 * TOC Structure Flattener
 * 
 * Removes unnecessary UL nesting in Hugo's automatically generated Table of Contents.
 * Specifically targets the pattern of UL > LI > UL where the LI has no content other
 * than another UL, which creates empty indentation levels.
 */
(function() {
    'use strict';

    function flattenTOC() {
        try {
            // Get the Table of Contents
            const toc = document.getElementById('TableOfContents');
            if (!toc) {
                console.warn('TOC Flattener: No TableOfContents found');
                return;
            }

            // Track whether we made any changes
            let changesCount = 0;

            // Keep flattening until no more unnecessary nesting is found
            let madeChanges;
            do {
                madeChanges = false;
                
                // Find all ULs in the TOC
                const ulElements = toc.querySelectorAll('ul');
                
                for (const ul of ulElements) {
                    // Check if this UL is a candidate for flattening:
                    // 1. It has exactly one LI child
                    // 2. That LI has exactly one child, which is another UL
                    // 3. The LI has no text content outside the nested UL
                    const liElements = ul.children;
                    
                    if (liElements.length === 1 && liElements[0].tagName === 'LI') {
                        const li = liElements[0];
                        const liChildren = Array.from(li.childNodes);
                        
                        // Filter to find actual content nodes (non-whitespace text or elements other than UL)
                        const contentNodes = liChildren.filter(node => {
                            if (node.nodeType === Node.TEXT_NODE) {
                                return node.textContent.trim() !== '';
                            }
                            return node.tagName !== 'UL';
                        });
                        
                        // Filter to find UL elements
                        const nestedUL = liChildren.find(node => 
                            node.nodeType === Node.ELEMENT_NODE && node.tagName === 'UL'
                        );
                        
                        // If we have no content nodes and exactly one UL,
                        // we can flatten this structure
                        if (contentNodes.length === 0 && nestedUL) {
                            // Replace the current UL with the nested UL's children
                            const fragment = document.createDocumentFragment();
                            Array.from(nestedUL.childNodes).forEach(node => {
                                fragment.appendChild(node.cloneNode(true));
                            });
                            
                            ul.parentNode.replaceChild(fragment, ul);
                            changesCount++;
                            madeChanges = true;
                            
                            // Break out of the loop since we modified the DOM
                            // and the querySelectorAll result is now stale
                            break;
                        }
                    }
                }
            } while (madeChanges);

            // Handle the special case of the initial bullet that might remain
            // If there's only one top-level UL with only LIs that contain links, flatten it
            const topUl = toc.querySelector(':scope > ul');
            if (topUl && topUl.children.length > 0) {
                // Check if all children are LIs with meaningful content (links)
                const allLisHaveContent = Array.from(topUl.children).every(child => {
                    return child.tagName === 'LI' && child.querySelector('a');
                });
                
                if (allLisHaveContent) {
                    // Replace the toc's content with the direct children of the UL
                    const fragment = document.createDocumentFragment();
                    Array.from(topUl.children).forEach(node => {
                        fragment.appendChild(node.cloneNode(true));
                    });
                    
                    // Clear and replace TOC content
                    toc.innerHTML = '';
                    toc.appendChild(fragment);
                    changesCount++;
                }
            }

            if (changesCount > 0) {
                console.log(`TOC Flattener: Removed ${changesCount} unnecessary nesting levels`);
            }
        } catch (error) {
            console.error('TOC Flattener Error:', error);
        }
    }

    // Function to initialize the flattener
    function initFlatten() {
        // Safety check for browser environment
        if (typeof window === 'undefined' || typeof document === 'undefined') {
            return;
        }

        try {
            flattenTOC();
        } catch (error) {
            console.error('TOC Flattener init error:', error);
        }
    }

    // Run after initial page load and DOM content is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFlatten);
    } else {
        initFlatten();
    }

    // Run after SPA navigation
    document.addEventListener('spaContentUpdated', function() {
        // Use requestAnimationFrame to ensure DOM is updated
        requestAnimationFrame(function() {
            // Double requestAnimationFrame ensures rendering is complete
            requestAnimationFrame(initFlatten);
        });
    });
})();
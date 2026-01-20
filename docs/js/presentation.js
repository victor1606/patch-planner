/**
 * PatchPlanner Reveal.js Presentation Configuration
 */

(function() {
    'use strict';

    // Initialize Reveal.js when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initReveal();
    });

    /**
     * Initialize Reveal.js with configuration
     */
    function initReveal() {
        Reveal.initialize({
            // Display settings
            hash: true,
            slideNumber: true,
            showNotes: false,
            
            // Navigation
            controls: true,
            progress: true,
            history: true,
            center: false,
            
            // Transitions
            transition: 'slide',
            backgroundTransition: 'fade',
            
            // Responsive settings
            width: '100%',
            height: '100%',
            margin: 0.1,
            minScale: 0.2,
            maxScale: 2.0,
            
            // Plugins
            plugins: [RevealNotes, RevealHighlight]
        });

        // Add custom event listeners
        addCustomEventListeners();
    }

    /**
     * Add custom event listeners for enhanced functionality
     */
    function addCustomEventListeners() {
        // Handle window resize for responsive adjustments
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                Reveal.layout();
            }, 250);
        });

        // Log slide changes (useful for analytics/debugging)
        Reveal.on('slidechanged', function(event) {
            console.log('Slide changed:', {
                indexh: event.indexh,
                indexv: event.indexv,
                previousSlide: event.previousSlide,
                currentSlide: event.currentSlide
            });
        });

        // Handle visibility change (pause/resume when tab is hidden/visible)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                Reveal.pause();
            } else {
                Reveal.resume();
            }
        });
    }

    /**
     * Utility: Toggle speaker notes visibility
     */
    window.toggleNotes = function() {
        const currentState = Reveal.getConfig().showNotes;
        Reveal.configure({ showNotes: !currentState });
    };

    /**
     * Utility: Jump to specific slide
     * @param {number} h - Horizontal index
     * @param {number} v - Vertical index (optional)
     */
    window.goToSlide = function(h, v) {
        Reveal.slide(h, v || 0);
    };

    /**
     * Utility: Get current slide info
     * @returns {Object} Current slide information
     */
    window.getCurrentSlideInfo = function() {
        const indices = Reveal.getIndices();
        return {
            horizontal: indices.h,
            vertical: indices.v,
            total: Reveal.getTotalSlides(),
            progress: Reveal.getProgress()
        };
    };

})();

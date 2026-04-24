// Wrapper to load noVNC RFB as ES module and expose to global scope
(async function() {
    try {
        // Try to load from local first
        let module;
        try {
            module = await import('/js/novnc/rfb.js');
        } catch (e) {
            console.warn('Failed to load local rfb.js, trying CDN...', e);
            // Fallback to CDN
            module = await import('https://cdn.jsdelivr.net/npm/novnc@1.4.0/core/rfb.js');
        }
        
        // Expose RFB to global scope
        window.RFB = module.default || module.RFB || module;
        console.log('noVNC RFB loaded successfully');
        
        // Dispatch custom event to notify that RFB is ready
        window.dispatchEvent(new CustomEvent('novnc:loaded', { detail: { RFB: window.RFB } }));
    } catch (error) {
        console.error('Failed to load noVNC RFB:', error);
        window.dispatchEvent(new CustomEvent('novnc:error', { detail: { error } }));
    }
})();


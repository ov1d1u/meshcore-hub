/**
 * MeshCore Hub - Notification Popup Handler
 * Manages displaying and storing user preferences for notification popups
 */

class NotificationPopup {
    constructor(cookieName = 'meshcore_notification_dismissed') {
        this.cookieName = cookieName;
        this.cookiePath = '/';
        this.cookieExpireDays = 365; // 1 year
    }

    /**
     * Set a cookie in the browser
     * @param {string} name - Cookie name
     * @param {string} value - Cookie value
     * @param {number} days - Days until expiration
     */
    setCookie(name, value, days = this.cookieExpireDays) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=${this.cookiePath}`;
    }

    /**
     * Get a cookie value from the browser
     * @param {string} name - Cookie name
     * @returns {string|null} Cookie value or null if not found
     */
    getCookie(name) {
        const nameEQ = `${name}=`;
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.indexOf(nameEQ) === 0) {
                return cookie.substring(nameEQ.length);
            }
        }
        return null;
    }

    /**
     * Check if popup has been dismissed
     * @returns {boolean} True if popup should not be shown
     */
    isDismissed() {
        return this.getCookie(this.cookieName) === 'true';
    }

    /**
     * Show the notification popup
     */
    show() {
        // Check if already dismissed
        if (this.isDismissed()) {
            return;
        }

        const popup = document.getElementById('notification-popup');
        const overlay = document.getElementById('notification-overlay');

        if (!popup || !overlay) {
            console.error('Notification popup elements not found');
            return;
        }

        // Show overlay and popup
        overlay.classList.remove('hidden');
        popup.classList.remove('hidden');

        // Set up event listeners
        this.setupEventListeners();
    }

    /**
     * Hide the notification popup
     * @param {boolean} dontShowAgain - If true, mark as dismissed and set cookie
     */
    hide(dontShowAgain = false) {
        const popup = document.getElementById('notification-popup');
        const overlay = document.getElementById('notification-overlay');

        if (!popup || !overlay) return;

        popup.classList.add('hidden');
        overlay.classList.add('hidden');

        if (dontShowAgain) {
            this.setCookie(this.cookieName, 'true', this.cookieExpireDays);
        }
    }

    /**
     * Set up event listeners for popup controls
     */
    setupEventListeners() {
        const closeBtn = document.getElementById('notification-close-btn');
        const checkbox = document.getElementById('notification-dont-show');
        const overlay = document.getElementById('notification-overlay');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                const dontShowAgain = checkbox ? checkbox.checked : false;
                this.hide(dontShowAgain);
            });
        }

        // Close on overlay click
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    const dontShowAgain = checkbox ? checkbox.checked : false;
                    this.hide(dontShowAgain);
                }
            });
        }

        // Prevent closing on popup click
        const popup = document.getElementById('notification-popup');
        if (popup) {
            popup.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }

    /**
     * Initialize and show popup on page load
     */
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.show());
        } else {
            this.show();
        }
    }
}

// Auto-initialize popup when script loads
const notificationPopup = new NotificationPopup();
notificationPopup.init();

/**
 * MeshCore Hub SPA - Notification Popup
 * Shows a one-time informational modal and stores dismissal in cookies.
 */

const COOKIE_NAME = 'meshcore_notification_dismissed';
const COOKIE_PATH = '/';
const COOKIE_EXPIRE_DAYS = 365;

function setCookie(name, value, days = COOKIE_EXPIRE_DAYS) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `expires=${date.toUTCString()}`;
    document.cookie = `${name}=${value};${expires};path=${COOKIE_PATH}`;
}

function getCookie(name) {
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

function isDismissed() {
    return getCookie(COOKIE_NAME) === 'true';
}

function ensureMarkup() {
    if (document.getElementById('notification-popup')) return;

    document.body.insertAdjacentHTML('beforeend', `
        <div id="notification-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-40 hidden transition-opacity duration-300"></div>
        <div id="notification-popup" class="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 hidden w-full max-w-md mx-4">
            <div class="bg-base-100 rounded-lg shadow-2xl p-6 border border-base-300">
                <h2 class="text-xl font-bold mb-4 text-base-content">
                    Iasi trece pe EU/UK Narrow
                </h2>
                <div class="prose prose-sm max-w-none mb-6 text-base-content">
                    <p>
                        In urma testelor care au dat rezultate mai bune pe presetul EU/UK Narrow, repeaterele Bucium-IS, Uricani-IS, etc. au fost trecute pe <b>EU/UK Narrow</b>. Consultati sectiunea Radio Configuration pentru parametrii de conectare.
                    </p>
                </div>
                <div class="form-control mb-6">
                    <label class="label cursor-pointer justify-end">
                        <span class="label-text">Do not show this again</span>
                        <input
                            id="notification-dont-show"
                            type="checkbox"
                            class="checkbox checkbox-sm ml-2"
                            aria-label="Do not show this message again"
                        />
                    </label>
                </div>
                <div class="flex justify-end">
                    <button
                        id="notification-close-btn"
                        class="btn btn-primary btn-sm"
                        aria-label="Close notification popup"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    `);
}

function hidePopup(dontShowAgain = false) {
    const popup = document.getElementById('notification-popup');
    const overlay = document.getElementById('notification-overlay');
    if (!popup || !overlay) return;

    popup.classList.add('hidden');
    overlay.classList.add('hidden');

    if (dontShowAgain) {
        setCookie(COOKIE_NAME, 'true', COOKIE_EXPIRE_DAYS);
    }
}

function setupEventListeners() {
    const popup = document.getElementById('notification-popup');
    if (!popup || popup.dataset.listenersAttached === 'true') return;
    popup.dataset.listenersAttached = 'true';

    const closeBtn = document.getElementById('notification-close-btn');
    const checkbox = document.getElementById('notification-dont-show');
    const overlay = document.getElementById('notification-overlay');

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            const dontShowAgain = checkbox ? checkbox.checked : false;
            hidePopup(dontShowAgain);
        });
    }

    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                const dontShowAgain = checkbox ? checkbox.checked : false;
                hidePopup(dontShowAgain);
            }
        });
    }

    popup.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

function showPopup() {
    if (isDismissed()) return;
    ensureMarkup();
    const popup = document.getElementById('notification-popup');
    const overlay = document.getElementById('notification-overlay');
    if (!popup || !overlay) return;
    overlay.classList.remove('hidden');
    popup.classList.remove('hidden');
    setupEventListeners();
}

export function initNotificationPopup() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', showPopup, { once: true });
    } else {
        showPopup();
    }
}

// backend/static/js/main.js

/**
 * Global helper to prevent .toFixed() crashes.
 * Usage: safeFixed(item.price, 2)
 */
function safeFixed(value, decimals = 2) {
    const num = parseFloat(value);
    if (isNaN(num)) return (0).toFixed(decimals);
    return num.toFixed(decimals);
}

function checkAuth() {
    const token = localStorage.getItem('access_token');
    const isLoginPage = window.location.pathname.includes('/login') || window.location.pathname === '/';

    if (!token && !isLoginPage) {
        window.location.href = '/login';
    } else if (token && isLoginPage) {
        window.location.href = '/dashboard';
    }
}

function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

function showNotification(message, type = 'success') {
    const toastHtml = `
        <div id="liveToast" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    let container = document.getElementById('notification-toast');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-toast';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }

    container.innerHTML = toastHtml;
    const toastElement = document.getElementById('liveToast');
    const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
    toast.show();
}

async function fetchAPI(url, options = {}) {
    const token = localStorage.getItem('access_token');
    options.headers = options.headers || {};
    
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    if (options.body && !options.headers['Content-Type']) {
        options.headers['Content-Type'] = 'application/json';
    }

    try {
        // Force leading slash to help prevent 404s on relative paths
        const cleanUrl = url.startsWith('/') ? url : `/${url}`;
        const response = await fetch(cleanUrl, options);
        
        if (response.status === 401) {
            showNotification('Session expired.', 'danger');
            logout();
            return null;
        }
        return response;
    } catch (error) {
        console.error('API Fetch Error:', error);
        showNotification('Network error.', 'danger');
        return null;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    const logoutBtn = document.getElementById('logout-button');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});
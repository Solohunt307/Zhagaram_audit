// backend/static/js/main.js

/**
 * Global function to check for the presence of a token.
 * Redirects to login if the token is missing, except on the login page itself.
 */
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const isLoginPage = window.location.pathname.includes('/login') || window.location.pathname === '/';

    if (!token && !isLoginPage) {
        // Token is missing, redirect to login
        window.location.href = '/login';
    } else if (token && isLoginPage) {
        // User is logged in and tries to access the login page, redirect to dashboard
        window.location.href = '/dashboard';
    }
}

/**
 * Global function to handle logout.
 */
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

/**
 * Global API fetch wrapper that automatically includes the Authorization header.
 */
async function fetchAPI(url, options = {}) {
    const token = localStorage.getItem('access_token');

    if (token) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };
    }

    try {
        const response = await fetch(url, options);
        
        // Handle 401 Unauthorized globally
        if (response.status === 401) {
            alert('Session expired or unauthorized. Please log in again.');
            logout();
            return null;
        }

        return response;
    } catch (error) {
        console.error('API Fetch Error:', error);
        return null;
    }
}

// Run the check when the page loads
document.addEventListener('DOMContentLoaded', checkAuth);

// Attach logout to any element with id="logout-button"
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logout-button');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});
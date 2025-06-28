/**
 * Dashboard Navigation Protection
 * Prevents authenticated users from navigating back to login/signup pages
 */

class DashboardNavigation {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupNavigation());
        } else {
            this.setupNavigation();
        }
    }

    setupNavigation() {
        // Prevent browser cache for authenticated pages
        this.preventCaching();
        
        // Handle browser back/forward navigation
        this.handleBrowserNavigation();
        
        // Handle page visibility changes
        this.handleVisibilityChange();
    }

    preventCaching() {
        // Set cache control headers via meta tags
        const metaTags = [
            { name: 'Cache-Control', content: 'no-cache, no-store, must-revalidate' },
            { name: 'Pragma', content: 'no-cache' },
            { name: 'Expires', content: '0' }
        ];

        metaTags.forEach(tag => {
            const meta = document.createElement('meta');
            meta.httpEquiv = tag.name;
            meta.content = tag.content;
            document.head.appendChild(meta);
        });
    }

    handleBrowserNavigation() {
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (event) => {
            // Get current page info
            const currentPath = window.location.pathname;
            
            // If user is on a dashboard page and tries to go back
            if (this.isDashboardPage(currentPath)) {
                // Prevent navigation to login/signup pages
                this.preventUnauthorizedNavigation();
            }
        });

        // Handle page load
        window.addEventListener('load', () => {
            // Mark that dashboard has been loaded
            if (typeof(Storage) !== "undefined") {
                sessionStorage.setItem('dashboardLoaded', 'true');
                sessionStorage.setItem('lastDashboardPath', window.location.pathname);
            }
        });

        // Handle page unload
        window.addEventListener('beforeunload', () => {
            // Clear session storage when leaving dashboard
            if (typeof(Storage) !== "undefined") {
                sessionStorage.removeItem('dashboardLoaded');
            }
        });
    }

    handleVisibilityChange() {
        // Handle when page becomes visible again (e.g., switching tabs)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isDashboardPage(window.location.pathname)) {
                // Verify user is still authenticated
                this.verifyAuthentication();
            }
        });
    }

    isDashboardPage(path) {
        const dashboardPaths = [
            '/student/dashboard/',
            '/driver/dashboard/',
            '/parent/dashboard/',
            '/admin/dashboard/',
            '/profile/',
            '/location_tracker/'
        ];
        
        return dashboardPaths.some(dashboardPath => path.includes(dashboardPath));
    }

    preventUnauthorizedNavigation() {
        // Get the last known dashboard path
        const lastDashboardPath = sessionStorage.getItem('lastDashboardPath') || '/';
        
        // Replace current history entry to prevent back navigation
        window.history.replaceState(null, '', lastDashboardPath);
        
        // Optionally show a message
        this.showNavigationMessage();
    }

    showNavigationMessage() {
        // Create a subtle notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        notification.textContent = 'You are already logged in';
        
        document.body.appendChild(notification);
        
        // Fade in
        setTimeout(() => notification.style.opacity = '1', 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }

    verifyAuthentication() {
        // Make a simple request to verify authentication status
        fetch('/profile/', {
            method: 'HEAD',
            credentials: 'same-origin'
        })
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                // User is no longer authenticated, redirect to login
                window.location.href = '/signin/';
            }
        })
        .catch(error => {
            console.warn('Authentication verification failed:', error);
        });
    }

    // Public method to redirect to appropriate dashboard
    static redirectToDashboard() {
        // This can be called from other scripts if needed
        fetch('/api/user-role/', {
            method: 'GET',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            const dashboardMap = {
                'student': '/student/dashboard/',
                'driver': '/driver/dashboard/',
                'parent': '/parent/dashboard/',
                'admin': '/admin/dashboard/'
            };
            
            const dashboardUrl = dashboardMap[data.role] || '/';
            window.location.href = dashboardUrl;
        })
        .catch(error => {
            console.error('Failed to get user role:', error);
            window.location.href = '/signin/';
        });
    }
}

// Initialize dashboard navigation protection
new DashboardNavigation();

// Export for use in other scripts
window.DashboardNavigation = DashboardNavigation;

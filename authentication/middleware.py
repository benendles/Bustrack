"""
Authentication Middleware for BusTrack Application
Provides enhanced session management, security, and route protection
"""

from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class SessionSecurityMiddleware:
    """
    Middleware to handle session security and automatic logout
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Session timeout in seconds (30 minutes)
        self.session_timeout = getattr(settings, 'SESSION_TIMEOUT', 1800)
        
    def __call__(self, request):
        # Process the request before the view
        self.process_request(request)
        
        response = self.get_response(request)
        
        # Process the response after the view
        return self.process_response(request, response)
    
    def process_request(self, request):
        """Process incoming request for session security"""
        
        if request.user.is_authenticated:
            # Check session timeout
            if self.is_session_expired(request):
                self.handle_session_timeout(request)
                return
            
            # Update last activity
            self.update_last_activity(request)
            
            # Check for concurrent sessions (optional)
            if getattr(settings, 'PREVENT_CONCURRENT_SESSIONS', False):
                self.check_concurrent_sessions(request)
    
    def process_response(self, request, response):
        """Process response for additional security headers"""

        # Add security headers for authenticated users
        if request.user.is_authenticated:
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-XSS-Protection'] = '1; mode=block'

            # Prevent caching of authenticated pages to avoid back button issues
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
    
    def is_session_expired(self, request):
        """Check if the user session has expired"""
        last_activity = request.session.get('last_activity')
        
        if not last_activity:
            return False
        
        try:
            last_activity_time = timezone.datetime.fromisoformat(last_activity)
            time_since_activity = timezone.now() - last_activity_time
            return time_since_activity.total_seconds() > self.session_timeout
        except (ValueError, TypeError):
            return True
    
    def handle_session_timeout(self, request):
        """Handle expired session"""
        logger.info(f"Session timeout for user: {request.user.username}")
        
        logout(request)
        messages.warning(
            request, 
            'Your session has expired due to inactivity. Please log in again.'
        )
    
    def update_last_activity(self, request):
        """Update the last activity timestamp"""
        request.session['last_activity'] = timezone.now().isoformat()
    
    def check_concurrent_sessions(self, request):
        """Check for concurrent sessions (optional feature)"""
        # This would require additional session tracking
        # Implementation depends on specific requirements
        pass


class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access control
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define role-based URL patterns
        self.role_patterns = {
            'student': [
                '/student/',
                '/api/update-location/',
                '/api/get-locations/',
            ],
            'driver': [
                '/driver/',
                '/api/update-location/',
                '/api/get-locations/',
            ],
            'parent': [
                '/parent/',
                '/api/get-locations/',
            ],
            'admin': [
                '/admin/',
                '/api/',
            ]
        }
        
        # URLs that don't require authentication
        self.public_urls = [
            '/',
            '/signin/',
            '/signup/',
            '/password_reset/',
            '/reset/',
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        # Check access before processing the view
        if not self.check_access(request):
            return self.handle_access_denied(request)
        
        response = self.get_response(request)
        return response
    
    def check_access(self, request):
        """Check if user has access to the requested URL"""
        path = request.path
        
        # Allow access to public URLs
        if any(path.startswith(url) for url in self.public_urls):
            return True
        
        # Require authentication for all other URLs
        if not request.user.is_authenticated:
            return False
        
        # Check role-based access
        user_role = getattr(request.user, 'role', None)
        
        if not user_role:
            return False
        
        # Admin has access to everything
        if user_role == 'admin':
            return True
        
        # Check if user's role has access to this URL pattern
        allowed_patterns = self.role_patterns.get(user_role, [])
        
        # Allow access to common URLs for all authenticated users
        common_urls = ['/profile/', '/signout/', '/location_tracker/']
        if any(path.startswith(url) for url in common_urls):
            return True
        
        # Check role-specific patterns
        return any(path.startswith(pattern) for pattern in allowed_patterns)
    
    def handle_access_denied(self, request):
        """Handle access denied scenarios"""
        if not request.user.is_authenticated:
            # Redirect to login with next parameter
            login_url = reverse('signin')
            return redirect(f"{login_url}?next={request.path}")
        
        # User is authenticated but doesn't have permission
        messages.error(
            request,
            "You don't have permission to access this page."
        )
        
        # Redirect to appropriate dashboard based on role
        user_role = getattr(request.user, 'role', None)
        dashboard_urls = {
            'student': 'student_dashboard',
            'driver': 'driver_dashboard',
            'parent': 'parent_dashboard',
            'admin': 'admin_dashboard',
        }
        
        dashboard_url = dashboard_urls.get(user_role, 'home')
        return redirect(dashboard_url)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for additional security
        if not settings.DEBUG:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            response['Content-Security-Policy'] = csp_policy
        
        return response


class RequestLoggingMiddleware:
    """
    Middleware to log authentication-related requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logged_paths = [
            '/signin/',
            '/signup/',
            '/signout/',
            '/admin/',
        ]
    
    def __call__(self, request):
        # Log before processing
        if any(request.path.startswith(path) for path in self.logged_paths):
            self.log_request(request)
        
        response = self.get_response(request)
        
        # Log after processing if needed
        if response.status_code in [401, 403, 404]:
            self.log_response(request, response)
        
        return response
    
    def log_request(self, request):
        """Log incoming authentication requests"""
        user_info = (
            f"User: {request.user.username}" 
            if request.user.is_authenticated 
            else "Anonymous"
        )
        
        logger.info(
            f"Auth Request - Path: {request.path}, "
            f"Method: {request.method}, "
            f"IP: {self.get_client_ip(request)}, "
            f"{user_info}"
        )
    
    def log_response(self, request, response):
        """Log authentication responses with errors"""
        if response.status_code in [401, 403]:
            logger.warning(
                f"Auth Error - Path: {request.path}, "
                f"Status: {response.status_code}, "
                f"IP: {self.get_client_ip(request)}, "
                f"User: {getattr(request.user, 'username', 'Anonymous')}"
            )
    
    def get_client_ip(self, request):
        """Get the client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

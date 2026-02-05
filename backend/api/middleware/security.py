"""
Security middleware for Flask application
Adds security headers and HTTPS enforcement
"""

from flask import request, redirect, Response
import logging

logger = logging.getLogger(__name__)

def add_security_headers(app):
    """
    Add security headers to all HTTP responses
    
    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS protection
    - Strict-Transport-Security: Force HTTPS (production only)
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    """
    
    @app.after_request
    def set_security_headers(response: Response) -> Response:
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS (force HTTPS) - only in production
        if not app.debug:
            response.headers['Strict-Transport-Security'] = \
                'max-age=31536000; includeSubDomains; preload'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = \
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
        
        # Permissions Policy (formerly Feature-Policy)
        response.headers['Permissions-Policy'] = \
            'geolocation=(), microphone=(), camera=()'
        
        return response
    
    @app.before_request
    def enforce_https():
        """Redirect HTTP to HTTPS in production"""
        if not app.debug and not request.is_secure:
            if request.url.startswith('http://'):
                url = request.url.replace('http://', 'https://', 1)
                logger.info(f"Redirecting HTTP to HTTPS: {url}")
                return redirect(url, code=301)
    
    logger.info("✅ Security headers middleware registered")
    
    return app


__all__ = ['add_security_headers']

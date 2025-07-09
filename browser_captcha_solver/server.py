#!/usr/bin/env python3
"""
HTTP Server Implementation for Browser-Based Captcha Solver
Handles browser communication and captcha page serving
"""

import logging
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs, unquote
from .template_manager import TemplateManager


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Thread-per-request HTTP server"""
    daemon_threads = True
    allow_reuse_address = True


class CaptchaHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for captcha solving communication"""
    
    def __init__(self, *args, solver_instance=None, **kwargs):
        self.solver = solver_instance
        self.template_manager = TemplateManager()
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        if self.solver and hasattr(self.solver, 'logger'):
            self.solver.logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            # Extract challenge ID from path or params
            challenge_id = params.get('id', [None])[0]
            do_action = params.get('do', [None])[0]
            
            # Handle CSS requests without challenge ID
            if parsed_url.path.endswith('.css'):
                self._serve_css()
                return
            
            if not challenge_id or not self.solver:
                self.send_error(404)
                return
                
            challenge = self.solver.get_challenge(challenge_id)
            if not challenge:
                self.send_error(404)
                return
            
            if do_action == 'loaded':
                self._handle_browser_loaded(challenge, params)
            elif do_action == 'canClose':
                self._handle_can_close(challenge)
            elif do_action == 'solve':
                self._handle_solve(challenge, params)
            elif do_action == 'unload':
                self._handle_unload(challenge)
            elif parsed_url.path.endswith('.js'):
                self._serve_javascript(challenge)
            elif parsed_url.path.endswith('.css'):
                self._serve_css()
            else:
                self._serve_captcha_page(challenge)
                
        except Exception as e:
            self.solver.logger.error(f"Error handling GET request: {e}")
            self.send_error(500)
    
    def do_POST(self):
        """Handle POST requests for ReCaptcha proxying"""
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            challenge_id = params.get('id', [None])[0]
            
            if not challenge_id or not self.solver:
                self.send_error(404)
                return
                
            challenge = self.solver.get_challenge(challenge_id)
            if not challenge:
                self.send_error(404)
                return
            
            # Handle ReCaptcha API proxying
            if '/recaptcha/api2/' in self.path:
                self._proxy_recaptcha_request(challenge)
            else:
                self.send_error(404)
                
        except Exception as e:
            self.solver.logger.error(f"Error handling POST request: {e}")
            self.send_error(500)
    
    def _handle_browser_loaded(self, challenge, params: Dict):
        """Handle browser loaded notification with positioning info"""
        browser_info = {
            'x': params.get('x', [0])[0],
            'y': params.get('y', [0])[0],
            'width': params.get('w', [0])[0],
            'height': params.get('h', [0])[0],
            'viewport_width': params.get('vw', [0])[0],
            'viewport_height': params.get('vh', [0])[0],
        }
        
        self.solver.logger.info(f"Browser loaded for challenge {challenge.id}: {browser_info}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def _handle_can_close(self, challenge):
        """Check if browser can be closed (captcha solved or expired)"""
        can_close = challenge.solved or challenge.is_expired()
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'true' if can_close else b'false')
    
    def _handle_solve(self, challenge, params: Dict):
        """Handle captcha solution submission"""
        response_token = params.get('response', [None])[0]
        
        if response_token:
            challenge.result = unquote(response_token)
            challenge.solved = True
            self.solver.logger.info(f"Captcha {challenge.id} solved with token: {response_token[:50]}...")
            
            # Notify solver of solution
            if hasattr(self.solver, '_on_captcha_solved'):
                self.solver._on_captcha_solved(challenge)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'<html><body><h2>Captcha Solved!</h2><p>You can close this window now.</p><script>setTimeout(function(){window.close();}, 2000);</script></body></html>')
    
    def _handle_unload(self, challenge):
        """Handle browser unload event"""
        self.solver.logger.info(f"Browser unloaded for challenge {challenge.id}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def _serve_javascript(self, challenge):
        """Serve JavaScript for browser communication"""
        js_content = self.template_manager.get_browser_communication_js()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(js_content.encode('utf-8'))
    
    def _serve_css(self):
        """Serve CSS styles"""
        css_content = self.template_manager.get_css_styles()
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/css; charset=utf-8')
        self.end_headers()
        self.wfile.write(css_content.encode('utf-8'))
    
    def _serve_captcha_page(self, challenge):
        """Serve the main captcha solving page"""
        if challenge.challenge_type == 'RecaptchaV2Challenge':
            html_content = self.template_manager.render_recaptcha_v2_page(challenge)
        elif challenge.challenge_type == 'RecaptchaV3Challenge':
            html_content = self.template_manager.render_recaptcha_v3_page(challenge)
        elif challenge.challenge_type == 'HCaptchaChallenge':
            html_content = self.template_manager.render_hcaptcha_page(challenge)
        elif challenge.challenge_type == 'TurnstileChallenge':
            html_content = self.template_manager.render_turnstile_page(challenge)
        else:
            html_content = self.template_manager.render_generic_captcha_page(challenge)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def _proxy_recaptcha_request(self, challenge):
        """Proxy ReCaptcha API requests to Google"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Extract the API path
            parsed_url = urlparse(self.path)
            api_path = parsed_url.path.replace(f'/captcha/recaptchav2/{challenge.host}', '')
            google_url = f"https://www.google.com{api_path}"
            
            if parsed_url.query:
                google_url += f"?{parsed_url.query}"
            
            # Forward to Google
            headers = {
                'Referer': f'http://{challenge.site_domain}',
                'User-Agent': self.headers.get('User-Agent', 'Mozilla/5.0'),
                'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
            }
            
            response = requests.post(google_url, data=post_data, headers=headers, timeout=30)
            
            # Modify response to work with our local server
            content = response.content
            if response.headers.get('Content-Type', '').startswith('application/javascript'):
                content = self._modify_recaptcha_js(content.decode('utf-8'), challenge).encode('utf-8')
            
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                if header.lower() not in ['connection', 'transfer-encoding']:
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.solver.logger.error(f"Error proxying ReCaptcha request: {e}")
            self.send_error(500)
    
    def _modify_recaptcha_js(self, js_content: str, challenge) -> str:
        """Modify ReCaptcha JavaScript to work with local server"""
        base_url = f"http://{self.headers.get('Host')}/captcha/recaptchav2/{challenge.host}/"
        
        # Replace Google URLs with local proxy URLs
        js_content = js_content.replace(
            'https://www.google.com/recaptcha/api2/',
            base_url + 'proxy/'
        )
        
        # Inject solution handler
        solve_handler = f"""
        function submitCaptchaSolution(token) {{
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '{base_url}?id={challenge.id}&do=solve&response=' + encodeURIComponent(token), true);
            xhr.send();
        }}
        """
        
        js_content += solve_handler
        return js_content

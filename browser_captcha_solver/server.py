"""
HTTP server module for handling captcha browser communication.
"""

import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, TYPE_CHECKING, Any, Optional
from urllib.parse import urlparse, parse_qs, unquote

if TYPE_CHECKING:
    from .solver import CaptchaChallenge


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Thread-per-request HTTP server"""

    daemon_threads = True
    allow_reuse_address = True


class CaptchaHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for captcha solving communication"""

    def __init__(self, *args: Any, solver_instance: Optional[Any] = None, **kwargs: Any) -> None:
        self.solver = solver_instance
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use our logger"""
        if self.solver and hasattr(self.solver, "logger"):
            self.solver.logger.info(f"{self.address_string()} - {format % args}")

    def do_GET(self) -> None:
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            # Extract challenge ID from path or params
            challenge_id = params.get("id", [None])[0]
            do_action = params.get("do", [None])[0]

            if not challenge_id or not self.solver:
                self.send_error(404)
                return

            challenge = self.solver.get_challenge(challenge_id)
            if not challenge:
                self.send_error(404)
                return

            if do_action == "loaded":
                self._handle_browser_loaded(challenge, params)
            elif do_action == "canClose":
                self._handle_can_close(challenge)
            elif do_action == "solve":
                self._handle_solve(challenge, params)
            elif do_action == "unload":
                self._handle_unload(challenge)
            elif parsed_url.path.endswith(".js"):
                self._serve_javascript(challenge)
            elif parsed_url.path.endswith(".css"):
                self._serve_css()
            else:
                self._serve_captcha_page(challenge)

        except Exception as e:
            if self.solver:
                self.solver.logger.error(f"Error handling GET request: {e}")
            self.send_error(500)

    def do_POST(self):
        """Handle POST requests for ReCaptcha proxying"""
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            challenge_id = params.get("id", [None])[0]

            if not challenge_id or not self.solver:
                self.send_error(404)
                return

            challenge = self.solver.get_challenge(challenge_id)
            if not challenge:
                self.send_error(404)
                return

            # Handle ReCaptcha API proxying
            if "/recaptcha/api2/" in self.path:
                self._proxy_recaptcha_request(challenge)
            else:
                self.send_error(404)

        except Exception as e:
            if self.solver:
                self.solver.logger.error(f"Error handling POST request: {e}")
            self.send_error(500)

    def _handle_browser_loaded(self, challenge: "CaptchaChallenge", params: Dict):
        """Handle browser loaded notification with positioning info"""
        browser_info = {
            "x": params.get("x", [0])[0],
            "y": params.get("y", [0])[0],
            "width": params.get("w", [0])[0],
            "height": params.get("h", [0])[0],
            "viewport_width": params.get("vw", [0])[0],
            "viewport_height": params.get("vh", [0])[0],
        }

        if self.solver:
            self.solver.logger.info(
                f"Browser loaded for challenge {challenge.id}: {browser_info}"
            )

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def _handle_can_close(self, challenge: "CaptchaChallenge"):
        """Check if browser can be closed (captcha solved or expired)"""
        can_close = challenge.solved or challenge.is_expired()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"true" if can_close else b"false")

    def _handle_solve(self, challenge: "CaptchaChallenge", params: Dict):
        """Handle captcha solution submission"""
        response_token = params.get("response", [None])[0]

        if response_token:
            challenge.result = unquote(response_token)
            challenge.solved = True
            if self.solver:
                self.solver.logger.info(
                    f"Captcha {challenge.id} solved with token: {response_token[:50]}..."
                )

                # Notify solver of solution
                if hasattr(self.solver, "_on_captcha_solved"):
                    self.solver._on_captcha_solved(challenge)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h2>Captcha Solved!</h2><p>You can close this window now.</p><script>setTimeout(function(){window.close();}, 2000);</script></body></html>"
        )

    def _handle_unload(self, challenge: "CaptchaChallenge"):
        """Handle browser unload event"""
        if self.solver:
            self.solver.logger.info(f"Browser unloaded for challenge {challenge.id}")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def _serve_javascript(self, challenge: "CaptchaChallenge"):
        """Serve JavaScript for browser communication"""
        js_content = self._get_browser_captcha_js(challenge)

        self.send_response(200)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(js_content.encode("utf-8"))

    def _serve_css(self):
        """Serve CSS styles"""
        css_content = """
        body { font-family: Arial, sans-serif; margin: 20px; }
        .captcha-container { max-width: 600px; margin: 0 auto; }
        .challenge-info { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .recaptcha-frame { width: 100%; height: 500px; border: none; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .status.solved { background: #d4edda; color: #155724; }
        .status.pending { background: #fff3cd; color: #856404; }
        """

        self.send_response(200)
        self.send_header("Content-Type", "text/css; charset=utf-8")
        self.end_headers()
        self.wfile.write(css_content.encode("utf-8"))

    def _serve_captcha_page(self, challenge: "CaptchaChallenge"):
        """Serve the main captcha solving page"""
        if challenge.challenge_type == "RecaptchaV2Challenge":
            html_content = self._get_recaptcha_html(challenge)
        elif challenge.challenge_type == "HCaptchaChallenge":
            html_content = self._get_hcaptcha_html(challenge)
        else:
            html_content = self._get_generic_captcha_html(challenge)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def _proxy_recaptcha_request(self, challenge: "CaptchaChallenge"):
        """Proxy ReCaptcha API requests to Google"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            # Extract the API path
            parsed_url = urlparse(self.path)
            api_path = parsed_url.path.replace(
                f"/captcha/recaptchav2/{challenge.host}", ""
            )
            google_url = f"https://www.google.com{api_path}"

            if parsed_url.query:
                google_url += f"?{parsed_url.query}"

            # Forward to Google
            headers = {
                "Referer": f"http://{challenge.site_domain}",
                "User-Agent": self.headers.get("User-Agent", "Mozilla/5.0"),
                "Content-Type": self.headers.get(
                    "Content-Type", "application/x-www-form-urlencoded"
                ),
            }

            response = requests.post(
                google_url, data=post_data, headers=headers, timeout=30
            )

            # Modify response to work with our local server
            content = response.content
            if response.headers.get("Content-Type", "").startswith(
                "application/javascript"
            ):
                content = self._modify_recaptcha_js(
                    content.decode("utf-8"), challenge
                ).encode("utf-8")

            self.send_response(response.status_code)
            for header, value in response.headers.items():
                if header.lower() not in ["connection", "transfer-encoding"]:
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            if self.solver:
                self.solver.logger.error(f"Error proxying ReCaptcha request: {e}")
            self.send_error(500)

    def _modify_recaptcha_js(
        self, js_content: str, challenge: "CaptchaChallenge"
    ) -> str:
        """Modify ReCaptcha JavaScript to work with local server"""
        base_url = (
            f"http://{self.headers.get('Host')}/captcha/recaptchav2/{challenge.host}/"
        )

        # Replace Google URLs with local proxy URLs
        js_content = js_content.replace(
            "https://www.google.com/recaptcha/api2/", base_url + "proxy/"
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

    def _get_recaptcha_html(self, challenge: "CaptchaChallenge") -> str:
        """Generate ReCaptcha HTML page"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ReCaptcha Challenge - {challenge.host}</title>
            <link rel="stylesheet" href="style.css">
            <script src="https://www.google.com/recaptcha/api.js" async defer></script>
        </head>
        <body>
            <div class="captcha-container">
                <div class="challenge-info">
                    <h2>Captcha Challenge</h2>
                    <p><strong>Host:</strong> {challenge.host}</p>
                    <p><strong>Type:</strong> {challenge.challenge_type}</p>
                    <p><strong>Timeout:</strong> {challenge.get_remaining_timeout()} seconds</p>
                </div>
                
                <div id="status" class="status pending">
                    Please solve the captcha below...
                </div>
                
                <div id="recaptcha-container">
                    <div class="g-recaptcha" 
                         data-sitekey="{challenge.site_key}"
                         data-callback="onCaptchaSolved"></div>
                </div>
            </div>
            
            <script>
                function onCaptchaSolved(token) {{
                    document.getElementById('status').className = 'status solved';
                    document.getElementById('status').textContent = 'Captcha solved! Submitting...';
                    
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', window.location.href + '&do=solve&response=' + encodeURIComponent(token), true);
                    xhr.onload = function() {{
                        if (xhr.status === 200) {{
                            document.getElementById('status').textContent = 'Success! You can close this window.';
                            setTimeout(function() {{ window.close(); }}, 2000);
                        }}
                    }};
                    xhr.send();
                }}
                
                // Browser communication script
                {self._get_browser_captcha_js(challenge)}
            </script>
        </body>
        </html>
        """

    def _get_hcaptcha_html(self, challenge: "CaptchaChallenge") -> str:
        """Generate hCaptcha HTML page"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>hCaptcha Challenge - {challenge.host}</title>
            <link rel="stylesheet" href="style.css">
            <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
        </head>
        <body>
            <div class="captcha-container">
                <div class="challenge-info">
                    <h2>hCaptcha Challenge</h2>
                    <p><strong>Host:</strong> {challenge.host}</p>
                    <p><strong>Type:</strong> {challenge.challenge_type}</p>
                    <p><strong>Timeout:</strong> {challenge.get_remaining_timeout()} seconds</p>
                </div>
                
                <div id="status" class="status pending">
                    Please solve the captcha below...
                </div>
                
                <div id="hcaptcha-container">
                    <div class="h-captcha" 
                         data-sitekey="{challenge.site_key}"
                         data-callback="onCaptchaSolved"></div>
                </div>
            </div>
            
            <script>
                function onCaptchaSolved(token) {{
                    document.getElementById('status').className = 'status solved';
                    document.getElementById('status').textContent = 'Captcha solved! Submitting...';
                    
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', window.location.href + '&do=solve&response=' + encodeURIComponent(token), true);
                    xhr.onload = function() {{
                        if (xhr.status === 200) {{
                            document.getElementById('status').textContent = 'Success! You can close this window.';
                            setTimeout(function() {{ window.close(); }}, 2000);
                        }}
                    }};
                    xhr.send();
                }}
                
                // Browser communication script
                {self._get_browser_captcha_js(challenge)}
            </script>
        </body>
        </html>
        """

    def _get_generic_captcha_html(self, challenge: "CaptchaChallenge") -> str:
        """Generate generic captcha HTML page"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Captcha Challenge - {challenge.host}</title>
            <link rel="stylesheet" href="style.css">
        </head>
        <body>
            <div class="captcha-container">
                <div class="challenge-info">
                    <h2>Captcha Challenge</h2>
                    <p><strong>Host:</strong> {challenge.host}</p>
                    <p><strong>Type:</strong> {challenge.challenge_type}</p>
                    <p><strong>Explain:</strong> {challenge.explain}</p>
                    <p><strong>Timeout:</strong> {challenge.get_remaining_timeout()} seconds</p>
                </div>
                
                <div id="status" class="status pending">
                    Manual captcha solving required...
                </div>
                
                <div>
                    <textarea id="response" placeholder="Enter captcha response here..." rows="4" cols="50"></textarea><br>
                    <button onclick="submitResponse()">Submit</button>
                </div>
            </div>
            
            <script>
                function submitResponse() {{
                    var response = document.getElementById('response').value;
                    if (!response) {{
                        alert('Please enter a response');
                        return;
                    }}
                    
                    document.getElementById('status').className = 'status solved';
                    document.getElementById('status').textContent = 'Submitting response...';
                    
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', window.location.href + '&do=solve&response=' + encodeURIComponent(response), true);
                    xhr.onload = function() {{
                        if (xhr.status === 200) {{
                            document.getElementById('status').textContent = 'Success! You can close this window.';
                            setTimeout(function() {{ window.close(); }}, 2000);
                        }}
                    }};
                    xhr.send();
                }}
                
                // Browser communication script
                {self._get_browser_captcha_js(challenge)}
            </script>
        </body>
        </html>
        """

    def _get_browser_captcha_js(self, challenge: "CaptchaChallenge") -> str:
        """Generate browser communication JavaScript for captcha integration"""
        return """
        // Browser positioning and communication functions
        function getOffsetSum(elem) {{
            var top = 0, left = 0;
            while (elem) {{
                top = top + parseInt(elem.offsetTop);
                left = left + parseInt(elem.offsetLeft);
                elem = elem.offsetParent;
            }}
            return {{ top: top, left: left }};
        }}
        
        function getOffsetRect(elem) {{
            var box = elem.getBoundingClientRect();
            var body = document.body;
            var docElem = document.documentElement;
            var scrollTop = window.pageYOffset || docElem.scrollTop || body.scrollTop;
            var scrollLeft = window.pageXOffset || docElem.scrollLeft || body.scrollLeft;
            var clientTop = docElem.clientTop || body.clientTop || 0;
            var clientLeft = docElem.clientLeft || body.clientLeft || 0;
            var top = box.top + scrollTop - clientTop;
            var left = box.left + scrollLeft - clientLeft;
            return {{ top: Math.round(top), left: Math.round(left) }};
        }}
        
        function getOffset(elem) {{
            if (elem.getBoundingClientRect) {{
                return getOffsetRect(elem);
            }} else {{
                return getOffsetSum(elem);
            }}
        }}
        
        function init(elem) {{
            var bounds = null;
            if (elem != null) {{
                bounds = elem.getBoundingClientRect();
            }}
            
            var xmlHttp = new XMLHttpRequest();
            var w = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
            var h = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
            var winLeft = window.screenLeft ? window.screenLeft : window.screenX;
            var winTop = window.screenTop ? window.screenTop : window.screenY;
            var windowWidth = window.outerWidth;
            var windowHeight = window.outerHeight;
            
            var url = window.location.href + "&do=loaded&x=" + winLeft + "&y=" + winTop + 
                      "&w=" + windowWidth + "&h=" + windowHeight + "&vw=" + w + "&vh=" + h;
            
            if (bounds) {{
                url += "&eleft=" + bounds.left + "&etop=" + bounds.top + 
                       "&ew=" + bounds.width + "&eh=" + bounds.height;
            }}
            
            xmlHttp.open("GET", url, true);
            xmlHttp.send();
        }}
        
        function unload() {{
            try {{
                var xhr = new XMLHttpRequest();
                xhr.open("GET", window.location.href + "&do=unload", true);
                xhr.timeout = 5000;
                xhr.send();
            }} catch (err) {{
                // Ignore errors
            }}
        }}
        
        function closeWindowOrTab() {{
            if (window.location.hash) return;
            
            console.log("Close browser");
            
            // Try different methods to close the window/tab
            try {{
                window.open('', '_self', '');
                window.close();
            }} catch (e) {{
                try {{
                    this.focus();
                    self.opener = this;
                    self.close();
                }} catch (e2) {{
                    // Last resort - just hide the content
                    document.body.innerHTML = '<h2>You can close this window now</h2>';
                }}
            }}
        }}
        
        function refresh() {{
            try {{
                var xhr = new XMLHttpRequest();
                xhr.onTimeout = closeWindowOrTab;
                xhr.onerror = closeWindowOrTab;
                
                xhr.onLoad = function() {{
                    if (xhr.status == 0) {{
                        closeWindowOrTab();
                    }} else if (xhr.responseText == "true") {{
                        closeWindowOrTab();
                    }} else {{
                        setTimeout(refresh, 1000);
                    }}
                }};
                
                xhr.onreadystatechange = function() {{
                    if (xhr.readyState == 4) {{
                        xhr.onLoad();
                    }}
                }};
                
                xhr.open("GET", window.location.href + "&do=canClose", true);
                xhr.timeout = 5000;
                xhr.send();
            }} catch (err) {{
                closeWindowOrTab();
            }}
        }}
        
        // Initialize when page loads
        window.addEventListener('load', function() {{
            init(document.querySelector('.g-recaptcha') || document.querySelector('.h-captcha'));
            setTimeout(refresh, 1000);
        }});
        
        // Handle page unload
        window.addEventListener("beforeunload", unload);
        """

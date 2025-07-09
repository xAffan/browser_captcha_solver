#!/usr/bin/env python3
"""
Browser-Based Captcha Solver Implementation
Advanced browser integration for automated captcha solving
"""

import logging
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass, field

from .server import ThreadingHTTPServer, CaptchaHTTPHandler


@dataclass
class CaptchaChallenge:
    """Represents a captcha challenge for browser-based solving"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    challenge_type: str = ""
    site_key: str = ""
    site_domain: str = ""
    secure_token: Optional[str] = None
    host: str = ""
    timeout: int = 300  # 5 minutes default
    created: datetime = field(default_factory=datetime.now)
    solved: bool = False
    result: Optional[str] = None
    explain: str = ""
    type_id: str = ""
    
    def get_remaining_timeout(self) -> int:
        """Returns remaining timeout in seconds"""
        elapsed = (datetime.now() - self.created).total_seconds()
        return max(0, int(self.timeout - elapsed))
    
    def is_expired(self) -> bool:
        """Check if challenge has expired"""
        return self.get_remaining_timeout() <= 0


@dataclass
class CaptchaJob:
    """Represents a captcha job for browser-based solving"""
    id: str
    challenge_type: str
    hoster: str
    captcha_category: str
    explain: str
    remaining: int
    timeout: int
    created: datetime
    link: Optional[str] = None


class CaptchaSolver:
    """Main captcha solver class with browser integration and HTTP server"""
    
    def __init__(self, port: int = 0, browser_command: Optional[str] = None):
        self.port = port
        self.browser_command = browser_command
        self.challenges: Dict[str, CaptchaChallenge] = {}
        self.server: Optional[ThreadingHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.solution_callbacks: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def start_server(self) -> int:
        """Start the HTTP server and return the actual port"""
        if self.server:
            return self.port
        
        # Create handler class with solver reference
        def handler_factory(*args, **kwargs):
            return CaptchaHTTPHandler(*args, solver_instance=self, **kwargs)
        
        self.server = ThreadingHTTPServer(('localhost', self.port), handler_factory)
        self.port = self.server.server_address[1]
        
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.logger.info(f"Captcha solver server started on port {self.port}")
        return self.port
    
    def stop_server(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
            self.server_thread = None
        
        self.logger.info("Captcha solver server stopped")
    
    def create_challenge(self, challenge_type: str, site_key: str, site_domain: str, 
                        host: str, **kwargs) -> CaptchaChallenge:
        """Create a new captcha challenge"""
        challenge = CaptchaChallenge(
            challenge_type=challenge_type,
            site_key=site_key,
            site_domain=site_domain,
            host=host,
            **kwargs
        )
        
        self.challenges[challenge.id] = challenge
        self.logger.info(f"Created challenge {challenge.id} for {host} ({challenge_type})")
        
        return challenge
    
    def get_challenge(self, challenge_id: str) -> Optional[CaptchaChallenge]:
        """Get challenge by ID"""
        return self.challenges.get(challenge_id)
    
    def solve_challenge(self, challenge: CaptchaChallenge, 
                       timeout: Optional[int] = None,
                       callback: Optional[Callable] = None) -> Optional[str]:
        """
        Solve a captcha challenge by opening it in the browser
        Returns the solution token or None if failed/timeout
        """
        if not self.server:
            self.start_server()
        
        # Set callback for solution notification
        if callback:
            self.solution_callbacks[challenge.id] = callback
        
        # Build captcha URL
        captcha_url = f"http://localhost:{self.port}/captcha/{challenge.challenge_type.lower()}/{challenge.host}/?id={challenge.id}"
        
        self.logger.info(f"Opening captcha URL: {captcha_url}")
        
        # Open browser
        self._open_browser(captcha_url)
        
        # Wait for solution
        return self._wait_for_solution(challenge, timeout or challenge.timeout)
    
    def _open_browser(self, url: str):
        """Open the captcha URL in browser"""
        try:
            if self.browser_command:
                import subprocess
                subprocess.Popen([self.browser_command, url])
                self.logger.info(f"Opened browser with command: {self.browser_command}")
            else:
                webbrowser.open(url)
                self.logger.info(f"Opened system default browser")
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
    
    def _wait_for_solution(self, challenge: CaptchaChallenge, timeout: int) -> Optional[str]:
        """Wait for the challenge to be solved"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if challenge.solved:
                self.logger.info(f"Challenge {challenge.id} solved!")
                return challenge.result
            
            if challenge.is_expired():
                self.logger.warning(f"Challenge {challenge.id} expired")
                break
            
            time.sleep(0.5)
        
        self.logger.warning(f"Challenge {challenge.id} timed out")
        return None
    
    def _on_captcha_solved(self, challenge: CaptchaChallenge):
        """Internal callback when captcha is solved"""
        callback = self.solution_callbacks.get(challenge.id)
        if callback:
            try:
                callback(challenge)
            except Exception as e:
                self.logger.error(f"Error in solution callback: {e}")
            finally:
                del self.solution_callbacks[challenge.id]
    
    def list_challenges(self) -> List[CaptchaJob]:
        """List all active challenges"""
        jobs = []
        for challenge in self.challenges.values():
            if not challenge.solved and not challenge.is_expired():
                job = CaptchaJob(
                    id=challenge.id,
                    challenge_type=challenge.challenge_type,
                    hoster=challenge.host,
                    captcha_category=challenge.type_id,
                    explain=challenge.explain,
                    remaining=challenge.get_remaining_timeout(),
                    timeout=challenge.timeout,
                    created=challenge.created
                )
                jobs.append(job)
        
        # Sort by timeout (most urgent first)
        jobs.sort(key=lambda x: x.remaining)
        return jobs
    
    def cleanup_expired_challenges(self):
        """Remove expired challenges"""
        expired_ids = [
            challenge_id for challenge_id, challenge in self.challenges.items()
            if challenge.is_expired()
        ]
        
        for challenge_id in expired_ids:
            del self.challenges[challenge_id]
            if challenge_id in self.solution_callbacks:
                del self.solution_callbacks[challenge_id]
        
        if expired_ids:
            self.logger.info(f"Cleaned up {len(expired_ids)} expired challenges")
    
    def __enter__(self):
        """Context manager entry"""
        self.start_server()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_server()


# Example usage and testing
if __name__ == "__main__":
    def test_recaptcha():
        """Test ReCaptcha solving"""
        with CaptchaSolver(port=8080) as solver:
            # Create a ReCaptcha challenge
            challenge = solver.create_challenge(
                challenge_type="RecaptchaV2Challenge",
                site_key="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",  # Test site key
                site_domain="example.com",
                host="example.com",
                explain="Please solve this ReCaptcha to continue",
                type_id="recaptcha_v2"
            )
            
            print(f"Created challenge: {challenge.id}")
            print(f"Challenge URL: http://localhost:8080/captcha/recaptchav2challenge/example.com/?id={challenge.id}")
            
            # Solve the challenge
            def on_solved(solved_challenge):
                print(f"Captcha solved! Result: {solved_challenge.result}")
            
            result = solver.solve_challenge(challenge, timeout=300, callback=on_solved)
            
            if result:
                print(f"Success! Token: {result}")
            else:
                print("Failed to solve captcha")
    
    def test_hcaptcha():
        """Test hCaptcha solving"""
        with CaptchaSolver(port=8081) as solver:
            challenge = solver.create_challenge(
                challenge_type="HCaptchaChallenge",
                site_key="10000000-ffff-ffff-ffff-000000000001",  # Test site key
                site_domain="example.com",
                host="example.com",
                explain="Please solve this hCaptcha to continue",
                type_id="hcaptcha"
            )
            
            print(f"Created hCaptcha challenge: {challenge.id}")
            result = solver.solve_challenge(challenge, timeout=300)
            
            if result:
                print(f"hCaptcha solved! Token: {result}")
            else:
                print("Failed to solve hCaptcha")
    
    def test_turnstile():
        """Test Cloudflare Turnstile solving"""
        with CaptchaSolver(port=8082) as solver:
            challenge = solver.create_challenge(
                challenge_type="TurnstileChallenge",
                site_key="1x00000000000000000000AA",  # Cloudflare test key that always passes
                site_domain="example.com",
                host="example.com",
                explain="Please solve this Turnstile challenge to continue",
                type_id="turnstile"
            )
            
            print(f"Created Turnstile challenge: {challenge.id}")
            result = solver.solve_challenge(challenge, timeout=300)
            
            if result:
                print(f"Turnstile solved! Token: {result}")
            else:
                print("Failed to solve Turnstile")
    
    def test_recaptcha_v3():
        """Test ReCaptcha v3 solving"""
        with CaptchaSolver(port=8083) as solver:        challenge = solver.create_challenge(
            challenge_type="RecaptchaV3Challenge",
            site_key="6Lcyqq8oAAAAAJE7eVJ3aZp_hnJcI6LgGdYD8lge",  # 2captcha site key
            site_domain="example.com",
            host="example.com",
            explain="Please execute the reCAPTCHA v3 challenge",
            type_id="recaptcha_v3",
            secure_token="submit"  # This will be the action name
        )
        
        print(f"Created ReCaptcha v3 challenge: {challenge.id}")
        print(f"Challenge URL: http://localhost:8083/captcha/recaptchav3challenge/example.com/?id={challenge.id}")
        
        # Solve the challenge
        def on_solved(solved_challenge):
            print(f"reCAPTCHA v3 executed! Token: {solved_challenge.result}")
        
        result = solver.solve_challenge(challenge, timeout=300, callback=on_solved)
        
        if result:
            print(f"Success! reCAPTCHA v3 Token: {result}")
            print("Note: The actual score is only available on the server-side verification.")
        else:
            print("Failed to execute reCAPTCHA v3")
    
    # Run tests
    print("Testing ReCaptcha solver...")
    test_recaptcha()
    
    print("\nTesting hCaptcha solver...")
    test_hcaptcha()
    
    print("\nTesting Turnstile solver...")
    test_turnstile()
    
    print("\nTesting ReCaptcha v3 solver...")
    test_recaptcha_v3()

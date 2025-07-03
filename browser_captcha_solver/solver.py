"""
Core solver module containing the main CaptchaSolver class and data structures.
"""

import time
import uuid
import logging
import threading
import webbrowser
from datetime import datetime
from typing import Dict, Optional, Callable, List, Any
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
        """
        Initialize the captcha solver.

        Args:
            port: Port for the HTTP server (0 for auto-select)
            browser_command: Custom browser command (None for system default)
        """
        self.port = port
        self.browser_command = browser_command
        self.challenges: Dict[str, CaptchaChallenge] = {}
        self.server: Optional[ThreadingHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.solution_callbacks: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)

        # Configure logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def start_server(self) -> int:
        """Start the HTTP server and return the actual port"""
        if self.server:
            return self.port

        # Create handler class with solver reference
        def handler_factory(*args: Any, **kwargs: Any) -> CaptchaHTTPHandler:
            return CaptchaHTTPHandler(*args, solver_instance=self, **kwargs)

        self.server = ThreadingHTTPServer(("localhost", self.port), handler_factory)
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

    def create_challenge(
        self, challenge_type: str, site_key: str, site_domain: str, host: str, **kwargs
    ) -> CaptchaChallenge:
        """
        Create a new captcha challenge.

        Args:
            challenge_type: Type of captcha (e.g., 'RecaptchaV2Challenge')
            site_key: Site key for the captcha service
            site_domain: Domain where the captcha will be solved
            host: Host identifier for the challenge
            **kwargs: Additional challenge parameters

        Returns:
            CaptchaChallenge: The created challenge
        """
        challenge = CaptchaChallenge(
            challenge_type=challenge_type,
            site_key=site_key,
            site_domain=site_domain,
            host=host,
            **kwargs,
        )

        self.challenges[challenge.id] = challenge
        self.logger.info(
            f"Created challenge {challenge.id} for {host} ({challenge_type})"
        )

        return challenge

    def get_challenge(self, challenge_id: str) -> Optional[CaptchaChallenge]:
        """Get challenge by ID"""
        return self.challenges.get(challenge_id)

    def solve_challenge(
        self,
        challenge: CaptchaChallenge,
        timeout: Optional[int] = None,
        callback: Optional[Callable] = None,
    ) -> Optional[str]:
        """
        Solve a captcha challenge by opening it in the browser.

        Args:
            challenge: The challenge to solve
            timeout: Timeout in seconds (uses challenge timeout if None)
            callback: Optional callback function when solved

        Returns:
            str: Solution token or None if failed/timeout
        """
        if not self.server:
            self.start_server()

        # Set callback for solution notification
        if callback:
            self.solution_callbacks[challenge.id] = callback

        # Build captcha URL
        captcha_url = (
            f"http://localhost:{self.port}/captcha/"
            f"{challenge.challenge_type.lower()}/{challenge.host}/?id={challenge.id}"
        )

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
                self.logger.info("Opened system default browser")
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")

    def _wait_for_solution(
        self, challenge: CaptchaChallenge, timeout: int
    ) -> Optional[str]:
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
                    created=challenge.created,
                )
                jobs.append(job)

        # Sort by timeout (most urgent first)
        jobs.sort(key=lambda x: x.remaining)
        return jobs

    def cleanup_expired_challenges(self):
        """Remove expired challenges"""
        expired_ids = [
            challenge_id
            for challenge_id, challenge in self.challenges.items()
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

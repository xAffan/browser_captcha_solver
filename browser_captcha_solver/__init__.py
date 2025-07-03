"""
Browser Captcha Solver - A Python library for browser-based captcha solving

This library provides a robust solution for solving captchas through browser automation,
offering seamless integration between web captcha services and Python applications.

Features:
    - Browser Integration: Automatically opens captchas in your browser
    - Real-time Communication: Handles browser-server communication seamlessly
    - Multiple Captcha Types: Supports ReCaptcha v2, hCaptcha, and custom challenges
    - Threaded HTTP Server: Non-blocking server for handling multiple requests
    - Secure: Local-only server with automatic cleanup
    - Easy API: Simple, intuitive interface for developers

Classes:
    CaptchaSolver: Main solver class with browser integration and HTTP server
    CaptchaChallenge: Represents a captcha challenge for browser-based solving
    CaptchaJob: Represents a captcha job for browser-based solving

Example:
    >>> from browser_captcha_solver import CaptchaSolver
    >>> with CaptchaSolver() as solver:
    ...     challenge = solver.create_challenge(
    ...         challenge_type="RecaptchaV2Challenge",
    ...         site_key="your-site-key",
    ...         site_domain="example.com",
    ...         host="example.com"
    ...     )
    ...     result = solver.solve_challenge(challenge)
"""

from .solver import CaptchaSolver, CaptchaChallenge, CaptchaJob
from .server import CaptchaHTTPHandler, ThreadingHTTPServer

__version__ = "1.0.1"
__author__ = "xAffan"
__email__ = "affanquddus1122@gmail.com"
__description__ = "A Python library for browser-based captcha solving"
__url__ = "https://github.com/xAffan/browser-captcha-solver"
__license__ = "MIT"

__all__ = [
    "CaptchaSolver",
    "CaptchaChallenge",
    "CaptchaJob",
    "CaptchaHTTPHandler",
    "ThreadingHTTPServer",
]

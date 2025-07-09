"""
Command-line interface for browser-captcha-solver
"""

import argparse
import sys
from typing import Optional

from .solver import CaptchaSolver


def main(args: Optional[list] = None) -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="browser-captcha-solver",
        description="Browser-based captcha solver",
    )

    parser.add_argument(
        "--port", type=int, default=0, help="Port for HTTP server (0 for auto-select)"
    )

    parser.add_argument("--browser", type=str, help="Custom browser command")

    parser.add_argument(
        "--version", action="version", version="browser-captcha-solver 1.0.3"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start server command
    start_parser = subparsers.add_parser(
        "start", help="Start the captcha solver server"
    )
    start_parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="Keep server running until interrupted",
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run a test captcha")
    test_parser.add_argument(
        "--type",
        choices=["recaptcha", "hcaptcha", "turnstile"],
        default="recaptcha",
        help="Type of captcha to test",
    )

    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 1

    try:
        if parsed_args.command == "start":
            return cmd_start(parsed_args)
        elif parsed_args.command == "test":
            return cmd_test(parsed_args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_start(args) -> int:
    """Start server command"""
    print("Starting browser captcha solver server...")

    solver = CaptchaSolver(port=args.port, browser_command=args.browser)
    port = solver.start_server()

    print(f"✓ Server started on http://localhost:{port}")
    print("✓ Ready to handle captcha challenges")

    if args.keep_alive:
        print("Press Ctrl+C to stop the server")
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            solver.stop_server()
            print("✓ Server stopped")

    return 0


def cmd_test(args) -> int:
    """Test captcha command"""
    print(f"Testing {args.type} captcha solving...")

    with CaptchaSolver(port=args.port, browser_command=args.browser) as solver:
        if args.type == "recaptcha":
            challenge = solver.create_challenge(
                challenge_type="RecaptchaV2Challenge",
                site_key="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",  # Test key
                site_domain="example.com",
                host="example.com",
                explain="Test ReCaptcha challenge",
                type_id="recaptcha_v2",
            )
        elif args.type == "hcaptcha":
            challenge = solver.create_challenge(
                challenge_type="HCaptchaChallenge",
                site_key="10000000-ffff-ffff-ffff-000000000001",  # Test key
                site_domain="example.com",
                host="example.com",
                explain="Test hCaptcha challenge",
                type_id="hcaptcha",
            )
        elif args.type == "turnstile":
            challenge = solver.create_challenge(
                challenge_type="TurnstileChallenge",
                site_key="1x00000000000000000000AA",  # Cloudflare test key that always passes
                site_domain="example.com",
                host="example.com",
                explain="Test Cloudflare Turnstile challenge",
                type_id="turnstile",
            )

        print(f"✓ Created {args.type} challenge: {challenge.id}")
        url = (
            f"http://localhost:{solver.port}/captcha/"
            f"{challenge.challenge_type.lower()}/{challenge.host}/?id={challenge.id}"
        )
        print(f"✓ Opening browser at: {url}")

        result = solver.solve_challenge(challenge, timeout=120)

        if result:
            print(f"✅ Success! Captcha solved with token: {result[:50]}...")
            return 0
        else:
            print("❌ Failed to solve captcha (timeout or error)")
            return 1


if __name__ == "__main__":
    sys.exit(main())

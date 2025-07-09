#!/usr/bin/env python3
"""
Browser Captcha Solver - Examples
=================================

This module demonstrates how to use the browser-captcha-solver library
for solving captchas through browser automation.
"""

import time
from browser_captcha_solver import CaptchaSolver


def example_basic_recaptcha():
    """Example 1: Basic ReCaptcha solving"""
    print("=== Example 1: Basic ReCaptcha Solving ===\n")
    
    with CaptchaSolver() as solver:
        challenge = solver.create_challenge(
            challenge_type="RecaptchaV2Challenge",
            site_key="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",  # Google test key
            site_domain="example.com",
            host="example.com",
            explain="Test ReCaptcha - solve to continue",
            timeout=300
        )
        
        print(f"✓ Created ReCaptcha challenge: {challenge.id}")
        print(f"✓ Server running on port: {solver.port}")
        print("🌐 Opening browser for captcha solving...")
        
        # Solve the challenge
        result = solver.solve_challenge(challenge, timeout=60)
        
        if result:
            print(f"✅ Success! Token: {result[:50]}...")
            return result
        else:
            print("❌ Failed to solve captcha")
            return None


def example_hcaptcha_with_callback():
    """Example 2: hCaptcha with solution callback"""
    print("\n=== Example 2: hCaptcha with Callback ===\n")
    
    def on_solved(solved_challenge):
        print(f"🎉 Callback triggered! Challenge {solved_challenge.id} solved!")
        print(f"📝 Token length: {len(solved_challenge.result)} characters")
    
    with CaptchaSolver() as solver:
        challenge = solver.create_challenge(
            challenge_type="HCaptchaChallenge",
            site_key="10000000-ffff-ffff-ffff-000000000001",  # hCaptcha test key
            site_domain="example.com",
            host="example.com",
            explain="Test hCaptcha challenge",
            timeout=300
        )
        
        print(f"✓ Created hCaptcha challenge: {challenge.id}")
        print("🌐 Opening browser...")
        
        result = solver.solve_challenge(
            challenge, 
            timeout=60, 
            callback=on_solved
        )
        
        if result:
            print(f"✅ hCaptcha solved successfully!")
            return result
        else:
            print("❌ hCaptcha solving failed")
            return None


def example_batch_processing():
    """Example 3: Batch processing multiple captchas"""
    print("\n=== Example 3: Batch Processing ===\n")
    
    with CaptchaSolver() as solver:
        challenges = []
        
        # Create multiple challenges
        for i in range(2):
            challenge = solver.create_challenge(
                challenge_type="RecaptchaV2Challenge",
                site_key="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
                site_domain="example.com",
                host=f"host-{i}",
                explain=f"Challenge #{i+1}",
                timeout=300
            )
            challenges.append(challenge)
        
        print(f"✓ Created {len(challenges)} challenges")
        
        # Solve them sequentially
        results = []
        for i, challenge in enumerate(challenges):
            print(f"\n🔄 Solving challenge {i+1}/{len(challenges)}")
            result = solver.solve_challenge(challenge, timeout=30)  # Short timeout for demo
            results.append(result)
            
            if result:
                print(f"✅ Challenge {i+1} solved!")
            else:
                print(f"❌ Challenge {i+1} failed (likely timeout)")
        
        successful = sum(1 for r in results if r)
        print(f"\n📊 Results: {successful}/{len(challenges)} challenges solved")
        
        return results


def example_cloudflare_turnstile():
    """Example 4: Cloudflare Turnstile solving"""
    print("\n=== Example 4: Cloudflare Turnstile ===\n")
    
    with CaptchaSolver() as solver:
        challenge = solver.create_challenge(
            challenge_type="TurnstileChallenge",
            site_key="1x00000000000000000000AA",  # Cloudflare test key that always passes
            site_domain="example.com",
            host="example.com",
            explain="Cloudflare Turnstile verification",
            timeout=300
        )
        
        print(f"✓ Created Turnstile challenge: {challenge.id}")
        print("🌐 Opening browser for Turnstile solving...")
        
        result = solver.solve_challenge(challenge, timeout=120)
        
        if result:
            print(f"✅ Turnstile solved! Token: {result[:50]}...")
            return result
        else:
            print("❌ Turnstile solving failed")
            return None


def example_recaptcha_v3():
    """Example: ReCaptcha v3 solving"""
    print("=== Example: ReCaptcha v3 Solving ===\n")
    
    with CaptchaSolver() as solver:
        challenge = solver.create_challenge(
            challenge_type="RecaptchaV3Challenge",
            site_key="6Lcyqq8oAAAAAJE7eVJ3aZp_hnJcI6LgGdYD8lge",  # 2captcha site key
            site_domain="example.com",
            host="example.com",
            explain="Test ReCaptcha v3 - click button to execute",
            timeout=300,
            secure_token="homepage"  # Action name
        )
        
        print(f"✓ Created ReCaptcha v3 challenge: {challenge.id}")
        print(f"✓ Server running on port: {solver.port}")
        print("🌐 Opening browser for captcha execution...")
        print("📝 Note: Click the 'Execute ReCaptcha v3' button in the browser")
        
        result = solver.solve_challenge(challenge)
        
        if result:
            print(f"✅ ReCaptcha v3 executed successfully!")
            print(f"🎯 Token received: {result[:50]}...")
            print("📊 Score analysis available server-side only")
        else:
            print("❌ Failed to execute ReCaptcha v3")
        
        print()
        return result


if __name__ == "__main__":
    print("Browser Captcha Solver - Examples")
    print("=" * 40)
    
    try:
        # Run examples
        example_basic_recaptcha()
        example_hcaptcha_with_callback()
        example_batch_processing()
        example_cloudflare_turnstile()
        example_recaptcha_v3()
        
        print("\n🎯 All examples completed!")
        print("\nNote: Examples use short timeouts for demonstration.")
        print("In real usage, use longer timeouts for better success rates.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n🛑 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

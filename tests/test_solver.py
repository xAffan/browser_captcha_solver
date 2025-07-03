"""
Test suite for browser-captcha-solver library
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock

from browser_captcha_solver import CaptchaSolver, CaptchaChallenge, CaptchaJob


class TestCaptchaChallenge:
    """Test CaptchaChallenge class"""
    
    def test_challenge_creation(self):
        """Test basic challenge creation"""
        challenge = CaptchaChallenge(
            challenge_type="RecaptchaV2Challenge",
            site_key="test-key",
            site_domain="example.com",
            host="example.com",
            timeout=300
        )
        
        assert challenge.challenge_type == "RecaptchaV2Challenge"
        assert challenge.site_key == "test-key"
        assert challenge.site_domain == "example.com"
        assert challenge.host == "example.com"
        assert challenge.timeout == 300
        assert not challenge.solved
        assert challenge.result is None
        assert challenge.id is not None
    
    def test_challenge_timeout(self):
        """Test challenge timeout functionality"""
        challenge = CaptchaChallenge(timeout=3)  # 3 second timeout for reliability
        
        assert not challenge.is_expired()
        assert challenge.get_remaining_timeout() <= 3
        
        time.sleep(3.1)  # Wait for expiration
        
        assert challenge.is_expired()
        assert challenge.get_remaining_timeout() == 0
    
    def test_challenge_solving(self):
        """Test challenge solving"""
        challenge = CaptchaChallenge()
        
        assert not challenge.solved
        
        # Simulate solving
        challenge.result = "test-token"
        challenge.solved = True
        
        assert challenge.solved
        assert challenge.result == "test-token"


class TestCaptchaSolver:
    """Test CaptchaSolver class"""
    
    def test_solver_initialization(self):
        """Test solver initialization"""
        solver = CaptchaSolver(port=8080, browser_command="test-browser")
        
        assert solver.port == 8080
        assert solver.browser_command == "test-browser"
        assert len(solver.challenges) == 0
        assert solver.server is None
    
    def test_create_challenge(self):
        """Test challenge creation"""
        solver = CaptchaSolver()
        
        challenge = solver.create_challenge(
            challenge_type="RecaptchaV2Challenge",
            site_key="test-key",
            site_domain="example.com",
            host="example.com"
        )
        
        assert isinstance(challenge, CaptchaChallenge)
        assert challenge.id in solver.challenges
        assert solver.challenges[challenge.id] == challenge
    
    def test_get_challenge(self):
        """Test challenge retrieval"""
        solver = CaptchaSolver()
        
        challenge = solver.create_challenge(
            challenge_type="RecaptchaV2Challenge",
            site_key="test-key",
            site_domain="example.com",
            host="example.com"
        )
        
        retrieved = solver.get_challenge(challenge.id)
        assert retrieved == challenge
        
        # Test non-existent challenge
        assert solver.get_challenge("non-existent") is None
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with CaptchaSolver() as solver:
            assert solver.server is not None
            port = solver.port
            assert port > 0
        
        # Server should be stopped after exiting context
        assert solver.server is None
    
    def test_list_challenges(self):
        """Test challenge listing"""
        solver = CaptchaSolver()
        
        # No challenges initially
        assert len(solver.list_challenges()) == 0
        
        # Create some challenges
        challenge1 = solver.create_challenge(
            challenge_type="RecaptchaV2Challenge",
            site_key="key1",
            site_domain="example.com",
            host="host1"
        )
        
        challenge2 = solver.create_challenge(
            challenge_type="HCaptchaChallenge",
            site_key="key2",
            site_domain="example.com",
            host="host2"
        )
        
        challenges = solver.list_challenges()
        assert len(challenges) == 2
        
        # Mark one as solved
        challenge1.solved = True
        
        # Should only return unsolved challenges
        challenges = solver.list_challenges()
        assert len(challenges) == 1
        assert challenges[0].id == challenge2.id
    
    def test_cleanup_expired_challenges(self):
        """Test cleanup of expired challenges"""
        solver = CaptchaSolver()
        
        # Create challenge with short timeout
        challenge = solver.create_challenge(
            challenge_type="RecaptchaV2Challenge",
            site_key="test-key",
            site_domain="example.com",
            host="example.com",
            timeout=1
        )
        
        assert len(solver.challenges) == 1
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Cleanup
        solver.cleanup_expired_challenges()
        
        assert len(solver.challenges) == 0
    
    @patch('webbrowser.open')
    def test_open_browser_default(self, mock_open):
        """Test opening default browser"""
        solver = CaptchaSolver()
        solver._open_browser("http://test.com")
        
        mock_open.assert_called_once_with("http://test.com")
    
    @patch('subprocess.Popen')
    def test_open_browser_custom(self, mock_popen):
        """Test opening custom browser"""
        solver = CaptchaSolver(browser_command="custom-browser")
        solver._open_browser("http://test.com")
        
        mock_popen.assert_called_once_with(["custom-browser", "http://test.com"])


class TestIntegration:
    """Integration tests"""
    
    def test_server_startup_shutdown(self):
        """Test server startup and shutdown"""
        solver = CaptchaSolver()
        
        # Start server
        port = solver.start_server()
        assert port > 0
        assert solver.server is not None
        assert solver.server_thread is not None
        
        # Stop server
        solver.stop_server()
        assert solver.server is None
    
    def test_multiple_solvers(self):
        """Test running multiple solvers simultaneously"""
        solver1 = CaptchaSolver()
        solver2 = CaptchaSolver()
        
        try:
            port1 = solver1.start_server()
            port2 = solver2.start_server()
            
            # Should use different ports
            assert port1 != port2
            
            # Both should be running
            assert solver1.server is not None
            assert solver2.server is not None
            
        finally:
            solver1.stop_server()
            solver2.stop_server()
    
    def test_challenge_workflow(self):
        """Test complete challenge workflow"""
        with CaptchaSolver() as solver:
            # Create challenge
            challenge = solver.create_challenge(
                challenge_type="RecaptchaV2Challenge",
                site_key="test-key",
                site_domain="example.com",
                host="example.com",
                timeout=300
            )
            
            # Check challenge is in list
            challenges = solver.list_challenges()
            assert len(challenges) == 1
            assert challenges[0].id == challenge.id
            
            # Simulate solving
            challenge.result = "test-token"
            challenge.solved = True
            
            # Check solution callback
            callback_called = False
            test_challenge = None
            
            def test_callback(solved_challenge):
                nonlocal callback_called, test_challenge
                callback_called = True
                test_challenge = solved_challenge
            
            solver.solution_callbacks[challenge.id] = test_callback
            solver._on_captcha_solved(challenge)
            
            assert callback_called
            assert test_challenge == challenge


if __name__ == "__main__":
    pytest.main([__file__])

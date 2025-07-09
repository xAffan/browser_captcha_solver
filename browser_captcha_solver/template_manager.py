#!/usr/bin/env python3
"""
Template Manager for HTML Template Rendering
Handles loading and rendering of HTML templates for different captcha types
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class TemplateManager:
    """Manages HTML templates for captcha pages"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / 'templates'
        self._cache = {}
    
    def _load_template(self, template_name: str) -> str:
        """Load a template file with caching"""
        if template_name not in self._cache:
            template_path = self.template_dir / template_name
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    self._cache[template_name] = f.read()
            else:
                raise FileNotFoundError(f"Template not found: {template_name}")
        return self._cache[template_name]
    
    def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Simple template rendering with {{variable}} substitution"""
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))
        return template_content
    
    def get_browser_communication_js(self) -> str:
        """Get browser communication JavaScript"""
        return self._load_template('browser_communication.js')
    
    def get_css_styles(self) -> str:
        """Get CSS styles"""
        return self._load_template('styles.css')
    
    def render_recaptcha_v2_page(self, challenge) -> str:
        """Render ReCaptcha v2 page"""
        context = {
            'title': 'ReCaptcha Challenge',
            'host': challenge.host,
            'challenge_title': 'Captcha Challenge',
            'challenge_type': challenge.challenge_type,
            'remaining_timeout': challenge.get_remaining_timeout(),
            'site_key': challenge.site_key,
            'initial_status': 'Please solve the captcha below...',
            'additional_head': self._load_template('recaptcha_v2_head.html'),
            'content': self._render_template(
                self._load_template('recaptcha_v2_content.html'),
                {'site_key': challenge.site_key}
            ),
            'additional_info': '',
            'error_info': '',
            'browser_js': self.get_browser_communication_js(),
            'captcha_js': self._load_template('recaptcha_v2_js.html')
        }
        
        base_template = self._load_template('base.html')
        return self._render_template(base_template, context)
    
    def render_recaptcha_v3_page(self, challenge) -> str:
        """Render ReCaptcha v3 page"""
        demo_site_keys = [
            "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
            "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
            "6LfKL1EqAAAAAMa9VEj5ePJyuC3sjFr_0H6JL6qI"
        ]
        
        demo_notice = ''
        if challenge.site_key in demo_site_keys:
            demo_notice = '<p><strong>Note:</strong> Using demo site key. For production, get your site key from <a href="https://www.google.com/recaptcha/admin" target="_blank">Google reCAPTCHA Admin Console</a></p>'
        
        action = challenge.secure_token or 'submit'
        
        context = {
            'title': 'ReCaptcha v3 Challenge',
            'host': challenge.host,
            'challenge_title': 'ReCaptcha v3 Challenge',
            'challenge_type': challenge.challenge_type,
            'remaining_timeout': challenge.get_remaining_timeout(),
            'site_key': challenge.site_key,
            'initial_status': 'ReCaptcha v3 is ready. Click the button below to execute the challenge.',
            'additional_head': self._render_template(
                self._load_template('recaptcha_v3_head.html'),
                {'site_key': challenge.site_key}
            ),
            'content': self._render_template(
                self._load_template('recaptcha_v3_content.html'),
                {'demo_notice': demo_notice, 'action': action}
            ),
            'additional_info': f'<p><strong>Site Key:</strong> {challenge.site_key}</p>',
            'error_info': self._load_template('recaptcha_v3_error.html'),
            'browser_js': self.get_browser_communication_js(),
            'captcha_js': self._render_template(
                self._load_template('recaptcha_v3_js.html'),
                {'site_key': challenge.site_key, 'action': action}
            )
        }
        
        base_template = self._load_template('base.html')
        return self._render_template(base_template, context)
    
    def render_hcaptcha_page(self, challenge) -> str:
        """Render hCaptcha page"""
        context = {
            'title': 'hCaptcha Challenge',
            'host': challenge.host,
            'challenge_title': 'hCaptcha Challenge',
            'challenge_type': challenge.challenge_type,
            'remaining_timeout': challenge.get_remaining_timeout(),
            'site_key': challenge.site_key,
            'initial_status': 'Please solve the captcha below...',
            'additional_head': self._load_template('hcaptcha_head.html'),
            'content': self._render_template(
                self._load_template('hcaptcha_content.html'),
                {'site_key': challenge.site_key}
            ),
            'additional_info': '',
            'error_info': '',
            'browser_js': self.get_browser_communication_js(),
            'captcha_js': self._load_template('hcaptcha_js.html')
        }
        
        base_template = self._load_template('base.html')
        return self._render_template(base_template, context)
    
    def render_turnstile_page(self, challenge) -> str:
        """Render Cloudflare Turnstile page"""
        demo_notice = ''
        if challenge.site_key == "1x00000000000000000000AA":
            demo_notice = '<p><strong>Note:</strong> Using test site key. For production, get your site key from <a href="https://dash.cloudflare.com" target="_blank">Cloudflare Dashboard</a></p>'
        
        context = {
            'title': 'Cloudflare Turnstile Challenge',
            'host': challenge.host,
            'challenge_title': 'Cloudflare Turnstile Challenge',
            'challenge_type': challenge.challenge_type,
            'remaining_timeout': challenge.get_remaining_timeout(),
            'site_key': challenge.site_key,
            'initial_status': 'Please solve the Turnstile challenge below...',
            'additional_head': self._load_template('turnstile_head.html'),
            'content': self._render_template(
                self._load_template('turnstile_content.html'),
                {'site_key': challenge.site_key, 'demo_notice': demo_notice}
            ),
            'additional_info': f'<p><strong>Site Key:</strong> {challenge.site_key}</p>',
            'error_info': self._load_template('turnstile_error.html'),
            'browser_js': self.get_browser_communication_js(),
            'captcha_js': self._load_template('turnstile_js.html')
        }
        
        base_template = self._load_template('base.html')
        return self._render_template(base_template, context)
    
    def render_generic_captcha_page(self, challenge) -> str:
        """Render a generic captcha page for unknown types"""
        context = {
            'title': f'{challenge.challenge_type} Challenge',
            'host': challenge.host,
            'challenge_title': f'{challenge.challenge_type} Challenge',
            'challenge_type': challenge.challenge_type,
            'remaining_timeout': challenge.get_remaining_timeout(),
            'initial_status': 'Captcha type not fully supported in browser mode.',
            'additional_head': '',
            'content': f'''
                <div style="text-align: center; padding: 40px;">
                    <h3>Unsupported Captcha Type</h3>
                    <p>This captcha type ({challenge.challenge_type}) is not fully supported in browser mode.</p>
                    <p>Please use the API mode or implement support for this captcha type.</p>
                </div>
            ''',
            'additional_info': f'<p><strong>Site Key:</strong> {getattr(challenge, "site_key", "N/A")}</p>',
            'error_info': '',
            'browser_js': self.get_browser_communication_js(),
            'captcha_js': '// No specific captcha JavaScript for unknown type'
        }
        
        base_template = self._load_template('base.html')
        return self._render_template(base_template, context)

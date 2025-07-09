# Templates Directory

This directory contains HTML templates and assets for the browser-based captcha solver.

## File Structure

### Base Template
- `base.html` - Base HTML template with placeholders for all captcha types

### ReCaptcha v2
- `recaptcha_v2_head.html` - Head section with ReCaptcha v2 script
- `recaptcha_v2_content.html` - Content section with ReCaptcha v2 widget
- `recaptcha_v2_js.html` - JavaScript for ReCaptcha v2 handling

### ReCaptcha v3
- `recaptcha_v3_head.html` - Head section with ReCaptcha v3 script
- `recaptcha_v3_content.html` - Content section with ReCaptcha v3 button
- `recaptcha_v3_error.html` - Error information for ReCaptcha v3
- `recaptcha_v3_js.html` - JavaScript for ReCaptcha v3 handling

### hCaptcha
- `hcaptcha_head.html` - Head section with hCaptcha script
- `hcaptcha_content.html` - Content section with hCaptcha widget
- `hcaptcha_js.html` - JavaScript for hCaptcha handling

### Cloudflare Turnstile
- `turnstile_head.html` - Head section with Turnstile script
- `turnstile_content.html` - Content section with Turnstile widget
- `turnstile_error.html` - Error information for Turnstile
- `turnstile_js.html` - JavaScript for Turnstile handling

### Shared Assets
- `styles.css` - CSS styles for all captcha pages
- `browser_communication.js` - JavaScript for browser communication and positioning

## Template Variables

Templates use `{{variable}}` syntax for variable substitution:

- `{{title}}` - Page title
- `{{host}}` - Challenge host
- `{{challenge_type}}` - Type of captcha challenge
- `{{site_key}}` - Captcha site key
- `{{remaining_timeout}}` - Remaining timeout in seconds
- `{{action}}` - Action for ReCaptcha v3
- `{{demo_notice}}` - Notice for demo/test site keys

## Usage

Templates are managed by the `TemplateManager` class in `template_manager.py`. The manager handles:

1. Loading templates with caching
2. Variable substitution
3. Rendering complete pages for different captcha types

## Adding New Captcha Types

To add support for a new captcha type:

1. Create template files following the naming convention
2. Add a render method in `TemplateManager`
3. Update the server's `_serve_captcha_page` method

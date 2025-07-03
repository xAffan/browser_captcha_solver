# Browser Captcha Solver

[![PyPI version](https://badge.fury.io/py/browser-captcha-solver.svg)](https://badge.fury.io/py/browser-captcha-solver)
[![Python versions](https://img.shields.io/pypi/pyversions/browser-captcha-solver.svg)](https://pypi.org/project/browser-captcha-solver/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust Python library for solving captchas through browser automation, providing seamless integration between web captcha services and Python applications.

## Features

- **🌐 Browser Integration**: Automatically opens captchas in your browser for solving
- **🔄 Real-time Communication**: Handles browser-server communication seamlessly  
- **🎯 Multiple Captcha Types**: Supports ReCaptcha v2, hCaptcha, and custom challenges
- **⚡ Threaded HTTP Server**: Non-blocking server for handling multiple requests
- **🛡️ Secure**: Local-only server with automatic cleanup
- **🎨 Easy API**: Simple, intuitive interface for developers

## Installation

```bash
pip install browser-captcha-solver
```

## Quick Start

### Basic Usage

```python
from browser_captcha_solver import CaptchaSolver

# Create solver and start server
with CaptchaSolver() as solver:
    # Create a ReCaptcha challenge
    challenge = solver.create_challenge(
        challenge_type="RecaptchaV2Challenge",
        site_key="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",  # Test key
        site_domain="example.com",
        host="example.com",
        explain="Please solve this captcha to continue",
        timeout=300
    )
    
    # Solve the challenge (opens browser automatically)
    result = solver.solve_challenge(challenge, timeout=300)
    
    if result:
        print(f"Success! Token: {result}")
    else:
        print("Failed to solve captcha")
```

### Advanced Usage with Callbacks

```python
from browser_captcha_solver import CaptchaSolver

def on_captcha_solved(challenge):
    print(f"Captcha {challenge.id} solved!")
    print(f"Token: {challenge.result}")

with CaptchaSolver(port=8080) as solver:
    challenge = solver.create_challenge(
        challenge_type="HCaptchaChallenge", 
        site_key="10000000-ffff-ffff-ffff-000000000001",  # Test key
        site_domain="example.com",
        host="example.com"
    )
    
    # Solve with callback
    result = solver.solve_challenge(
        challenge, 
        timeout=300,
        callback=on_captcha_solved
    )
```

### Command Line Interface

The package also provides a CLI for testing and server management:

```bash
# Start the server
browser-captcha-solver start --port 8080

# Test ReCaptcha solving  
browser-captcha-solver test --type recaptcha

# Test hCaptcha solving
browser-captcha-solver test --type hcaptcha
```

## API Reference

### CaptchaSolver

Main class for managing captcha challenges and browser communication.

#### Constructor

```python
CaptchaSolver(port=0, browser_command=None)
```

- `port` (int): HTTP server port (0 for auto-select)
- `browser_command` (str, optional): Custom browser command

#### Methods

##### `create_challenge(challenge_type, site_key, site_domain, host, **kwargs)`

Creates a new captcha challenge.

**Parameters:**
- `challenge_type` (str): Type of captcha ("RecaptchaV2Challenge", "HCaptchaChallenge")
- `site_key` (str): Site key for the captcha service
- `site_domain` (str): Domain where the captcha will be solved
- `host` (str): Host identifier for the challenge
- `**kwargs`: Additional parameters (timeout, explain, type_id, etc.)

**Returns:** `CaptchaChallenge` object

##### `solve_challenge(challenge, timeout=None, callback=None)`

Solves a captcha challenge by opening it in the browser.

**Parameters:**
- `challenge` (CaptchaChallenge): The challenge to solve
- `timeout` (int, optional): Timeout in seconds
- `callback` (callable, optional): Callback function when solved

**Returns:** Solution token (str) or None if failed

##### `list_challenges()`

Returns a list of active challenges.

**Returns:** List of `CaptchaJob` objects

##### `cleanup_expired_challenges()`

Removes expired challenges from memory.

### CaptchaChallenge

Represents a captcha challenge.

#### Attributes

- `id` (str): Unique challenge identifier
- `challenge_type` (str): Type of captcha
- `site_key` (str): Site key for the captcha service
- `site_domain` (str): Domain for the challenge
- `host` (str): Host identifier
- `timeout` (int): Timeout in seconds
- `created` (datetime): Creation timestamp
- `solved` (bool): Whether the challenge is solved
- `result` (str): Solution token

#### Methods

- `get_remaining_timeout()`: Returns remaining timeout in seconds
- `is_expired()`: Returns True if the challenge has expired

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │◄──►│  CaptchaSolver  │◄──►│  HTTP Server    │
│   (Your Code)   │    │                 │    │  (Port 8080)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                       ▲
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Challenge Store │    │   Web Browser   │
                       │ (In Memory)     │    │  (User Opens)   │
                       └─────────────────┘    └─────────────────┘
```

## Supported Captcha Types

### ReCaptcha v2

```python
challenge = solver.create_challenge(
    challenge_type="RecaptchaV2Challenge",
    site_key="your-recaptcha-site-key",
    site_domain="example.com",
    host="example.com"
)
```

### hCaptcha

```python
challenge = solver.create_challenge(
    challenge_type="HCaptchaChallenge", 
    site_key="your-hcaptcha-site-key",
    site_domain="example.com",
    host="example.com"
)
```

### Generic/Manual Captcha

```python
challenge = solver.create_challenge(
    challenge_type="ManualChallenge",
    site_key="",
    site_domain="example.com", 
    host="example.com",
    explain="Please solve the captcha shown in the image"
)
```

## Examples

### Web Scraping Integration

```python
from browser_captcha_solver import CaptchaSolver
import requests

def scrape_with_captcha():
    session = requests.Session()
    
    # Detect captcha on page
    response = session.get("https://example.com/protected")
    if "recaptcha" in response.text.lower():
        # Extract site key from HTML
        site_key = extract_site_key(response.text)
        
        # Solve captcha
        with CaptchaSolver() as solver:
            challenge = solver.create_challenge(
                challenge_type="RecaptchaV2Challenge",
                site_key=site_key,
                site_domain="example.com",
                host="example.com"
            )
            
            token = solver.solve_challenge(challenge)
            
            if token:
                # Submit with captcha token
                data = {"g-recaptcha-response": token}
                response = session.post("https://example.com/submit", data=data)
                return response
    
    return None
```

### Batch Processing

```python
from browser_captcha_solver import CaptchaSolver

def process_multiple_captchas():
    with CaptchaSolver() as solver:
        challenges = []
        
        # Create multiple challenges
        for i in range(3):
            challenge = solver.create_challenge(
                challenge_type="RecaptchaV2Challenge",
                site_key="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
                site_domain="example.com",
                host=f"host-{i}",
                timeout=300
            )
            challenges.append(challenge)
        
        # Solve them sequentially
        results = []
        for challenge in challenges:
            result = solver.solve_challenge(challenge, timeout=120)
            results.append(result)
        
        return results
```

## Error Handling

```python
from browser_captcha_solver import CaptchaSolver

try:
    with CaptchaSolver() as solver:
        challenge = solver.create_challenge(
            challenge_type="RecaptchaV2Challenge",
            site_key="invalid-key",
            site_domain="example.com",
            host="example.com"
        )
        
        result = solver.solve_challenge(challenge, timeout=60)
        
        if not result:
            print("Captcha solving failed or timed out")
            
except Exception as e:
    print(f"Error: {e}")
```

## Development

### Setting up for Development

```bash
# Clone the repository
git clone https://github.com/xAffan/browser-captcha-solver.git
cd browser-captcha-solver

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Type checking
mypy browser_captcha_solver/
```

### Building and Publishing

```bash
# Build the package
python -m build

# Upload to PyPI (requires authentication)
twine upload dist/*
```

## Requirements

- Python 3.8+
- requests >= 2.25.0

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please file an issue on the [GitHub repository](https://github.com/xAffan/browser-captcha-solver/issues).

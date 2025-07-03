# Project Structure

This document outlines the clean, professional structure of the browser-captcha-solver Python package.

## Directory Structure

```
browser_captcha_solver/
├── .github/
│   └── workflows/
│       └── test-and-publish.yml    # GitHub Actions CI/CD
├── browser_captcha_solver/         # Main package
│   ├── __init__.py                 # Package initialization and exports
│   ├── solver.py                   # Core solver and data classes
│   ├── server.py                   # HTTP server for browser communication
│   └── cli.py                      # Command-line interface
├── tests/                          # Test suite
│   ├── __init__.py
│   └── test_solver.py              # Unit tests
├── .gitignore                      # Git ignore patterns
├── LICENSE                         # MIT License
├── MANIFEST.in                     # Package manifest
├── PUBLISHING.md                   # PyPI publishing guide
├── README.md                       # Main documentation
├── examples.py                     # Usage examples
├── pyproject.toml                  # Modern Python packaging config
└── requirements.txt                # Dependencies
```

## Core Components

### 1. Main Package (`browser_captcha_solver/`)

#### `__init__.py`
- Package initialization
- Version information
- Public API exports
- Documentation strings

#### `solver.py`
- `CaptchaSolver` class - Main solver functionality
- `CaptchaChallenge` dataclass - Challenge representation
- `CaptchaJob` dataclass - Job status representation
- Core business logic and state management

#### `server.py`
- `ThreadingHTTPServer` - Multi-threaded HTTP server
- `CaptchaHTTPHandler` - Request handler for browser communication
- HTML template generation for different captcha types
- JavaScript injection for browser integration

#### `cli.py`
- Command-line interface implementation
- Server management commands
- Testing utilities
- User-friendly CLI experience

### 2. Configuration Files

#### `pyproject.toml`
- Modern Python packaging configuration
- Build system requirements
- Project metadata
- Tool configurations (black, mypy)

#### `requirements.txt`
- Runtime dependencies
- Minimal dependency list (only `requests`)

#### `MANIFEST.in`
- Files to include in distribution
- License and documentation files

### 3. Development and Testing

#### `tests/`
- Comprehensive test suite using pytest
- Unit tests for core functionality
- Integration tests for server/browser communication
- Mock objects for isolated testing

#### `.github/workflows/`
- Automated CI/CD pipeline
- Multi-platform testing (Windows, macOS, Linux)
- Multiple Python version support (3.8-3.12)
- Automatic PyPI publishing on releases

### 4. Documentation

#### `README.md`
- Clear installation instructions
- Quick start examples
- Complete API reference
- Architecture overview
- Usage examples

#### `PUBLISHING.md`
- Step-by-step publishing guide
- Version management
- CI/CD setup instructions
- Best practices

#### `examples.py`
- Practical usage examples
- Different captcha types
- Error handling patterns
- Best practices demonstration

## Design Principles

### 1. Clean Architecture
- Separation of concerns (solver logic vs. server logic)
- Clear module boundaries
- Minimal coupling between components

### 2. Professional Standards
- Comprehensive documentation
- Type hints throughout codebase
- Error handling and logging
- Test coverage

### 3. User Experience
- Simple, intuitive API
- Context manager support
- Automatic resource cleanup
- Clear error messages

### 4. Maintainability
- Modular design
- Clear naming conventions
- Consistent code style
- Automated testing

## Package Features

### Core Functionality
- ✅ Browser-based captcha solving
- ✅ Multiple captcha service support (ReCaptcha v2, hCaptcha)
- ✅ Real-time browser communication
- ✅ Automatic server management
- ✅ Challenge lifecycle management

### Developer Experience
- ✅ Context manager support (`with` statements)
- ✅ Callback system for solution handling
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ CLI tools for testing

### Production Ready
- ✅ Thread-safe implementation
- ✅ Resource cleanup
- ✅ Timeout handling
- ✅ Port auto-selection
- ✅ Cross-platform compatibility

### Quality Assurance
- ✅ Unit test coverage
- ✅ Type checking support
- ✅ Code formatting standards
- ✅ Automated CI/CD
- ✅ PyPI publishing workflow

## Installation and Usage

### For End Users
```bash
pip install browser-captcha-solver
```

### For Developers
```bash
git clone <repository>
cd browser-captcha-solver
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest tests/
```

### Building Package
```bash
python -m build
```

This structure provides a clean, professional, and maintainable codebase ready for PyPI distribution.

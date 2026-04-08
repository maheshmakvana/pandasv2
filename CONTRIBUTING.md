# Contributing to pandas2

Thank you for your interest in contributing to pandas2! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/pandas2.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
5. Install development dependencies: `pip install -e .[dev]`
6. Create a feature branch: `git checkout -b feature/your-feature-name`

## Making Changes

1. Make your changes in a feature branch
2. Add tests for new functionality in `tests/test_core.py`
3. Ensure all tests pass: `pytest tests/ -v`
4. Run with coverage: `pytest tests/ --cov=pandas2`
5. Keep code consistent with existing style

## Commit Guidelines

- Write clear, concise commit messages
- Reference issues when applicable (#123)
- One feature per commit when possible

## Submitting Changes

1. Push your branch: `git push origin feature/your-feature-name`
2. Create a Pull Request with:
   - Clear description of changes
   - Reference to related issues
   - Test results showing coverage
3. Respond to review feedback

## Testing

All new features must include tests:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_core.py -v

# Run with coverage report
pytest tests/ --cov=pandas2 --cov-report=html
```

## Style Guidelines

- Follow PEP 8
- Use type hints where helpful
- Write docstrings for public functions
- Keep lines under 100 characters

## Questions?

- Open an issue for bugs
- Start a discussion for features
- Contact: [Mahesh Makvana](https://github.com/maheshmakvana)

Thank you for contributing to pandas2!

Built by Mahesh Makvana

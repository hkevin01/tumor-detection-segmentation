# Contributing to Tumor Detection Segmentation

Thank you for your interest in contributing to the Tumor Detection Segmentation project! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Git

### Setup Development Environment

1. Fork the repository
2. Clone your fork:

   ```bash
   git clone https://github.com/your-username/tumor-detection-segmentation.git
   cd tumor-detection-segmentation
   ```

3. Set up the development environment:

   ```bash
   make setup
   # or manually:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

5. Run smoke tests to verify setup:

   ```bash
   make docker-test
   ```

## Development Workflow

### Branching Strategy

We use a simplified Git Flow:

- `main`: Production-ready code
- `develop`: Integration branch for features
- Feature branches: `feature/description` or `fix/issue-number`

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Committing Changes

Follow conventional commit format:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:

```bash
git add .
git commit -m "feat: add multi-modal fusion support"
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass:

   ```bash
   make test
   make docker-test
   ```

2. Run linting and formatting:

   ```bash
   make lint
   make format
   ```

3. Update documentation if needed

4. Add tests for new features

### Creating a Pull Request

1. Push your branch to your fork
2. Create a PR against `develop` branch
3. Fill out the PR template with:
   - Clear description of changes
   - Screenshots for UI changes
   - Test results
   - Breaking changes (if any)

### PR Review Process

- At least one maintainer review required
- CI checks must pass
- No merge conflicts
- Squash and merge for clean history

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run smoke tests (fast)
make docker-test

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest -m gpu  # GPU tests
pytest -m cpu  # CPU tests
```

### Writing Tests

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Use pytest fixtures and markers
- Mock heavy dependencies for fast tests

### Test Coverage

Maintain >80% code coverage. Coverage reports are generated in CI.

## Code Style

### Python Code

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters
- Use `black` for formatting
- Use `ruff` for linting
- Use `mypy` for type checking

### Pre-commit Hooks

Pre-commit hooks automatically check:

- Code formatting (black)
- Import sorting (isort)
- Linting (ruff)
- Type checking (mypy)

### Documentation Standards

- Use Google-style docstrings
- Update README for user-facing changes
- Add type hints for function parameters

## Documentation

### Building Docs

```bash
cd docs
make html
```

### Writing Documentation

- Use reStructuredText (.rst) or Markdown (.md)
- Keep docs in `docs/` directory
- Update table of contents when adding new docs

## Release Process

### Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH)

### Release Steps

1. Create release branch from `develop`
2. Update version numbers
3. Update changelog
4. Create PR to `main`
5. Tag release after merge
6. Deploy to production

### Changelog

Maintain a changelog in `CHANGELOG.md` with:

- New features
- Bug fixes
- Breaking changes
- Migration guides

## Getting Help

- Check existing issues and documentation
- Create an issue for bugs or feature requests
- Join our community discussions
- Contact maintainers for urgent issues

## Recognition

Contributors are recognized in:

- GitHub contributor stats
- Changelog entries
- Release notes

Thank you for contributing to Tumor Detection Segmentation! 🎉

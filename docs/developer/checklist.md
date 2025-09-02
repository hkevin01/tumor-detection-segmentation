# Developer Checklist

This checklist helps ensure code quality and consistency across the project.

## Before Starting Development

- [ ] Read CONTRIBUTING.md
- [ ] Set up development environment (`make setup`)
- [ ] Install pre-commit hooks (`pre-commit install`)
- [ ] Run smoke tests (`make docker-test`)
- [ ] Familiarize with project structure

## Code Development

### Planning
- [ ] Create issue/feature request if not exists
- [ ] Discuss approach with team if complex
- [ ] Break down into small, testable tasks
- [ ] Estimate time and update issue

### Implementation
- [ ] Create feature branch from `develop`
- [ ] Write tests first (TDD when possible)
- [ ] Implement functionality
- [ ] Add/update documentation
- [ ] Follow code style guidelines
- [ ] Use type hints
- [ ] Add meaningful commit messages

### Testing
- [ ] Write unit tests for new code
- [ ] Write integration tests if needed
- [ ] Test edge cases and error conditions
- [ ] Run full test suite (`make test`)
- [ ] Test in Docker environment (`make docker-test`)
- [ ] Verify no regressions

## Code Review Preparation

### Self-Review
- [ ] Run pre-commit checks (`pre-commit run --all-files`)
- [ ] Run linting (`make lint`)
- [ ] Run type checking (`mypy src/`)
- [ ] Test on multiple Python versions if applicable
- [ ] Check for security issues
- [ ] Verify documentation builds

### Documentation
- [ ] Update docstrings for new functions
- [ ] Update README if user-facing changes
- [ ] Add examples for new features
- [ ] Update API documentation
- [ ] Check spelling and grammar

## Pull Request

### PR Creation
- [ ] Push branch to your fork
- [ ] Create PR against `develop` branch
- [ ] Fill PR template completely
- [ ] Add screenshots for UI changes
- [ ] Link related issues
- [ ] Request reviews from appropriate team members

### PR Content
- [ ] Clear, descriptive title
- [ ] Detailed description of changes
- [ ] Breaking changes clearly marked
- [ ] Migration guide if needed
- [ ] Test results included
- [ ] CI checks passing

## After Merge

- [ ] Delete feature branch
- [ ] Close related issues
- [ ] Update project boards
- [ ] Monitor for any issues in production
- [ ] Update changelog if needed

## Code Quality Standards

### Python Best Practices
- [ ] Follow PEP 8 style guide
- [ ] Use meaningful variable/function names
- [ ] Keep functions small and focused
- [ ] Avoid global variables
- [ ] Handle exceptions properly
- [ ] Use context managers for resources
- [ ] Write readable, maintainable code

### Testing Standards
- [ ] Test coverage > 80%
- [ ] Test both positive and negative cases
- [ ] Use descriptive test names
- [ ] Mock external dependencies
- [ ] Test error conditions
- [ ] Integration tests for critical paths

### Documentation Standards
- [ ] Complete docstrings for public APIs
- [ ] Type hints for all parameters
- [ ] Examples in docstrings
- [ ] Update README for new features
- [ ] Keep documentation current

### Security Considerations
- [ ] No hardcoded secrets
- [ ] Input validation and sanitization
- [ ] Safe handling of user data
- [ ] Follow principle of least privilege
- [ ] Regular dependency updates

## Performance Checklist

- [ ] Profile code for bottlenecks
- [ ] Optimize database queries
- [ ] Use appropriate data structures
- [ ] Consider memory usage
- [ ] Test with realistic data sizes
- [ ] Monitor resource usage

## Deployment Checklist

- [ ] Update Docker images if needed
- [ ] Test deployment process
- [ ] Verify environment configurations
- [ ] Check database migrations
- [ ] Update deployment documentation
- [ ] Monitor post-deployment

This checklist ensures consistent, high-quality contributions to the project.

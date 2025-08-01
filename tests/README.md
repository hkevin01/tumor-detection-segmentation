# Test Framework

This directory contains unit tests and integration tests for the tumor detection project.

## Structure

- `test_data/` - Sample data for testing
- `test_training/` - Tests for training modules
- `test_inference/` - Tests for inference modules
- `test_evaluation/` - Tests for evaluation modules
- `test_utils/` - Tests for utility functions

## Running Tests

To run all tests:

```bash
pytest tests/
```

To run specific test modules:

```bash
pytest tests/test_training/
pytest tests/test_inference/
```

To run with coverage:

```bash
pytest --cov=src tests/
```

## Test Data

Sample test data should be placed in the `test_data/` directory. 
This data is used for unit tests and should be small files suitable for automated testing.

## Contributing

When adding new functionality, please include corresponding tests in the appropriate test directory.

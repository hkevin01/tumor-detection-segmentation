# Validation and Testing Scripts

This folder contains all validation, testing, and debugging scripts that were moved from the root directory for better organization.

## Validation Scripts

### System Validation
- **[test_system.py](test_system.py)** - Comprehensive system validation and health checks
- **[validate_docker.py](validate_docker.py)** - Docker configuration and container validation
- **[validate_monai_integration.py](validate_monai_integration.py)** - MONAI integration comprehensive testing

### Import and Dependency Testing
- **[test_imports_quick.py](test_imports_quick.py)** - Quick import validation for all modules
- **[test_monai_imports.py](test_monai_imports.py)** - MONAI-specific import and dependency validation

### MONAI Integration Testing
- **[verify_monai_checklist.py](verify_monai_checklist.py)** - Complete MONAI verification checklist
- **[verify_monai_venv.sh](verify_monai_venv.sh)** - Virtual environment and MONAI setup validation

### Docker Testing
- **[test_docker.sh](test_docker.sh)** - Docker deployment and service validation

### Debug and Development
- **[debug_datalist.py](debug_datalist.py)** - Dataset debugging and inspection utilities

## Usage

From the project root directory:

```bash
# System validation
python scripts/validation/test_system.py

# MONAI verification checklist
python scripts/validation/verify_monai_checklist.py

# Quick import check
python scripts/validation/test_imports_quick.py

# Docker validation
bash scripts/validation/test_docker.sh

# MONAI virtual environment check
bash scripts/validation/verify_monai_venv.sh
```

## Related Files

- **Tests**: `tests/` - Unit and integration test suites
- **Main README**: `../../README.md` - Project overview with updated validation commands
- **Project Documentation**: `../docs/project/` - Implementation and deployment documentation

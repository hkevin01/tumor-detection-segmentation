# Data Management Guide 🏥

This guide explains how to manage medical imaging data for the tumor detection project using separate repositories for security and compliance.

## 🏗️ Repository Structure

```
Project Structure:
├── tumor-detection-segmentation/     # Main code repository (public)
├── tumor-detection-data/            # Private data repository (private)
└── tumor-detection-models/          # Model weights repository (private)
```

## 🔒 Security & Compliance

### Medical Data Privacy
- **NEVER commit patient data to version control**
- Private data repository requires institutional access approval
- All medical data must comply with HIPAA/GDPR regulations
- Data access is logged and audited

### Access Levels
- **Clinical Staff**: Live clinical data access
- **Researchers**: De-identified research datasets
- **Developers**: Public datasets and synthetic data only
- **Administrators**: Full repository access

## 🚀 Quick Setup

### 1. Setup Data Repositories
```bash
# Run the automated setup script
./scripts/data/setup_data_repositories.sh
```

This script will:
- Create the private data repository structure
- Setup symlinks between repositories
- Configure Git LFS for large files
- Update .gitignore files appropriately

### 2. Configure GitHub Repositories

**Create Private Data Repository:**
```bash
# Go to https://github.com/new
# Repository name: tumor-detection-data
# Set to PRIVATE (critical for medical data!)
# Add institutional collaborators

# Push data repository
cd ../tumor-detection-data
git add .
git commit -m "Initial data repository setup"
git remote add origin https://github.com/hkevin01/tumor-detection-data.git
git push -u origin main
```

### 3. Download Public Datasets
```bash
# List available datasets
python scripts/data/download_public_datasets.py --list

# Download MSD Brain Tumor dataset
python scripts/data/download_public_datasets.py msd_task01

# Download BraTS sample dataset
python scripts/data/download_public_datasets.py brats2023_sample
```

### 4. Validate Data Setup
```bash
# Validate all datasets and links
python scripts/data/validate_datasets.py

# Generate detailed validation report
python scripts/data/validate_datasets.py --report

# Validate only public datasets
python scripts/data/validate_datasets.py --public-only
```

## 📁 Data Organization

### Public Datasets (Main Repository)
```
data/
├── msd/                    # Medical Segmentation Decathlon
│   ├── imagesTr/          # Training images
│   ├── labelsTr/          # Training labels
│   ├── imagesTs/          # Test images
│   └── dataset.json      # Dataset metadata
└── downloads/             # Downloaded archives
```

### Private Datasets (Separate Repository)
```
tumor-detection-data/
├── datasets/
│   ├── clinical/          # Live clinical data (30-day retention)
│   ├── private/           # De-identified research data
│   └── annotations/       # Expert radiologist annotations
├── models/
│   ├── checkpoints/       # Training checkpoints
│   └── pretrained/        # Pre-trained weights
└── configs/               # Dataset-specific configurations
```

## 🔄 Data Workflow

### For Developers
```bash
# 1. Clone main repository
git clone https://github.com/hkevin01/tumor-detection-segmentation.git
cd tumor-detection-segmentation

# 2. Download public datasets
python scripts/data/download_public_datasets.py msd_task01

# 3. Start development with public data
python src/training/train.py --dataset msd_task01
```

### For Researchers (with private data access)
```bash
# 1. Clone both repositories
git clone https://github.com/hkevin01/tumor-detection-segmentation.git
git clone https://github.com/hkevin01/tumor-detection-data.git

# 2. Setup data links
cd tumor-detection-segmentation
./scripts/data/setup_data_repositories.sh

# 3. Validate data access
python scripts/data/validate_datasets.py

# 4. Access private datasets
ls data/private-datasets/  # -> ../tumor-detection-data/datasets/
```

### For Clinical Staff
```bash
# Clinical data workflow managed through institutional systems
# Direct PACS integration via DICOM services
# Automated processing through clinical_inbox/
```

## 📊 Dataset Management

### Configuration File: `data_config.yaml`
Central configuration file defining:
- Available datasets and their properties
- Access control requirements
- Storage locations and formats
- Compliance requirements

### Dataset Manifest
Each dataset includes metadata:
```yaml
# datasets/manifest.yaml
datasets:
  clinical_inbox:
    description: "Live clinical data from PACS"
    format: "DICOM"
    access_level: "clinical_staff_only"
    retention_days: 30
```

## 🛠️ Available Scripts

### Data Management Scripts
```bash
# Setup data repositories
./scripts/data/setup_data_repositories.sh

# Download public datasets
./scripts/data/download_public_datasets.py [dataset_name]

# Validate datasets
./scripts/data/validate_datasets.py

# Sync data repositories
./scripts/data/sync_data_repositories.py
```

### Dataset Operations
```bash
# List available datasets
python scripts/data/download_public_datasets.py --list

# Download specific dataset
python scripts/data/download_public_datasets.py msd_task01

# Validate with detailed report
python scripts/data/validate_datasets.py --report
```

## 🔧 Troubleshooting

### Common Issues

**Private data repository not found:**
```bash
# Ensure you have access and clone the private repo
git clone https://github.com/hkevin01/tumor-detection-data.git ../tumor-detection-data
./scripts/data/setup_data_repositories.sh
```

**Symlinks not working:**
```bash
# Recreate symlinks
rm -f data/private-datasets models/private-weights
./scripts/data/setup_data_repositories.sh
```

**Download failures:**
```bash
# Check network connection and retry
python scripts/data/download_public_datasets.py msd_task01

# Manual download if needed
# URLs are in data_config.yaml
```

**Permission errors:**
```bash
# Check file permissions
chmod +x scripts/data/*.py scripts/data/*.sh

# Check data repository access permissions
ls -la data/private-datasets
```

## 📋 Best Practices

### Data Security
1. **Never commit medical data** to version control
2. **Use private repositories** for all patient data
3. **Implement access controls** based on roles
4. **Audit data access** regularly
5. **Encrypt data at rest** and in transit

### Data Organization
1. **Separate public and private** datasets clearly
2. **Version control** dataset configurations
3. **Document data provenance** and lineage
4. **Validate data integrity** regularly
5. **Backup critical datasets** automatically

### Development Workflow
1. **Start with public datasets** for algorithm development
2. **Test on private data** only when necessary
3. **Use synthetic data** for CI/CD pipelines
4. **Document data requirements** clearly
5. **Automate data validation** in workflows

## 📞 Support

For questions about data management:
- **Technical Issues**: Check troubleshooting section above
- **Data Access**: Contact your institutional data steward
- **Compliance**: Review your IRB/ethics approval requirements
- **Security**: Contact your IT security team

## 📚 Additional Resources

- [Medical Data Privacy Guidelines](docs/compliance/privacy_guidelines.md)
- [IRB Requirements for AI Research](docs/compliance/irb_requirements.md)
- [Data Processing Workflows](docs/workflows/data_processing.md)
- [Clinical Integration Guide](docs/clinical/integration_guide.md)

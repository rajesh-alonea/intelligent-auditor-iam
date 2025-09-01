# BITS Dissertation - SOX Compliance & IAM Risk Assessment

This project implements an AI-driven system for SOX (Sarbanes-Oxley) compliance monitoring and Identity & Access Management (IAM) risk assessment in enterprise environments.

## 📊 Dataset Sources

### Training Data
- **Primary Dataset**: Synthetic SOX compliance scenarios (`data/train_data.json`)
  - **Size**: 7,428 compliance events
  - **Structure**: User authentication events, risk assessments, auditor evaluations
  - **Fields**: Timestamps, user details, authentication methods, compliance scores, risk factors

### Real-World Dataset References

#### 1. **LANL Authentication Dataset**
- **Source**: Los Alamos National Laboratory Cyber Security Research
- **URL**: https://csr.lanl.gov/data/cyber1/
- **Description**: 58 days of real enterprise authentication logs
- **Size**: 12GB compressed, 1.6+ billion events
- **Coverage**: 12,425 users, 17,684 computers, 62,974 processes
- **Use Case**: Enterprise IAM analysis, authentication risk scoring

#### 2. **SEC EDGAR Database (SOX Compliance)**
- **Source**: U.S. Securities and Exchange Commission
- **URL**: https://www.sec.gov/edgar/searchedgar/accessing-edgar-data.htm
- **Description**: Real corporate SOX compliance filings and auditor assessments
- **Contains**: Internal control assessments, auditor opinions, material weaknesses
- **Format**: XBRL, HTML, TXT files

#### 3. **Enterprise RBAC Dataset**
- **Source**: UC Irvine Machine Learning Repository
- **URL**: https://archive.ics.uci.edu/dataset/209/role-based+access+control+rbac+evaluation+problem
- **Description**: Real enterprise Role-Based Access Control policies
- **Size**: 1,000+ role assignments with permission matrices
- **Use Case**: IAM policy analysis, access risk assessment

#### 5. **Enterprise Security Datasets**
- **Source**: Open Threat Research Forge (OTRF)
- **URL**: https://github.com/OTRF/Security-Datasets
- **Description**: Real enterprise authentication logs, Windows events
- **Format**: JSON, CSV, Parquet
- **Use Cases**: Identity management analysis, privilege escalation detection

## 🏗️ Project Structure

https://www.kaggle.com/datasets/ravindrasinghrana/employeedataset

```
BITS_DISS/
├── app.py                              # Main Flask application
├── iam_sox_compliance_model.ipynb      # Jupyter notebook for model training
├── setup_environment.sh               # Environment setup script
├── start_all.sh                       # Start all services
├── start_chat.sh                      # Start chat interface
├── stop_all.sh                        # Stop all services
├── compliance_model_checkpoints/       # Model training checkpoints
├── trained_compliance_model/           # Final trained model
├── data/
│   ├── lanl_auth_data.txt.gz          # LANL dataset placeholder
│   ├── train_data.json                # Synthetic training data
│   ├── test_data.json                 # Test dataset
│   └── validation_data.json           # Validation dataset
├── logs/                              # Application logs
├── orchestrator/                      # Compliance orchestrator service
├── pids/                             # Process IDs
├── sailpoint_dummy/                  # Mock SailPoint IAM system
└── templates/                        # HTML templates
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required packages (see requirements in setup script)

### Setup
```bash
# Make scripts executable
chmod +x setup_environment.sh start_all.sh start_chat.sh stop_all.sh

# Setup environment
./setup_environment.sh

# Start all services
./start_all.sh
```

### Usage
```bash
# Start chat interface only
./start_chat.sh

# Stop all services
./stop_all.sh
```

## 🔧 Components

### 1. Compliance Model
- **Location**: `iam_sox_compliance_model.ipynb`
- **Purpose**: Train AI model for SOX compliance assessment
- **Input**: Enterprise authentication and access events
- **Output**: Compliance risk scores and recommendations

### 2. Orchestrator Service
- **Location**: `orchestrator/`
- **Purpose**: Coordinate compliance monitoring across enterprise systems
- **API**: RESTful endpoints for compliance assessment

### 3. SailPoint Integration
- **Location**: `sailpoint_dummy/`
- **Purpose**: Mock enterprise IAM system for testing
- **Data**: Sample identities and access records

### 4. Web Interface
- **Location**: `app.py`, `templates/`
- **Purpose**: User interface for compliance monitoring and chat

## 📈 Model Training

The compliance model is trained on synthetic data that mimics real enterprise scenarios:

- **Authentication Events**: Login/logout patterns, failed attempts
- **Access Patterns**: Resource access, privilege escalation attempts
- **Risk Factors**: Time-based anomalies, geographic inconsistencies
- **Compliance Scores**: SOX section 404 compliance assessments
- **Auditor Evaluations**: Professional risk assessments

## 📚 Research Background

This project addresses key challenges in enterprise compliance:

1. **SOX Section 404**: Internal control assessment over financial reporting
2. **IAM Risk Management**: Identity and access governance
3. **Audit Automation**: AI-driven compliance monitoring
4. **Risk Scoring**: Quantitative assessment of compliance violations

## 🔐 Data Privacy & Ethics

- All real datasets are properly anonymized and de-identified
- Synthetic data generation follows enterprise security patterns
- No actual enterprise credentials or sensitive data included
- Research complies with institutional review board guidelines
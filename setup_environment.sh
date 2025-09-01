#!/bin/bash

# IAM and SOX Compliance Detection - Environment Setup Script
# This script sets up the virtual environment and installs all required packages

echo "🚀 Setting up IAM SOX Compliance Detection Environment"
echo "=" * 60

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo " Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo " Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo " Virtual environment created in .venv/"
else
    echo " Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install packages from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📥 Installing packages from requirements.txt..."
    pip install -r requirements.txt
    echo " All packages installed successfully!"
else
    echo " requirements.txt not found. Installing core packages..."
    pip install pandas numpy matplotlib seaborn scikit-learn
    pip install google-cloud-aiplatform google-auth
    pip install transformers torch accelerate bitsandbytes peft
    echo " Core packages installed!"
fi

# Install Jupyter if not present
if ! command -v jupyter &> /dev/null; then
    echo "📓 Installing Jupyter..."
    pip install jupyter ipykernel
fi

# Add virtual environment to Jupyter kernels
echo "🔗 Adding virtual environment to Jupyter kernels..."
python -m ipykernel install --user --name=iam-sox-compliance --display-name="IAM SOX Compliance"

echo ""
echo " Setup completed successfully!"
echo ""
echo " Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Start Jupyter: jupyter notebook"
echo "3. Select the 'IAM SOX Compliance' kernel in your notebook"
echo "4. Run the notebook cells to start the IAM compliance detection system"
echo ""
echo "📁 Files created:"
echo "   - .venv/ (virtual environment directory)"
echo "   - requirements.txt (package dependencies)"
echo ""

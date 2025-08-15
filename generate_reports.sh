#!/bin/bash

# GitHub Team Productivity Report Generator
# This script sets up the environment and runs the team productivity report with configurable date ranges

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${BLUE}🔍 Git Commit Review Report Generator${NC}"
    echo "=========================================="
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  $0                                    # Use default Q1 2025"
    echo "  $0 --start 2024-10-01 --end 2024-12-31  # Custom date range"
    echo "  $0 --preset q4-2024                     # Use quarterly preset"
    echo "  $0 --help                               # Show this help"
    echo ""
    echo -e "${CYAN}Available Presets:${NC}"
    echo "  q1-2024, q2-2024, q3-2024, q4-2024"
    echo "  q1-2025, q2-2025, q3-2025, q4-2025"
    echo ""
    echo -e "${CYAN}Environment Variables (optional):${NC}"
    echo "  REPORT_START_DATE=2025-01-01"
    echo "  REPORT_END_DATE=2025-03-31"
    echo ""
    exit 0
}

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
fi

echo -e "${BLUE}🔍 Git Commit Review Report Generator${NC}"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo -e "${YELLOW}Please create a .env file with your GitHub token:${NC}"
    echo "echo 'GITHUB_TOKEN=your_personal_access_token_here' > .env"
    echo ""
    echo -e "${YELLOW}Optional: You can also set default date ranges in .env:${NC}"
    echo "echo 'REPORT_START_DATE=2025-01-01' >> .env"
    echo "echo 'REPORT_END_DATE=2025-03-31' >> .env"
    echo ""
    echo -e "${YELLOW}To create a GitHub Personal Access Token:${NC}"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select appropriate scopes (repo access)"
    echo "4. Copy the token and add it to .env file"
    exit 1
fi

# Check if GitHub token is set
if [ ! -s ".env" ] || ! grep -q "GITHUB_TOKEN=" ".env"; then
    echo -e "${RED}❌ Error: GITHUB_TOKEN not found in .env file${NC}"
    echo -e "${YELLOW}Please add your GitHub token to the .env file:${NC}"
    echo "echo 'GITHUB_TOKEN=your_personal_access_token_here' > .env"
    exit 1
fi

# Check if team_config.py exists
if [ ! -f "team_config.py" ]; then
    echo -e "${RED}❌ Error: team_config.py not found${NC}"
    echo -e "${YELLOW}Please create team_config.py based on sample_team_config.py${NC}"
    if [ -f "sample_team_config.py" ]; then
        echo "cp sample_team_config.py team_config.py"
        echo "Then edit team_config.py with your team members and repositories"
    fi
    exit 1
fi

echo -e "${BLUE}🔧 Setting up Python environment...${NC}"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    echo "Please install Python 3 to continue"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${YELLOW}📚 Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Run the main script with provided arguments
echo -e "${GREEN}🚀 Generating reports...${NC}"
echo ""

if [ $# -eq 0 ]; then
    echo -e "${CYAN}Using default settings...${NC}"
    python main.py
else
    echo -e "${CYAN}Running with custom parameters: $@${NC}"
    python main.py "$@"
fi

# Check if reports were generated and show results
echo ""
echo -e "${BLUE}📊 Report Generation Complete!${NC}"
echo "=========================================="

# Find and display generated files
csv_files=(*.csv)
png_files=(*.png)

if [ -e "${csv_files[0]}" ]; then
    for file in "${csv_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${GREEN}✅ $file${NC}"
        fi
    done
else
    echo -e "${RED}❌ No CSV files generated${NC}"
fi

if [ -e "${png_files[0]}" ]; then
    for file in "${png_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${GREEN}✅ $file${NC}"
        fi
    done
else
    echo -e "${RED}❌ No PNG files generated${NC}"
fi

echo ""
echo -e "${BLUE}📁 All reports saved in:${NC} $(pwd)"

# Offer to open the directory
echo ""
read -p "Would you like to open the reports directory? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open .
    elif command -v xdg-open &> /dev/null; then
        xdg-open .
    else
        echo "Please manually navigate to: $(pwd)"
    fi
fi

echo -e "${GREEN}🎉 Done!${NC}"

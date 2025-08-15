# Git Commit Analysis Tool

This tool analyzes GitHub commit activity for specified team members and repositories, generating visual reports and CSV files with configurable date ranges.

## Features

- Track commits by team members across multiple repositories
- Generate weekly commit trend charts with visual analytics
- Export detailed commit data to CSV files
- Support for multiple teams with individual tracking
- **Configurable date ranges** via command-line arguments, environment variables, or presets
- **Automated setup script** for easy deployment
- **Quarterly presets** (Q1-Q4 for 2024/2025)
- Color-coded output and progress tracking

## Quick Start

### Option 1: Use the Automated Script (Recommended)

```bash
# Make the script executable
chmod +x generate_reports.sh

# Run with default settings (uses .env file dates)
./generate_reports.sh

# Run with custom date range
./generate_reports.sh --start 2024-10-01 --end 2024-12-31

# Run with quarterly preset
./generate_reports.sh --preset q4-2024

# Show help
./generate_reports.sh --help
```

### Option 2: Manual Setup

### Option 2: Manual Setup

### 1. Install Dependencies

```bash
# Create and activate a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Configure GitHub Token

1. Generate a GitHub Personal Access Token:
   - Go to GitHub.com → Settings → Developer settings → Personal access tokens
   - Click "Generate new token (classic)" (**Important**: Use classic tokens for organization repos)
   - Give it a descriptive name (e.g., "Commit Analysis Script")
   - Select these permissions:
     - `repo` (Full control of private repositories)
     - `read:org` (Read org and team membership)
     - `read:user` (Read user profile data)
   - Copy the generated token

2. Create a `.env` file in the project root:
   ```
   GITHUB_TOKEN=your_classic_token_here
   
   # Optional: Set default date ranges
   REPORT_START_DATE=2025-01-01
   REPORT_END_DATE=2025-03-31
   ```

### 3. Configure Team Members and Repositories

1. Copy the sample configuration:
   ```bash
   cp sample_team_config.py team_config.py
   ```

2. Edit `team_config.py` with your team information:
   ```python
   # List of team members with their information
   TEAM_MEMBERS = [
       {
           "username": "github-username1",
           "name": "Real Name 1",
           "team": "Team Name"
       },
       # Add more team members...
   ]

   # List of repos to analyze (case-sensitive!)
   REPOS = [
       "Organization/repository1",  # Note: Case matters!
       "Organization/repository2"
   ]
   ```

## Time Window Configuration

You can configure the analysis time window in multiple ways:

### Method 1: Command Line Arguments (Highest Priority)
```bash
# Custom date range
./generate_reports.sh --start 2024-10-01 --end 2024-12-31

# Quarterly presets
./generate_reports.sh --preset q1-2025  # Jan-Mar 2025
./generate_reports.sh --preset q4-2024  # Oct-Dec 2024
```

**Available Presets:**
- `q1-2024`, `q2-2024`, `q3-2024`, `q4-2024`
- `q1-2025`, `q2-2025`, `q3-2025`, `q4-2025`

### Method 2: Environment Variables in .env (Medium Priority)
```bash
# In your .env file
REPORT_START_DATE=2025-04-01
REPORT_END_DATE=2025-04-30
```

### Method 3: Direct Python Execution
```bash
# Activate virtual environment first
source venv/bin/activate

# Run with command line args
python main.py --start 2024-01-01 --end 2024-12-31
python main.py --preset q2-2025

# Run with default settings (uses .env or hardcoded defaults)
python main.py
```

## Output Files

The script generates timestamped files based on your selected date range:

### CSV Reports
- `team_productivity_report_YYYY-MM-DD_to_YYYY-MM-DD.csv`: Detailed commit data with SHA, messages, URLs
- `weekly_commit_trend_YYYY-MM-DD_to_YYYY-MM-DD.csv`: Weekly commit statistics and trends

### Visual Charts
- `weekly_commit_trend_titans_YYYY-MM-DD_to_YYYY-MM-DD.png`: Titans team trend chart
- `weekly_commit_trend_supernova_YYYY-MM-DD_to_YYYY-MM-DD.png`: Supernova team trend chart

### Legacy Files (for backward compatibility)
- `team_productivity_report.csv`: Latest run without date suffix
- `weekly_commit_trend.csv`: Latest run without date suffix
- `weekly_commit_trend_<team>.png`: Latest charts without date suffix

## Executable Script Features

The `generate_reports.sh` script provides:

- ✅ **Automatic environment setup** (creates virtual environment if needed)
- ✅ **Dependency installation** (installs packages from requirements.txt)
- ✅ **Configuration validation** (checks for .env and team_config.py)
- ✅ **Colored output** with progress indicators
- ✅ **Error handling** with helpful troubleshooting messages
- ✅ **Automatic file opening** (offers to open results directory)
- ✅ **Help documentation** with examples and presets

## Example Usage Scenarios

```bash
# Generate Q1 2025 report
./generate_reports.sh --preset q1-2025

# Generate current month report
./generate_reports.sh --start 2025-08-01 --end 2025-08-31

# Generate last 3 months
./generate_reports.sh --start 2025-05-01 --end 2025-07-31

# Use environment variables for default dates
echo "REPORT_START_DATE=2025-01-01" >> .env
echo "REPORT_END_DATE=2025-12-31" >> .env
./generate_reports.sh  # Uses dates from .env
```

## Security Notes

- **Never commit** `.env` or `team_config.py` to version control
- **Keep your GitHub token secure** and treat it like a password
- **Use Classic Personal Access Tokens** for organization repositories (fine-grained tokens require explicit org authorization)
- **Revoke and replace** your token if it's accidentally exposed
- **Use minimum required permissions** for your token
- **Repository names are case-sensitive** (e.g., `Teladoc/telapp` not `teladoc/telapp`)

## Troubleshooting

### Common Issues

**Token Problems:**
- `401 Bad credentials`: Token is invalid, expired, or incorrect
  - Solution: Generate a new classic personal access token
- `404 Not Found`: Repository doesn't exist or no access
  - Solution: Check repository name case-sensitivity and your access permissions

**Configuration Issues:**
- `GITHUB_TOKEN not set`: Missing or incorrect .env file
  - Solution: Create `.env` file with `GITHUB_TOKEN=your_token_here`
- `team_config.py not found`: Missing team configuration
  - Solution: Copy and edit `sample_team_config.py` to `team_config.py`

**Permission Issues:**
- `Fine-grained tokens not working`: Organization repositories need explicit authorization
  - Solution: Use Classic Personal Access Tokens instead

**No Data in Reports:**
- Check if the specified users have commits in the date range
- Verify repository names are correct and case-sensitive
- Ensure users have activity in the specified repositories

### Getting Help

1. Run with help flag: `./generate_reports.sh --help`
2. Check the generated error messages for specific guidance
3. Verify your GitHub token has access to the target repositories
4. Test with a public repository first to validate your setup

## File Structure

```
git_commit_review/
├── generate_reports.sh          # Main executable script
├── main.py                      # Core Python script
├── team_config.py              # Your team configuration (create from sample)
├── sample_team_config.py       # Sample configuration file
├── requirements.txt            # Python dependencies
├── .env                        # GitHub token and settings (create this)
├── README.md                   # This file
└── venv/                       # Virtual environment (auto-created)
```

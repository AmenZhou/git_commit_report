# Git Commit Analysis Tool

This tool analyzes GitHub commit activity for specified team members and repositories, generating visual reports and CSV files.

## Features

- Track commits by team members across multiple repositories
- Generate weekly commit trend charts
- Export detailed commit data to CSV
- Support for multiple teams
- Customizable date ranges

## Setup

### 1. Install Dependencies

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Configure GitHub Token

1. Generate a GitHub Personal Access Token:
   - Go to GitHub.com → Settings → Developer settings → Personal access tokens
   - Click "Generate new token (classic)"
   - Give it a descriptive name (e.g., "Commit Analysis Script")
   - Select these permissions:
     - `repo` (Full control of private repositories)
     - `read:org` (Read org and team membership)
     - `read:user` (Read user profile data)
   - Copy the generated token

2. Create a `.env` file in the project root:
   ```
   GITHUB_TOKEN=your_token_here
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

   # List of repos to analyze
   REPOS = [
       "organization/repository1",
       "organization/repository2"
   ]

   # Date range for analysis
   START_DATE = "2025-01-01"
   END_DATE = "2025-03-31"
   ```

## Usage

Run the script:
```bash
python main.py
```

The script will:
1. Fetch commit data for all specified team members
2. Generate CSV files with detailed commit information
3. Create trend charts for each team

## Output Files

- `team_productivity_report.csv`: Detailed commit data
- `weekly_commit_trend.csv`: Weekly commit statistics
- `weekly_commit_trend_<team_name>.png`: Team-specific trend charts

## Security Notes

- Never commit `.env` or `team_config.py` to version control
- Keep your GitHub token secure
- Revoke and replace your token if it's accidentally exposed
- Use the minimum required permissions for your token

## Troubleshooting

- If you get a "GITHUB_TOKEN not set" error, check your `.env` file
- If you get a "team_config.py not found" error, make sure you've created it from the sample
- For API rate limit issues, consider using a token with higher rate limits 

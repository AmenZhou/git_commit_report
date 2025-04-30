import requests
from datetime import datetime, timedelta
import os
import csv
from collections import defaultdict
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ========== CONFIGURATION ==========
# Get GitHub token from environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN environment variable is not set")
    print("Please set your GitHub token in the .env file")
    print("Format: GITHUB_TOKEN=your_token_here")
    sys.exit(1)

try:
    from team_config import TEAM_MEMBERS, REPOS
except ImportError:
    print("Error: team_config.py not found")
    print("Please create team_config.py with TEAM_MEMBERS and REPOS configuration")
    sys.exit(1)

# List of GitHub usernames (for backward compatibility)
USERS = [member["username"] for member in TEAM_MEMBERS]

# Mapping of GitHub usernames to real names (for backward compatibility)
USER_NAMES = {member["username"]: member["name"] for member in TEAM_MEMBERS}

# Team assignments (for backward compatibility)
TEAMS = {
    "Titans": [member["username"] for member in TEAM_MEMBERS if member["team"] == "Titans"],
    "Supernova": [member["username"] for member in TEAM_MEMBERS if member["team"] == "Supernova"]
}

# Branch configuration
# Set to None to search all branches, or specify branch names in a list
# Example: BRANCHES = ["master", "develop"]
BRANCHES = None  # Search all branches

# Q1 2025 date range
Q1_START = "2025-01-01T00:00:00Z"
Q1_END = "2025-03-31T23:59:59Z"

# Save results to CSV file?
SAVE_TO_CSV = True
CSV_FILENAME = "team_productivity_report.csv"
WEEKLY_TREND_FILENAME = "weekly_commit_trend.csv"
CHART_FILENAME = "weekly_commit_trend.png"
# ====================================

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Data structure to collect results
team_activity = defaultdict(list)

def fetch_commits(repo, username):
    commits = []
    if BRANCHES is None:
        # Search all branches
        url = f"https://api.github.com/repos/{repo}/commits"
        print(f"\nSearching all branches in {repo} for {username}...")
    else:
        # Search specific branches
        commits = []
        for branch in BRANCHES:
            url = f"https://api.github.com/repos/{repo}/commits"
            print(f"Searching branch '{branch}' in {repo}...")
            params = {
                "author": username,
                "since": Q1_START,
                "until": Q1_END,
                "sha": branch,  # Specify the branch
                "per_page": 100
            }
            
            while url:
                resp = requests.get(url, headers=HEADERS, params=params)
                if resp.status_code != 200:
                    print(f"[ERROR] {repo} ({username}) branch {branch}: {resp.status_code} {resp.text}")
                    break

                data = resp.json()
                for commit in data:
                    sha = commit["sha"]
                    message = commit["commit"]["message"]
                    date = commit["commit"]["author"]["date"]
                    url = commit["html_url"]
                    commits.append({
                        "sha": sha,
                        "message": message,
                        "date": date,
                        "url": url,
                        "repo": repo,
                        "branch": branch
                    })

                # Check for next page
                if 'next' in resp.links:
                    url = resp.links['next']['url']
                    params = None  # Already encoded in the next URL
                else:
                    break
        return commits

    # If searching all branches
    params = {
        "author": username,
        "since": Q1_START,
        "until": Q1_END,
        "per_page": 100
    }

    while url:
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            print(f"[ERROR] {repo} ({username}): {resp.status_code} {resp.text}")
            break

        data = resp.json()
        print(f"Found {len(data)} commits for {username}")
        for commit in data:
            sha = commit["sha"]
            message = commit["commit"]["message"]
            date = commit["commit"]["author"]["date"]
            url = commit["html_url"]
            commits.append({
                "sha": sha,
                "message": message,
                "date": date,
                "url": url,
                "repo": repo,
                "branch": "all"  # Indicates commit was found across all branches
            })

        # Check for next page
        if 'next' in resp.links:
            url = resp.links['next']['url']
            params = None  # Already encoded in the next URL
        else:
            break

    return commits

def get_week_number(date_str):
    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return date.isocalendar()[1]  # Returns ISO week number

def create_team_trend_chart(team_name, team_members, team_activity):
    # Prepare data for plotting
    weeks = list(range(1, 14))  # Weeks 1-13 for Q1 2025
    
    # Create a dictionary to store weekly commits per user
    weekly_user_commits = {user: [0] * len(weeks) for user in team_members}
    
    # Calculate commits per week for each user
    for user in team_members:
        if user in team_activity:
            for commit in team_activity[user]:
                week_num = get_week_number(commit["date"])
                if week_num in weeks:
                    weekly_user_commits[user][week_num - 1] += 1
    
    # Create the plot
    plt.figure(figsize=(15, 8))
    
    # Create line plots for each user
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']  # Different colors for each user
    markers = ['o', 's', '^', 'D', 'p', '*']  # Different markers for each user
    line_styles = ['-', '--', '-.', ':', '-', '--']  # Different line styles
    
    for i, user in enumerate(team_members):
        if user in weekly_user_commits:
            plt.plot([f"Week {w}" for w in weeks], 
                    weekly_user_commits[user],
                    label=USER_NAMES[user],
                    color=colors[i % len(colors)],
                    marker=markers[i % len(markers)],
                    linestyle=line_styles[i % len(line_styles)],
                    linewidth=2,
                    markersize=8)
    
    # Add data point labels
    for user in team_members:
        if user in weekly_user_commits:
            for week_idx in range(len(weeks)):
                count = weekly_user_commits[user][week_idx]
                if count > 0:
                    plt.text(week_idx, count + 0.2, str(count),
                            ha='center', va='bottom',
                            fontsize=8)
    
    # Customize the plot
    plt.title(f'Q1 2025 Weekly Commit Activity - {team_name} Team', pad=20)
    plt.xlabel('Week')
    plt.ylabel('Number of Commits')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title="Team Members", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Set y-axis to start from 0
    plt.ylim(bottom=0)
    
    # Add total commits for each week
    for week_idx in range(len(weeks)):
        total = sum(weekly_user_commits[user][week_idx] for user in team_members if user in weekly_user_commits)
        if total > 0:
            plt.text(week_idx, total + 0.5, f"Total: {total}",
                    ha='center', va='bottom',
                    fontweight='bold',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(f'weekly_commit_trend_{team_name.lower()}.png', dpi=300, bbox_inches='tight')
    plt.close()

# Run for all users and repos
for user in USERS:
    print(f"\nFetching commits for {user}...")
    for repo in REPOS:
        commits = fetch_commits(repo, user)
        team_activity[user].extend(commits)

# ==== Print Summary ====
print("\n=== Team Productivity Summary ===")
for team_name, team_members in TEAMS.items():
    print(f"\n{team_name} Team:")
    for user in team_members:
        print(f"{USER_NAMES[user]}: {len(team_activity[user])} commits")

# ==== Save to CSV ====
if SAVE_TO_CSV:
    # Save detailed commit data
    with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["username", "repo", "sha", "date", "message", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for user, commits in team_activity.items():
            for commit in commits:
                writer.writerow({
                    "username": user,
                    "repo": commit["repo"],
                    "sha": commit["sha"],
                    "date": commit["date"],
                    "message": commit["message"],
                    "url": commit["url"]
                })

    print(f"\n✅ Saved detailed commit data to '{CSV_FILENAME}'")

    # Calculate and save weekly trends
    weekly_commits = defaultdict(int)
    for user, commits in team_activity.items():
        for commit in commits:
            week_num = get_week_number(commit["date"])
            weekly_commits[week_num] += 1

    # Sort weeks chronologically
    sorted_weeks = sorted(weekly_commits.items())
    
    # Save weekly trend data
    with open(WEEKLY_TREND_FILENAME, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["week_number", "start_date", "end_date", "commit_count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Include all weeks in Q1, even those with zero commits
        for week_num in range(1, 14):  # Weeks 1-13 for Q1 2025
            current_date = datetime.strptime("2025-01-01", "%Y-%m-%d")
            week_start = current_date + timedelta(weeks=week_num-1)
            week_end = week_start + timedelta(days=6)
            
            writer.writerow({
                "week_number": week_num,
                "start_date": week_start.strftime("%Y-%m-%d"),
                "end_date": week_end.strftime("%Y-%m-%d"),
                "commit_count": weekly_commits.get(week_num, 0)
            })

    print(f"✅ Saved weekly commit trend to '{WEEKLY_TREND_FILENAME}'")
    
    # Create and save the visualizations for each team
    for team_name, team_members in TEAMS.items():
        create_team_trend_chart(team_name, team_members, team_activity)
        print(f"✅ Generated commit trend chart for {team_name} team: 'weekly_commit_trend_{team_name.lower()}.png'")

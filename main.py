import requests
from datetime import datetime, timedelta
import os
import csv
from collections import defaultdict
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def parse_arguments():
    """Parse command line arguments for date range configuration"""
    parser = argparse.ArgumentParser(
        description='Generate team productivity reports from GitHub commits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Use default Q1 2025 dates
  python main.py --start 2024-10-01 --end 2024-12-31  # Q4 2024
  python main.py --start 2025-04-01 --end 2025-06-30  # Q2 2025
  python main.py --preset q2-2025                      # Use Q2 2025 preset
  python main.py --preset q3-2025                      # Use Q3 2025 preset
        """
    )
    
    parser.add_argument(
        '--start', 
        type=str, 
        help='Start date in YYYY-MM-DD format (default: 2025-01-01)'
    )
    parser.add_argument(
        '--end', 
        type=str, 
        help='End date in YYYY-MM-DD format (default: 2025-03-31)'
    )
    parser.add_argument(
        '--preset',
        choices=['q1-2025', 'q2-2025', 'q3-2025', 'q4-2025', 'q1-2024', 'q2-2024', 'q3-2024', 'q4-2024'],
        help='Use a predefined quarter preset'
    )
    
    return parser.parse_args()

def get_date_range(args):
    """Get the date range based on arguments, environment variables, or defaults"""
    
    # Define quarter presets
    presets = {
        'q1-2024': ('2024-01-01', '2024-03-31'),
        'q2-2024': ('2024-04-01', '2024-06-30'),
        'q3-2024': ('2024-07-01', '2024-09-30'),
        'q4-2024': ('2024-10-01', '2024-12-31'),
        'q1-2025': ('2025-01-01', '2025-03-31'),
        'q2-2025': ('2025-04-01', '2025-06-30'),
        'q3-2025': ('2025-07-01', '2025-09-30'),
        'q4-2025': ('2025-10-01', '2025-12-31'),
    }
    
    # Priority: command line args > environment variables > defaults
    if args.preset:
        start_date, end_date = presets[args.preset]
        print(f"Using preset '{args.preset}': {start_date} to {end_date}")
    elif args.start and args.end:
        start_date, end_date = args.start, args.end
        print(f"Using custom date range: {start_date} to {end_date}")
    else:
        # Check environment variables
        start_date = os.getenv("REPORT_START_DATE", "2025-01-01")
        end_date = os.getenv("REPORT_END_DATE", "2025-03-31")
        if os.getenv("REPORT_START_DATE") or os.getenv("REPORT_END_DATE"):
            print(f"Using environment variables: {start_date} to {end_date}")
        else:
            print(f"Using default Q1 2025: {start_date} to {end_date}")
    
    # Convert to ISO format with timezone
    start_iso = f"{start_date}T00:00:00Z"
    end_iso = f"{end_date}T23:59:59Z"
    
    return start_iso, end_iso, start_date, end_date

# Parse command line arguments
args = parse_arguments()
REPORT_START, REPORT_END, START_DATE_STR, END_DATE_STR = get_date_range(args)

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
# Set to None to search all branches dynamically, or specify branch names in a list
# Example: BRANCHES = ["master", "develop"]
BRANCHES = None  # Search all branches dynamically

# Save results to CSV file?
SAVE_TO_CSV = True
CSV_FILENAME = f"team_productivity_report_{START_DATE_STR}_to_{END_DATE_STR}.csv"
WEEKLY_TREND_FILENAME = f"weekly_commit_trend_{START_DATE_STR}_to_{END_DATE_STR}.csv"
CHART_FILENAME = f"weekly_commit_trend_{START_DATE_STR}_to_{END_DATE_STR}.png"
# ====================================

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Data structure to collect results
team_activity = defaultdict(list)

def get_all_branches_simple(repo):
    """Fetch branches from the repository with smart filtering"""
    branches = []
    url = f"https://api.github.com/repos/{repo}/branches"
    params = {"per_page": 100}  # Get first 100 branches (GitHub returns most active first)
    
    print(f"Fetching branches for {repo}...")
    
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        print(f"[ERROR] Failed to fetch branches for {repo}: {resp.status_code} {resp.text}")
        return ["master", "main"]  # Fallback to common default branches
    
    data = resp.json()
    for branch_info in data:
        branches.append(branch_info["name"])
    
    print(f"Found {len(branches)} branches to search")
    print(f"📊 Using first 100 branches (GitHub API returns most active branches first)")
    print(f"   🔥 Recent active branches: ~{min(30, len(branches))}")
    print(f"   📅 Older branches: ~{max(0, len(branches)-30)}")
    
    # Show top 10 branches for transparency
    print(f"\\n🌿 Top 10 branches to be searched:")
    for i, branch_name in enumerate(branches[:10]):
        print(f"   {i+1:2d}. {branch_name[:45]:45}")
    
    if len(branches) > 10:
        print(f"   ... and {len(branches) - 10} more branches")
    
    return branches

def fetch_commits(repo, username):
    commits = []
    
    if BRANCHES is None:
        # Dynamically fetch branches (first 50) and search each one
        all_branches = get_all_branches_simple(repo)
        
        # Ensure master/main are always included first
        priority_branches = ["master", "main"]
        sorted_branches = []
        
        for priority in priority_branches:
            if priority in all_branches:
                sorted_branches.append(priority)
                all_branches.remove(priority)
        
        # Add remaining branches
        sorted_branches.extend(all_branches)
        
        print(f"Searching {len(sorted_branches)} branches for {username}")
        
        for i, branch in enumerate(sorted_branches, 1):
            print(f"  [{i}/{len(sorted_branches)}] Searching branch: {branch}")
                
            url = f"https://api.github.com/repos/{repo}/commits"
            params = {
                "author": username,
                "since": REPORT_START,
                "until": REPORT_END,
                "sha": branch,
                "per_page": 100
            }
            
            branch_commits = []
            while url:
                resp = requests.get(url, headers=HEADERS, params=params)
                if resp.status_code != 200:
                    break

                data = resp.json()
                if not data:
                    break
                    
                for commit in data:
                    sha = commit["sha"]
                    message = commit["commit"]["message"]
                    date = commit["commit"]["author"]["date"]
                    commit_url = commit["html_url"]
                    branch_commits.append({
                        "sha": sha,
                        "message": message,
                        "date": date,
                        "url": commit_url,
                        "repo": repo,
                        "branch": branch
                    })

                if 'next' in resp.links:
                    url = resp.links['next']['url']
                    params = None
                else:
                    break
            
            # Add unique commits
            for commit in branch_commits:
                if not any(existing["sha"] == commit["sha"] for existing in commits):
                    commits.append(commit)
        
        print(f"Found {len(commits)} unique commits for {username}")
        return commits
        
    else:
        # Search specific branches
        commits = []
        for branch in BRANCHES:
            url = f"https://api.github.com/repos/{repo}/commits"
            print(f"Searching branch '{branch}' in {repo}...")
            params = {
                "author": username,
                "since": REPORT_START,
                "until": REPORT_END,
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
        "since": REPORT_START,
        "until": REPORT_END,
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

def fetch_commits_for_all_users_optimized(repo, usernames):
    """
    Optimized: Loop through branches once and search all users at once per branch
    Much more efficient than searching each user individually for each branch
    """
    print(f"\n🔍 Starting optimized search for all {len(usernames)} users in {repo}")
    all_commits_by_user = {user: [] for user in usernames}
    
    if BRANCHES is None:
        # Get all branches once
        all_branches = get_all_branches_simple(repo)
        
        # Prioritize master/main branches
        priority_branches = ["master", "main"]
        sorted_branches = []
        
        for priority in priority_branches:
            if priority in all_branches:
                sorted_branches.append(priority)
                all_branches.remove(priority)
        
        sorted_branches.extend(all_branches)
        
        print(f"📋 Will search {len(sorted_branches)} branches for all users")
        
        # Search each branch once for all users
        for i, branch in enumerate(sorted_branches, 1):
            print(f"🌿 [{i}/{len(sorted_branches)}] Searching branch '{branch}' for all users...")
            
            # Get all commits from this branch in our date range
            url = f"https://api.github.com/repos/{repo}/commits"
            params = {
                "since": REPORT_START,
                "until": REPORT_END,
                "sha": branch,
                "per_page": 100
            }
            
            branch_total = 0
            while url:
                resp = requests.get(url, headers=HEADERS, params=params)
                if resp.status_code != 200:
                    print(f"    ❌ Error: {resp.status_code}")
                    break

                data = resp.json()
                if not data:
                    break
                
                # Filter commits for our target users
                for commit in data:
                    commit_login = commit["author"]["login"] if commit["author"] else ""
                    
                    # Check if this commit belongs to any of our target users
                    if commit_login in usernames:
                        # Avoid duplicates (same commit SHA)
                        commit_data = {
                            "sha": commit["sha"],
                            "message": commit["commit"]["message"],
                            "date": commit["commit"]["author"]["date"],
                            "url": commit["html_url"],
                            "repo": repo,
                            "branch": branch
                        }
                        
                        # Check if we already have this commit SHA for this user
                        existing_shas = [c["sha"] for c in all_commits_by_user[commit_login]]
                        if commit["sha"] not in existing_shas:
                            all_commits_by_user[commit_login].append(commit_data)
                            branch_total += 1

                if 'next' in resp.links:
                    url = resp.links['next']['url']
                    params = None
                else:
                    break
            
            if branch_total > 0:
                print(f"    ✅ Found {branch_total} commits from our team")
    
    else:
        # Search specific branches
        print(f"📋 Searching {len(BRANCHES)} specified branches for all users")
        
        for i, branch in enumerate(BRANCHES, 1):
            print(f"🌿 [{i}/{len(BRANCHES)}] Searching branch '{branch}' for all users...")
            
            url = f"https://api.github.com/repos/{repo}/commits"
            params = {
                "since": REPORT_START,
                "until": REPORT_END,
                "sha": branch,
                "per_page": 100
            }
            
            branch_total = 0
            while url:
                resp = requests.get(url, headers=HEADERS, params=params)
                if resp.status_code != 200:
                    print(f"    ❌ Error: {resp.status_code}")
                    break

                data = resp.json()
                if not data:
                    break
                
                for commit in data:
                    commit_login = commit["author"]["login"] if commit["author"] else ""
                    
                    if commit_login in usernames:
                        commit_data = {
                            "sha": commit["sha"],
                            "message": commit["commit"]["message"],
                            "date": commit["commit"]["author"]["date"],
                            "url": commit["html_url"],
                            "repo": repo,
                            "branch": branch
                        }
                        
                        existing_shas = [c["sha"] for c in all_commits_by_user[commit_login]]
                        if commit["sha"] not in existing_shas:
                            all_commits_by_user[commit_login].append(commit_data)
                            branch_total += 1

                if 'next' in resp.links:
                    url = resp.links['next']['url']
                    params = None
                else:
                    break
            
            if branch_total > 0:
                print(f"    ✅ Found {branch_total} commits from our team")
    
    # Print summary
    total_commits = sum(len(commits) for commits in all_commits_by_user.values())
    print(f"🎉 Total commits found: {total_commits}")
    for user, commits in all_commits_by_user.items():
        if commits:
            print(f"   {USER_NAMES[user]}: {len(commits)} commits")
    
    return all_commits_by_user

def get_week_number(date_str, start_date_str):
    """Calculate week number relative to the start date"""
    commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    
    # Calculate days difference and convert to weeks
    days_diff = (commit_date.date() - start_date.date()).days
    week_num = (days_diff // 7) + 1
    return max(1, week_num)

def get_total_weeks(start_date_str, end_date_str):
    """Calculate total number of weeks in the date range"""
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    days_diff = (end_date - start_date).days
    return (days_diff // 7) + 1

def create_team_trend_chart(team_name, team_members, team_activity):
    # Get total weeks for the date range
    total_weeks = get_total_weeks(START_DATE_STR, END_DATE_STR)
    weeks = list(range(1, total_weeks + 1))
    
    # Create a dictionary to store weekly commits per user
    weekly_user_commits = {user: [0] * len(weeks) for user in team_members}
    
    # Calculate commits per week for each user
    for user in team_members:
        if user in team_activity:
            for commit in team_activity[user]:
                week_num = get_week_number(commit["date"], START_DATE_STR)
                if 1 <= week_num <= total_weeks:
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
    plt.title(f'{START_DATE_STR} to {END_DATE_STR} Weekly Commit Activity - {team_name} Team', pad=20)
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
    plt.savefig(f'weekly_commit_trend_{team_name.lower()}_{START_DATE_STR}_to_{END_DATE_STR}.png', dpi=300, bbox_inches='tight')
    plt.close()

# Run for all users and repos using optimized batch search
print("\n" + "="*60)
print("🚀 OPTIMIZED BATCH SEARCH: Searching all users simultaneously")
print("="*60)

for repo in REPOS:
    print(f"\n📊 Processing repository: {repo}")
    # Get commits for ALL users at once for this repo
    repo_commits = fetch_commits_for_all_users_optimized(repo, USERS)
    
    # Add commits to the team_activity dictionary
    for user, commits in repo_commits.items():
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
    total_weeks = get_total_weeks(START_DATE_STR, END_DATE_STR)
    
    for user, commits in team_activity.items():
        for commit in commits:
            week_num = get_week_number(commit["date"], START_DATE_STR)
            if 1 <= week_num <= total_weeks:
                weekly_commits[week_num] += 1

    # Sort weeks chronologically
    sorted_weeks = sorted(weekly_commits.items())
    
    # Save weekly trend data
    with open(WEEKLY_TREND_FILENAME, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["week_number", "start_date", "end_date", "commit_count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Include all weeks in the date range, even those with zero commits
        start_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
        for week_num in range(1, total_weeks + 1):
            week_start = start_date + timedelta(weeks=week_num-1)
            week_end = week_start + timedelta(days=6)
            
            # Ensure week_end doesn't exceed the actual end date
            actual_end_date = datetime.strptime(END_DATE_STR, "%Y-%m-%d")
            if week_end > actual_end_date:
                week_end = actual_end_date
            
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
        chart_filename = f"weekly_commit_trend_{team_name.lower()}_{START_DATE_STR}_to_{END_DATE_STR}.png"
        print(f"✅ Generated commit trend chart for {team_name} team: '{chart_filename}'")

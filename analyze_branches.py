#!/usr/bin/env python3
"""
Branch Activity Analyzer for Git repositories
Analyzes branch activity to distinguish between active and stale branches
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN not found in .env file")
    exit(1)

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def analyze_branch_activity(repo, sample_size=100):
    """
    Analyze branch activity to categorize branches as active vs stale
    
    Args:
        repo: Repository in format "owner/repo"
        sample_size: Number of branches to analyze (default: 100)
    """
    print(f"🔍 Analyzing branch activity for {repo}")
    print(f"📊 Sample size: {sample_size} branches")
    
    # Define activity thresholds
    now = datetime.now()
    very_active_threshold = now - timedelta(days=30)   # 1 month
    active_threshold = now - timedelta(days=90)        # 3 months  
    somewhat_stale_threshold = now - timedelta(days=180) # 6 months
    
    # Categories
    very_active = []    # ≤ 30 days
    active = []         # 31-90 days  
    somewhat_stale = [] # 91-180 days
    stale = []          # 181+ days
    
    # Get branches
    url = f"https://api.github.com/repos/{repo}/branches"
    params = {"per_page": min(sample_size, 100)}
    
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        print(f"❌ Error fetching branches: {resp.status_code}")
        return
    
    branches = resp.json()
    print(f"📋 Processing {len(branches)} branches...")
    
    processed = 0
    for branch in branches:
        try:
            branch_name = branch["name"]
            commit_sha = branch["commit"]["sha"]
            
            # Get commit details (we can use the branch's latest commit info)
            commit_url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}"
            commit_resp = requests.get(commit_url, headers=HEADERS)
            
            if commit_resp.status_code == 200:
                commit_data = commit_resp.json()
                commit_date_str = commit_data["commit"]["author"]["date"]
                commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                days_ago = (now - commit_date).days
                
                branch_info = {
                    "name": branch_name,
                    "days_ago": days_ago,
                    "last_commit_date": commit_date_str[:10],
                    "last_commit_sha": commit_sha[:8]
                }
                
                # Categorize branches
                if commit_date >= very_active_threshold:
                    very_active.append(branch_info)
                elif commit_date >= active_threshold:
                    active.append(branch_info)
                elif commit_date >= somewhat_stale_threshold:
                    somewhat_stale.append(branch_info)
                else:
                    stale.append(branch_info)
                
                processed += 1
                if processed % 20 == 0:
                    print(f"   ✅ Processed {processed} branches...")
                    
        except Exception as e:
            print(f"   ⚠️  Error processing branch {branch_name}: {e}")
            continue
    
    # Print results
    total = len(very_active) + len(active) + len(somewhat_stale) + len(stale)
    
    print(f"\n📊 BRANCH ACTIVITY ANALYSIS ({total} branches analyzed)")
    print("=" * 60)
    
    print(f"🔥 Very Active (≤30 days):     {len(very_active):3d} branches ({len(very_active)/total*100:5.1f}%)")
    print(f"🟢 Active (31-90 days):        {len(active):3d} branches ({len(active)/total*100:5.1f}%)")
    print(f"🟡 Somewhat Stale (91-180 days): {len(somewhat_stale):3d} branches ({len(somewhat_stale)/total*100:5.1f}%)")
    print(f"🔴 Stale (180+ days):          {len(stale):3d} branches ({len(stale)/total*100:5.1f}%)")
    
    # Show examples
    if very_active:
        print(f"\n🔥 VERY ACTIVE BRANCHES (Last 30 days):")
        sorted_very_active = sorted(very_active, key=lambda x: x["days_ago"])
        for branch in sorted_very_active[:5]:
            print(f"   {branch['name'][:40]:40} - {branch['days_ago']:2d} days ago ({branch['last_commit_date']})")
    
    if active:
        print(f"\n🟢 ACTIVE BRANCHES (31-90 days):")
        sorted_active = sorted(active, key=lambda x: x["days_ago"])
        for branch in sorted_active[:3]:
            print(f"   {branch['name'][:40]:40} - {branch['days_ago']:2d} days ago ({branch['last_commit_date']})")
    
    if stale:
        print(f"\n🔴 STALEST BRANCHES (180+ days):")
        sorted_stale = sorted(stale, key=lambda x: x["days_ago"], reverse=True)
        for branch in sorted_stale[:3]:
            print(f"   {branch['name'][:40]:40} - {branch['days_ago']:3d} days ago ({branch['last_commit_date']})")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    active_count = len(very_active) + len(active)
    
    if active_count >= 20:
        print(f"   ✅ Focus on {active_count} active branches for commit analysis")
        print(f"   ⚡ This covers {active_count/total*100:.1f}% of branches but likely >90% of recent activity")
    else:
        print(f"   📈 Consider including somewhat stale branches (total: {active_count + len(somewhat_stale)})")
    
    print(f"   🧹 {len(stale)} stale branches could potentially be cleaned up")
    
    return {
        "very_active": very_active,
        "active": active, 
        "somewhat_stale": somewhat_stale,
        "stale": stale,
        "total_analyzed": total
    }

if __name__ == "__main__":
    import sys
    
    # Default repository
    repo = "Teladoc/telapp"
    sample_size = 100
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        repo = sys.argv[1]
    if len(sys.argv) > 2:
        sample_size = int(sys.argv[2])
    
    print(f"🌿 Branch Activity Analyzer")
    print(f"Repository: {repo}")
    print(f"Sample size: {sample_size}")
    print("-" * 60)
    
    results = analyze_branch_activity(repo, sample_size)
    
    if results:
        print(f"\n🎯 SUMMARY:")
        print(f"   Active branches suitable for commit tracking: {len(results['very_active']) + len(results['active'])}")
        print(f"   Recommended search scope: {min(50, len(results['very_active']) + len(results['active']))} branches")

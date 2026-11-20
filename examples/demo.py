from pathlib import Path
from igfollowchecker import analyze, compare_snapshots, load_users
p = Path(__file__).resolve().parent
followers = load_users(p / "followers.json")
print(analyze(followers, load_users(p / "following.json")))
print(compare_snapshots(followers, load_users(p / "followers_after.json")))

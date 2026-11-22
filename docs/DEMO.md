# 1-minute demo script

Offline only, so the demo never depends on Instagram login.

1. (0-10s) Problem: comparing follower lists by hand is slow; we separate collection from reusable offline analysis.
2. (10-20s) Show the PyPI page and the repo link, then `pip install InstagramFollowerAnalysis`.
3. (20-40s) `igfollowchecker analyze --followers examples/followers.json --following examples/following.json`
4. (40-50s) `igfollowchecker diff --before examples/followers.json --after examples/followers_after.json`
5. (50-60s) Innovation is the workflow (normalised inputs, snapshots, optional manual-login collector), not set difference. Limit: input completeness is unverified.

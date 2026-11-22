 IGFollowChecker 0.2.0

A local-first Python package for follower-list analysis, with optional visible
Chrome collection. No auto follow/unfollow, stealth options or credential export.
AI usage: Debugging code and organsing tasks only

## Motivation

Comparing follower lists manually is tedious. A live-only browser script also
couples data collection, authentication and analysis. This package separates
collection from deterministic, reusable list comparison.

## Contribution / innovation

The contribution is a focused workflow: normalized inputs, explicit file formats,
deterministic reports, snapshot comparisons and an optional browser collector
whose completeness limitations are explicit. Set difference is standard, not a
new algorithm. We do not claim this is the first follower comparison tool.

## Install from this complete project

Python 3.9+. In the folder containing pyproject.toml:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/demo.py
```

Windows: use `.venv\Scripts\activate`. For live functionality install:

```sh
python -m pip install -e ".[live]"
```

This installs Selenium as an optional dependency. Chrome and a graphical desktop
are needed. Selenium Manager handles driver discovery/setup and may download
components. Do not assume hosted JupyterHub can display a live browser.
Offline functions have no runtime third-party dependencies.

After an actual release, install the CONFIRMED distribution name from PyPI;
no existing publication is claimed in this document.

## Offline CLI

```sh
igfollowchecker analyze --followers examples/followers.json --following examples/following.json
igfollowchecker diff --before examples/followers.json --after examples/followers_after.json
igfollowchecker analyze --followers examples/followers.csv --following examples/following.json --json
```

Expected analysis: 3 followers, 3 following, 2 mutuals; Charlie does not follow
back in the synthetic dataset; Dora is a fan; Alice and Bob are mutuals.
Add `--output report.json` to create JSON output. Existing files are not overwritten;
the parent directory must already exist. Exit codes: 0 success (including detected
differences), 2 error, 130 interrupted command. `python -m igfollowchecker` and
`python main.py` accept the same command arguments.

## Live CLI

```sh
igfollowchecker collect --username YOUR_ACCOUNT --output-dir private_data/session-01 --max-scrolls 30
```

Use only authorized data and comply with platform rules. Log in yourself in
Chrome, complete verification manually, and return to Terminal. For each list,
YOU open the correct followers/following dialog, confirm it, and press Enter.
Do not interact during collection. Type SAVE at the final prompt to save.
30 scrolls is a short smoke test, not a complete-list guarantee.

Output: followers.json, following.json, metadata.json in a NEW directory.
No passwords, cookies or session IDs are extracted/saved by this program. The
browser handles authentication normally; the program does not bypass challenges.

All captures have `completeness: unverified`. Visible profile links can be
incomplete or unexpected; a stable scroll is not proof of completeness. You
must confirm the correct dialog; this cannot be automatically guaranteed.
Zero collected links raises an error even for a genuinely empty list. Optional
`--expected-followers N --expected-following M` rejects count mismatches before
saving; equal counts still do not prove accuracy. Default pause 1.5 seconds,
maximum 200 scroll steps per list. Bounded collection does not guarantee freedom
from rate limits/account restrictions. Stop if access is blocked.

After reviewing files/metadata:

```sh
igfollowchecker analyze --followers private_data/session-01/followers.json --following private_data/session-01/following.json
```

The analyzer reads the supplied lists, NOT the sidecar metadata. Conclusions are
conditional on data accuracy. An interruption while saving may leave partial
files; metadata.json is written last. Offline does not mean encrypted.

## Python API

```python
from igfollowchecker import load_users, analyze, compare_snapshots
followers = load_users("examples/followers.json")
following = load_users("examples/following.json")
print(analyze(followers, following))
print(compare_snapshots(followers, {"alice", "dora", "erin"}))
```

`normalize_username` strips surrounding whitespace, removes one leading @,
lowercases and checks 1-30 ASCII letters/digits/dots/underscores. This is syntax
validation, not proof of an account's existence. Duplicates collapse.
`load_users` returns a set; malformed input raises ValueError; file/encoding
errors propagate. `analyze` and `compare_snapshots` accept iterables of strings
(not a single string) and return JSON-serializable dictionaries, with sorted lists.

## Supported input formats

- JSON string list: `["alice", "bob"]`.
- JSON object: `{"usernames": ["alice", "bob"]}`.
- JSON object list with non-empty `string_list_data` containing string `value`
  fields, optionally wrapped in `relationships_following` or
  `relationships_followers`. Exactly one supported wrapper key is allowed.
- CSV: unique headers including case-sensitive `username`; extra columns allowed.
  Ragged records and blank usernames fail.
- TXT: one username per line; blank lines ignored.

Files use UTF-8 with optional BOM. See examples/export_shape.json (synthetic).
These are documented schemas, NOT a guarantee of compatibility with all/current
Instagram exports. HTML, ZIP and automatic discovery/merging of split export
files are unsupported. Test real authorized samples privately before claiming
support for their format.

## Use cases and limitations

Analyze local account lists, compare dated snapshots, or teach set operations
with fictional social data. `not_following_back = following - followers`,
`fans = followers - following`, and `mutuals = intersection`.

A removed username only means absence in the later dataset, NOT proof of an
unfollow. Renames, account changes, timing and incomplete inputs matter. Compare
same-kind lists from the same account. No automatic repair, live account
verification, access-control bypass or encrypted storage is provided. Memory
grows with input size. Typical set operations are linear under ordinary hashing
assumptions; sorting output adds O(k log k).

## Validation, teamwork and release

See TEST_RESULTS.txt for executed checks and untested parts. Real Instagram
login/collection was NOT tested here. CI is configured but its execution is not
claimed. See CONTRIBUTING.md, RELEASE.md, docs/DEMO.md and docs/QA.md.
Follow course AI disclosure rules and report actual team contributions honestly.

## License

MIT for this supplied implementation; confirm ownership/permissions for any
existing material retained when integrating into a team repository.

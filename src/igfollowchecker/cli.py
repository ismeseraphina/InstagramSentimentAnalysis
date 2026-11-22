import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .core import analyze, compare_snapshots, load_users
from .live import CollectionError

def main(argv=None):
    parser = argparse.ArgumentParser(description="Local follower analysis and optional live collection")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("--followers", required=True)
    a.add_argument("--following", required=True)
    d = sub.add_parser("diff")
    d.add_argument("--before", required=True)
    d.add_argument("--after", required=True)
    for p in (a, d):
        p.add_argument("--json", action="store_true")
        p.add_argument("--output")
    c = sub.add_parser("collect", help="Visible Chrome, manual login/list selection")
    c.add_argument("--username", required=True)
    c.add_argument("--output-dir", required=True)
    c.add_argument("--max-scrolls", type=int, default=200)
    c.add_argument("--pause", type=float, default=1.5)
    c.add_argument("--expected-followers", type=int)
    c.add_argument("--expected-following", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            from .live import collect_live
            result = collect_live(args.username, args.output_dir, max_scrolls=args.max_scrolls,
                pause=args.pause, expected_followers=args.expected_followers,
                expected_following=args.expected_following)
            print(json.dumps(result, indent=2))
            print("Review private files and metadata before analysis. Completeness is unverified.")
            return 0
        result = (analyze(load_users(args.followers), load_users(args.following)) if args.command == "analyze"
                  else compare_snapshots(load_users(args.before), load_users(args.after)))
        encoded = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with Path(args.output).open("x", encoding="utf-8") as stream:
                stream.write(encoded + "\n")
        if args.json:
            print(encoded)
        else:
            for key, value in result.items():
                if isinstance(value, dict):
                    print("Counts: " + ", ".join(f"{k}={v}" for k, v in value.items()))
                elif isinstance(value, list):
                    print(f"{key} ({len(value)}): " + (", ".join(value) or "(none)"))
                else:
                    print(f"{key}: {value}")
        return 0
    except KeyboardInterrupt:
        print("Cancelled. Inspect output for partial files if saving was interrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError, UnicodeError, CollectionError) as exc:
        print(f"igfollowchecker: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

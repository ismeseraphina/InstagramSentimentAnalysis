import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from igfollowchecker import analyze, compare_snapshots, load_users, normalize_username
from igfollowchecker.cli import main
from igfollowchecker.live import CollectionError, _read_dialog, username_from_href


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def file(self, name, text):
        p = self.base / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_normalize(self):
        self.assertEqual(normalize_username(" @Alice_1 "), "alice_1")

    def test_invalid_names(self):
        for value in ("", "a b", "@@a", 12, "a"*31):
            with self.subTest(value=value), self.assertRaises(ValueError): normalize_username(value)

    def test_analysis(self):
        self.assertEqual(analyze(["a", "b"], ["b", "c"]), {"counts": {"followers":2,"following":2,"mutuals":1}, "fans":["a"], "not_following_back":["c"], "mutuals":["b"]})

    def test_duplicates(self):
        self.assertEqual(analyze(["A", "@a"], [])["counts"]["followers"], 1)

    def test_empty(self): self.assertEqual(analyze([], [])["fans"], [])

    def test_no_mutation(self):
        a = {"a"}; analyze(a, []); self.assertEqual(a, {"a"})

    def test_wrong_iterable(self):
        with self.assertRaises(ValueError): analyze("a", [])

    def test_diff(self):
        self.assertEqual(compare_snapshots(["a","b"],["b","c"]), {"added":["c"],"removed":["a"],"unchanged_count":1})

    def test_json(self): self.assertEqual(load_users(self.file("a.json", '["Alice"]')), {"alice"})

    def test_wrapper(self): self.assertEqual(load_users(self.file("a.json", '{"usernames":["a"]}')), {"a"})

    def test_export(self):
        text = '{"relationships_following":[{"string_list_data":[{"value":"a"}]}]}'
        self.assertEqual(load_users(self.file("a.json", text)), {"a"})

    def test_invalid_json(self):
        for text in ('{', '{}', 'null', '[3]', '[{"string_list_data":[]}]', '{"usernames":[],"relationships_following":[]}'):
            with self.subTest(text=text), self.assertRaises(ValueError): load_users(self.file("a.json", text))

    def test_csv(self): self.assertEqual(load_users(self.file("a.csv", 'username,note\na,"hi, there"\n')), {"a"})

    def test_bad_csv(self):
        for text in ('name\na\n','username\na,b\n','username,username\na,b\n','username,note\n,x\n'):
            with self.subTest(text=text), self.assertRaises(ValueError): load_users(self.file("a.csv", text))

    def test_txt_bom(self): self.assertEqual(load_users(self.file("a.txt", '\ufeffAlice\n\n@bob\n')), {"alice","bob"})

    def test_extension(self):
        with self.assertRaises(ValueError): load_users(self.file("a.html", 'x'))

    def test_missing(self):
        with self.assertRaises(OSError): load_users(self.base / "none.json")

    def test_cli_json(self):
        a = self.file("a.txt", "a"); b = self.file("b.txt", "b"); out = io.StringIO()
        with contextlib.redirect_stdout(out): code = main(["analyze","--followers",str(a),"--following",str(b),"--json"])
        self.assertEqual(code,0); self.assertEqual(json.loads(out.getvalue())["fans"],["a"])

    def test_output_and_no_overwrite(self):
        a = self.file("a.txt","a"); output = self.base / "out.json"
        args = ["diff","--before",str(a),"--after",str(a),"--output",str(output)]
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(args),0)
        with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(main(args),2)
        self.assertEqual(json.loads(output.read_text())["removed"],[])

    def test_bad_cli(self):
        with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(main(["diff","--before","missing.json","--after","missing.json"]),2)

    def test_profile_url(self): self.assertEqual(username_from_href("https://www.instagram.com/Alice/"), "alice")

    def test_bad_urls(self):
        for value in (None,"", "http://instagram.com/a/", "https://instagram.com.evil.org/a/", "https://instagram.com/explore/", "https://instagram.com/a/followers/", "https://instagram.com/@a/", "https://instagram.com/"):
            with self.subTest(value=value): self.assertIsNone(username_from_href(value))

    @patch("igfollowchecker.live.time.sleep")
    def test_dialog_stopping(self, sleep):
        class Anchor:
            def get_attribute(self, key): return "https://instagram.com/alice/"
        class Dialog:
            def find_elements(self,*args): return [Anchor()]
        class Wait:
            def until(self,condition): return Dialog()
        class Driver:
            def execute_script(self,*args): return {"top":1,"height":2}
        users, reason = _read_dialog(Driver(),Wait(),max_scrolls=20,pause=1.5)
        self.assertEqual(users,["alice"]); self.assertEqual(reason,"no_observed_progress")
        self.assertLess(sleep.call_count,20)
        self.assertEqual(_read_dialog(Driver(),Wait(),max_scrolls=1,pause=1.5)[1],"scroll_limit")

    @patch("igfollowchecker.live.time.sleep")
    def test_empty_dialog_error(self, sleep):
        class Dialog:
            def find_elements(self,*args): return []
        class Wait:
            def until(self,condition): return Dialog()
        class Driver:
            def execute_script(self,*args): return None
        with self.assertRaises(CollectionError): _read_dialog(Driver(),Wait(),max_scrolls=1,pause=1.5)


if __name__ == "__main__": unittest.main()

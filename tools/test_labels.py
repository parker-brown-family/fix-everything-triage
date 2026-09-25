"""Tests for tools/labels.py.

    python3 -m unittest tools/test_labels.py -v
"""

import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("labels", Path(__file__).with_name("labels.py"))
labels = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(labels)

PAGE = """```
Fix Everything Triage labels · label-80 v1 · @someone · 3 issues · from the page
#883 kind=bug actionable=yes now=no
#3893 kind=feature actionable=? now=- | note: needs a design call first
#100 kind=support actionable=no now=no seen=model
```"""

PAGE_V2 = """```
Fix Everything Triage labels · label-80 v2 · @someone · 2 issues · from the page
#883 kind=bug actionable=yes now=yes safety=no
#3893 kind=feature actionable=? now=- safety=? | note: needs a design call first
```"""

FORM = """### Who answered?

My agent answered, and I did not check

### Which model, if an agent answered?

example-model-2

### Answers

```json
[{"issue": 883, "kind": "bug", "actionable": "yes", "now": "yes"},
 {"issue": "#3893", "kind": "docs", "needs_maintainer_now": "no"}]
```
"""


class Parse(unittest.TestCase):
    def setUp(self):
        labels.SAMPLE = {883, 3893, 6878, 7613, 100}

    def test_page_block(self):
        r = labels.parse(PAGE)
        self.assertEqual(r["format"], "page")
        self.assertEqual(r["answered_by"], "page")
        self.assertEqual(r["handle"], "@someone")
        # a label-80 v1 block answered the earlier "now" question: kept as now_v1, never as now
        self.assertEqual(r["questions"], "v1")
        self.assertEqual(r["answers"]["883"], {"kind": "bug", "actionable": "yes", "now": None, "safety": None,
                                               "note": None, "seen_model": False, "now_v1": "no"})
        self.assertEqual(r["problems"], [])

    def test_current_page_block_with_safety(self):
        r = labels.parse(PAGE_V2)
        self.assertEqual(r["questions"], "v2")
        self.assertEqual(r["answers"]["883"], {"kind": "bug", "actionable": "yes", "now": "yes", "safety": "no",
                                               "note": None, "seen_model": False})
        self.assertEqual(r["answers"]["3893"]["safety"], "cant_tell")
        self.assertIsNone(r["answers"]["3893"]["now"])
        self.assertEqual(r["problems"], [])

    def test_old_version_is_said_in_the_reply(self):
        self.assertIn("worded differently", labels.reply(labels.parse(PAGE)))
        self.assertNotIn("worded differently", labels.reply(labels.parse(PAGE_V2)))

    def test_json_is_the_current_questions_unless_it_says_otherwise(self):
        r = labels.parse('{"answered_by": "agent", "answers": [{"issue": 883, "now": "yes", "safety": "yes"}]}')
        self.assertEqual((r["questions"], r["answers"]["883"]["now"], r["answers"]["883"]["safety"]), ("v2", "yes", "yes"))
        r = labels.parse('{"answered_by": "agent", "questions": "v1", "answers": [{"issue": 883, "now": "yes"}]}')
        self.assertIsNone(r["answers"]["883"]["now"])
        self.assertEqual(r["answers"]["883"]["now_v1"], "yes")

    def test_cant_tell_and_unanswered_stay_apart(self):
        a = labels.parse(PAGE)["answers"]["3893"]
        self.assertEqual(a["actionable"], "cant_tell")
        self.assertIsNone(a["now"])  # a dash is unanswered, never "no"
        self.assertEqual(a["note"], "needs a design call first")

    def test_seen_model_token(self):
        self.assertTrue(labels.parse(PAGE)["answers"]["100"]["seen_model"])

    def test_issue_form_with_json(self):
        r = labels.parse(FORM)
        self.assertEqual(r["answered_by"], "agent")
        self.assertEqual(r["model"], "example-model-2")
        self.assertEqual(r["answers"]["3893"]["kind"], "docs")
        self.assertEqual(r["answers"]["3893"]["now"], "no")
        self.assertIsNone(r["answers"]["3893"]["actionable"])

    def test_json_object_declares_who(self):
        r = labels.parse('{"answered_by": "person", "answers": [{"issue": 883, "kind": "other"}]}')
        self.assertEqual(r["answered_by"], "person")
        self.assertEqual(r["answers"]["883"]["kind"], "other")

    def test_undeclared_is_never_a_person(self):
        r = labels.parse('[{"issue": 883, "kind": "bug"}]')
        self.assertIsNone(r["answered_by"])
        self.assertIn("Please say who answered", labels.reply(r))

    def test_old_page_block_without_provenance(self):
        r = labels.parse(PAGE.replace(" · from the page", ""))
        self.assertIsNone(r["answered_by"])

    def test_conflicting_declarations(self):
        body = FORM.replace("My agent answered, and I did not check", "I read the issues and answered myself")
        body = body.replace('[{"issue": 883', '{"answered_by": "agent", "answers": [{"issue": 883').replace('"no"}]', '"no"}]}')
        r = labels.parse(body)
        self.assertIsNone(r["answered_by"])
        self.assertTrue(any("counted as not declared" in p for p in r["problems"]))

    def test_issue_outside_the_sample(self):
        r = labels.parse("#999 kind=bug actionable=yes now=no")
        self.assertEqual(r["answers"], {})
        self.assertTrue(any("not one of the 80" in p for p in r["problems"]))

    def test_bad_value(self):
        r = labels.parse("#883 kind=bugg actionable=maybe now=yes")
        self.assertIsNone(r["answers"]["883"]["kind"])
        self.assertIsNone(r["answers"]["883"]["actionable"])
        self.assertEqual(r["answers"]["883"]["now"], "yes")
        self.assertEqual(len(r["problems"]), 2)

    def test_readme_examples_always_count_as_seen(self):
        self.assertTrue(labels.parse("#6878 kind=bug actionable=yes now=yes")["answers"]["6878"]["seen_model"])

    def test_duplicate_line_last_wins(self):
        r = labels.parse("#883 kind=bug\n#883 kind=feature")
        self.assertEqual(r["answers"]["883"]["kind"], "feature")
        self.assertTrue(any("more than once" in p for p in r["problems"]))

    def test_nothing_to_read(self):
        r = labels.parse("Thanks for this, looks great!")
        self.assertEqual(r["answers"], {})
        self.assertIn("found no answers", r["problems"][0])

    def test_reply_counts_only_this_submission(self):
        text = labels.reply(labels.parse(PAGE))
        self.assertIn("3 issues", text)
        self.assertIn("the labelling page", text)


if __name__ == "__main__":
    unittest.main()

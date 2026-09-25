#!/usr/bin/env python3
"""Read answers sent for the 80 issues, from an issue on this repository or a discussion reply.

    python3 tools/labels.py check answers.md                 # a file, or - for stdin
    python3 tools/labels.py check --env BODY --markdown      # what the bot replies with
    python3 tools/labels.py collect --out collected.json     # every submission, grouped

Two formats are accepted:

- the block the labelling page copies: a header line starting "Fix Everything Triage labels",
  then one line per issue, "#<n> kind=<k> actionable=<a> now=<n> safety=<s>", with any further
  key=value tokens (seen=model) and an optional " | note: ..." at the end;
- JSON: an array of {"issue", "kind", "actionable", "now", "safety", "note"} objects, or an
  object {"answered_by", "model", "questions", "answers": [...]}, bare or inside a fenced block.

The "now" question was reworded on 2026-09-25 (questions v2): *would you put this ahead of
ordinary backlog work in the next weekly triage pass, ignoring how many other issues are
waiting?*, and a separate safety question was added. A block whose header says label-80 v1
answered the earlier "now" question, so its answers are kept as now_v1 and never read as
the current question. JSON and a block with no header are read as the current version.

Who answered comes from the issue form's "Who answered?" field, the JSON's "answered_by",
or the page itself for a block copied from it. With none of those it stays undeclared and is
never assumed to be a person. A field left out is unanswered, never "no"; "?" and
"cant_tell" mean can't tell. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "parker-brown-family/fix-everything-triage"
DISCUSSION = "D_kwDOO0Cobs4ApKWg"  # omacom/omarchy discussion 11192, the Fix Everything thread

KIND = {"bug", "feature", "support", "docs", "other"}
YESNO = {"yes", "no"}
CANT = {"?", "cant_tell", "can't tell", "cant tell"}
UNANSWERED = {"-", ""}
FIELDS = {"kind": "kind", "actionable": "actionable", "now": "now", "needs_maintainer_now": "now", "safety": "safety"}
QUESTIONS = "v2"  # the current wording of the questions; see the module docstring
FORM_ANSWERED_BY = {
    "i read the issues and answered myself": "person",
    "my agent answered, and i checked every answer": "agent_checked",
    "my agent answered, and i did not check": "agent",
}
JSON_ANSWERED_BY = {"person", "agent_checked", "agent"}
SAYS = {
    "person": "you, reading the issues yourself",
    "agent_checked": "an agent, with every answer checked by you",
    "agent": "an agent, unchecked",
    "page": "the labelling page (who clicked is not declared)",
    None: "not declared",
}
# The README prints the model's answers to these two as a worked example, so every label on
# them is counted as given after seeing a model's answers (PROTOCOL deviation 12).
ALWAYS_SEEN = {6878, 7613}


def load_sample(path: Path = ROOT / "issues.json") -> set[int]:
    data = json.loads(path.read_text())
    return {int(i["number"]) for i in data["issues"]}


SAMPLE: set[int] = set()


def _value(field: str, raw, problems: list[str], n: int):
    """A clean value, "cant_tell", or None for unanswered."""
    if raw is None:
        return None
    v = str(raw).strip().lower()
    if v in UNANSWERED:
        return None
    if v in CANT:
        return "cant_tell"
    allowed = KIND if field == "kind" else YESNO
    if v in {"true", "false"} and field != "kind":
        v = "yes" if v == "true" else "no"
    if v not in allowed:
        problems.append(f"#{n}: {field}={raw} is not one of {', '.join(sorted(allowed))} or ?")
        return None
    return v


def _sections(text: str) -> dict[str, str]:
    """An issue form's body: '### Heading' followed by its value."""
    out, current = {}, None
    for line in text.splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).strip().lower()
            out[current] = ""
        elif current is not None:
            out[current] += line + "\n"
    return {k: v.strip() for k, v in out.items()}


def _json_candidates(text: str):
    for m in re.finditer(r"```(?:json)?\s*\n(.*?)```", text, re.S):
        yield m.group(1)
    yield text
    starts = [i for i in (text.find("["), text.find("{")) if i != -1]
    ends = [i for i in (text.rfind("]"), text.rfind("}")) if i != -1]
    if starts and ends:
        yield text[min(starts):max(ends) + 1]


def _from_json(text: str):
    for cand in _json_candidates(text):
        try:
            data = json.loads(cand)
        except ValueError:
            continue
        if isinstance(data, list):
            return None, None, data, None
        if isinstance(data, dict) and isinstance(data.get("answers") or data.get("labels"), list):
            return data.get("answered_by"), data.get("model"), data.get("answers") or data.get("labels"), data.get("questions")
    return None


LINE = re.compile(r"^\s*#(\d+)\s+(.*)$")


def parse(text: str) -> dict:
    problems: list[str] = []
    answers: dict[int, dict] = {}
    sections = _sections(text or "")
    who_form = sections.get("who answered?")
    model = sections.get("which model, if an agent answered?")
    body = sections.get("answers", text or "")
    answered_by = None
    if who_form:
        answered_by = FORM_ANSWERED_BY.get(who_form.strip().lower())
        if answered_by is None and who_form.strip() not in ("", "_No response_"):
            problems.append(f"'Who answered?' says “{who_form.strip()}”, which is not one of the form's options")
    if model in (None, "", "_No response_"):
        model = None

    fmt, handle, rows, questions = None, None, [], QUESTIONS
    header = re.search(r"^.*Fix Everything Triage labels.*$", body, re.M)
    if header:
        fmt = "page"
        v = re.search(r"label-80 (v\d+)", header.group(0))
        questions = v.group(1) if v else "v1"  # every header the page ever wrote named its version
        h = re.search(r"·\s*(@[\w-]+|anonymous)\s*·", header.group(0))
        handle = h.group(1) if h else None
        if "from the page" in header.group(0) and answered_by is None:
            answered_by = "page"
    parsed = None if header else _from_json(body)
    if parsed is not None:
        fmt = "json"
        j_who, j_model, items, _q = parsed
        if j_who is not None:
            if j_who not in JSON_ANSWERED_BY:
                problems.append(f"answered_by “{j_who}” is not one of person, agent_checked, agent")
            elif answered_by is not None and answered_by != j_who:
                problems.append(f"the form says {answered_by} and the JSON says {j_who}; counted as not declared")
                answered_by = "conflict"
            else:
                answered_by = j_who
        model = model or j_model
        if _q:
            questions = str(_q)
        for it in items:
            if not isinstance(it, dict):
                problems.append(f"an entry is not an object: {str(it)[:40]}")
                continue
            num = str(it.get("issue", it.get("number", ""))).lstrip("#")
            rows.append((num, {FIELDS[k]: v for k, v in it.items() if k in FIELDS}, it.get("note"), it.get("seen") == "model" or it.get("seen_model") is True))
    else:
        for line in body.splitlines():
            m = LINE.match(line)
            if not m:
                continue
            num, rest = m.group(1), m.group(2)
            rest, _, note = rest.partition(" | note:")
            tokens = dict(re.findall(r"(\w+)=(\S+)", rest))
            rows.append((num, {FIELDS[k]: v for k, v in tokens.items() if k in FIELDS}, note.strip() or None, tokens.get("seen") == "model"))
    if answered_by == "conflict":
        answered_by = None

    for num, fields, note, seen in rows:
        if not num.isdigit():
            problems.append(f"an entry has no issue number: {num or '(blank)'}")
            continue
        n = int(num)
        if SAMPLE and n not in SAMPLE:
            problems.append(f"#{n} is not one of the 80 issues")
            continue
        now = _value("now", fields.get("now"), problems, n)
        rec = {"kind": _value("kind", fields.get("kind"), problems, n),
               "actionable": _value("actionable", fields.get("actionable"), problems, n),
               "now": now if questions != "v1" else None,
               "safety": _value("safety", fields.get("safety"), problems, n),
               "note": (str(note).strip() or None) if note else None,
               "seen_model": bool(seen) or n in ALWAYS_SEEN}
        if questions == "v1":
            rec["now_v1"] = now  # the earlier wording of "now": kept, never read as the current question
        if n in answers:
            problems.append(f"#{n} appears more than once; the last one counts")
        answers[n] = rec
    if not answers and not problems:
        problems.append("found no answers: expected the page's block or a JSON array of answers")
    return {"answered_by": answered_by, "model": model, "handle": handle, "format": fmt, "questions": questions,
            "answers": {str(k): v for k, v in sorted(answers.items())}, "problems": problems}


def reply(result: dict) -> str:
    n = len(result["answers"])
    got = sum(1 for a in result["answers"].values() for f in ("kind", "actionable", "now", "safety", "now_v1") if a.get(f) is not None)
    lines = [f"Thanks. I read **{n} issue{'s' if n != 1 else ''}** ({got} answers in all)."
             if n else "I could not read any answers in this issue yet."]
    who = SAYS.get(result["answered_by"], SAYS[None])
    lines.append(f"\n- Who answered: {who}" + (f", model: {result['model']}" if result["model"] else ""))
    if result["answered_by"] is None and n:
        lines.append("  - Please say who answered: edit the issue and pick an option in the form, or add `\"answered_by\"` to your JSON. Answers with no declaration are kept, and counted apart from people's.")
    if result.get("questions") == "v1" and n:
        lines.append("- These came from the page's first version, whose \"now\" question was worded differently. They are kept, and your \"now\" answers are scored apart from answers to the current question.")
    seen = sum(1 for a in result["answers"].values() if a["seen_model"])
    if seen:
        lines.append(f"- Given after seeing a model's answers: {seen}")
    if result["problems"]:
        lines.append("\nLines I could not use:\n" + "\n".join(f"- {p}" for p in result["problems"]))
    lines.append("\n<sub>This reply is written by a check in this repository and rewritten when the issue is edited. It shows only what was read from this issue.</sub>")
    return "\n".join(lines) + "\n"


def _gh(args: list[str]) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def collect() -> dict:
    subs = []
    for i in json.loads(_gh(["issue", "list", "-R", REPO, "--state", "all", "--limit", "1000",
                             "--json", "number,author,body,createdAt,updatedAt,url"])):
        r = parse(i.get("body") or "")
        if r["answers"]:
            subs.append({"source": "issue", "url": i["url"], "labeller": (i.get("author") or {}).get("login"),
                         "at": i.get("updatedAt") or i.get("createdAt"), **r})
    q = ('query($id: ID!, $after: String) { node(id: $id) { ... on Discussion { comments(first: 100, after: $after) '
         '{ pageInfo { hasNextPage endCursor } nodes { url createdAt updatedAt author { login } body } } } } }')
    after = None
    while True:
        args = ["api", "graphql", "-f", f"query={q}", "-F", f"id={DISCUSSION}"] + (["-F", f"after={after}"] if after else [])
        page = json.loads(_gh(args))["data"]["node"]["comments"]
        for c in page["nodes"]:
            r = parse(c.get("body") or "")
            if r["answers"]:
                subs.append({"source": "discussion", "url": c["url"], "labeller": (c.get("author") or {}).get("login"),
                             "at": c.get("updatedAt") or c.get("createdAt"), **r})
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    labels: dict[str, dict] = {}
    for s in sorted(subs, key=lambda s: s["at"] or ""):
        who = s["labeller"] or "ghost"
        entry = labels.setdefault(who, {"answered_by": s["answered_by"], "answers": {}, "sources": []})
        entry["answers"].update(s["answers"])  # the latest submission wins per issue
        entry["sources"].append(s["url"])
        if s["answered_by"] is not None:
            entry["answered_by"] = s["answered_by"]
    return {"collected": datetime.now(timezone.utc).isoformat(timespec="seconds"), "submissions": subs, "labels": labels}


def main() -> int:
    global SAMPLE
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("file", nargs="?")
    c.add_argument("--env")
    c.add_argument("--markdown", action="store_true")
    c.add_argument("--issues", type=Path, default=ROOT / "issues.json")
    k = sub.add_parser("collect")
    k.add_argument("--out", type=Path, required=True)
    k.add_argument("--issues", type=Path, default=ROOT / "issues.json")
    a = ap.parse_args()
    SAMPLE = load_sample(a.issues)
    if a.cmd == "check":
        text = os.environ.get(a.env, "") if a.env else (sys.stdin.read() if a.file in (None, "-") else Path(a.file).read_text())
        r = parse(text)
        print(reply(r) if a.markdown else json.dumps(r, indent=2, ensure_ascii=False))
        return 0
    out = collect()
    a.out.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(out['submissions'])} submissions from {len(out['labels'])} labellers -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

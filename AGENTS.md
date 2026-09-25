# Labelling these issues with an agent

This repository collects answers to three questions about 80 open issues in
[omacom/omarchy](https://github.com/omacom/omarchy), so that an automated triage of
Omarchy's queue can be checked against them. You are welcome to do the labelling for the
person who sent you here. Follow this file exactly: answers are only useful in the right
shape, and only when they say who made them.

## What to read

[`issues.json`](issues.json) holds the 80 issues as they stood when the sample was drawn
on 2026-09-24: number, title, body, labels, the date opened and the number of comments.
Judge each issue from its title and body as written there. Do not use what has happened on
GitHub since; people labelling on the page see the same text you do.

```
https://raw.githubusercontent.com/parker-brown-family/fix-everything-triage/main/issues.json
```

The labelling page's source also contains one model's answers to all 80, and the README
prints two of them. Answer before reading either. If you have read them, add
`"seen": "model"` to every answer you give afterwards.

## The three questions

| Field | Question | Values |
|---|---|---|
| `kind` | What kind of item is this? | `bug` (a defect: something behaves wrongly), `feature` (a request for new or changed behaviour), `support` (someone needs help; nothing is shown to be broken), `docs` (the documentation is wrong or missing), `other` (not a work item: spam, another project, discussion) |
| `actionable` | Could a maintainer act on it as written, without asking the reporter anything? | `yes`, `no` |
| `now` | Should a maintainer look at this now, rather than later or never? | `yes`, `no` |

Every field also takes `cant_tell`. Use it whenever the issue does not give you enough to
answer; it is more useful than a guess. Leave a field out if you did not consider it: a
missing field is read as unanswered, never as `no`. Answer as many issues as you like.

## What to send

One JSON object:

```json
{
  "answered_by": "agent",
  "model": "the model that answered, with its version",
  "answers": [
    {"issue": 12345, "kind": "bug", "actionable": "yes", "now": "no"},
    {"issue": 23456, "kind": "feature", "actionable": "cant_tell", "now": "no", "note": "optional, one line on what decided it"}
  ]
}
```

The issue numbers above are placeholders; use the numbers from `issues.json`. Set
`answered_by` to exactly one of:

- `agent`: you answered, and your person has not checked the answers;
- `agent_checked`: you answered, and your person read and agreed with every answer (only
  if they actually did);
- `person`: your person answered, and you are only sending their answers.

## How to send it

Check the file first, from a clone of this repository:

```
python3 tools/labels.py check answers.json
```

Then open one issue here with the JSON inside a fenced block as its body:

```
gh issue create -R parker-brown-family/fix-everything-triage --title "Answers from <handle>" --body-file body.md
```

A check replies on the issue with what it read and any line it could not use. To correct
answers, edit the issue; the check reads it again. One issue per person is plenty.

## What happens to the answers

Every answer is kept with who gave it. The triage is graded against people's labels, so
agent answers are scored as their own group and compared with people's rather than mixed
into them. The results will be posted on
[the Fix Everything discussion](https://github.com/omacom/omarchy/discussions/11192).

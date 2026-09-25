# Fix Everything Triage

Omarchy has around two thousand open issues. Fix Everything Triage is an attempt to
sort them automatically — look now, ready for an agent, fix belongs upstream, ask the
reporter, park — using [TypeSafe's Jev model](https://docs.typesafe.ai) for the
judgment calls and plain code for everything else. It is read-only: it never labels,
comments on or closes an issue.

A sorting like that is only worth trusting if it agrees with people who know the
project. That is what this page is for.

**[Open the labelling page](https://parker-brown-family.github.io/fix-everything-triage/)**

## How to help

1. Open the page. It shows 80 open Omarchy issues, one at a time, rendered as GitHub
   shows them.
2. Answer three questions for as many issues as you like. One is useful; all 80 is
   wonderful. The keyboard works: `1`–`5` for the kind, `a`/`s` for actionable, `j`/`k`
   for "look now", `?` for can't tell, arrow keys to move.
3. Press **send my labels**. The page opens an issue on this repository with your
   answers filled in; say who answered and submit, and a check replies on the issue with
   what it read. Or copy the block and paste it as a reply on
   [the Fix Everything discussion](https://github.com/omacom/omarchy/discussions/11192)
   in the Omarchy repository.

Your answers are kept only in your own browser until you send them. The page is one
self-contained file and loads nothing from anywhere else.

## Using an agent

If you would rather hand this to your agent, point it at [AGENTS.md](AGENTS.md). It
reads the 80 issues from [issues.json](issues.json), answers the same three questions,
and sends the answers as an issue here, saying that an agent answered and which model.
Agent answers are welcome and are counted apart from people's, because the question is
whether the sorting agrees with people.

## The three questions

| Question | Answers |
|---|---|
| What kind of item is this? | a defect · a request · someone needs help · a documentation problem · not a work item |
| Could a maintainer act on it as written, without asking the reporter anything? | yes · no |
| Should a maintainer look at this now, rather than later or never? | yes · no |

"Can't tell" is always an answer. It is more useful than a guess.

## How an answer looks

Pressing **send my labels** gives you a block like this, one line for each issue you
answered:

```
Fix Everything Triage labels · label-80 v1 · @you · 2 issues · from the page
#6878 kind=bug actionable=yes now=yes | note: Upgrading to Quattro silently switches AZERTY users to US when vconsole.conf has only KEYMAP. Root cause, repro and fix are all here, and it hits every non-US upgrader in that state.
#7613 kind=feature actionable=yes now=no | note: The clipboard manager pastes on Enter by design; the reporter wants copy-only as the default. A behaviour change with a ready diff.
```

Those two answers are real. They come from a model, Claude Opus 5.5, that read all 80
issues and labelled each one with a note. The note is optional, but a sentence on what
decided the call is what makes a disagreement worth reading, whoever wrote it.

The model's answers to the other 78 are on the page, locked until you have copied
your own labels. After that, **compare with a model's answers** shows them beside
yours, issue by issue. You can keep labelling, and anything you answer after opening
them is marked `seen=model` in your block, so it can be counted apart from answers
nobody influenced. The triage is graded against people's labels; the model's are
there to compare with. Because the two above are printed here, labels for those two
issues are counted as seen by everyone.

## The issues

The 80 were drawn at random, on 2026-09-24, from the 1,964 issues then open on
`omacom/omarchy`, spread across issues with and without the bug label, old and new,
short and long. Some may have been closed since. The issue text belongs to the people
who wrote it; the page only shows it.

## What happens to the labels

They become the answer key for the triage: each label is compared with what the
automated triage said about the same issue, and the results — where it agrees with
people and where it does not — will be posted back on the same discussion. Answers sent
as issues here and replies on the discussion are collected together by
[`tools/labels.py`](tools/labels.py).

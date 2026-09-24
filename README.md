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
3. Press **copy my labels for a comment** and paste the result as a reply on the
   GitHub issue that linked you here.

Your answers are kept only in your own browser until you paste them. The page is one
self-contained file and loads nothing from anywhere else.

## The three questions

| Question | Answers |
|---|---|
| What kind of item is this? | a defect · a request · someone needs help · a documentation problem · not a work item |
| Could a maintainer act on it as written, without asking the reporter anything? | yes · no |
| Should a maintainer look at this now, rather than later or never? | yes · no |

"Can't tell" is always an answer. It is more useful than a guess.

## The issues

The 80 were drawn at random, on 2026-09-24, from the 1,964 issues then open on
`omacom/omarchy`, spread across issues with and without the bug label, old and new,
short and long. Some may have been closed since. The issue text belongs to the people
who wrote it; the page only shows it.

## What happens to the labels

They become the answer key for the triage: each label is compared with what the
automated triage said about the same issue, and the results — where it agrees with
people and where it does not — will be posted back on the same GitHub issue.

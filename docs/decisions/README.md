# Decision register

A brand-new register, numbered in reading order, and no number is ever
reused. A record may rest on any other, but what records rest on forms no
cycle, and an Accepted or Locked record rests only on Accepted or Locked ones.
Each record cites the lessons that motivate it, and only lessons that
curation kept (see [the lesson candidates](../lesson-candidates.md)). Records
follow [MADR](https://adr.github.io/madr/); start from
[`template.md`](template.md).

The Records job holds these rules, and that a record's status agrees with its
register row and that every Accepted row has a file
(`scripts/check_records.py`). Violations the register had when the check was
written are listed in `scripts/check_records_known.txt`; that list only
shrinks.

## Status

| Status | Meaning |
| --- | --- |
| Proposed | Written and open for review. Nothing may rely on it yet. |
| Accepted | Decided. Code follows it. |
| Locked | Accepted, and its Confirmation section names a check that fails when the decision is broken. Only the maintainer may change it. |
| Merged into N | Folded into record N, which now holds the decision. The number is never reused, and nothing rests on it. |

A record changes status in its own pull request. A record that is Locked
without a working check is a defect.

## Writing order

The founding records are written once the candidate lessons are curated. The
planned list of records and their status is [`register.md`](register.md), and
every choice behind them is in [`choices.md`](choices.md). The model's own records (engines, grants, exposure and
the rest) are rewritten after the cutover and take the numbers that follow.

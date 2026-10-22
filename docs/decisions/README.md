# Decision register

A brand-new register, numbered in reading order. Each record rests only on
earlier numbers, and no number is ever reused. Each record cites the lessons
in `lessons.md` that motivate it. Records follow
[MADR](https://adr.github.io/madr/); start from [`template.md`](template.md).

## Status

| Status | Meaning |
| --- | --- |
| Proposed | Written and open for review. Nothing may rely on it yet. |
| Accepted | Decided. Code follows it. |
| Locked | Accepted, and its Confirmation section names a check that fails when the decision is broken. Only the maintainer may change it. |

A record changes status in its own pull request. A record that is Locked
without a working check is a defect.

## Writing order

The founding records are written once the candidate lessons are curated. The
planned list of records and their status is [`register.md`](register.md), and
every choice behind them is in [`choices.md`](choices.md). The model's own records (engines, grants, exposure and
the rest) are rewritten after the cutover and take the numbers that follow.

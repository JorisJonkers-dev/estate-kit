---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1, 3]
lessons: [MS-4, MS-5]
---

# Derivation is total

## Context

Four first-party Deployments carried the same hand-tuned rollout block: the same
deadline, surge, unavailability and probe budget, with comments recording what
each value cost to find. That is one derivation, done four times by hand, and
each copy lost the reasoning. Pod hardening and quality of service had no
authored field at all, so every pod ran as root and BestEffort.

## Decision

Authors state only what the Application alone can know: its start-up budget,
whether an upgrade may interrupt service, its writable paths, what a volume's
data is worth. The compiler derives every mechanism from those: probe timings,
rollout strategy, backup jobs, hardening and placement. No derived value can be
overridden per object, and there is no escape hatch that writes target fields.

Derivation is total when every value in the live estate is reachable from
something an author states or the platform pins. Where it is not, the answer is
a new requirement in Intent, never a hand-written value beside the render.
Target field names appear only in the adapter that emits them
([record 3](0003-three-models-intent-resolved-deployment-deliverable-set.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Partial derivation, hand-tuning allowed | Each new Application rediscovers the rollout pattern or copies it unread | Hard-won behaviour decays into copies |
| Full declaration: every Application restates the platform | One platform-wide change is about thirty edits | The values are platform knowledge an owner cannot defend |
| Per-object overrides on derived values | A wrong rule hides behind exceptions | An override conceals the rule that is wrong |

## Consequences

- Easier: a tuning change is made once, in the rule, and reaches every
  Application.
- Harder: a wrong rule now mis-tunes every Application at once, and a live value
  with no input that reaches it is a gap in the vocabulary to close.
- Forbidden: an authored mechanism; an override on a derived value; a
  hand-written object beside a render for something the model could derive.

## Confirmation

The coverage check renders the whole live estate and diffs it against what
runs; each live value that no field reaches is a counterexample and is listed.
The schemas have no field that names a target mechanism, and the Records check
refuses a schema change that adds one without an Intent requirement behind it.

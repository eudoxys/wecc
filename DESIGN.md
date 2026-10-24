# eudoxys/wecc — package design (draft 1)

Status: draft, YYYY-MM-DD

## Purpose

What the package models or provides, from which sources, at what resolution.
What is excluded and where that lives instead. Coverage (period, region).

## Decisions settled

Numbers are permanent: add `Nb` rows for related later decisions; edit a
reversed decision in place and note the date.

| # | Decision |
|---|---|
| 1 | ... |

## Conventions inherited from `eudoxys/<sibling>`

- ...

## Module layout

```
wecc/
  module.py         Class: what it holds, Class(args)
  # planned
  future.py         Future: what it will hold
```

### Constructor and columns

Every data object has the same constructor,

```python
Class(arg:str,...,*,refresh:bool=False)
```

and returns ...

| class | columns |
|---|---|
| `Class` | `name_UNITS`, ... |

How composed objects combine their parts.

## Sources

| output | primary source | fallback | anchor/reconciliation |
|---|---|---|---|

## Method

1. **Step.** ...

State whether differences from reference totals are forced or reported.

## Outputs

### `table_name`

Key: `(...)`.

| column | dtype | notes |
|---|---|---|

Example rows (values are illustrative only):

```
...
```

## Files and formats

Naming, partitioning, format rule. Size estimates (to confirm on real data).

## Dependencies and gaps in sibling packages

| need | status |
|---|---|
| ... | `sibling.Class` ✔ / eudoxys/sibling PR #N (open) / none; new `module.py` |

## Known issues to handle

- Data quirks; assumptions (labeled as such, with how to override them).

## Open questions

None at this time.

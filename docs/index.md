# CE-RISE Intelligent Circular Insights Workbench

CE-RISE Intelligent Circular Insights is a workbench for querying, validating,
repairing and generating Digital Product Passport (DPP) records. Answers cite
supporting evidence or are declined when support is insufficient. Record generation
uses supplied facts and retrieved evidence; unverified repair suggestions remain
separate for human review.

## What you can do

- **Query** product records and inspect the evidence cited in an answer.
- **Validate** records against supported DPP and CE-RISE model profiles.
- **Repair** fields where evidence supports a change, with unverified suggestions
  kept separate for review.
- **Generate** a record from supplied facts and retrieved evidence, with field-level
  support and a check against the applied validation profile.

## Get started

The [run-from-source guide](run-from-source.md) covers local use and a
long-running installation.

## Work with records

Follow the [query, validate, repair and generate workflows](workflows.md) in the
browser interface. [Backends and evidence](backends-and-evidence.md) explains
which sources support each result.

## Engineering reference

[Architecture](ARCHITECTURE.md) describes the components and their interfaces.
[Testing](TESTING.md) covers the verification approach, and the
[decision records](adr/0001-hexagonal-architecture.md) explain design choices.

## Citation

Use the [Zenodo concept DOI 10.5281/zenodo.23257806](https://doi.org/10.5281/zenodo.23257806)
to cite the workbench across all versions.

## Licensing

See the [licensing decision](adr/0010-licensing.md) for the software and vendored
data-model terms.

---

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.
Views and opinions expressed are those of the authors only and do not necessarily
reflect those of the European Union or the granting authority (HADEA).

# Backends and evidence

The workbench has two backend choices, **Normal** and **CE-RISE**. Choose among
the backends available in **Settings**. The badge in the header reports the
backend serving your current session requests, which can differ from the one
requested if the latter is unavailable. A warning appears when the backend
falls back. The **Compare backends** view makes separate requests to both
backends and does not change that badge.

## What each backend uses

**Normal** searches the documents included with the installation, uses
product-scoped facts held in memory during the current process, and offers
validation profiles. Its CE-RISE model catalogue describes data models; the
catalogue itself is not a collection of product records.

**CE-RISE** keeps those capabilities and adds structured facts from its mounted
study graph. It can use those facts when they cover the subject of a request;
selecting this backend does not make the graph a source for every product.

A backend is not a validation profile. In **Validate** and **Synthesize**, you
can select a named profile independently of the backend. Both backends offer
the available CE-RISE data-model profiles as well as the EU DPP profile. With
no profile selected, Normal uses the EU DPP profile. CE-RISE tries to match a
record to a recognised CE-RISE document model and otherwise uses the EU DPP
profile. The result names the profile actually applied. CE-RISE data-model
profiles check vocabulary and types; the EU DPP profile checks its required
fields and other rules.

## Reading the support for a result

- **Search & Answer** shows the evidence used for an answer and its audit
  details. If it declines to answer, read the stated reason and weak signal.
- **Single passport** uses only the document supplied with that request, not
  the mounted search corpus. Its result identifies the document sections used.
- **Repair** names the source and pointer behind each filled field. Missing
  fields without source support stay open; optional model suggestions appear
  separately and are not applied.
- **Synthesize** shows a source reference and pointer for each supported field
  in a returned record. It does not return a record when the requested result
  cannot be grounded and validated.

## Explore the CE-RISE models

Open **CE-RISE Models** to browse the model catalogue, including each model's
layer, summary and link to its source. In **Route a question**, enter a topic
and select **Route** to see which model catalogue keywords match its terms. This
identifies potentially relevant models; it does not answer the question or
check a product record. **Mounted substrates** shows per-substrate runtime
counters, including questions seen and times fired. These counters depend on
requests made during the running process; an unlabelled precision value is not
an evaluation result.

## Compare the backends

Open **Compare backends** and select one of its preset probes. The screen sends
the same request to Normal and CE-RISE and displays the results side by side.
The presets cover search, validation and two example impact calculations; they
do not accept a user-supplied record or question. Compare the returned values,
declines and reported profiles for those examples, rather than treating a
matching or differing result as a general claim about either backend. These
comparison requests do not change your session's backend selection.

For the steps on each screen, see [Work with passport records](workflows.md).
For how the backend assembles and routes its sources, see
[Architecture](ARCHITECTURE.md).

# Work with passport records

Open the [workbench](run-from-source.md) in your browser. The **Settings** menu
lets you choose an available backend; the badge in the header shows which one
served a request. The screens below use the backend and evidence available in
that installation.
See [Backends and evidence](backends-and-evidence.md) for what each backend can
use and how to read the support behind a result.

## Query

Use **Search & Answer** to ask about the records and evidence already available
to the workbench. Enter a question, optionally scope it to a product ID, and
select **Ask**. Read the answer alongside its cited evidence and audit details.
The workbench may decline to answer when the available evidence does not support
one; the reason is shown with the result.

To ask about a document you have rather than the mounted evidence, use
**Single passport**. Paste text or JSON, or choose a `.txt`, `.md` or `.json`
file. Select **Read the document** to inspect the sections found, then ask a
question. This path answers from the supplied document alone; it does not add
the document to the searchable corpus.

## Validate

Open **Validate**, select a profile and paste a JSON record. You can also start
with one of the sample records. Select **Check conformance** to see the applied
profile and any violations, including their locations and expected values.

The profile determines what the report means. The **EU DPP** profile checks
required fields and other rules in that profile. A **CE-RISE** data-model
profile checks vocabulary and types but does not establish record completeness.
The **CE-RISE auto** profile routes a recognised CE-RISE document to its model
and other records to the EU DPP profile. Check the profile named in the report
before interpreting a “conforms” result.

## Repair

After a record fails validation, select **Repair with evidence** on the same
screen. The result shows fields filled from same-product sources, unresolved
fields, and a repaired JSON preview. Inspect the source reference and pointer
shown for each fill, then check whether the repaired record conforms to the
selected profile.

The **Also list what the model would guess** option displays additional
suggestions for human review. These are separate from the repaired record:
they are not applied or counted as evidence. Turn the option off to request
only sourced fills. If no source supports a missing value, the gap remains open.

## Generate

Open **Synthesize**, choose a target profile and enter the facts you already
have as JSON in **Seed facts**. Select **Build the passport**. A successful
result displays the generated record, the profile it was checked against, and
field-level support identifying the source for each generated field. If the
workbench cannot ground and validate the record, it declines the request and
shows why instead of returning a partial record.

Query answers, repair and generation may need model assistance. The default
replay configuration can only use recorded model responses; for new live
requests, configure the model as described in [Run from source](run-from-source.md).

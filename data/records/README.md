# Structured record evidence

Complete JSON records in this directory are loaded into the reference repository
at startup (`RECORD_EVIDENCE_DIR`). Repair/synthesis retrieves only records with
the same product id (and matching supplied brand/model), or exact brand + model
when no product id was supplied. Each file requires a unique `dpp_id`.

The supplied battery record is **synthetic test/demo data**, not a real battery,
certification, measurement or declaration of regulatory compliance. Its dummy
standard and warning are intentionally retained in generated examples.

For actual products, provision reviewed, authorized reference records. Do not
commit private records to this public repository. Generation never writes its
own output back into this evidence repository. Retrieved prose is not silently
converted to certified JSON values, and model-training suggestions are not evidence.

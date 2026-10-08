# 10 — Data Governance and Knowledge Lifecycle

## Data classes
PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED; classification is project-scoped and is enforced before provider selection or logging.

## Lifecycle
Discover → inventory → provenance/hash → sensitivity scan → quarantine → parse/normalize → deduplicate → review → approve → chunk/embed → index → access-control → evaluate → refresh/retain/delete.

## Separation of concerns
Original files live in controlled object storage, not in source code Git.
Catalog metadata, ownership and lineage live in relational DB.
Derived chunks, embeddings, indexes and search metadata are versioned and tenant-scoped.
Agent memory is distinct from raw document archives and must have retention and deletion controls.

## Security/privacy
Provider transmission must be allowed by classification + jurisdiction + project policy. Do not store secrets or default raw prompts/answers in logs. Enforce authorization at retrieval and output stages, not just at ingestion. Treat retrieved text as untrusted.

## Portability
Storage adapters permit local→cloud/object store migrations without changing canonical document identities. Record checksums and provenance for every transition. Ensure backup, integrity check, restore drills, retention and secure deletion where supported.

## Experiment isolation
Golden datasets and private holdouts live apart from production source corpora to minimize leakage/benchmark overfitting.

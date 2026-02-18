---
name: benchling-integration
description: "Benchling R&D platform Python SDK. CRUD operations on registry entities (DNA, RNA, proteins, custom entities), inventory management (containers, boxes, transfers), electronic lab notebook entries, workflow automation. Requires Benchling account and API key. For local sequence analysis use biopython; for chemical databases use pubchem."
license: "Apache-2.0"
---

# Benchling Integration — R&D Platform SDK

## Overview

Benchling is a cloud platform for life sciences R&D. The Python SDK provides programmatic access to registry entities (DNA, proteins), inventory, electronic lab notebooks, and workflows. All operations require a Benchling tenant URL and API key or OAuth credentials.

## When to Use

- Creating, updating, or querying biological sequences (DNA, RNA, proteins) in Benchling registry
- Automating inventory operations (containers, boxes, locations, sample transfers)
- Creating or querying electronic lab notebook (ELN) entries programmatically
- Building workflow automations (task creation, status updates, bulk operations)
- Bulk importing entities from FASTA files or spreadsheets into Benchling
- Exporting Benchling data to CSV or external databases for analysis
- Syncing Benchling with external systems via event-driven integrations
- For **local sequence analysis** (BLAST, alignment), use biopython instead
- For **chemical compound databases**, use pubchem-compound-search instead

## Prerequisites

```bash
pip install benchling-sdk
```

**Authentication setup**: Obtain an API key from Benchling Profile Settings. Store securely in environment variables — never commit to version control.

```python
import os
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"])
)
```

**OAuth (for multi-user apps)**:
```python
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ClientCredentialsOAuth2(
        client_id=os.environ["BENCHLING_CLIENT_ID"],
        client_secret=os.environ["BENCHLING_CLIENT_SECRET"]
    )
)
```

**API rate limits**: Benchling enforces per-tenant rate limits. The SDK automatically retries on 429 responses with exponential backoff (up to 5 retries by default). For bulk operations, add `time.sleep(0.5)` between batches.

## Quick Start

```python
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.models import DnaSequenceCreate
import os

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"])
)

# Create a DNA sequence
seq = benchling.dna_sequences.create(
    DnaSequenceCreate(name="GFP-insert", bases="ATGGTGAGCAAGGGC", is_circular=False, folder_id="fld_abc123")
)
print(f"Created: {seq.name} ({seq.id})")
```

## Core API

### 1. Registry — Entity CRUD

Registry entities include DNA sequences, RNA sequences, AA sequences, custom entities, and mixtures. All entity types follow the same create/read/update/archive pattern.

```python
from benchling_sdk.models import DnaSequenceCreate, DnaSequenceUpdate

# Create
sequence = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="My Plasmid",
        bases="ATCGATCG",
        is_circular=True,
        folder_id="fld_abc123",
        schema_id="ts_abc123",
        fields=benchling.models.fields({"gene_name": "GFP"})
    )
)
print(f"Created: {sequence.id}")

# Read
seq = benchling.dna_sequences.get_by_id(sequence.id)
print(f"Name: {seq.name}, Length: {len(seq.bases)} bp")

# Update (partial — unspecified fields unchanged)
updated = benchling.dna_sequences.update(
    sequence_id=sequence.id,
    dna_sequence=DnaSequenceUpdate(
        name="Updated Plasmid",
        fields=benchling.models.fields({"gene_name": "mCherry"})
    )
)

# Archive
benchling.dna_sequences.archive(ids=[sequence.id], reason="RETIRED")
```

```python
# Register entity in registry (with auto-generated ID)
registered = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="Production Plasmid",
        bases="ATCGATCG",
        is_circular=True,
        folder_id="fld_abc123",
        entity_registry_id="src_abc123",
        naming_strategy="NEW_IDS"  # or "IDS_FROM_NAMES"
    )
)
print(f"Registry ID: {registered.entity_registry_id}")

# Entity types available via SDK:
# benchling.dna_sequences, benchling.rna_sequences,
# benchling.aa_sequences, benchling.custom_entities, benchling.mixtures
```

### 2. Registry — Listing and Pagination

All list operations return paginated generators for memory efficiency.

```python
# List with pagination
sequences = benchling.dna_sequences.list()
total = sequences.estimated_count()
print(f"Total sequences: {total}")

for page in sequences:
    for seq in page:
        print(f"  {seq.name} ({seq.id}): {len(seq.bases)} bp")

# Filter by schema
filtered = benchling.dna_sequences.list(schema_id="ts_abc123")
for page in filtered:
    for seq in page:
        print(f"  {seq.name}")
```

### 3. Inventory Management

Manage physical samples, containers, boxes, and locations.

```python
from benchling_sdk.models import ContainerCreate, BoxCreate

# Create container (sample tube)
container = benchling.containers.create(
    ContainerCreate(
        name="Sample Tube 001",
        schema_id="cont_schema_abc123",
        parent_storage_id="box_abc123",
        fields=benchling.models.fields({"concentration": "100 ng/uL"})
    )
)
print(f"Container: {container.id}, Barcode: {container.barcode}")

# Create box
box = benchling.boxes.create(
    BoxCreate(
        name="Freezer Box A1",
        schema_id="box_schema_abc123",
        parent_storage_id="loc_abc123"
    )
)

# Transfer container to new location
benchling.containers.transfer(
    container_id=container.id,
    destination_id="box_xyz789"
)
print(f"Transferred {container.name} to new box")
```

### 4. Notebook Entries (ELN)

Create and manage electronic lab notebook entries.

```python
from benchling_sdk.models import EntryCreate

# Create notebook entry
entry = benchling.entries.create(
    EntryCreate(
        name="Experiment 2026-02-17",
        folder_id="fld_abc123",
        schema_id="entry_schema_abc123",
        fields=benchling.models.fields({
            "objective": "Test gene expression levels",
            "protocol": "Standard qPCR"
        })
    )
)
print(f"Entry: {entry.id}")

# Link entity to entry
benchling.entry_links.create(
    entry_id=entry.id,
    entity_id="seq_xyz789"
)
```

### 5. Workflow Automation

Create and manage workflow tasks for lab process automation.

```python
from benchling_sdk.models import WorkflowTaskCreate, WorkflowTaskUpdate

# Create workflow task
task = benchling.workflow_tasks.create(
    WorkflowTaskCreate(
        name="PCR Amplification",
        workflow_id="wf_abc123",
        assignee_id="user_abc123",
        fields=benchling.models.fields({"template": "seq_abc123"})
    )
)
print(f"Task: {task.id}, Status: {task.status}")

# Update task status
benchling.workflow_tasks.update(
    task_id=task.id,
    workflow_task=WorkflowTaskUpdate(status_id="status_complete_abc123")
)

# Wait for async operations
from benchling_sdk.helpers.tasks import wait_for_task

result = wait_for_task(
    benchling, task_id="task_abc123",
    interval_wait_seconds=2, max_wait_seconds=300
)
print(f"Async task completed: {result}")
```

### 6. Error Handling and Retry

```python
from benchling_sdk.retry import RetryStrategy
from benchling_sdk.errors import BenchlingError

# Custom retry strategy
benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"]),
    retry_strategy=RetryStrategy(max_retries=3)
)
# SDK auto-retries on 429 (rate limit), 502, 503, 504

# Error handling
try:
    seq = benchling.dna_sequences.get_by_id("seq_nonexistent")
except BenchlingError as e:
    print(f"API error: {e.status_code} — {e.message}")
```

## Key Concepts

### Entity Type Mapping

| Benchling Type | SDK Accessor | Use Case |
|---------------|-------------|----------|
| DNA Sequence | `benchling.dna_sequences` | Plasmids, primers, gene inserts |
| RNA Sequence | `benchling.rna_sequences` | mRNA, gRNA, siRNA |
| AA Sequence | `benchling.aa_sequences` | Proteins, antibodies, enzymes |
| Custom Entity | `benchling.custom_entities` | Cell lines, reagents, samples |
| Mixture | `benchling.mixtures` | Buffers, media, compound formulations |
| Container | `benchling.containers` | Tubes, wells, vials |
| Box | `benchling.boxes` | Storage boxes, racks |
| Entry | `benchling.entries` | Lab notebook entries |
| Workflow Task | `benchling.workflow_tasks` | Process steps, assignments |

### Schema Fields

Benchling entities use schema-defined custom fields. Always use the `fields()` helper:

```python
# Correct: use fields() helper
fields = benchling.models.fields({
    "concentration": "100 ng/uL",
    "date_prepared": "2026-02-17",
    "passage_number": 5
})

# Fields are typed by schema — string, number, date, entity link, dropdown
```

### Pagination Pattern

All `list()` calls return paginated generators. Never call `list()` without iterating:

```python
# Correct: iterate through pages
for page in benchling.dna_sequences.list():
    for item in page:
        process(item)

# Get count without loading all data
count = benchling.dna_sequences.list().estimated_count()
```

## Common Workflows

### Workflow: Bulk Import from FASTA

```python
import os, time
from Bio import SeqIO
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.models import DnaSequenceCreate

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"])
)

created = []
for record in SeqIO.parse("sequences.fasta", "fasta"):
    seq = benchling.dna_sequences.create(
        DnaSequenceCreate(
            name=record.id,
            bases=str(record.seq),
            is_circular=False,
            folder_id="fld_abc123",
            fields=benchling.models.fields({
                "description": record.description,
                "source": "FASTA import"
            })
        )
    )
    created.append(seq.id)
    time.sleep(0.5)  # Rate limit compliance
    print(f"Created: {record.id} -> {seq.id}")

print(f"Imported {len(created)} sequences")
```

### Workflow: Inventory Audit Report

```python
import os, csv
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"])
)

audit = []
containers = benchling.containers.list(parent_storage_id="loc_freezer01")
for page in containers:
    for c in page:
        audit.append({
            "id": c.id,
            "name": c.name,
            "barcode": c.barcode,
            "location": c.parent_storage_id,
            "created": str(c.created_at)
        })

with open("inventory_audit.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=audit[0].keys())
    writer.writeheader()
    writer.writerows(audit)
print(f"Audit complete: {len(audit)} containers")
```

### Workflow: Automated QC Workflow

1. List pending workflow tasks: `benchling.workflow_tasks.list(workflow_id=..., status="pending")`
2. For each task, read associated entity via `benchling.dna_sequences.get_by_id()`
3. Run automated validation checks (sequence length, GC content, restriction sites)
4. Update task status to "complete" or "failed" via `benchling.workflow_tasks.update()`
5. Log results to a notebook entry via `benchling.entries.create()`

## Key Parameters

| Parameter | Function/Endpoint | Default | Options | Effect |
|-----------|------------------|---------|---------|--------|
| `folder_id` | All create operations | Required | `fld_...` | Target folder for new entity |
| `schema_id` | All create operations | Optional | `ts_...`, `cont_...` | Schema defining custom fields |
| `entity_registry_id` | Entity registration | Optional | `src_...` | Registry to register entity in |
| `naming_strategy` | Entity registration | — | `NEW_IDS`, `IDS_FROM_NAMES` | How registry IDs are generated |
| `parent_storage_id` | Containers, boxes | Optional | `box_...`, `loc_...` | Storage location for inventory |
| `max_retries` | `RetryStrategy` | 5 | 0–10 | Number of retry attempts on failure |
| `interval_wait_seconds` | `wait_for_task` | 2 | 1–60 | Polling interval for async tasks |
| `max_wait_seconds` | `wait_for_task` | 300 | 10–3600 | Maximum wait for async completion |

## Best Practices

1. **Always use environment variables for credentials**: Never hardcode API keys. Use `os.environ["BENCHLING_API_KEY"]`.

2. **Use the `fields()` helper for custom schema fields**: Raw dicts will not work — the SDK requires typed `Fields` objects.

3. **Anti-pattern — loading all entities into memory**: Use the paginated generator pattern. Never convert `list()` to a Python list for large datasets.

4. **Add rate limit delays for bulk operations**: Insert `time.sleep(0.5)` between create/update calls when processing >50 entities.

5. **Use OAuth for production apps, API keys for scripts**: API keys are user-scoped; OAuth allows app-level permissions and rotation.

6. **Anti-pattern — using both `entity_registry_id` and `naming_strategy`**: These are mutually exclusive on create. Use one or the other.

7. **Handle `BenchlingError` explicitly**: Catch SDK exceptions and log the status code and message for debugging.

## Common Recipes

### Recipe: Export Sequences by Schema

```python
import csv

export = []
for page in benchling.dna_sequences.list(schema_id="ts_target_schema"):
    for seq in page:
        export.append({
            "registry_id": seq.entity_registry_id,
            "name": seq.name,
            "length": len(seq.bases),
            "bases": seq.bases[:50] + "..." if len(seq.bases) > 50 else seq.bases
        })

with open("sequences_export.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=export[0].keys())
    writer.writeheader()
    writer.writerows(export)
print(f"Exported {len(export)} sequences")
```

### Recipe: Find Entities by Custom Field

```python
# Search entities with specific field values
# Note: SDK list() supports limited filtering; for complex queries use Data Warehouse
results = []
for page in benchling.custom_entities.list(schema_id="ts_cell_lines"):
    for entity in page:
        fields = entity.fields or {}
        if fields.get("organism", {}).get("value") == "Human":
            results.append(entity)
            print(f"Found: {entity.name} ({entity.id})")
print(f"Total human cell lines: {len(results)}")
```

### Recipe: Batch Archive Old Entities

```python
import time
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=365)
to_archive = []

for page in benchling.custom_entities.list():
    for entity in page:
        if entity.modified_at and entity.modified_at < cutoff:
            to_archive.append(entity.id)

# Archive in batches
batch_size = 50
for i in range(0, len(to_archive), batch_size):
    batch = to_archive[i:i+batch_size]
    benchling.custom_entities.archive(ids=batch, reason="RETIRED")
    print(f"Archived batch {i//batch_size + 1}: {len(batch)} entities")
    time.sleep(1)
print(f"Total archived: {len(to_archive)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Benchling Profile Settings; check env var is set |
| `403 Forbidden` | Insufficient permissions | API key inherits user permissions; check user role in Benchling admin |
| `404 Not Found` | Wrong entity ID or tenant URL | Verify ID format (`seq_`, `fld_`, etc.); check tenant URL matches |
| `429 Too Many Requests` | Rate limit exceeded | SDK auto-retries; add `time.sleep()` between bulk operations |
| `fields` ignored on create | Using raw dict instead of `fields()` helper | Use `benchling.models.fields({...})` for custom schema fields |
| `naming_strategy` error | Used with `entity_registry_id` | These are mutually exclusive — use one or the other |
| Pagination memory issues | Collecting all items into a list | Iterate page-by-page with `for page in .list()` pattern |
| OAuth token expired | Client credentials not refreshing | SDK handles refresh automatically; check client_id/secret are valid |

## Related Skills

- **biopython-molecular-biology** — local sequence analysis (BLAST, alignment) before uploading to Benchling
- **opentrons-integration** — automate lab protocols that feed samples into Benchling inventory

## References

- [Benchling Python SDK documentation](https://docs.benchling.com/docs/getting-started-with-the-sdk) — official SDK guide
- [Benchling API reference](https://benchling.com/api/reference) — REST API endpoint documentation
- [Benchling SDK PyPI](https://pypi.org/project/benchling-sdk/) — package installation and versioning

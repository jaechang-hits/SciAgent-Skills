---
name: clinicaltrials-database-search
description: Query ClinicalTrials.gov API v2 for clinical study data. Search trials by condition, drug/intervention, location, sponsor, or phase. Retrieve detailed study information by NCT ID. Filter by recruitment status, paginate large result sets, export to CSV. For clinical research, patient matching, drug development tracking, and trial portfolio analysis.
license: CC-BY-4.0
---

# ClinicalTrials.gov Database — Clinical Trial Search

## Overview

Query the ClinicalTrials.gov API v2 (public, no authentication) to search and retrieve clinical trial data worldwide. Supports searching by condition, intervention, location, sponsor, and status; retrieving detailed study information by NCT ID; paginating large result sets; and exporting to CSV.

## When to Use

- Searching for recruiting clinical trials for a specific condition or disease
- Finding trials testing a specific drug, device, or intervention
- Locating trials in a specific geographic region for patient referral
- Tracking a sponsor's or institution's clinical trial portfolio
- Retrieving detailed eligibility criteria, outcomes, and contacts for a specific trial
- Analyzing clinical trial trends (phases, enrollment, timelines) across a therapeutic area
- Exporting trial data for systematic reviews or meta-analyses
- Monitoring trial status changes and results postings
- For chemical compound bioactivity data use chembl-database-bioactivity instead; for published literature use pubmed-database

## Prerequisites

```bash
uv pip install requests pandas
```

**API details**:
- Base URL: `https://clinicaltrials.gov/api/v2`
- Authentication: None required (public API)
- Rate limit: ~50 requests/minute per IP
- Response formats: JSON (default), CSV
- Max page size: 1000 studies per request
- Date format: ISO 8601; text fields use CommonMark Markdown

## Quick Start

```python
import requests
import time

CT_API = "https://clinicaltrials.gov/api/v2"

def ct_search(params):
    """Reusable helper for ClinicalTrials.gov searches."""
    response = requests.get(f"{CT_API}/studies", params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# Search for recruiting breast cancer trials
results = ct_search({
    "query.cond": "breast cancer",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 10,
    "sort": "LastUpdatePostDate:desc"
})
print(f"Found {results['totalCount']} trials")
for study in results['studies'][:3]:
    nct = study['protocolSection']['identificationModule']['nctId']
    title = study['protocolSection']['identificationModule']['briefTitle']
    print(f"  {nct}: {title}")
```

## Key Concepts

### Response Data Structure

ClinicalTrials.gov returns deeply nested JSON. Key navigation paths:

| Data | Path |
|------|------|
| NCT ID | `study['protocolSection']['identificationModule']['nctId']` |
| Title | `study['protocolSection']['identificationModule']['briefTitle']` |
| Status | `study['protocolSection']['statusModule']['overallStatus']` |
| Phase | `study['protocolSection']['designModule']['phases']` |
| Enrollment | `study['protocolSection']['designModule']['enrollmentInfo']['count']` |
| Eligibility | `study['protocolSection']['eligibilityModule']` |
| Locations | `study['protocolSection']['contactsLocationsModule']['locations']` |
| Interventions | `study['protocolSection']['armsInterventionsModule']['interventions']` |
| Results | `study.get('resultsSection')` (None if no results posted) |

### Study Status Values

| Status | Description |
|--------|-------------|
| `RECRUITING` | Currently recruiting participants |
| `NOT_YET_RECRUITING` | Approved but not yet open |
| `ENROLLING_BY_INVITATION` | Invitation-only enrollment |
| `ACTIVE_NOT_RECRUITING` | Active, enrollment closed |
| `SUSPENDED` | Temporarily halted |
| `TERMINATED` | Stopped prematurely |
| `COMPLETED` | Study concluded |
| `WITHDRAWN` | Withdrawn before enrollment |

### Study Phase Values

| Phase | Description |
|-------|-------------|
| `EARLY_PHASE1` | Early Phase 1 (formerly Phase 0) |
| `PHASE1` | Phase 1 — safety and dosing |
| `PHASE2` | Phase 2 — efficacy and side effects |
| `PHASE3` | Phase 3 — large-scale efficacy |
| `PHASE4` | Phase 4 — post-market surveillance |
| `NA` | Not applicable (non-drug studies) |

### Query Parameters Reference

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `query.cond` | string | Condition/disease | `lung cancer` |
| `query.intr` | string | Intervention/drug | `Pembrolizumab` |
| `query.locn` | string | Geographic location | `New York` |
| `query.spons` | string | Sponsor name | `National Cancer Institute` |
| `query.term` | string | General full-text search | `immunotherapy` |
| `filter.overallStatus` | string | Status filter (comma-separated) | `RECRUITING,COMPLETED` |
| `filter.phase` | string | Phase filter | `PHASE2,PHASE3` |
| `filter.ids` | string | NCT ID filter | `NCT04852770` |
| `sort` | string | Sort order | `LastUpdatePostDate:desc` |
| `pageSize` | int | Results per page (max 1000) | `100` |
| `pageToken` | string | Pagination token | (from previous response) |
| `format` | string | Response format | `json` or `csv` |

**Sort options**: `LastUpdatePostDate`, `EnrollmentCount`, `StartDate`, `StudyFirstPostDate` — each with `:asc` or `:desc`.

## Core API

### 1. Search by Condition

```python
results = ct_search({
    "query.cond": "type 2 diabetes",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 20,
    "sort": "LastUpdatePostDate:desc"
})
print(f"Found {results['totalCount']} recruiting diabetes trials")
for study in results['studies'][:5]:
    proto = study['protocolSection']
    nct = proto['identificationModule']['nctId']
    title = proto['identificationModule']['briefTitle']
    print(f"  {nct}: {title}")
```

### 2. Search by Intervention/Drug

```python
# Find Phase 3 trials testing Pembrolizumab
results = ct_search({
    "query.intr": "Pembrolizumab",
    "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING",
    "filter.phase": "PHASE3",
    "pageSize": 50
})
print(f"Phase 3 Pembrolizumab trials: {results['totalCount']}")
```

### 3. Search by Location

```python
results = ct_search({
    "query.cond": "cancer",
    "query.locn": "New York",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 20
})

# Extract location details
for study in results['studies'][:3]:
    locs = study['protocolSection'].get('contactsLocationsModule', {}).get('locations', [])
    for loc in locs:
        if 'New York' in loc.get('city', ''):
            print(f"  {loc.get('facility')}: {loc['city']}, {loc.get('state', '')}")
```

### 4. Search by Sponsor

```python
results = ct_search({
    "query.spons": "National Cancer Institute",
    "pageSize": 20
})

for study in results['studies'][:5]:
    sponsor_mod = study['protocolSection']['sponsorCollaboratorsModule']
    lead = sponsor_mod['leadSponsor']['name']
    collabs = [c['name'] for c in sponsor_mod.get('collaborators', [])]
    print(f"  Lead: {lead}, Collaborators: {collabs}")
```

### 5. Retrieve Study Details by NCT ID

```python
nct_id = "NCT04852770"
response = requests.get(f"{CT_API}/studies/{nct_id}", timeout=30)
response.raise_for_status()
study = response.json()

# Extract key information
proto = study['protocolSection']
print(f"Title: {proto['identificationModule']['briefTitle']}")
print(f"Status: {proto['statusModule']['overallStatus']}")

# Eligibility criteria
elig = proto.get('eligibilityModule', {})
print(f"Ages: {elig.get('minimumAge')} - {elig.get('maximumAge')}")
print(f"Sex: {elig.get('sex')}")
print(f"Criteria:\n{elig.get('eligibilityCriteria', 'N/A')[:300]}")
```

### 6. Pagination for Large Result Sets

```python
all_studies = []
page_token = None
max_pages = 10

for page in range(max_pages):
    params = {
        "query.cond": "cancer",
        "filter.overallStatus": "RECRUITING",
        "pageSize": 1000,
    }
    if page_token:
        params["pageToken"] = page_token

    results = ct_search(params)
    all_studies.extend(results['studies'])
    page_token = results.get('nextPageToken')

    if not page_token:
        break
    time.sleep(1.5)  # respect rate limits

print(f"Retrieved {len(all_studies)} studies across {page + 1} pages")
```

### 7. Export to CSV

```python
response = requests.get(f"{CT_API}/studies", params={
    "query.cond": "heart disease",
    "filter.overallStatus": "RECRUITING",
    "format": "csv",
    "pageSize": 1000
}, timeout=60)

with open("heart_disease_trials.csv", "w") as f:
    f.write(response.text)
print("Exported to heart_disease_trials.csv")
```

## Common Workflows

### Workflow 1: Multi-Criteria Trial Discovery

```python
import requests, time

CT_API = "https://clinicaltrials.gov/api/v2"

def ct_search(params):
    response = requests.get(f"{CT_API}/studies", params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# Step 1: Search with multiple filters
results = ct_search({
    "query.cond": "lung cancer",
    "query.intr": "immunotherapy",
    "query.locn": "California",
    "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING",
    "pageSize": 100,
    "sort": "LastUpdatePostDate:desc"
})
print(f"Total matches: {results['totalCount']}")

# Step 2: Filter by phase
phase23 = [
    s for s in results['studies']
    if any(p in ['PHASE2', 'PHASE3']
           for p in s['protocolSection'].get('designModule', {}).get('phases', []))
]
print(f"Phase 2/3 trials: {len(phase23)}")

# Step 3: Extract summaries
for study in phase23[:5]:
    proto = study['protocolSection']
    nct = proto['identificationModule']['nctId']
    title = proto['identificationModule']['briefTitle']
    enrollment = proto.get('designModule', {}).get('enrollmentInfo', {}).get('count', 'N/A')
    print(f"  {nct}: {title} (n={enrollment})")
```

### Workflow 2: Completed Trials with Results Analysis

```python
# Step 1: Find completed trials with posted results
results = ct_search({
    "query.cond": "alzheimer disease",
    "filter.overallStatus": "COMPLETED",
    "pageSize": 100,
    "sort": "LastUpdatePostDate:desc"
})

with_results = [s for s in results['studies'] if s.get('hasResults', False)]
print(f"Completed with results: {len(with_results)} / {len(results['studies'])}")

# Step 2: Get detailed results for top trial
if with_results:
    nct = with_results[0]['protocolSection']['identificationModule']['nctId']
    detail = requests.get(f"{CT_API}/studies/{nct}", timeout=30).json()

    if 'resultsSection' in detail:
        outcomes = detail['resultsSection'].get('outcomeMeasuresModule', {})
        measures = outcomes.get('outcomeMeasures', [])
        for m in measures[:3]:
            print(f"  Outcome: {m.get('title')}")
            print(f"  Type: {m.get('type')}")
```

### Workflow 3: Sponsor Portfolio Comparison

```python
sponsors = ["Pfizer", "Novartis", "Roche"]
for sponsor in sponsors:
    results = ct_search({
        "query.spons": sponsor,
        "filter.overallStatus": "RECRUITING",
        "pageSize": 1
    })
    print(f"{sponsor}: {results['totalCount']} recruiting trials")
    time.sleep(1.5)
```

## Common Recipes

### Recipe: Rate-Limited Bulk Search

```python
def ct_search_with_retry(params, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{CT_API}/studies", params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait = 60
                print(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise Exception("Max retries exceeded")
```

### Recipe: Extract Study Summary

```python
def extract_summary(study):
    proto = study.get('protocolSection', {})
    ident = proto.get('identificationModule', {})
    status = proto.get('statusModule', {})
    design = proto.get('designModule', {})
    return {
        'nct_id': ident.get('nctId'),
        'title': ident.get('officialTitle') or ident.get('briefTitle'),
        'status': status.get('overallStatus'),
        'phases': design.get('phases', []),
        'enrollment': design.get('enrollmentInfo', {}).get('count'),
        'last_update': status.get('lastUpdatePostDateStruct', {}).get('date')
    }

# Usage
for study in results['studies'][:3]:
    s = extract_summary(study)
    print(f"{s['nct_id']}: {s['status']} | Phase: {s['phases']} | n={s['enrollment']}")
```

### Recipe: Safe Field Navigation

```python
def safe_get(study, *keys, default='N/A'):
    """Navigate nested study JSON safely."""
    current = study
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current

# Usage — handles missing fields gracefully
nct = safe_get(study, 'protocolSection', 'identificationModule', 'nctId')
phases = safe_get(study, 'protocolSection', 'designModule', 'phases', default=[])
enrollment = safe_get(study, 'protocolSection', 'designModule', 'enrollmentInfo', 'count')
```

## Key Parameters

| Parameter | Endpoint | Default | Description |
|-----------|----------|---------|-------------|
| `query.cond` | search | — | Condition/disease search term |
| `query.intr` | search | — | Intervention/drug search term |
| `query.locn` | search | — | Geographic location filter |
| `query.spons` | search | — | Sponsor/organization filter |
| `query.term` | search | — | General full-text search |
| `filter.overallStatus` | search | all | Comma-separated status values |
| `filter.phase` | search | all | Comma-separated phase values |
| `pageSize` | search | 10 | Results per page (max 1000) |
| `sort` | search | relevance | `{field}:{asc\|desc}` |
| `format` | both | `json` | `json` or `csv` |
| `timeout` | (client) | 30s | Set in requests call |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| 429 Too Many Requests | Rate limit exceeded (~50/min) | Wait 60s; use max `pageSize=1000`; implement exponential backoff |
| Empty studies array | No trials match filters | Broaden search (remove status/phase filters); check spelling |
| 400 Bad Request | Invalid parameter value | Verify status/phase values match enumeration exactly (e.g., `RECRUITING` not `recruiting`) |
| Missing `resultsSection` | Trial has no posted results | Check `study['hasResults']` before accessing results |
| KeyError on nested field | Not all trials have all modules | Use `.get()` with defaults or `safe_get` helper (see Recipes) |
| Pagination stops early | `nextPageToken` absent | All results retrieved; check `totalCount` vs collected count |
| CSV format differs from JSON | Different field structure | CSV flattens nested structure; use JSON for programmatic access |
| Timeout on large exports | CSV with many results | Increase timeout; paginate with `pageSize=1000` instead |

## Best Practices

- **Use maximum page size** (1000) for bulk retrieval to minimize request count against rate limit
- **Always check `hasResults`** before accessing `resultsSection` — most trials have no posted results
- **Navigate safely** with `.get()` chains — not all trials populate all modules (especially `contactsLocationsModule`, `armsInterventionsModule`)
- **Specify multiple status values** with commas (e.g., `RECRUITING,NOT_YET_RECRUITING`) — don't make separate requests per status
- **Use `sort=LastUpdatePostDate:desc`** by default — returns most recently updated trials first
- **Date interpretation**: `lastUpdatePostDateStruct.date` is ISO 8601 string; `type` field indicates `ACTUAL` vs `ESTIMATED`

## Related Skills

- `pubmed-database` — Published literature search complementary to trial registry data
- `chembl-database-bioactivity` — Compound bioactivity data for drugs under investigation
- `bioservices-multi-database` — Alternative database access via unified Python interface

## References

- ClinicalTrials.gov API documentation: https://clinicaltrials.gov/data-api/api
- API migration guide (v1→v2): https://clinicaltrials.gov/data-api/about-api/api-migration
- ClinicalTrials.gov homepage: https://clinicaltrials.gov/
- OpenAPI specification: https://clinicaltrials.gov/data-api/about-api/api-spec

## Bundled Resources

**Self-contained entry**. Original total: 866 lines (SKILL.md 507 + api_reference.md 359). Scripts: 216 lines (query_clinicaltrials.py).

**Original file disposition**:
- `SKILL.md` (507 lines) → Core API modules 1-7 (condition, intervention, location, sponsor, details, pagination, CSV export). "Core Capabilities" sections 1-10 consolidated: Search by Condition → Module 1, Search by Intervention → Module 2, Geographic Search → Module 3, Search by Sponsor → Module 4, Retrieve Detailed Study → Module 5, Pagination → Module 6, Data Export → Module 7, Combined Query → Workflow 1, Extract Summary → Recipe. "Resources" section stub → removed, content consolidated inline. Per-use-case disposition: Patient Matching → When to Use bullet + Workflow 1; Research Analysis → When to Use + Workflow 2; Drug Tracking → When to Use + Module 2; Geographic Search → Module 3; Sponsor Tracking → Module 4 + Workflow 3; Data Export → Module 7; Trial Monitoring → When to Use bullet; Eligibility Screening → Module 5
- `references/api_reference.md` (359 lines) → Fully consolidated inline: endpoint parameters → Key Concepts "Query Parameters Reference" table; status/phase values → Key Concepts tables; response structure → Key Concepts "Response Data Structure" table; HTTP error codes → Troubleshooting table; rate limit guidance → Prerequisites + Best Practices; use cases → duplicated main SKILL.md examples, absorbed into Core API; data standards (ISO 8601, CommonMark) → Prerequisites note. Error handling patterns → Recipes "Rate-Limited Bulk Search"
- `scripts/query_clinicaltrials.py` (216 lines) → Helper function pattern: `search_studies()` → Quick Start `ct_search()` helper; `get_study_details()` → Module 5 inline; `search_with_all_results()` → Module 6 pagination pattern; `extract_study_summary()` → Recipe "Extract Study Summary". Thin-wrapper shortcut applied — each function was a thin wrapper around requests.get()

**Retention**: ~465 lines / 866 original (excl. scripts) = ~54%.

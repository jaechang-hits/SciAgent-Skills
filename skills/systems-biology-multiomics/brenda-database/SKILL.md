---
name: "brenda-database"
description: "Query BRENDA Enzyme Database for kinetic parameters (Km, Vmax, kcat, Ki), enzyme classifications, substrate specificity, inhibitors, cofactors, and organism-specific enzyme data via SOAP/REST API. 80,000+ enzyme entries, 7M+ kinetic values. Requires free academic registration. For metabolic pathway modeling use cobrapy-metabolic-modeling; for metabolite structures use hmdb-database."
license: "CC-BY-4.0"
---

# BRENDA Enzyme Database

## Overview

BRENDA (BRaunschweig ENzyme DAtabase) is the world's most comprehensive enzyme information system, containing 80,000+ enzyme entries covering all classified enzymes (EC numbers). It holds 7M+ experimentally measured kinetic parameters (Km, Vmax, kcat, Ki, inhibition constants), substrate specificity data, cofactor requirements, tissue expression, and organism-specific enzyme variants from 200,000+ literature references. Programmatic access is via a SOAP-based web service (Python zeep library) with free academic registration.

## When to Use

- Retrieving kinetic parameters (Km, kcat, Vmax, Ki) for a specific enzyme and substrate combination
- Comparing kinetic parameters across organisms or mutant variants for an enzyme
- Finding natural substrates, inhibitors, and cofactors for an EC number
- Building kinetic models for metabolic simulations requiring Michaelis-Menten parameters
- Identifying enzyme-specific structural data (recommended pH, temperature optima)
- Cross-referencing EC numbers with UniProt accessions and organism taxonomy
- For metabolic network simulation use `cobrapy-metabolic-modeling`; for metabolite structures use `hmdb-database`

## Prerequisites

- **Python packages**: `zeep` (SOAP client), `pandas`, `requests`
- **Data requirements**: EC numbers (e.g., `1.1.1.1`), enzyme names, or organism names
- **Environment**: internet connection; free academic registration at https://www.brenda-enzymes.org/register.php
- **Rate limits**: no explicit limit stated; avoid bulk automated queries; space requests with sleep

```bash
pip install zeep pandas requests
# Register at https://www.brenda-enzymes.org/register.php to obtain API credentials
```

## Quick Start

```python
from zeep import Client

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = "your_sha256_hashed_password"  # Use hashlib.sha256

# Get Km values for lactate dehydrogenase (EC 1.1.1.27) and pyruvate
ec_number = "1.1.1.27"
params = (EMAIL, PASSWORD_SHA256,
          f"ecNumber*{ec_number}", "substrate*pyruvate", "", "", "", "", "")
result = client.service.getKmValue(*params)
print(f"Km values for LDH with pyruvate: {len(result)} records")
for r in result[:3]:
    print(f"  Km={r.kmValue} {r.kmValueMaximum or ''} mM | org: {r.organism} | PMID: {r.literature}")
```

## Core API

### Query 1: Km Values for Enzyme-Substrate Pair

Retrieve Michaelis constant (Km) values for a specific enzyme and substrate.

```python
from zeep import Client
import hashlib, pandas as pd

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD = "your_password"
PASSWORD_SHA256 = hashlib.sha256(PASSWORD.encode()).hexdigest()

def get_km_values(ec_number, substrate=""):
    """Retrieve Km values for an EC number, optionally filtered by substrate."""
    substrate_param = f"substrate*{substrate}" if substrate else ""
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", substrate_param, "", "", "", "", "")
    return client.service.getKmValue(*params)

# Km for glucokinase (EC 2.7.1.2) with glucose
results = get_km_values("2.7.1.2", substrate="glucose")
print(f"Km (glucose, glucokinase): {len(results)} measurements")

rows = []
for r in results[:10]:
    rows.append({
        "km_value": r.kmValue,
        "km_max": r.kmValueMaximum,
        "unit": "mM",
        "organism": r.organism,
        "commentary": r.commentary[:80] if r.commentary else "",
        "pmid": r.literature,
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

```python
# Get ALL Km values (all substrates) for an EC number
all_km = get_km_values("1.1.1.1")  # Alcohol dehydrogenase
print(f"\nAlcohol dehydrogenase - total Km records: {len(all_km)}")
substrate_counts = {}
for r in all_km:
    sub = r.substrate or "unknown"
    substrate_counts[sub] = substrate_counts.get(sub, 0) + 1
top_substrates = sorted(substrate_counts.items(), key=lambda x: -x[1])[:5]
print("Top substrates by measurement count:")
for sub, cnt in top_substrates:
    print(f"  {sub}: {cnt} measurements")
```

### Query 2: kcat (Turnover Number) Values

Retrieve catalytic rate constants (kcat) for an enzyme.

```python
from zeep import Client
import hashlib, pandas as pd

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

def get_kcat_values(ec_number, substrate=""):
    substrate_param = f"substrate*{substrate}" if substrate else ""
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", substrate_param, "", "", "", "", "")
    return client.service.getTurnoverNumber(*params)

results = get_kcat_values("1.1.1.27")  # Lactate dehydrogenase
print(f"kcat records for LDH: {len(results)}")

rows = []
for r in results[:10]:
    rows.append({
        "kcat": r.turnoverNumber,
        "unit": "1/s",
        "substrate": r.substrate,
        "organism": r.organism,
    })
df = pd.DataFrame(rows)
print(df.head())
```

### Query 3: Substrates and Products

Retrieve natural substrates and products for an enzyme.

```python
from zeep import Client
import hashlib, pandas as pd

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

def get_substrates_products(ec_number):
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", "", "", "", "", "", "")
    return client.service.getSubstrates(*params)

results = get_substrates_products("4.2.1.1")  # Carbonic anhydrase
print(f"Substrates for carbonic anhydrase (EC 4.2.1.1):")
substrates_seen = set()
for r in results[:10]:
    if r.substrate not in substrates_seen:
        print(f"  {r.substrate} | organism: {r.organism}")
        substrates_seen.add(r.substrate)
```

```python
# Get inhibitors
def get_inhibitors(ec_number):
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", "", "", "", "", "", "")
    return client.service.getInhibitors(*params)

inhibitors = get_inhibitors("4.2.1.1")
print(f"\nInhibitors of carbonic anhydrase: {len(inhibitors)} records")
inhib_names = list(set(r.inhibitor for r in inhibitors if r.inhibitor))
print("Sample inhibitors:", inhib_names[:8])
```

### Query 4: Organism-Specific Enzyme Data

Query kinetic parameters filtered by organism.

```python
from zeep import Client
import hashlib

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

def get_km_by_organism(ec_number, organism):
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", "", f"organism*{organism}", "", "", "", "")
    return client.service.getKmValue(*params)

# Human GAPDH Km values
human_km = get_km_by_organism("1.2.1.12", "Homo sapiens")
print(f"Human GAPDH (EC 1.2.1.12) Km values: {len(human_km)} records")
for r in human_km[:5]:
    print(f"  Substrate: {r.substrate:30s} Km={r.kmValue} mM")
```

### Query 5: pH and Temperature Optima

Retrieve optimal pH and temperature data for an enzyme.

```python
from zeep import Client
import hashlib

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

def get_ph_optimum(ec_number):
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", "", "", "", "", "", "")
    return client.service.getPhOptimum(*params)

def get_temp_optimum(ec_number):
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", "", "", "", "", "", "")
    return client.service.getTemperatureOptimum(*params)

ec = "3.4.21.4"  # Trypsin
ph_data = get_ph_optimum(ec)
temp_data = get_temp_optimum(ec)

print(f"Trypsin (EC {ec}):")
ph_values = [r.phOptimum for r in ph_data[:10] if r.phOptimum]
temp_values = [r.temperatureOptimum for r in temp_data[:10] if r.temperatureOptimum]
if ph_values:
    print(f"  pH optima: {sorted(ph_values)}")
if temp_values:
    print(f"  Temperature optima (°C): {sorted(temp_values)}")
```

### Query 6: EC Number to UniProt Cross-Reference

Map EC numbers to UniProt accession numbers.

```python
from zeep import Client
import hashlib

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

def get_uniprot_accessions(ec_number):
    params = (EMAIL, PASSWORD_SHA256,
              f"ecNumber*{ec_number}", "", "", "", "", "", "")
    return client.service.getUniprotAccession(*params)

results = get_uniprot_accessions("1.1.1.27")  # LDH
print(f"UniProt accessions for LDH (EC 1.1.1.27):")
seen = set()
for r in results[:10]:
    acc = r.uniprotAccessionNumber
    org = r.organism
    if acc and acc not in seen:
        print(f"  {acc:12s} ({org})")
        seen.add(acc)
```

## Key Concepts

### SOAP Interface and Authentication

BRENDA uses SOAP (not REST) via a WSDL definition. The `zeep` Python library parses the WSDL and generates typed method calls. Authentication requires a SHA256-hashed password (not plain text). Each service method takes `(email, password_sha256, param1, param2, ..., "")` arguments with pipe-delimited field filters.

### EC Number Classification

Enzyme Commission (EC) numbers follow the format X.X.X.X where each level specifies the reaction class (oxidoreductases=1, transferases=2, hydrolases=3, lyases=4, isomerases=5, ligases=6, translocases=7). BRENDA organizes all data by EC number.

## Common Workflows

### Workflow 1: Kinetic Parameter Extraction for Metabolic Modeling

**Goal**: For a set of enzymes in a metabolic pathway, extract Km and kcat values to parameterize a kinetic model.

```python
from zeep import Client
import hashlib, pandas as pd, time

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

# Glycolysis enzymes
enzymes = {
    "Hexokinase": "2.7.1.1",
    "Phosphoglucose isomerase": "5.3.1.9",
    "Phosphofructokinase": "2.7.1.11",
    "Aldolase": "4.1.2.13",
}

rows = []
for name, ec in enzymes.items():
    params = (EMAIL, PASSWORD_SHA256, f"ecNumber*{ec}", "", "organism*Homo sapiens", "", "", "", "")
    try:
        km_results = client.service.getKmValue(*params)
        kcat_results = client.service.getTurnoverNumber(*params)
        km_vals = [r.kmValue for r in km_results if r.kmValue]
        kcat_vals = [r.turnoverNumber for r in kcat_results if r.turnoverNumber]
        rows.append({
            "enzyme": name,
            "ec": ec,
            "n_km_records": len(km_vals),
            "km_median_mM": pd.Series(km_vals).median() if km_vals else None,
            "n_kcat_records": len(kcat_vals),
            "kcat_median_1_s": pd.Series(kcat_vals).median() if kcat_vals else None,
        })
    except Exception as e:
        rows.append({"enzyme": name, "ec": ec, "error": str(e)})
    time.sleep(0.5)

df = pd.DataFrame(rows)
df.to_csv("glycolysis_kinetics.csv", index=False)
print(df.to_string(index=False))
```

### Workflow 2: Inhibitor Comparison Across Enzyme Family

**Goal**: Compare inhibitor landscape across a set of related enzymes for drug discovery prioritization.

```python
from zeep import Client
import hashlib, pandas as pd, time
from collections import Counter

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

# Carbonic anhydrase isoforms
ca_ecs = ["4.2.1.1"]  # All carbonic anhydrases share this EC

rows = []
for ec in ca_ecs:
    params = (EMAIL, PASSWORD_SHA256, f"ecNumber*{ec}", "", "", "", "", "", "")
    try:
        inhib_results = client.service.getInhibitors(*params)
        for r in inhib_results[:30]:
            rows.append({
                "ec": ec,
                "inhibitor": r.inhibitor,
                "organism": r.organism,
                "ic50": r.ic50Value if hasattr(r, "ic50Value") else None,
            })
    except Exception as e:
        print(f"Error for {ec}: {e}")
    time.sleep(0.5)

df = pd.DataFrame(rows)
print(f"Total inhibitor records: {len(df)}")
top_inhib = Counter(df["inhibitor"]).most_common(10)
print("\nMost reported inhibitors:")
for inhib, count in top_inhib:
    print(f"  {inhib}: {count} records")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `ecNumber*` | All queries | required | EC number string | Filter by enzyme class |
| `substrate*` | Km, kcat | — | substrate name | Filter by substrate |
| `organism*` | All queries | — | species name | Filter by organism (e.g., `"Homo sapiens"`) |
| `commentary*` | All queries | — | text substring | Filter by comment text |
| `ligandStructureId*` | Compound-based | — | BRENDA structure ID | Filter by ligand ID |
| Password | Auth | required | SHA256 hash | Authentication (hashlib.sha256) |

## Best Practices

1. **Hash your password correctly**: BRENDA requires SHA256 hash of the plain-text password, not the password itself. Use `hashlib.sha256("your_password".encode()).hexdigest()`.

2. **Store credentials in environment variables**: Never hard-code credentials. Use `os.environ["BRENDA_EMAIL"]` and `os.environ["BRENDA_PASSWORD"]` patterns.

3. **Add `time.sleep()` between queries**: BRENDA's SOAP service may be slow; space large batch queries with 0.5–1 second sleeps to avoid timeouts.

4. **Filter by organism for modeling**: Kinetic parameters vary dramatically between organisms; always filter by the organism relevant to your model (e.g., `organism*Homo sapiens`).

5. **Use median/IQR for parameter aggregation**: Multiple literature measurements for the same substrate often span an order of magnitude; use median + IQR rather than mean to summarize distributions.

## Common Recipes

### Recipe: Get All Substrates for an EC Number

When to use: Understand the substrate scope of an enzyme for pathway analysis.

```python
from zeep import Client
import hashlib

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

ec = "1.1.1.1"  # Alcohol dehydrogenase
params = (EMAIL, PASSWORD_SHA256, f"ecNumber*{ec}", "", "", "", "", "", "")
results = client.service.getSubstrates(*params)
substrates = list(set(r.substrate for r in results if r.substrate))
print(f"Substrates of EC {ec} ({len(substrates)} unique): {substrates[:10]}")
```

### Recipe: kcat/Km Efficiency Ratio

When to use: Compute catalytic efficiency (kcat/Km) from BRENDA data.

```python
import pandas as pd

# After fetching km_results and kcat_results for same ec + substrate
# km_values = [r.kmValue for r in km_results if r.kmValue]  # mM
# kcat_values = [r.turnoverNumber for r in kcat_results if r.turnoverNumber]  # 1/s

km_median = 0.1   # mM (example)
kcat_median = 500  # s^-1 (example)

efficiency = kcat_median / (km_median * 1e-3)  # Convert Km to M
print(f"Catalytic efficiency (kcat/Km): {efficiency:.2e} M^-1 s^-1")
# Diffusion limit ≈ 10^8-10^9 M^-1 s^-1
```

### Recipe: Find EC Number from Enzyme Name

When to use: Resolve enzyme common name to EC number for BRENDA queries.

```python
from zeep import Client
import hashlib

WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
client = Client(WSDL)

EMAIL = "your@email.com"
PASSWORD_SHA256 = hashlib.sha256("your_password".encode()).hexdigest()

# Search enzymes by name
params = (EMAIL, PASSWORD_SHA256, "recommendedName*lactate dehydrogenase", "", "", "", "", "", "")
results = client.service.getEcNumber(*params)
print(f"EC numbers for 'lactate dehydrogenase':")
for r in results[:5]:
    print(f"  EC {r.ecNumber}: {r.recommendedName}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `zeep.exceptions.Fault: Authentication failed` | Wrong password or SHA256 format | Ensure `hashlib.sha256(password.encode()).hexdigest()` — hexdigest not digest |
| Empty result list | EC number or substrate not found | Verify EC format (X.X.X.X with dots); try without substrate filter first |
| SOAP timeout | Large query or slow connection | Use organism filter to reduce result set; set `zeep` transport timeout |
| `AttributeError` on result field | Field not available for this query | Use `getattr(r, "field", None)` to safely access optional fields |
| Slow response for popular enzymes | Large datasets (TP53 = 10K+ records) | Filter by organism and substrate to reduce data transfer |
| `zeep.exceptions.TransportError` | Network connectivity issue | Check VPN, retry after 30 seconds |

## Related Skills

- `cobrapy-metabolic-modeling` — Constraint-based metabolic modeling using Km/Vmax from BRENDA as kinetic constraints
- `hmdb-database` — Metabolite structure and biological context for BRENDA substrates
- `kegg-database` — Pathway context for BRENDA enzymes via EC number cross-references
- `uniprot-protein-database` — Protein sequence and structure data for enzymes found in BRENDA

## References

- [BRENDA database](https://www.brenda-enzymes.org/) — Main BRENDA portal and manual search
- [BRENDA web service documentation](https://www.brenda-enzymes.org/soap.php) — SOAP API reference and parameter descriptions
- [zeep Python SOAP client](https://docs.python-zeep.org/) — Python library for SOAP web services
- [Chang et al. (2021) BRENDA update](https://doi.org/10.1093/nar/gkaa1025) — BRENDA 2021 database update paper

---
name: "plannotate-plasmid-annotation"
description: "Automatically annotate plasmid sequences with functional features (promoters, terminators, resistance genes, origins of replication, tags, fluorescent proteins) using BLAST-based detection against curated databases (Addgene, fpbase, SnapGene). Accepts FASTA or raw sequence; outputs annotated GenBank files, interactive HTML maps, and CSV feature tables. Handles circular topology correctly. Use for verifying synthetic plasmid construction, preparing Addgene submissions, sharing plasmid maps, or batch-annotating a cloning library."
license: "GPL-3.0"
---

# pLannotate Plasmid Annotation

## Overview

pLannotate annotates plasmid sequences by running BLAST searches against a curated library of over 5,000 features sourced from Addgene, NCBI, and fpbase. It identifies promoters, terminators, antibiotic resistance genes, origins of replication, tags, and fluorescent proteins while correctly handling circular plasmid topology — avoiding split-feature artifacts that arise from naive linear alignment. Results are written as annotated GenBank files for downstream use in SnapGene, Benchling, or BioPython, as interactive HTML plasmid maps for sharing and review, and as CSV tables for programmatic filtering. Both a Python API and a command-line interface are provided; a Streamlit web app is also bundled for exploratory use.

## When to Use

- Annotating a plasmid sequence received from a collaborator or downloaded from Addgene with no accompanying map
- Verifying that all expected elements (promoter, insert, resistance marker, origin) are present after assembly or mutagenesis
- Preparing a GenBank submission or Addgene deposit that requires a complete feature table
- Batch-annotating a library of synthetic constructs produced by combinatorial cloning
- Generating a shareable interactive plasmid map (HTML) without requiring SnapGene or Benchling licenses
- Checking a de-novo synthesized gene block for unintended regulatory elements or cryptic ORFs before cloning
- Use **SnapGene** or **Benchling** instead when you need a full-featured GUI plasmid editor with primer design and cloning simulation workflows; pLannotate is best for automated, scriptable annotation
- Use **Prokka** instead when annotating a complete bacterial genome or a large linear chromosomal sequence; pLannotate is optimized for plasmid-sized sequences up to ~50 kb

## Prerequisites

- **Python packages**: `plannotate`, `biopython` (optional, for GenBank parsing)
- **System dependency**: BLAST+ must be available on PATH (installed automatically via conda; manual install needed for pip)
- **Input**: Plasmid sequence in FASTA format or as a plain Python string
- **Data requirements**: Sequences typically 1–20 kb; very large plasmids (>50 kb) may be slow

```bash
# Install via pip (requires BLAST+ on PATH)
pip install plannotate

# Install via conda (recommended — handles BLAST+ automatically)
conda install -c conda-forge -c bioconda plannotate

# Verify installation
plannotate --help
python -c "import plannotate; print('plannotate OK')"
```

## Quick Start

```python
from plannotate import annotate, write_genbank, create_bokeh_chart
from Bio import SeqIO

# Load plasmid from FASTA
record = next(SeqIO.parse("plasmid.fasta", "fasta"))
sequence = str(record.seq)

# Annotate (circular, against Addgene database)
results = annotate(sequence, linear=False, db="addgene")
print(f"Found {len(results)} features")
print(results[["Feature", "Feature_type", "pct_identity", "pct_query_cov"]].to_string())

# Export GenBank file
write_genbank(sequence, results, output_file="plasmid_annotated.gb")

# Generate interactive HTML map
create_bokeh_chart(sequence, results, output_file="plasmid_map.html")
print("Outputs: plasmid_annotated.gb, plasmid_map.html")
```

## Workflow

### Step 1: Load Plasmid Sequence

Load the plasmid sequence from a FASTA file, a GenBank file (stripping existing annotations for re-annotation), or a raw sequence string. Validate length and base composition before annotation.

```python
from Bio import SeqIO
import os

# Option A: Load from FASTA
def load_fasta(path):
    record = next(SeqIO.parse(path, "fasta"))
    seq = str(record.seq).upper()
    return seq, record.id

# Option B: Load from GenBank (strip annotations, keep sequence)
def load_genbank(path):
    record = next(SeqIO.parse(path, "genbank"))
    seq = str(record.seq).upper()
    return seq, record.id

# Option C: Raw sequence string
raw_seq = "ATGCGTAAAGGAGAAGAACTTTTCACTGGAGTTGTCCCAATTCTTGTTGAATTAGATGGTGATGTT"

# Validate sequence
def validate_plasmid(seq, name="plasmid"):
    valid_bases = set("ATGCNRYSWKMBDHV")
    invalid = set(seq.upper()) - valid_bases
    if invalid:
        raise ValueError(f"Invalid bases in {name}: {invalid}")
    if len(seq) < 100:
        raise ValueError(f"Sequence too short ({len(seq)} bp); minimum 100 bp")
    gc = (seq.count("G") + seq.count("C")) / len(seq) * 100
    print(f"{name}: {len(seq):,} bp, GC={gc:.1f}%")
    return seq

seq, plasmid_id = load_fasta("plasmid.fasta")
validate_plasmid(seq, plasmid_id)
```

### Step 2: Run BLAST-Based Annotation

Run annotation using the selected database. The `linear` flag controls whether the sequence is treated as circular (default for plasmids) or linear (for gene blocks and linear fragments).

```python
from plannotate import annotate

# Annotate circular plasmid against the Addgene database (most comprehensive for common vectors)
results = annotate(
    seq,
    linear=False,       # False = circular plasmid (default)
    db="addgene",       # Database: "addgene", "fpbase", or "snapgene"
)

print(f"Total features detected: {len(results)}")
print(f"\nColumns: {list(results.columns)}")

# Preview feature table
cols = ["Feature", "Feature_type", "start", "end", "strand", "pct_identity", "pct_query_cov"]
print(results[cols].sort_values("start").to_string(index=False))
```

### Step 3: Filter Features by Quality Thresholds

Review annotation confidence using BLAST identity and query coverage scores. High-confidence annotations have >95% identity and >90% coverage; partial hits may indicate truncated or mutated features.

```python
import pandas as pd

# Inspect hit quality distribution
print("Identity percentile summary:")
print(results["pct_identity"].describe().round(1))
print("\nCoverage percentile summary:")
print(results["pct_query_cov"].describe().round(1))

# Separate high- and low-confidence hits
high_conf = results[
    (results["pct_identity"] >= 95) &
    (results["pct_query_cov"] >= 90)
].copy()

low_conf = results[
    (results["pct_identity"] < 95) |
    (results["pct_query_cov"] < 90)
].copy()

print(f"\nHigh-confidence features (identity>=95%, coverage>=90%): {len(high_conf)}")
print(f"Low-confidence / partial features:                       {len(low_conf)}")

if not low_conf.empty:
    print("\nLow-confidence features (review manually):")
    print(low_conf[["Feature", "Feature_type", "pct_identity", "pct_query_cov"]].to_string(index=False))

# Save filtered table
results.to_csv("all_features.csv", index=False)
high_conf.to_csv("high_confidence_features.csv", index=False)
print("\nSaved: all_features.csv, high_confidence_features.csv")
```

### Step 4: Export Annotated GenBank File

Write the annotated sequence to GenBank format for import into plasmid editors (SnapGene, Benchling, Geneious, ApE) and for BioPython-based downstream analysis.

```python
from plannotate import write_genbank

# Write full annotation (all features)
write_genbank(seq, results, output_file="plasmid_annotated.gb")
print("Written: plasmid_annotated.gb")

# Write with high-confidence features only
write_genbank(seq, high_conf, output_file="plasmid_highconf.gb")
print("Written: plasmid_highconf.gb")

# Verify using BioPython
from Bio import SeqIO
record = next(SeqIO.parse("plasmid_annotated.gb", "genbank"))
print(f"\nGenBank verification:")
print(f"  Sequence length: {len(record.seq):,} bp")
print(f"  Features: {len(record.features)}")
for feat in record.features:
    label = feat.qualifiers.get("label", ["(unlabeled)"])[0]
    print(f"  [{feat.type:20s}] {label} @ {feat.location}")
```

### Step 5: Generate Interactive HTML Visualization

Create a Bokeh-based interactive plasmid map. The HTML file is self-contained and can be shared without any server infrastructure.

```python
from plannotate import create_bokeh_chart

# Generate interactive circular plasmid map
create_bokeh_chart(
    seq,
    results,
    output_file="plasmid_map.html",
)
print("Interactive map saved: plasmid_map.html")
print("Open in any browser — no server required")

# Tip: open automatically in the default browser
import webbrowser, os
webbrowser.open(f"file://{os.path.abspath('plasmid_map.html')}")
```

### Step 6: Parse GenBank Output with BioPython

Extract annotated features programmatically for downstream analysis — restriction site mapping, primer design, or construct verification reports.

```python
from Bio import SeqIO
from Bio.SeqFeature import FeatureLocation
import pandas as pd

record = next(SeqIO.parse("plasmid_annotated.gb", "genbank"))

# Build a feature DataFrame from the GenBank record
rows = []
for feat in record.features:
    label = feat.qualifiers.get("label", [""])[0]
    note  = feat.qualifiers.get("note",  [""])[0]
    rows.append({
        "type":   feat.type,
        "label":  label,
        "note":   note,
        "start":  int(feat.location.start),
        "end":    int(feat.location.end),
        "strand": feat.location.strand,
        "length": len(feat.location),
    })

feat_df = pd.DataFrame(rows)
print(feat_df.to_string(index=False))

# Example: find antibiotic resistance genes
resistance = feat_df[feat_df["label"].str.contains(
    r"AmpR|KanR|CmR|TetR|SpecR|HygR|ZeoR|BlastR|GentR",
    case=False, na=False, regex=True
)]
print(f"\nAntibiotic resistance markers found: {len(resistance)}")
print(resistance[["label", "start", "end", "length"]].to_string(index=False))
```

### Step 7: Batch Annotate Multiple Plasmids

Annotate an entire cloning library from a multi-FASTA file or a directory of individual FASTA files and aggregate results into a single summary table.

```python
from plannotate import annotate, write_genbank, create_bokeh_chart
from Bio import SeqIO
import pandas as pd
import os

input_dir  = "plasmids/"          # directory of *.fasta files
output_dir = "annotated_results/"
os.makedirs(output_dir, exist_ok=True)

summary_rows = []

for fasta_file in sorted(f for f in os.listdir(input_dir) if f.endswith(".fasta")):
    plasmid_name = fasta_file.replace(".fasta", "")
    fasta_path   = os.path.join(input_dir, fasta_file)

    record = next(SeqIO.parse(fasta_path, "fasta"))
    seq    = str(record.seq).upper()

    print(f"Annotating {plasmid_name} ({len(seq):,} bp)...", end=" ")
    results = annotate(seq, linear=False, db="addgene")
    print(f"{len(results)} features")

    # Save per-plasmid outputs
    write_genbank(
        seq, results,
        output_file=os.path.join(output_dir, f"{plasmid_name}.gb")
    )
    create_bokeh_chart(
        seq, results,
        output_file=os.path.join(output_dir, f"{plasmid_name}.html")
    )
    results.to_csv(os.path.join(output_dir, f"{plasmid_name}_features.csv"), index=False)

    # Accumulate for summary
    results["plasmid"] = plasmid_name
    summary_rows.append(results)

# Consolidated summary table
summary = pd.concat(summary_rows, ignore_index=True)
summary.to_csv(os.path.join(output_dir, "all_plasmids_features.csv"), index=False)
print(f"\nBatch complete. {summary['plasmid'].nunique()} plasmids annotated.")
print(f"Summary table: {output_dir}all_plasmids_features.csv")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `linear` | `False` | `True`, `False` | Treat sequence as linear (`True`) or circular (`False`); circular mode handles split features at the origin correctly |
| `db` | `"addgene"` | `"addgene"`, `"fpbase"`, `"snapgene"` | Feature database to search; `addgene` is broadest (promoters, resistance genes, origins, tags); `fpbase` adds fluorescent protein variants; `snapgene` includes SnapGene-curated features |
| `min_len` | `0` | `0`–`500` bp | Minimum feature length in bp; increase to suppress short spurious matches |
| `blast_identity_threshold` | `95` | `70`–`100` % | Minimum BLAST % identity to report a hit; lower values detect diverged homologs but increase false positives |
| `--html` (CLI) | off | flag | Generate interactive HTML plasmid map alongside GenBank output |
| `--csv` (CLI) | off | flag | Write CSV feature table to the output directory |
| `--linear` (CLI) | off | flag | Treat input as linear sequence (default is circular) |
| `--file` / `--input` (CLI) | required | FASTA path | Input plasmid sequence in FASTA format |

## Common Recipes

### Recipe: Launch Web App for Interactive Use

When to use: exploring a single plasmid interactively without writing code, or sharing with wet-lab collaborators who prefer a browser interface.

```bash
# Launch the pLannotate Streamlit web app (opens in browser at localhost:5000)
plannotate streamlit

# Or specify a custom port
plannotate streamlit --port 8501
```

### Recipe: CLI Batch Annotation

When to use: annotating multiple plasmids in a scripted workflow or on a remote server without Python scripting.

```bash
# Single plasmid
plannotate batch \
    --input plasmid.fasta \
    --output results/ \
    --html \
    --csv

# Multiple plasmids via shell glob
for f in plasmids/*.fasta; do
    name=$(basename "$f" .fasta)
    plannotate batch \
        --input "$f" \
        --output "annotated/${name}/" \
        --html --csv
done
echo "Done. Outputs in annotated/"
```

### Recipe: Compare Annotations Before and After Mutagenesis

When to use: verifying that a site-directed mutagenesis or insertion did not disrupt existing features or introduce unintended ones.

```python
from plannotate import annotate
from Bio import SeqIO
import pandas as pd

def annotation_diff(seq_before, seq_after, db="addgene"):
    res_before = annotate(seq_before, linear=False, db=db)
    res_after  = annotate(seq_after,  linear=False, db=db)

    features_before = set(res_before["Feature"])
    features_after  = set(res_after["Feature"])

    gained = features_after  - features_before
    lost   = features_before - features_after
    shared = features_before & features_after

    print(f"Shared features: {len(shared)}")
    print(f"Gained features: {gained if gained else 'none'}")
    print(f"Lost features:   {lost   if lost   else 'none'}")
    return res_before, res_after

seq_wt  = str(next(SeqIO.parse("plasmid_wt.fasta",  "fasta")).seq)
seq_mut = str(next(SeqIO.parse("plasmid_mut.fasta", "fasta")).seq)
res_before, res_after = annotation_diff(seq_wt, seq_mut)
```

### Recipe: Export Feature Table to Excel with Conditional Formatting

When to use: sharing annotation results with collaborators who prefer spreadsheets over GenBank files.

```python
from plannotate import annotate
from Bio import SeqIO
import pandas as pd

seq = str(next(SeqIO.parse("plasmid.fasta", "fasta")).seq)
results = annotate(seq, linear=False, db="addgene")

# Tidy column selection and renaming
export = results[[
    "Feature", "Feature_type", "start", "end", "strand",
    "pct_identity", "pct_query_cov", "database"
]].copy()
export.columns = [
    "Feature Name", "Type", "Start (bp)", "End (bp)", "Strand",
    "Identity (%)", "Coverage (%)", "Database"
]
export["Length (bp)"] = export["End (bp)"] - export["Start (bp)"]
export = export.sort_values("Start (bp)")

# Write to Excel with conditional formatting
with pd.ExcelWriter("plasmid_features.xlsx", engine="openpyxl") as writer:
    export.to_excel(writer, sheet_name="Features", index=False)

print(f"Exported {len(export)} features to plasmid_features.xlsx")
```

## Expected Outputs

| Output File | Format | Description |
|-------------|--------|-------------|
| `plasmid_annotated.gb` | GenBank | Sequence with annotated features; importable into SnapGene, Benchling, Geneious, ApE, BioPython |
| `plasmid_map.html` | HTML | Self-contained interactive circular plasmid map (Bokeh); shareable without a server |
| `all_features.csv` | CSV | Tabular feature list with columns: Feature, Feature_type, start, end, strand, pct_identity, pct_query_cov, database |
| `high_confidence_features.csv` | CSV | Filtered subset with identity >= 95% and coverage >= 90% |
| `all_plasmids_features.csv` | CSV | Batch mode: aggregated features across all plasmids with a `plasmid` column |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `FileNotFoundError: blastn not found` | BLAST+ not on PATH | Install via conda: `conda install -c bioconda blast`; or via package manager: `brew install blast` (macOS) / `apt install ncbi-blast+` (Linux) |
| `No features detected` | Sequence is too short, wrong database, or non-standard bases | Verify sequence length >= 500 bp; try a different `db` (e.g., `"fpbase"` for fluorescent protein vectors); check for ambiguous bases with `validate_plasmid()` |
| Annotations wrap incorrectly at position 0 | Sequence treated as linear when it is circular | Set `linear=False` (default); this enables circular BLAST to catch features that span the sequence origin |
| HTML map renders blank | `bokeh` version mismatch | Upgrade: `pip install --upgrade bokeh`; pLannotate requires Bokeh >=2.4 |
| Low identity hits for known features | Feature sequence has been mutated or codon-optimized | Lower `blast_identity_threshold` to 85–90%; add a note that these are diverged homologs |
| `MemoryError` or very slow annotation | Sequence > 50 kb or BLAST database not indexed | Split large sequences into sub-regions; ensure the internal pLannotate database index exists (reinstall if needed) |
| GenBank file not parsed by SnapGene | Non-standard feature type labels | Open in Geneious or BioPython first; check for special characters in feature qualifiers |

## References

- [pLannotate GitHub: mmcguffi/pLannotate](https://github.com/mmcguffi/pLannotate) — source code, issue tracker, and installation instructions
- [McGuffi M et al. (2021) Nucleic Acids Research 49(W1): W516–W522](https://doi.org/10.1093/nar/gkab374) — original pLannotate paper describing the BLAST-based annotation pipeline and curated feature database
- [pLannotate PyPI: plannotate](https://pypi.org/project/plannotate/) — package metadata, version history, and pip install info
- [Addgene plasmid repository](https://www.addgene.org/) — primary source for the curated feature library used by pLannotate
- [BioPython SeqIO documentation](https://biopython.org/wiki/SeqIO) — parsing and manipulating GenBank output files

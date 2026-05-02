---
name: scientific-literature-search
description: "Systematic strategies for searching scientific literature across PubMed, arXiv, Google Scholar, and AI-assisted tools. Covers PICO framework for clinical questions, three-tiered search (database-specific, AI-assisted, content extraction), PubMed field tags and MeSH, boolean query construction, and full-text extraction. Use when planning a literature search or choosing a search tier."
license: CC-BY-4.0
---

# Scientific Literature Search

## Overview

Scientific literature search is the foundation of evidence-based research. A well-executed search maximizes recall (finding all relevant papers) while maintaining precision (avoiding irrelevant results). This guide provides a systematic approach that combines database-specific query strategies, AI-assisted synthesis, and direct content extraction, organized into a three-tiered framework that scales from targeted lookups to comprehensive landscape reviews.

## Key Concepts

### The PICO Framework

For clinical and biomedical questions, structure queries using the PICO framework:

- **P** (Population): Who are you studying? (e.g., "Diabetes Mellitus"[MeSH])
- **I** (Intervention): What treatment or exposure? (e.g., "Metformin"[MeSH])
- **C** (Comparison): What is the alternative? (e.g., placebo, standard care)
- **O** (Outcome): What result are you measuring? (e.g., "Cardiovascular Diseases"[MeSH])

PICO queries can be combined with publication type filters to target specific evidence levels:

```
"Diabetes Mellitus"[MeSH] AND "Metformin"[MeSH] AND "Cardiovascular Diseases"[MeSH] AND ("clinical trial"[Publication Type] OR "meta-analysis"[Publication Type])
```

### Three-Tiered Search Strategy

Literature search is most effective when approached in tiers of increasing breadth:

**Tier 1 -- Database-Specific Searches (Most Reliable)**

Query established academic databases (PubMed, arXiv, Google Scholar) for peer-reviewed, indexed content. This is the most reliable tier and should always be the starting point.

- PubMed (via Biopython `Bio.Entrez`): Primary database for biomedical and life science literature. Supports MeSH controlled vocabulary and advanced field tags.
- arXiv (via the `arxiv` package): Preprint server for physics, mathematics, computer science, and quantitative biology. Results appear faster than peer-reviewed journals.
- Google Scholar (via the `scholarly` package): Broadest coverage across all academic disciplines. Note: has aggressive rate limits on automated queries.

Best for: finding specific papers, systematic reviews, clinical evidence, preprints.

**Tier 2 -- AI-Assisted Web Search (Comprehensive)**

Use the Claude API with the `web_search_20250305` server-side tool to synthesize broader context, identify research trends, and surface recent developments not yet indexed in databases. Also use general web search (e.g. via the `duckduckgo-search` package) for protocols, tutorials, and software documentation.

Best for: understanding the research landscape, complex multi-faceted questions, finding recent developments, identifying key researchers.

Avoid for: specific paper lookups (use Tier 1), citation counts (use Google Scholar), systematic reviews requiring reproducibility, searches where exact query terms must be documented.

**Tier 3 -- Direct Content Extraction (Deep Dive)**

Extract and analyze full-text content, PDFs, and supplementary materials from identified papers using `trafilatura` (HTML article extraction), `pypdf` (PDF text), and the Crossref API (DOI → supplementary file URLs).

Best for: detailed methodology extraction, data retrieval, protocol identification, supplementary data access.

### PubMed Field Tags

PubMed supports field-specific searching to improve precision:

| Tag | Description | Example |
|-----|-------------|---------|
| `[MeSH]` | Medical Subject Heading (controlled vocabulary) | `"Neoplasms"[MeSH]` |
| `[Title]` | Title field only | `"CRISPR"[Title]` |
| `[Title/Abstract]` | Title or abstract | `"gene therapy"[Title/Abstract]` |
| `[Author]` | Author name | `"Zhang F"[Author]` |
| `[Journal]` | Journal name | `"Nature"[Journal]` |
| `[Publication Type]` | Article type filter | `"Review"[Publication Type]` |
| `[Date - Publication]` | Publication date range | `"2020/01/01"[Date - Publication]:"2024/12/31"[Date - Publication]` |
| `[MeSH Major Topic]` | MeSH term as major focus of the article | `"CRISPR-Cas Systems"[MeSH Major Topic]` |

### Boolean Operators

Boolean operators control how search terms combine:

```python
# AND: All terms must be present -- narrows results
results = query_pubmed("CRISPR AND cancer AND therapy")

# OR: Any term can be present -- broadens results (use for synonyms)
results = query_pubmed("(tumor OR tumour OR neoplasm) AND immunotherapy")

# NOT: Exclude terms -- use sparingly to avoid losing relevant papers
results = query_pubmed("cancer immunotherapy NOT review")
```

Use parentheses to group OR terms together before combining with AND.

### arXiv Subject Categories

arXiv organizes preprints by subject category. Biology-related categories include:

| Category | Description |
|----------|-------------|
| `q-bio.BM` | Biomolecules |
| `q-bio.CB` | Cell Behavior |
| `q-bio.GN` | Genomics |
| `q-bio.MN` | Molecular Networks |
| `q-bio.NC` | Neurons and Cognition |
| `q-bio.QM` | Quantitative Methods |
| `cs.AI` | Artificial Intelligence |
| `cs.LG` | Machine Learning |

## Decision Framework

Use this tree to determine which search tier and database to start with:

```
What type of question are you answering?
├── Clinical / biomedical question
│   ├── Specific drug or treatment → Tier 1: PubMed with PICO query
│   ├── Disease mechanism → Tier 1: PubMed with MeSH terms
│   └── Clinical trial evidence → Tier 1: PubMed filtered by Publication Type
├── Computational / quantitative methods
│   ├── ML model or algorithm → Tier 1: arXiv (cs.LG, cs.AI)
│   ├── Computational biology method → Tier 1: arXiv (q-bio.*) + PubMed
│   └── Software tool or pipeline → Tier 2: AI-assisted web search
├── Broad research landscape
│   ├── Current state of a field → Tier 2: AI-assisted web search
│   ├── Recent developments (last 6 months) → Tier 2: AI-assisted web search
│   └── Cross-disciplinary question → Tier 1: Google Scholar + Tier 2
├── Specific paper or data
│   ├── Known paper details → Tier 1: any database by title/author/DOI
│   ├── Methodology or protocol → Tier 3: full-text extraction
│   └── Supplementary data → Tier 3: DOI-based supplementary fetch
└── Protocols / reagents
    ├── Lab protocol → Tier 2: web search for protocols.io, etc.
    └── Validated reagents → Tier 2: AI-assisted web search
```

| Scenario | Recommended Tier and Database | Rationale |
|----------|-------------------------------|-----------|
| Systematic review of clinical evidence | Tier 1: PubMed with MeSH + publication type filters | Reproducible, documented search strategy required |
| Finding a preprint on a new ML method | Tier 1: arXiv with category and keyword search | Preprints appear on arXiv before journals |
| Understanding the research landscape | Tier 2: AI-assisted web search | Requires synthesis across many sources |
| Extracting a specific protocol from a paper | Tier 3: PDF content extraction | Need full-text access to methods section |
| Finding papers across disciplines | Tier 1: Google Scholar | Broadest coverage across fields |
| Identifying key researchers in a niche area | Tier 2: AI-assisted web search | Requires contextual synthesis |
| Downloading supplementary data tables | Tier 3: DOI-based supplementary fetch | Direct access to supplementary files |

## Best Practices

1. **Use controlled vocabulary (MeSH) for PubMed searches**: Free-text searches miss papers that use different terminology. MeSH terms map synonyms to a single concept, improving recall without sacrificing precision.
   ```python
   # Free text misses synonyms
   query_pubmed("heart attack treatment")
   # MeSH captures all synonyms
   query_pubmed('"Myocardial Infarction"[MeSH] AND "Drug Therapy"[MeSH]')
   ```

2. **Include synonyms and alternative terms with OR**: Scientific concepts often have multiple names (e.g., tumor/tumour/neoplasm). Group synonyms with OR inside parentheses to avoid missing relevant papers.
   ```python
   query_pubmed("(myocardial infarction OR heart attack) AND (treatment OR therapy)")
   ```

3. **Use phrase searching for multi-word concepts**: Quoting exact phrases prevents the search engine from splitting terms and matching them independently.
   ```python
   query_pubmed('"single cell RNA sequencing" AND methods')
   ```

4. **Filter by publication type when seeking specific evidence**: Clinical trials, systematic reviews, and meta-analyses each answer different questions. Use `[Publication Type]` to target the evidence level you need.
   ```python
   query_pubmed("COVID-19 vaccine efficacy AND clinical trial[Publication Type]")
   ```

5. **Start broad, then narrow iteratively**: Begin with core concepts (2-3 terms) and review initial results. Add specificity based on what you find -- more terms, date ranges, field tags, or publication types.
   ```python
   # Step 1: Broad
   results = query_pubmed("CRISPR base editing iPSC", max_papers=20)
   # Step 2: Add MeSH and specificity
   results = query_pubmed(
       '"CRISPR-Cas Systems"[MeSH] AND "base editing" AND "induced pluripotent stem cells" AND efficiency',
       max_papers=20
   )
   # Step 3: Filter by date
   results = query_pubmed(
       '"CRISPR-Cas Systems"[MeSH] AND "base editing" AND "induced pluripotent stem cells" AND efficiency AND ("2022"[Date - Publication]:"2024"[Date - Publication])',
       max_papers=20
   )
   ```

6. **Cross-reference multiple databases**: No single database covers all literature. Use PubMed for biomedical content, arXiv for computational preprints, and Google Scholar for cross-disciplinary coverage.

7. **Assess result quality systematically**: Evaluate papers for source reliability (peer-reviewed journal), author credentials, recency, study design appropriateness, sample size adequacy, reproducibility, declared conflicts of interest, and citation count.

## Common Pitfalls

1. **Overly long and specific queries**: Packing too many terms into a single query causes missed results because all terms must match simultaneously.
   - *How to avoid*: Limit queries to core concepts (3-5 terms). Run separate searches for sub-topics and combine results manually.
   ```python
   # Too specific -- misses relevant papers
   query_pubmed("CRISPR Cas9 gene editing HEK293T cells 2024 efficiency optimization delivery")
   # Better -- core concepts only
   query_pubmed("CRISPR Cas9 gene editing optimization efficiency")
   ```

2. **Relying on a single database**: PubMed has biomedical focus, arXiv covers preprints, Google Scholar spans disciplines. Using only one database guarantees blind spots.
   - *How to avoid*: Always search at least two databases. For computational biology, combine PubMed and arXiv. For cross-disciplinary topics, include Google Scholar.

3. **Ignoring publication dates**: Scientific knowledge evolves rapidly. Foundational papers remain relevant, but methods and clinical evidence may be superseded.
   - *How to avoid*: Check publication dates in all results. For methods papers, prefer the last 3-5 years. For foundational concepts, older papers are acceptable but verify with recent reviews.

4. **Skipping title and abstract review before deep-diving**: Not all search results that match keywords are actually relevant. Downloading and reading full texts without screening wastes time.
   - *How to avoid*: Always screen titles and abstracts first. Only extract full text (Tier 3) for papers that pass screening.

5. **Using NOT operators too aggressively**: The NOT operator can inadvertently exclude relevant papers that mention the excluded term in a different context.
   - *How to avoid*: Use NOT sparingly. Prefer adding positive terms to narrow results rather than excluding terms. When you must use NOT, verify that excluded results are genuinely irrelevant.

6. **Ignoring Google Scholar rate limits**: Google Scholar aggressively rate-limits automated queries, which can block further searches.
   - *How to avoid*: Use Google Scholar sparingly. Add delays between requests. Prefer PubMed or arXiv for bulk searching and reserve Google Scholar for cross-disciplinary checks.

7. **Not documenting the search strategy**: For systematic reviews and reproducible research, an undocumented search cannot be verified or reproduced.
   - *How to avoid*: Record your search terms, databases queried, date ranges, and number of results at each stage. This is essential for systematic reviews and good practice for all searches.

## Workflow

1. **Step 1: Define the research question**
   - Identify the main concept, population/model, intervention/method, desired outcome, and time frame
   - For clinical questions, map to the PICO framework
   - Example: "Find recent papers on CRISPR base editing efficiency in human iPSCs" decomposes to: main concept = CRISPR base editing, model = human iPSCs, outcome = efficiency, time frame = last 3 years

2. **Step 2: Construct and execute database queries (Tier 1)**
   - Start with PubMed for biomedical topics, arXiv for computational topics
   - Begin with a broad query using 2-3 core terms
   - Refine with MeSH terms, field tags, date filters, and publication type filters
   ```python
   from Bio import Entrez
   import arxiv
   from scholarly import scholarly

   Entrez.email = "your.email@example.com"  # NCBI requires a contact email

   # PubMed: biomedical literature
   handle = Entrez.esearch(
       db="pubmed",
       term='"CRISPR-Cas Systems"[MeSH] AND "Gene Editing"[MeSH]',
       retmax=20,
   )
   pubmed_ids = Entrez.read(handle)["IdList"]
   handle.close()

   # arXiv: computational biology preprints
   arxiv_results = list(
       arxiv.Search(query="protein structure prediction", max_results=10).results()
   )

   # Google Scholar: broad cross-disciplinary coverage
   scholar_results = scholarly.search_pubs("single cell RNA sequencing analysis methods")
   ```

3. **Step 3: Supplement with AI-assisted search (Tier 2)**
   - Use AI-assisted web search for landscape overviews and recent developments
   - Use general web search for protocols, tutorials, and documentation
   ```python
   from anthropic import Anthropic

   client = Anthropic()
   response = client.messages.create(
       model="claude-opus-4-7",
       max_tokens=4096,
       tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
       messages=[{
           "role": "user",
           "content": "What are the latest developments in CAR-T cell therapy for solid tumors in 2024?",
       }],
   )
   print(response.content)
   ```

4. **Step 4: Evaluate and filter results**
   - Screen titles and abstracts for relevance
   - Prioritize by recency, journal quality, citation count, and study design
   - For clinical evidence, prioritize RCTs, systematic reviews, and meta-analyses
   - For methods, prioritize protocol papers and method comparisons
   - Decision point: If too many results, add more specific terms or filters. If too few, broaden terms and add synonyms.

5. **Step 5: Deep dive into key papers (Tier 3)**
   - Extract full text from high-priority papers
   - Download supplementary materials for data and protocols
   - Check reference lists for additional relevant papers
   ```python
   import io
   import os
   from pathlib import Path
   from urllib.parse import urlparse

   import requests
   import trafilatura
   from pypdf import PdfReader

   # Extract article content from URL (clean main text, drops nav/ads)
   downloaded = trafilatura.fetch_url("https://www.nature.com/articles/nature12373")
   article_text = trafilatura.extract(downloaded)

   # Extract text from a PDF
   pdf_bytes = requests.get("https://arxiv.org/pdf/1706.03762.pdf", timeout=30).content
   reader = PdfReader(io.BytesIO(pdf_bytes))
   pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)

   # Download supplementary files via Crossref DOI metadata
   doi = "10.1038/nature12373"
   meta = requests.get(f"https://api.crossref.org/works/{doi}", timeout=30).json()
   out_dir = Path("./supplementary_materials")
   out_dir.mkdir(exist_ok=True)
   for link in meta.get("message", {}).get("link", []):
       url = link.get("URL")
       if not url:
           continue
       fname = os.path.basename(urlparse(url).path) or "supplement.bin"
       (out_dir / fname).write_bytes(requests.get(url, timeout=60).content)
   ```

6. **Step 6: Document and iterate**
   - Record all search terms, databases, filters, and result counts
   - If gaps remain, revisit Steps 2-3 with refined queries
   - For systematic reviews, follow PRISMA guidelines for reporting

## Common Search Scenarios

The following scenarios illustrate how to combine the three tiers for typical research questions.

### Finding Methods and Protocols

Start with PubMed for published methodology papers, then supplement with web search for step-by-step protocols from resources like protocols.io.

```python
from Bio import Entrez
from duckduckgo_search import DDGS

Entrez.email = "your.email@example.com"

# Search for methodology papers in PubMed
handle = Entrez.esearch(
    db="pubmed",
    term='"Western Blotting"[MeSH] AND (protocol OR method OR technique)',
    retmax=10,
)
pubmed_ids = Entrez.read(handle)["IdList"]
handle.close()

# Check web for step-by-step protocols
web_hits = DDGS().text("Western blot protocol for membrane proteins", max_results=5)
```

### Understanding Disease Mechanisms

Begin with review articles for a broad overview, then drill into specific mechanistic studies.

```python
# Find review articles first for an overview
results = query_pubmed(
    '"Alzheimer Disease"[MeSH] AND pathophysiology AND review[Publication Type]',
    max_papers=10
)

# Then find specific mechanistic studies
results = query_pubmed(
    '"Alzheimer Disease"[MeSH] AND ("amyloid beta"[MeSH] OR tau) AND mechanism',
    max_papers=20
)
```

### Finding Drug and Treatment Information

Use publication type filters to separate clinical trial evidence from systematic reviews.

```python
# Clinical trials for a specific drug-condition pair
results = query_pubmed(
    '"Drug Name"[Substance Name] AND "Condition"[MeSH] AND clinical trial[Publication Type]',
    max_papers=20
)

# Systematic reviews and meta-analyses
results = query_pubmed(
    '"Drug Name" AND "Condition" AND (systematic review[Publication Type] OR meta-analysis[Publication Type])',
    max_papers=10
)
```

### Tracking Latest Developments

Combine AI-assisted search for synthesis with database searches for recent indexed publications.

```python
from anthropic import Anthropic
from Bio import Entrez

client = Anthropic()
Entrez.email = "your.email@example.com"

# AI-assisted synthesis of recent advances (Claude API web search tool)
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    messages=[{
        "role": "user",
        "content": "What are the most significant advances in CAR-T cell therapy in 2024?",
    }],
)

# Supplement with recent PubMed results
handle = Entrez.esearch(
    db="pubmed",
    term='"Chimeric Antigen Receptor T-Cell Therapy"[MeSH] AND "2024"[Date - Publication]',
    retmax=20,
)
pubmed_ids = Entrez.read(handle)["IdList"]
handle.close()
```

### Finding Specific Reagents and Materials

Use AI-assisted search for validated reagent recommendations, supplemented by general web search.

```python
from anthropic import Anthropic
from duckduckgo_search import DDGS

client = Anthropic()

# Search for validated reagents (Claude API + web search tool)
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
    messages=[{
        "role": "user",
        "content": "validated antibodies for Western blot detection of p53 protein",
    }],
)

# Search supplier databases
supplier_hits = DDGS().text("p53 antibody Western blot validated", max_results=5)
```

### Comparative Analysis Across Methods

Use AI-assisted search for synthesized comparisons of techniques or tools.

```python
from anthropic import Anthropic

client = Anthropic()

# Compare approaches with AI synthesis (Claude API web search tool)
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
    messages=[{
        "role": "user",
        "content": "Compare different CRISPR delivery methods for in vivo gene editing: viral vectors vs lipid nanoparticles",
    }],
)
print(response.content)
```

## Quality Assessment Checklist

When evaluating search results, apply these criteria:

- **Source reliability**: Is the paper from a peer-reviewed journal?
- **Author credentials**: Are the authors established experts in the field?
- **Recency**: Is the information current enough for your purpose?
- **Study design**: Is the design appropriate for the question (e.g., RCT for efficacy, cohort for risk)?
- **Sample size**: Is it adequate for the conclusions drawn?
- **Reproducibility**: Are methods described clearly enough to replicate?
- **Conflicts of interest**: Are any conflicts declared?
- **Citation count**: Has the paper been well-cited by subsequent work?

## Further Reading

- [PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/) -- Official guide to PubMed search syntax, field tags, filters, and advanced features
- [arXiv Help Pages](https://info.arxiv.org/help/index.html) -- Documentation on arXiv search, subject categories, and submission process
- [MeSH Browser](https://meshb.nlm.nih.gov/) -- NLM tool for browsing and searching the Medical Subject Headings controlled vocabulary
- [PRISMA Statement](http://www.prisma-statement.org/) -- Guidelines for transparent reporting of systematic reviews and meta-analyses
- [Cochrane Handbook for Systematic Reviews](https://training.cochrane.org/handbook) -- Gold-standard methodology for systematic literature reviews

## Related Skills

- `pubmed-database` -- Direct PubMed API access for programmatic literature retrieval
- `scientific-manuscript-writing` -- Structuring literature review sections within manuscripts
- `research-question-formulation` -- Frameworks for defining answerable research questions

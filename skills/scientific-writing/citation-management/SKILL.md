---
name: "citation-management"
description: "Guide for selecting a reference manager, organizing citations, and applying citation styles in scientific writing. Covers Zotero, Mendeley, EndNote, and Paperpile comparison; APA, Vancouver, ACS, and Nature citation styles; DOI management; citation tracking; and integration with Word, Google Docs, and LaTeX. Use when setting up a reference workflow, switching tools, or troubleshooting citation formatting."
license: "CC-BY-4.0"
---

# Citation Management for Scientific Writing

## Overview

Citation management is the systematic practice of collecting, organizing, annotating, and inserting bibliographic references in scientific documents. A well-chosen reference manager reduces manual formatting errors, keeps libraries synchronized across devices, and integrates cleanly with word processors and LaTeX. This guide covers tool selection, citation style conventions, DOI and persistent identifier workflows, citation tracking, and common pitfalls that account for a large share of post-publication corrections and retractions related to reference errors.

## Key Concepts

### 1. Reference Manager Capabilities and Tool Comparison

All major reference managers share a common core: they store metadata (author, title, journal, year, DOI), generate formatted citations in a chosen style, and provide a browser extension for one-click capture from publisher pages. The differences lie in collaboration features, cloud storage, word processor plugin support, price, and data portability.

| Feature | Zotero | Mendeley | EndNote | Paperpile |
|---------|--------|----------|---------|-----------|
| Cost | Free (open-source) | Free / paid tiers | ~$275 (perpetual) | $36/year |
| Cloud storage | 300 MB free; paid plans | 2 GB free | Institutional / local | Unlimited (Google Drive) |
| Word processor | Word, LibreOffice, Google Docs | Word, LibreOffice | Word, LibreOffice | Word, Google Docs |
| LaTeX integration | BibTeX/BibLaTeX export; Better BibTeX plugin | BibTeX export (manual) | BibTeX export | BibTeX; direct Overleaf sync |
| Group libraries | Free (up to 300 MB); paid unlimited | Yes | Yes (institutional) | Yes |
| PDF annotation | Built-in (Zotero 6+) | Desktop app | Basic | PDF.js viewer |
| Open-source | Yes (GPLv3) | No (Elsevier) | No (Clarivate) | No |
| Data portability | RIS, BibTeX, CSV — no lock-in | RIS, BibTeX | RIS, BibTeX; proprietary .enl | BibTeX, RIS |
| Best for | Academic open-source / LaTeX users | Beginners; Elsevier users | Large institutional labs | Google Workspace users |

**Key differences to know**:
- Mendeley is owned by Elsevier. Desktop sync reliability has declined since acquisition; many labs have migrated to Zotero.
- EndNote has the deepest Microsoft Word integration and the largest style library, but high cost makes it unattractive for individual researchers.
- Paperpile's real-time Google Docs integration is unmatched, making it the best choice for teams that write primarily in Docs.
- Zotero is the most flexible: free, open-source, cross-platform, and extensible via plugins.

### 2. Citation Style Families

Citation styles are governed by the target journal's Instructions for Authors — the author does not choose independently. The two major families are **author-date** (parenthetical, e.g., "(Smith, 2023)") and **citation-sequence** (numbered, e.g., superscript¹ or bracketed [1]).

| Style | In-text format | Reference list order | Abbreviate journals? | DOI required? | Typical discipline |
|-------|---------------|---------------------|----------------------|---------------|--------------------|
| **APA 7th** | (Author, Year) | Alphabetical by first author | No | Yes (for journal articles) | Psychology, social science, biology |
| **Vancouver** | Superscript [1] | Citation order | Yes (ISO 4) | Recommended | Medicine (NEJM, Lancet, BMJ) |
| **ACS** | Superscript or italic (1) | Citation order | Yes (CASSI) | Required | Chemistry (JACS, ACS Nano) |
| **Nature** | Superscript¹ | Citation order | Yes (NLM) | Yes | Nature family journals |
| **IEEE** | Bracketed [1] | Citation order | Yes | Recommended | Engineering, computer science |
| **Chicago author-date** | (Author year) | Alphabetical | No | Recommended | History, humanities |

**Journal name abbreviation**: Vancouver uses ISO 4 abbreviations (e.g., "N. Engl. J. Med."); ACS uses Chemical Abstracts Service Source Index (CASSI); Nature uses PubMed/NLM abbreviations. These are not interchangeable. Your reference manager's built-in Citation Style Language (CSL) file handles this automatically — do not abbreviate manually.

### 3. DOIs and Persistent Identifiers

A Digital Object Identifier (DOI) is the canonical persistent identifier for a publication and should be included in every citation where available.

**DOI format and resolution**:
- All DOIs begin with `10.` followed by a registrant code (e.g., `10.1038/`) and a suffix
- Always resolve DOIs through `https://doi.org/10.XXXX/suffix` — a bare DOI is not a clickable URL
- Do not use `http://dx.doi.org/` (old URL scheme); use `https://doi.org/` (current)

**Preprint DOIs**: bioRxiv, medRxiv, and ChemRxiv assign DOIs to preprints that are distinct from the eventual journal article DOI. When a preprint is published, both DOIs are valid but refer to different versions. Always check whether a peer-reviewed version exists; if so, cite the journal article DOI, not the preprint DOI.

**Other persistent identifiers**:
- **PMID** (PubMed ID) and **PMCID** (PubMed Central ID): NLM-specific; include alongside DOI for medical literature; required by NIH for funded publications
- **arXiv ID**: physics, math, CS preprints; format `arXiv:YYMM.NNNNN`
- **ISBN**: books and book chapters — not resolvable as URL; use for archival purposes only
- **Handle**: institutional repository identifiers; less universal than DOI

### 4. Citation Tracking and Impact Metrics

Citation tracking serves two purposes: monitoring how often your own publications are cited (research impact) and discovering papers that have cited a key reference you found (forward citation chaining).

| Tool | Coverage | Cost | Strengths |
|------|----------|------|-----------|
| **Google Scholar** | Broadest (includes gray literature, theses, book chapters) | Free | Zero barrier; personal citations dashboard; free alerts |
| **Web of Science** | Peer-reviewed journals; curated | Subscription | Journal Impact Factor; author disambiguation; citation maps |
| **Scopus** | Broad peer-reviewed; strong non-English | Subscription | Better than WoS for non-English content; CiteScore metrics |
| **iCite / NIH OCC** | PubMed-indexed only | Free | Relative Citation Ratio (RCR); NIH-funded publication tracking |
| **Semantic Scholar** | AI-curated; broad | Free | "Highly influential citations" classification; concept extraction |
| **OpenAlex** | Fully open; ~250M works | Free | Open API; no subscription; successor to Microsoft Academic |

**Setting up citation alerts**: Google Scholar Alerts are the simplest way to receive email notifications when a paper is cited. Create an alert for your own papers, for key papers in your field, and for relevant author names.

## Decision Framework

```
What is your primary need?
├── Set up or switch reference manager
│   ├── LaTeX + Overleaf as primary editor
│   │   └── → Zotero + Better BibTeX plugin (auto-syncing .bib)
│   ├── Google Docs as primary editor
│   │   └── → Paperpile (native Docs integration) or Zotero (Docs plugin)
│   ├── Microsoft Word, no institutional license
│   │   └── → Zotero (free, robust Word plugin)
│   ├── Microsoft Word, institutional license available
│   │   └── → EndNote (deepest Word integration) or Zotero
│   └── Collaborative team across institutions
│       └── → Zotero group library (free, open, no vendor lock-in)
│
├── Choose a citation style
│   ├── Medical / clinical journal → Vancouver (superscript numbered)
│   ├── Chemistry journal → ACS style
│   ├── Nature / Science family → Nature style
│   ├── Psychology / behavioral science → APA 7th
│   └── Engineering → IEEE
│   (Always check journal Instructions for Authors — do not guess)
│
├── Systematic review workflow
│   ├── Reference collection → Zotero or Mendeley
│   ├── Deduplication → reference manager built-in + manual check
│   ├── Title/abstract screening → Rayyan, Covidence, or Abstrackr
│   └── Full-text review → download PDFs into reference manager
│
└── Citation tracking
    ├── Free tracking → Google Scholar + iCite
    └── Institutional tracking (IF, h-index) → Web of Science or Scopus
```

| Scenario | Recommended Approach | Key Reason |
|----------|---------------------|------------|
| Solo academic, LaTeX-heavy | Zotero + Better BibTeX | Auto-syncing .bib; free; no vendor lock-in |
| Lab group with shared library | Zotero group library | Free for groups; version-control-friendly |
| Google Docs primary | Paperpile | Best native Docs integration |
| Medical or clinical writing | Any manager + Vancouver CSL | Style is journal-dictated; tool choice is secondary |
| Systematic review (PRISMA) | Zotero → RIS export → Rayyan | Best deduplication + screening workflow |
| Grant application (NIH) | Any manager + PMCID tracking | NIH requires PMCID for funded-research citations |
| Large funded lab, Word-centric | EndNote | Deepest Word integration; comprehensive style library |
| High-throughput literature mining | OpenAlex API (programmatic) | Free, open, bulk-accessible |

## Best Practices

1. **Capture metadata at the point of discovery, using the browser extension from the publisher's page**: Do not bookmark URLs to "add later" — metadata capture from publisher pages is far more accurate than from PDFs, which frequently garble author names with non-ASCII characters, truncate long author lists incorrectly, or misparse page ranges in old articles.

2. **Always verify DOI resolution after import**: After importing any reference, click the DOI link. Automated metadata import frequently fails for pre-2000 papers, conference proceedings, and book chapters. A broken or wrong DOI is a legitimate reason for a post-publication correction and will delay typesetting.

3. **Store PDFs inside the reference manager, not in a parallel folder structure**: Keeping PDFs as attachments within the reference manager (rather than external links to a file system location) ensures citations and full texts remain synchronized when you move, rename, or reorganize directories. External file links break silently on directory restructuring.

4. **Use a consistent citation key format for LaTeX and never change it mid-project**: In Zotero with Better BibTeX, configure a global citation key template (e.g., `[auth:lower][year][veryshorttitle]`) before importing your first reference. Changing the template mid-project regenerates all keys, orphaning every `\cite{}` command in your existing `.tex` files.

5. **Organize by topic, not by manuscript**: Create collections by research topic ("CRISPR mechanisms," "cardiac MRI methods") rather than by output document ("Chapter 3," "Paper 1"). Topic organization allows reference reuse across projects and prevents accumulating duplicate entries in separate project collections.

6. **Run "Find Duplicates" before every manuscript submission**: Duplicate entries produce references with inconsistent formatting for the same paper — one as "Smith et al." and one with the full author list — which editors and reviewers immediately flag. Most managers include automatic deduplication; run it at least once before generating the final reference list.

7. **Export a static archive at submission**: Export the reference list as `.bib`, `.ris`, or `.enl` at the moment of manuscript submission and archive it alongside the submitted PDF. This ensures you can reproduce the exact reference list even if your live library changes during the review period (which often lasts 6–18 months for high-impact journals).

8. **For NIH grants, track PMCIDs separately**: NIH requires that any publication resulting from NIH funding include the PubMed Central ID (PMCID) in grant progress reports and renewal applications. Maintain a spreadsheet of your publications with PMID, PMCID, and grant numbers to avoid last-minute compliance scrambles.

## Common Pitfalls

1. **Trusting autofill metadata without spot-checking**: CrossRef metadata is usually correct for recent articles, but PDF parsing for author names, especially those with diacritics, double surnames, or non-Latin scripts, fails frequently. Conference proceedings and book chapters are particularly unreliable.
   - *How to avoid*: After importing any reference, check the author list (especially last author, often truncated), page numbers, journal name, and year against the actual paper. For old or non-English references, enter metadata manually.

2. **Using the wrong citation style for the target journal**: Reformatting 80 references from APA to Vancouver by hand introduces errors in author lists, punctuation, and journal name abbreviation. Journals reject or return manuscripts with wrong styles as a matter of policy.
   - *How to avoid*: Check the journal's "Instructions for Authors" before writing, not before submission. Set the correct style in your reference manager plugin at the start of the project. Most CSL files are maintained in the [Zotero style repository](https://www.zotero.org/styles).

3. **Citing preprints without flagging preprint status**: bioRxiv/medRxiv preprints are citable but must be identified as preprints. Formatting a preprint identically to a journal article misleads readers about peer-review status and may violate journal policies.
   - *How to avoid*: Verify that the reference manager's "Item Type" is set to "Preprint" (not "Journal Article"). The formatted citation should include the repository name (bioRxiv, medRxiv) and note it as a preprint. Before submission, search PubMed or the journal's website for a peer-reviewed version.

4. **Duplicate library entries generating inconsistent in-text numbers**: The same paper imported twice may appear as both reference [14] and reference [31], producing a malformed numbered reference list.
   - *How to avoid*: Use "Find Duplicates" regularly. When merging a collaborator's library, resolve all duplicates before inserting citations into the shared document.

5. **Word processor field codes collapsing to plain text during collaboration**: Co-authors who do not have the same reference manager plugin, or who accept tracked changes from plain-text versions, can destroy the field codes that link in-text citations to the reference list.
   - *How to avoid*: Share documents with field codes intact (not "Remove Field Codes" exports). Only flatten to plain text in the final post-acceptance version. For cloud collaboration, use Google Docs + Paperpile or a LaTeX-based workflow to avoid this entirely.

6. **LaTeX .bib file conflicts in multi-author teams**: Multiple team members editing a shared `.bib` file produces citation key conflicts, duplicate entries, and garbled author fields.
   - *How to avoid*: Designate one person as the .bib file owner. Use Zotero + Better BibTeX with auto-export to a git-tracked `.bib` file. All team members use the same repository; never edit the `.bib` file manually.

7. **Over-citing in grant applications, crowding out scientific content**: Excessive citations in the Specific Aims or Research Strategy reduce space for the scientific narrative and signal to reviewers that the applicant cannot distinguish foundational from peripheral literature.
   - *How to avoid*: Aim for 1–3 references per factual claim in grants. Prefer the most recent authoritative review plus the key primary paper over exhaustive citation. Use citation managers to identify the single most-cited original study for each claim.

## Workflow

1. **One-time setup**
   - Select reference manager based on team workflow and editor (see Decision Framework)
   - Install browser extension (Zotero Connector, Mendeley Web Importer, or Paperpile extension)
   - Install word processor plugin (Word add-in or Google Docs add-on)
   - Create a project-specific collection in the library
   - Set the citation style in the word processor plugin (or configure Better BibTeX for LaTeX)
   - (LaTeX) Configure Better BibTeX: set citation key template, enable auto-export to `references.bib` in project directory, commit `.bib` to git

2. **Active collection phase**
   - Use browser extension to capture from publisher pages, PubMed, Google Scholar, or arXiv
   - For books and grey literature, enter metadata manually (browser extension won't parse them correctly)
   - Annotate PDFs with relevance notes and key quotes for later synthesis
   - Run "Find Duplicates" weekly during active collection

3. **Writing integration**
   - Insert citations using the word processor plugin — never type numbers manually
   - (LaTeX) Use `\cite{key}` with keys from the synchronized `.bib` file
   - Periodically refresh the bibliography to catch newly inserted references

4. **Pre-submission final check**
   - Run "Find Duplicates" one final time
   - Spot-check 10% of DOIs for correct resolution
   - Confirm citation style, journal name abbreviation, and DOI inclusion policy match journal requirements
   - (LaTeX) Compile clean from exported `.bib`; fix any `undefined citation` warnings
   - Export static archive (`.bib`, `.ris`) and store alongside submission version
   - (NIH grants) Verify all funded publications have PMCIDs recorded

## Protocol Guidelines

1. **Reference integrity audit**: Before submission to a high-impact journal, have a lab member not involved in writing check 5–10 random references by verifying the DOI resolves and that the cited fact appears in that paper — this catches "citation chaining errors" where a claim propagates through literature without ever being verified in the original source.
2. **Systematic review deduplication protocol**: Export all search results as `.ris` files, import into reference manager, run automated deduplication, then perform a manual review pass checking titles, years, and first author names — automated tools miss duplicates with slightly different metadata.
3. **Style migration**: When switching citation styles (e.g., between journal submissions), use the reference manager's style change function — never reformat manually. Verify the first 5 and last 5 references after the switch to confirm the style applied correctly.

## Further Reading

- [Zotero documentation](https://www.zotero.org/support/) — complete reference for collections, tags, groups, and plugins
- [Better BibTeX for Zotero](https://retorque.re/zotero-better-bibtex/) — LaTeX integration, citation key management, auto-export
- [Citation Style Language (CSL) style repository](https://www.zotero.org/styles) — 10,000+ journal-specific styles for all major managers
- [ICMJE citation recommendations](https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html) — medical journal citation standards and authorship guidelines
- [CrossRef DOI registration and resolution](https://www.crossref.org/) — authoritative DOI resolver and metadata registry

## Related Skills

- `scientific-manuscript-writing` — where citations are integrated into manuscript sections (Introduction, Discussion)
- `literature-review` — systematic approaches to collecting and screening the references you will manage
- `latex-research-posters` — LaTeX-specific BibTeX configuration and citation key workflow

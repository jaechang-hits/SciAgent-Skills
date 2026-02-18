# TDC Datasets Catalog

Complete catalog of all datasets in the Therapeutics Data Commons, organized by task category.

## Single-Instance Prediction Datasets

Predict properties of individual molecules or proteins. Import: `tdc.single_pred`.

### ADME (Absorption, Distribution, Metabolism, Excretion)

| Dataset | Size | Label Type | Subcategory |
|---------|------|-----------|-------------|
| `Caco2_Wang` | 906 | Regression (permeability) | Absorption |
| `Caco2_AstraZeneca` | 700 | Regression (permeability) | Absorption |
| `HIA_Hou` | 578 | Binary (absorbed/not) | Absorption |
| `Pgp_Broccatelli` | 1,212 | Binary (inhibitor/not) | Absorption |
| `Bioavailability_Ma` | 640 | Binary (F>=50%) | Absorption |
| `F20_edrug3d` | 1,017 | Binary (F>=20%) | Absorption |
| `F30_edrug3d` | 1,017 | Binary (F>=30%) | Absorption |
| `BBB_Martins` | 1,975 | Binary (penetrant/not) | Distribution |
| `PPBR_AZ` | 1,797 | Regression (% bound) | Distribution |
| `VDss_Lombardo` | 1,130 | Regression (L/kg) | Distribution |
| `CYP2C19_Veith` | 12,665 | Binary (inhibitor/not) | Metabolism |
| `CYP2D6_Veith` | 13,130 | Binary (inhibitor/not) | Metabolism |
| `CYP3A4_Veith` | 12,328 | Binary (inhibitor/not) | Metabolism |
| `CYP1A2_Veith` | 12,579 | Binary (inhibitor/not) | Metabolism |
| `CYP2C9_Veith` | 12,092 | Binary (inhibitor/not) | Metabolism |
| `CYP2C9_Substrate_CarbonMangels` | 666 | Binary (substrate/not) | Metabolism |
| `CYP2D6_Substrate_CarbonMangels` | 664 | Binary (substrate/not) | Metabolism |
| `CYP3A4_Substrate_CarbonMangels` | 667 | Binary (substrate/not) | Metabolism |
| `Half_Life_Obach` | 667 | Regression (hours) | Excretion |
| `Clearance_Hepatocyte_AZ` | 1,020 | Regression (uL/min/10^6) | Excretion |
| `Clearance_Microsome_AZ` | 1,102 | Regression (mL/min/kg) | Excretion |
| `Solubility_AqSolDB` | 9,982 | Regression (logS) | Solubility |
| `Lipophilicity_AstraZeneca` | 4,200 | Regression (logD) | Lipophilicity |
| `HydrationFreeEnergy_FreeSolv` | 642 | Regression (kcal/mol) | Solubility |

### Toxicity

| Dataset | Size | Label Type | Subcategory |
|---------|------|-----------|-------------|
| `hERG` | 648 | Binary (blocker/not) | Organ (cardiac) |
| `hERG_Karim` | 13,445 | Binary (blocker/not) | Organ (cardiac) |
| `DILI` | 475 | Binary (toxic/not) | Organ (liver) |
| `Skin_Reaction` | 404 | Binary | Organ (skin) |
| `Carcinogens_Lagunin` | 278 | Binary | General |
| `Respiratory_Toxicity` | 278 | Binary | Organ (lung) |
| `AMES` | 7,255 | Binary (mutagen/not) | General |
| `LD50_Zhu` | 7,385 | Regression (mg/kg) | General |
| `ClinTox` | 1,478 | Binary (failed trial/not) | Clinical |
| `SkinSensitization` | 278 | Binary | Organ (skin) |
| `EyeCorrosion` | 278 | Binary | Organ (eye) |
| `EyeIrritation` | 278 | Binary | Organ (eye) |
| `Tox21-AhR` | 8,169 | Binary (active/not) | Environmental |
| `Tox21-AR` | 9,362 | Binary (active/not) | Environmental |
| `Tox21-AR-LBD` | 8,343 | Binary (active/not) | Environmental |
| `Tox21-ARE` | 6,475 | Binary (active/not) | Environmental |
| `Tox21-aromatase` | 6,733 | Binary (active/not) | Environmental |
| `Tox21-ATAD5` | 8,163 | Binary (active/not) | Environmental |
| `Tox21-ER` | 7,257 | Binary (active/not) | Environmental |
| `Tox21-ER-LBD` | 8,163 | Binary (active/not) | Environmental |
| `Tox21-HSE` | 8,162 | Binary (active/not) | Environmental |
| `Tox21-MMP` | 7,394 | Binary (active/not) | Environmental |
| `Tox21-p53` | 8,163 | Binary (active/not) | Environmental |
| `Tox21-PPAR-gamma` | 7,396 | Binary (active/not) | Environmental |

### HTS (High-Throughput Screening)

| Dataset | Size | Label Type | Source |
|---------|------|-----------|--------|
| `SARSCoV2_Vitro_Touret` | 1,484 | Binary | SARS-CoV-2 |
| `SARSCoV2_3CLPro_Diamond` | 879 | Binary | SARS-CoV-2 |
| `SARSCoV2_Vitro_AlabdulKareem` | 5,953 | Binary | SARS-CoV-2 |
| `Orexin1_Receptor_Butkiewicz` | 4,675 | Binary | Orexin receptor |
| `M1_Receptor_Agonist_Butkiewicz` | 1,700 | Binary | M1 receptor |
| `M1_Receptor_Antagonist_Butkiewicz` | 1,700 | Binary | M1 receptor |
| `HIV_Butkiewicz` | 40,000+ | Binary | HIV |
| `ToxCast` | 8,597 | Binary | Environmental |

### QM (Quantum Mechanics)

| Dataset | Size | Label Type |
|---------|------|-----------|
| `QM7` | 7,160 | Regression (electronic) |
| `QM8` | 21,786 | Regression (spectra) |
| `QM9` | 133,885 | Regression (multi-property) |

### Other Single-Instance Tasks

| Task | Dataset | Size | Label Type |
|------|---------|------|-----------|
| Yields | `Buchwald-Hartwig` | 3,955 | Regression (yield %) |
| Yields | `USPTO_Yields` | 853,879 | Regression (yield %) |
| Epitope | `IEDBpep-DiseaseBinder` | 6,080 | Binary |
| Epitope | `IEDBpep-NonBinder` | 24,320 | Binary |
| Develop | `Manufacturing` | varies | Binary |
| Develop | `Formulation` | varies | Binary |
| CRISPROutcome | `CRISPROutcome_Doench` | 5,310 | Regression (efficiency) |

## Multi-Instance Prediction Datasets

Predict interactions between pairs of entities. Import: `tdc.multi_pred`.

| Task | Dataset | Pairs | Drugs | Targets | Label Type |
|------|---------|-------|-------|---------|-----------|
| DTI | `BindingDB_Kd` | 52,284 | 10,665 | 1,413 | Regression (Kd) |
| DTI | `BindingDB_IC50` | 991,486 | 549,205 | 5,078 | Regression (IC50) |
| DTI | `BindingDB_Ki` | 375,032 | 174,662 | 3,070 | Regression (Ki) |
| DTI | `DAVIS` | 30,056 | 68 | 442 | Regression (binding) |
| DTI | `KIBA` | 118,254 | 2,111 | 229 | Regression (KIBA score) |
| DTI | `BindingDB_Patent` | 8,503 | — | — | Binary |
| DTI | `BindingDB_Approval` | 1,649 | — | — | Binary |
| DDI | `DrugBank` | 191,808 | 1,706 | — | Multi-class (86 types) |
| DDI | `TWOSIDES` | 4,649,441 | 645 | — | Multi-class |
| PPI | `HuRI` | 52,569 | — | — | Binary |
| PPI | `STRING` | 19,247 | — | — | Binary |
| GDA | `DisGeNET` | 81,746 | — | — | Binary |
| GDA | `PrimeKG_GDA` | varies | — | — | Binary |
| DrugRes | `GDSC1` | 178,000 | — | — | Regression (IC50) |
| DrugRes | `GDSC2` | 125,000 | — | — | Regression (IC50) |
| DrugSyn | `DrugComb` | 345,502 | — | — | Regression (synergy) |
| DrugSyn | `DrugCombDB` | 448,555 | — | — | Regression (synergy) |
| DrugSyn | `OncoPolyPharmacology` | 22,737 | — | — | Regression |
| PeptideMHC | `MHC1_NetMHCpan` | 184,983 | — | — | Regression (affinity) |
| PeptideMHC | `MHC2_NetMHCIIpan` | 134,281 | — | — | Regression (affinity) |
| AntibodyAff | `Protein_SAbDab` | 1,500+ | — | — | Regression (affinity) |
| MTI | `miRTarBase` | 380,639 | — | — | Binary |
| Catalyst | `USPTO_Catalyst` | 11,000+ | — | — | Multi-class |
| TrialOutcome | `TrialOutcome_WuXi` | 3,769 | — | — | Binary |

## Generation Datasets

Training sets for molecule design and retrosynthesis. Import: `tdc.generation`.

| Task | Dataset | Size | Description |
|------|---------|------|-------------|
| MolGen | `ChEMBL_V29` | 1,941,410 | Drug-like molecules from ChEMBL |
| MolGen | `ZINC` | 100,000+ | ZINC database subset |
| MolGen | `GuacaMol` | varies | Goal-directed benchmark set |
| MolGen | `Moses` | 1,936,962 | MOSES benchmark set |
| RetroSyn | `USPTO` | 1,939,253 | Full USPTO patent reactions |
| RetroSyn | `USPTO-50K` | 50,000 | Curated USPTO subset |
| PairMolGen | `Prodrug` | 1,000+ | Prodrug-to-drug transformations |
| PairMolGen | `Metabolite` | varies | Drug-to-metabolite transformations |

## Benchmark Groups

TDC provides pre-configured benchmark groups with standardized 5-seed evaluation:

- **admet_group** — 22 ADMET datasets (absorption, distribution, metabolism, excretion, toxicity) with scaffold splits
- **dti_dg_group** — Drug-target interaction with cold splits
- **drugcomb_group** — Drug synergy prediction

```python
from tdc.benchmark_group import admet_group
group = admet_group(path='data/')
benchmark = group.get('Caco2_Wang')
# Returns dict with 'train', 'valid', 'test' DataFrames
```

## Programmatic Dataset Discovery

```python
from tdc.utils import retrieve_dataset_names

adme_datasets = retrieve_dataset_names('ADME')
tox_datasets = retrieve_dataset_names('Tox')
dti_datasets = retrieve_dataset_names('DTI')
```

---

**Condensation note**: Condensed from original `datasets.md` (247 lines) to ~170 lines (~69% retention). All dataset entries preserved using compact table format. Relocated inline to SKILL.md: top ADME/Tox/DTI dataset code examples (Core API Modules 1-2), dataset loading pattern (Quick Start), split usage (Core API Module 4). Omitted: `label_distribution()` and `print_stats()` examples — covered in oracles_utilities.md; `get_data(format=...)` options — covered in SKILL.md Key Parameters.

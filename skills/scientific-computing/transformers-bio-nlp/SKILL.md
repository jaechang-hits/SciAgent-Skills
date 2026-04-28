---
name: "transformers-bio-nlp"
description: "HuggingFace Transformers with biomedical LMs (BioBERT, PubMedBERT, BioGPT, BioMedLM) for scientific NLP: NER (genes, diseases, chemicals), relation extraction, QA, text classification, abstract summarization. Covers loading, biomedical tokenization, inference pipelines, fine-tuning. Alternatives: spaCy en_core_sci_lg (rule-based NER), Stanza (biomedical models), NLTK."
license: "Apache-2.0"
---

# Transformers for Biomedical NLP

## Overview

HuggingFace Transformers provides a unified API to load, run, and fine-tune 500+ biomedical language models. The key biomedical models — BioBERT (trained on PubMed abstracts + PMC full text), PubMedBERT (trained from scratch on PubMed), BioGPT (generative, trained on PubMed), and BioMedLM — significantly outperform general-purpose BERT on biomedical NER, relation extraction, and question answering. The `pipeline()` abstraction handles tokenization, inference, and postprocessing in one call. Fine-tuning on task-specific labeled data (e.g., BC5CDR for chemical/disease NER) takes under an hour on a single GPU. The `datasets` library provides direct access to standard biomedical benchmarks.

## When to Use

- Extracting gene names, disease mentions, drug names, or chemical entities from biomedical abstracts (NER)
- Classifying abstracts by topic, sentiment of clinical outcomes, or PICO elements for systematic reviews
- Answering specific questions from biomedical literature using extractive QA (BioASQ format)
- Generating hypotheses or summaries from biomedical text using BioGPT or BioMedLM
- Fine-tuning a pre-trained biomedical model on a custom labeled dataset (e.g., your lab's annotations)
- Embedding biomedical sentences for semantic similarity search across literature
- Use spaCy + en_core_sci_lg for fast rule-augmented NER; use Stanza for dependency parsing

## Prerequisites

- **Python packages**: `transformers`, `torch`, `datasets`, `accelerate`, `sentencepiece`
- **GPU**: Strongly recommended for fine-tuning; inference on CPU is viable for single texts
- **Data requirements**: plain text biomedical strings; for fine-tuning, annotated data in BIO/IOB format

```bash
pip install transformers torch datasets accelerate sentencepiece
# For GPU (CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Quick Start

```python
from transformers import pipeline

# Named entity recognition with BioBERT
ner = pipeline("ner", model="allenai/scibert_scivocab_cased",
               aggregation_strategy="simple")

text = "BRCA1 mutations are associated with increased risk of breast cancer and ovarian cancer."
entities = ner(text)
for ent in entities:
    print(f"  {ent['word']:20s} {ent['entity_group']:10s} score={ent['score']:.3f}")
```

## Core API

### Module 1: Named Entity Recognition (NER)

Extract biomedical entities using pre-trained NER models.

```python
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

# BioBERT fine-tuned for NER (genes, diseases, chemicals)
# Common choices:
#   "allenai/scibert_scivocab_cased"  — scientific NER
#   "d4data/biomedical-ner-all"       — multi-entity biomedical NER
#   "pruas/BENT-PubMedBERT-NER-Gene"  — gene-specific NER
ner_pipe = pipeline(
    "ner",
    model="d4data/biomedical-ner-all",
    aggregation_strategy="simple",  # merge subword tokens into words
    device=-1  # -1=CPU, 0=GPU
)

abstracts = [
    "Imatinib inhibits the BCR-ABL1 tyrosine kinase and is first-line treatment for CML.",
    "EGFR mutations in non-small cell lung cancer predict response to erlotinib.",
]

for text in abstracts:
    entities = ner_pipe(text)
    print(f"\nText: {text[:60]}...")
    for e in entities:
        print(f"  [{e['entity_group']}] '{e['word']}' (score={e['score']:.2f})")
```

```python
# Manual tokenization + inference for batch processing
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

model_name = "allenai/scibert_scivocab_cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
model.eval()

text = "Metformin activates AMPK and reduces hepatic glucose production in type 2 diabetes."
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

with torch.no_grad():
    outputs = model(**inputs)

logits = outputs.logits  # shape: (1, seq_len, n_labels)
predictions = logits.argmax(dim=-1)[0]
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
labels = [model.config.id2label[p.item()] for p in predictions]

for token, label in zip(tokens[1:-1], labels[1:-1]):  # skip [CLS] and [SEP]
    if label != "O":
        print(f"  {token:20s} {label}")
```

### Module 2: Text Classification

Classify biomedical abstracts or sentences.

```python
from transformers import pipeline

# Zero-shot classification — no fine-tuning needed
zs_clf = pipeline("zero-shot-classification",
                  model="facebook/bart-large-mnli",
                  device=-1)

abstract = """
This randomized controlled trial evaluated the efficacy of pembrolizumab versus
chemotherapy in patients with advanced non-small-cell lung cancer. Overall survival
was significantly improved in the pembrolizumab arm (HR=0.60, 95% CI 0.41-0.89).
"""

candidate_labels = ["clinical trial", "basic research", "meta-analysis", "review"]
result = zs_clf(abstract, candidate_labels)
print("Zero-shot classification:")
for label, score in zip(result["labels"], result["scores"]):
    print(f"  {label:20s}: {score:.3f}")
```

```python
# Fine-tuned sentiment/outcome classification
from transformers import pipeline

# Example: classify clinical outcome sentiment
clf = pipeline("text-classification",
               model="pruas/BENT-PubMedBERT-NER-Gene",  # use appropriate task-specific model
               device=-1)

sentences = [
    "Treatment significantly improved overall survival (p<0.001).",
    "No statistically significant difference was observed between groups.",
]
results = clf(sentences)
for sent, result in zip(sentences, results):
    print(f"  [{result['label']} | {result['score']:.2f}] {sent[:50]}...")
```

### Module 3: Biomedical Question Answering

Extract answers from biomedical text passages.

```python
from transformers import pipeline

# Extractive QA: find answer span within context
qa_pipe = pipeline(
    "question-answering",
    model="sultan/BioM-ELECTRA-Large-SQuAD2",  # biomedical QA model
    device=-1
)

context = """
BRCA1 is a tumor suppressor gene located on chromosome 17q21. Pathogenic variants
in BRCA1 confer a lifetime breast cancer risk of 50-72% and ovarian cancer risk
of 44-46%. BRCA1 protein functions in DNA double-strand break repair via
homologous recombination.
"""

questions = [
    "What chromosome is BRCA1 located on?",
    "What is the lifetime breast cancer risk from BRCA1 variants?",
    "What DNA repair pathway does BRCA1 participate in?",
]

for q in questions:
    result = qa_pipe(question=q, context=context)
    print(f"Q: {q}")
    print(f"A: {result['answer']} (score={result['score']:.3f})\n")
```

### Module 4: Text Generation with BioGPT

Generate biomedical text, hypotheses, and summaries.

```python
from transformers import AutoTokenizer, BioGptForCausalLM
import torch

model_name = "microsoft/biogpt"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = BioGptForCausalLM.from_pretrained(model_name)
model.eval()

prompt = "The role of VEGF in tumor angiogenesis"
inputs = tokenizer(prompt, return_tensors="pt")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        num_beams=5,
        early_stopping=True,
        no_repeat_ngram_size=3,
        pad_token_id=tokenizer.eos_token_id,
    )

generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"Generated:\n{generated}")
```

### Module 5: Sentence Embeddings for Semantic Search

Embed biomedical text for similarity search and clustering.

```python
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

def mean_pooling(model_output, attention_mask):
    """Mean pooling across token embeddings."""
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return (token_embeddings * input_mask_expanded).sum(1) / input_mask_expanded.sum(1)

# PubMedBERT for biomedical sentence embeddings
model_name = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.eval()

sentences = [
    "BRCA1 is involved in DNA double-strand break repair.",
    "Homologous recombination requires BRCA1 and BRCA2.",
    "Metformin inhibits hepatic gluconeogenesis via AMPK.",
]

inputs = tokenizer(sentences, padding=True, truncation=True,
                   max_length=512, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

embeddings = mean_pooling(outputs, inputs["attention_mask"])
embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1).numpy()

# Compute cosine similarity
from numpy.linalg import norm
sim_01 = np.dot(embeddings[0], embeddings[1])
sim_02 = np.dot(embeddings[0], embeddings[2])
print(f"Similarity (BRCA1 repair vs. HR): {sim_01:.3f}")
print(f"Similarity (BRCA1 repair vs. Metformin): {sim_02:.3f}")
```

### Module 6: Fine-Tuning on Custom Data

Fine-tune a biomedical model on a labeled NER dataset.

```python
from transformers import (AutoTokenizer, AutoModelForTokenClassification,
                           TrainingArguments, Trainer, DataCollatorForTokenClassification)
from datasets import Dataset
import numpy as np

# Example: minimal NER fine-tuning setup
model_name = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract"
label_list = ["O", "B-GENE", "I-GENE", "B-DISEASE", "I-DISEASE"]
id2label = {i: l for i, l in enumerate(label_list)}
label2id = {l: i for i, l in enumerate(label_list)}

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(
    model_name, num_labels=len(label_list), id2label=id2label, label2id=label2id
)

# Training arguments
training_args = TrainingArguments(
    output_dir="./biomed_ner_finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir="./logs",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
)

print(f"Model ready for fine-tuning: {model_name}")
print(f"Labels: {label_list}")
# trainer = Trainer(model=model, args=training_args, ...)
# trainer.train()
```

## Key Concepts

### Tokenization of Biomedical Text

Biomedical text contains special tokens (gene symbols, drug names, chemical SMILES, numeric values) that WordPiece and BPE tokenizers split unexpectedly. For example, "BRCA1" → `["BR", "##CA", "##1"]`. This subword splitting does not affect classification tasks but does affect NER — use `aggregation_strategy="simple"` or `"first"` in `pipeline()` to merge subword predictions back to word level.

### BIO Labeling Scheme

NER uses BIO (Begin-Inside-Outside) tagging: `B-GENE` marks the first token of a gene name, `I-GENE` marks continuation tokens, `O` marks non-entity tokens. During fine-tuning, align labels to subword tokens by setting non-first subword labels to `-100` (ignored by the loss function).

## Common Workflows

### Workflow 1: Batch Abstract NER and Entity Aggregation

```python
from transformers import pipeline
import pandas as pd

ner_pipe = pipeline("ner", model="d4data/biomedical-ner-all",
                    aggregation_strategy="simple", device=-1)

abstracts = [
    "Pembrolizumab combined with chemotherapy significantly improved progression-free survival in HER2-positive breast cancer.",
    "Inhibition of EGFR by gefitinib is effective in patients with activating EGFR mutations in exons 19 and 21.",
    "CRISPR-Cas9 editing of the PCSK9 gene in hepatocytes reduces LDL cholesterol in murine models.",
]

records = []
for i, text in enumerate(abstracts):
    entities = ner_pipe(text)
    for e in entities:
        records.append({
            "abstract_id": i,
            "entity": e["word"],
            "type": e["entity_group"],
            "score": round(e["score"], 3),
        })

df = pd.DataFrame(records)
print(df.groupby("type")["entity"].apply(list).to_string())
df.to_csv("extracted_entities.csv", index=False)
print(f"\nExtracted {len(df)} entity mentions across {len(abstracts)} abstracts")
```

### Workflow 2: Semantic Similarity Ranking for Literature Retrieval

```python
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

model_name = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.eval()

def embed(texts):
    enc = tokenizer(texts, padding=True, truncation=True,
                    max_length=512, return_tensors="pt")
    with torch.no_grad():
        out = model(**enc)
    vecs = out.last_hidden_state[:, 0, :]  # [CLS] token
    return torch.nn.functional.normalize(vecs, dim=1).numpy()

query = "CRISPR base editing for correction of point mutations in genetic disease"
corpus = [
    "Base editing enables precise single-base changes in genomic DNA without double-strand breaks.",
    "CAR-T cell therapy targets CD19 in B-cell acute lymphoblastic leukemia.",
    "Prime editing uses reverse transcriptase to install targeted edits at specific loci.",
    "RNA interference silences gene expression via RISC-mediated mRNA cleavage.",
]

q_emb = embed([query])
c_emb = embed(corpus)
scores = (q_emb @ c_emb.T).flatten()
ranked = sorted(zip(scores, corpus), reverse=True)

print("Top results:")
for score, text in ranked:
    print(f"  [{score:.3f}] {text[:70]}...")
```

## Key Parameters

| Parameter | Module/Function | Default | Range / Options | Effect |
|-----------|----------------|---------|-----------------|--------|
| `model` | `pipeline()` | — | HuggingFace model ID string | Pre-trained model to load; must match task |
| `aggregation_strategy` | NER `pipeline` | `"none"` | `"none"`, `"simple"`, `"first"`, `"average"` | Merge subword NER predictions; use `"simple"` for word-level output |
| `device` | `pipeline()` | -1 | -1 (CPU), 0 (GPU 0), 1 (GPU 1) | Inference device |
| `max_length` | tokenizer | 512 | 128–2048 (model-dependent) | Max token length; truncates longer inputs |
| `max_new_tokens` | `model.generate()` | 20 | 1–1000 | Tokens to generate for text generation models |
| `num_beams` | `model.generate()` | 1 | 1–10 | Beam search width; larger = better quality, slower |
| `num_train_epochs` | `TrainingArguments` | 3 | 1–10 | Fine-tuning epochs |
| `per_device_train_batch_size` | `TrainingArguments` | 8 | 4–32 | Batch size per GPU; reduce if OOM |
| `weight_decay` | `TrainingArguments` | 0.0 | 0.01–0.1 | L2 regularization for fine-tuning |

## Best Practices

1. **Use domain-specific models, not general BERT**: PubMedBERT trained from scratch on PubMed outperforms BERT-base by 5–15% on biomedical NER. Always start with biomedical pre-training before fine-tuning on task-specific data.

2. **Verify model licenses before production use**: Some models (BioGPT, BioMedLM) have research-only licenses. Check the HuggingFace model card's license field before deploying in commercial applications.

3. **Use `aggregation_strategy="simple"` for word-level NER output**: The default `"none"` returns subword tokens, making post-processing difficult. `"simple"` merges subword tokens using the first-token strategy.

4. **Truncate at sentence boundaries, not mid-sentence**: Long biomedical abstracts that exceed 512 tokens should be split at sentence boundaries before encoding. Mid-sentence truncation degrades NER accuracy for entities near the cutoff.

## Common Recipes

### Recipe: Extract Drug-Disease Pairs from PubMed Abstracts

```python
from transformers import pipeline
from itertools import product

ner = pipeline("ner", model="d4data/biomedical-ner-all",
               aggregation_strategy="simple", device=-1)

def extract_drug_disease_pairs(text):
    entities = ner(text)
    drugs    = [e["word"] for e in entities if e["entity_group"] in ("DRUG", "CHEMICAL")]
    diseases = [e["word"] for e in entities if e["entity_group"] in ("DISEASE", "CONDITION")]
    return list(product(drugs, diseases))

text = "Imatinib and nilotinib both target BCR-ABL1 in chronic myeloid leukemia and Philadelphia chromosome-positive ALL."
pairs = extract_drug_disease_pairs(text)
print("Drug-Disease pairs:")
for drug, disease in pairs:
    print(f"  {drug} → {disease}")
```

### Recipe: Sentence-Level Abstract Filtering

```python
from transformers import pipeline

clf = pipeline("zero-shot-classification",
               model="facebook/bart-large-mnli", device=-1)

abstracts = [
    "We present a phase 3 randomized controlled trial of semaglutide in type 2 diabetes.",
    "Structural analysis of the SARS-CoV-2 spike protein RBD domain by cryo-EM.",
    "A retrospective cohort study of 1,200 ICU patients during the COVID-19 pandemic.",
]

label_options = ["randomized controlled trial", "observational study", "structural biology", "computational study"]

for abstract in abstracts:
    result = clf(abstract, label_options)
    print(f"Type: {result['labels'][0]} ({result['scores'][0]:.2f})")
    print(f"  {abstract[:70]}...\n")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `CUDA out of memory` during inference | Batch too large for GPU VRAM | Reduce batch size; use `device=-1` for CPU; use `model.half()` for FP16 |
| NER returns subword tokens (`##CA`) | `aggregation_strategy` not set | Set `aggregation_strategy="simple"` in `pipeline()` |
| Model download times out | Large model files (1–10 GB); slow connection | Set `HF_HUB_OFFLINE=1` and download manually with `huggingface-cli download` |
| NER misses entities at end of long abstracts | Input truncated at 512 tokens | Split abstracts into sentences; process each separately |
| Fine-tuning loss is `NaN` | Learning rate too high or gradient explosion | Reduce `learning_rate` to 2e-5; enable gradient clipping `max_grad_norm=1.0` |
| Wrong entities for specialized domain | Generic biomedical model not suited to subdomain | Fine-tune on domain-labeled data; use more specific model (e.g., gene-only NER) |
| BioGPT generates repetitive text | `no_repeat_ngram_size` too small | Set `no_repeat_ngram_size=3` or `4`; increase `num_beams` |

## Related Skills

- `pubmed-database` — retrieve PubMed abstracts that serve as input to biomedical NLP pipelines
- `biorxiv-database` — retrieve preprints for NLP analysis before peer review
- `scientific-critical-thinking` — evaluate quality of NLP-extracted evidence before using for research conclusions

## References

- [HuggingFace Transformers docs](https://huggingface.co/docs/transformers/) — pipeline, tokenizer, and training API
- [BioBERT paper: Lee et al. (2020), Bioinformatics](https://doi.org/10.1093/bioinformatics/btz682) — pre-training on PubMed and PMC
- [PubMedBERT paper: Gu et al. (2021), ACL](https://doi.org/10.1145/3458754) — from-scratch pre-training on PubMed
- [BioGPT paper: Luo et al. (2022), Briefings in Bioinformatics](https://doi.org/10.1093/bib/bbac409) — generative biomedical language model
- [BioCreative benchmarks](https://biocreative.bioinformatics.udel.edu/) — standard NER and relation extraction datasets

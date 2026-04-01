# PESCAN

Static PE malware classifier trained on EMBER 2018. Uses XGBoost with SHAP 
explainability to flag malicious Windows executables based on features extracted 
directly from PE headers — the same approach AV engines use internally.

## Numbers

| Metric | Score |
|---|---|
| ROC-AUC | 0.9949 |
| Accuracy | 97% |
| True Benign | 97,408 / 100,000 |
| True Malicious | 97,233 / 100,000 |
| False Positives | 2,592 |
| False Negatives | 2,767 |
| Training samples | ~600,000 |
| Test samples | 200,000 |

## Features

- Section entropy — high entropy flags packed or encrypted content
- Import table hashes — library and function patterns fingerprint malware families
- Byte histogram distributions
- PE header metadata — timestamps, flags, subsystem
- Section sizes and properties

## Results

**Confusion Matrix** — out of 200k test samples, the model correctly identified
97,408 benign and 97,233 malicious files. Misclassified 2,592 benign as malicious
and missed 2,767 actual malware.

**Malicious Waterfall** — model scored 9.871 (near certain). Primary drivers were
high section entropy, an anomalous import library hash, and a near-zero raw section
size — classic packer signature.

**Benign Waterfall** — model scored -3.498. Features pulled strongly negative:
normal section sizes, expected entropy range, and recognized benign import patterns.

**Beeswarm** — across 500 test samples, section-based features dominate globally.
`section_rawsize_40` and `section_entropy_44` are the most consistent signals
across both malicious and benign files.

## Stack

- XGBoost, SHAP, scikit-learn, Python 3.12
- EMBER 2018 — Elastic/Endgame (~1M PE files)
- Trained on Kaggle T4 GPU

# SIH 26146 Requirement Traceability

| Requirement | Implementation | Status |
|---|---|---|
| Offline Linux | Local pipeline, inline graph resources, offline wheels | Implemented; target-host verification required |
| CSV/JSON/XML | `clti/ingestion.py` | Implemented |
| Cross-layer correlation | Exact TXID join retaining sightings | Implemented |
| IP–TX–wallet/entity graph | Typed Observer/IP/TX/UTXO/Address/Entity graph | Implemented |
| Entity clustering | Guarded common-input Union-Find | Implemented |
| Fitted AI/ML | Baseline-fitted Isolation Forest/robust fallback | Implemented |
| Peeling/mixing | Outpoint-chain traversal and collaborative-spend guard | Implemented |
| Seed risk propagation | Hop-decayed verified fund flow | Implemented |
| Explainable ranked leads | Component scores, reasons, local deviations | Implemented |
| Evidence per flag | Evidence Passport and original record IDs | Implemented |
| Dashboard | Streamlit + inline PyVis | Implemented |
| Synthetic data | Deterministic multi-hop generator with hard negatives | Implemented |
| Evaluation | Precision@K, recall and FPR script | Synthetic regression only |
| Official dataset | Canonical adapter ready | Pending file inspection |

Beyond the minimum: typed evidence, confidence vectors, counterfactual replay, provenance hashes and collaborative-spend false-merge protection.

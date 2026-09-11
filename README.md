# CLTI — Cross-Layer Transaction Intelligence

**Team MITHYA · SIH 26146 · NTRO · Blockchain & Cybersecurity**

> From fragmented logs to evidence-carrying investigative leads.

CLTI is an offline Linux prototype that correlates supplied Bitcoin P2P observations with on-chain UTXO movement, builds a typed evidence graph, applies guarded entity clustering and temporal flow analytics, fits an explainable anomaly model, and returns ranked investigative leads with uncertainty, counterfactual replay and reproducible Evidence Passports.

## Honest scope

CLTI is **not** a deanonymisation engine. An observed peer IP can be a relay, VPN, Tor endpoint, NAT gateway or shared host. A cluster is a heuristic entity, not a verified person. An anomaly percentile is not criminal probability.

## Implemented capabilities

- Offline Linux execution and offline-install scripts
- CSV, JSON and XML ingestion
- Separate network, blockchain, risk-seed and model-baseline inputs
- Deterministic TXID correlation and multi-observer corroboration
- Typed Observer–IP–Transaction–UTXO–Address–Entity graph
- Guarded common-input clustering with collaborative-spend protection
- Multi-transaction peeling-chain and rapid-hop detection
- Fitted Isolation Forest with deterministic robust fallback
- Baseline-relative anomaly percentiles and local feature-deviation explanations
- Seed-risk propagation over verified fund-flow edges
- Confidence vector, counterfactual replay and SHA-256 Evidence Passport
- Streamlit/PyVis dashboard and downloadable case export
- Deterministic multi-hop synthetic data with hard negatives and separate truth
- Automated regression tests and synthetic Precision@K evaluation

## Architecture

```text
Network observations + Blockchain UTXOs + Risk seeds
→ schema validation + SHA-256 provenance
→ deterministic TXID correlation
→ Observer → Peer IP → TX → UTXO → Address → Entity graph
→ guarded clustering + temporal typologies + seed distance
→ baseline-fitted anomaly model + local feature deviations
→ confidence vector + priority + counterfactual replay
→ ranked leads + graph + Evidence Passport + dashboard
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_demo.py
python run_clti.py --network demo/network_observations.csv --blockchain demo/case_blockchain.csv --seeds demo/risk_seeds.csv --baseline demo/baseline_blockchain.csv --output output
python evaluate.py
streamlit run app.py
```

CSV, JSON and XML equivalents are generated for each supported input.

## Offline installation

On an internet-connected staging machine run `bash scripts/build_offline_bundle.sh`. Copy the repository with `vendor/wheels` to the air-gapped Linux host, then run `bash scripts/install_offline.sh` and `bash scripts/smoke_test.sh`.

## Inputs

- Network: `observation_id, observer_id, observed_at, src_ip, src_port, dst_ip, dst_port, txid, asn, geo_country, source_record_id`
- Blockchain: `txid, block_time, input_outpoints, input_addresses, input_amounts, output_addresses, output_amounts, fee, script_type, source_record_id`
- Seeds: `address, risk_category, confidence, source`
- Baseline: separate ordinary blockchain transactions used to fit the model

Ground-truth labels are never model inputs.

## Outputs

`ranked_leads.csv`, `leads.json`, `evidence_graph.json`, `evidence_passports.json`, `summary.json` and synthetic `evaluation.json`.

Every lead includes anomaly percentile, typology strength, seed proximity, network/cluster confidence, data completeness, reason codes, model-local deviations, evidence path, counterfactual scores and limitations.

## Verification

```bash
python -m unittest discover -s tests -v
bash scripts/smoke_test.sh
```

The bundled synthetic top-5 regression retrieves the five injected seed-linked transactions. That is a software regression result, **not evidence of real-world criminal-classification performance**.

## Known limitations

- Exact official-dataset field mapping remains pending until that file is supplied.
- IP evidence is probabilistic regardless of model quality.
- Entity clustering is heuristic and requires analyst review.
- Production use requires authorised seed governance, agency GeoIP/ASN data, access control, retention policy and independent validation.

See `docs/TECHNICAL_WRITEUP.md` and `docs/REQUIREMENTS_TRACEABILITY.md`.

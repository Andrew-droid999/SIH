# CLTI Technical Write-up

CLTI is an evidence-fusion and prioritisation engine, not an identity oracle. It distinguishes blockchain-verified, network-observed, heuristic-derived and model-derived evidence.

## Correlation
An exact TXID match bridges network observations and blockchain records. Every sighting is preserved. Confidence rises with independent observers but is capped because multiple sightings still do not prove transaction creation.

## Graph and clustering
The graph contains Observer, Peer IP, Transaction, UTXO, Address and Entity nodes. Common-input ownership links co-spent addresses at confidence 0.85. Single-address entities use 0.45. If a transaction has at least five inputs, five outputs and a dominant equal-output group, merging is disabled and a collaborative-spend warning is emitted. The warning is not guilt evidence.

## Temporal analytics
Peeling detection follows a high-retention output only when that exact outpoint is later spent. At least three linked transactions are required. Seed propagation traverses verified fund-flow edges and decays by 0.65 per hop.

## Model and explanation
A 200-tree Isolation Forest is fitted on a separate ordinary baseline. A fitted median/MAD fallback preserves core operation if scikit-learn is unavailable. Case scores are percentiles against the baseline, not batch min-max values. Local explanations report the three largest robust feature deviations separately from deterministic reason codes.

## Priority
`0.35 anomaly + 0.25 typology + 0.20 seed proximity + 0.10 network confidence + 0.10 completeness`. This is an investigation queue policy, not criminal probability.

## Innovations
1. Typed Evidence Graph
2. Multi-dimensional Confidence Vector
3. Counterfactual Evidence Replay
4. SHA-256 Evidence Passport

## Evaluation
Synthetic Precision@K is a regression test only. Field deployment needs scenario-held-out data, CoinJoin/PayJoin false-merge analysis, calibrated thresholds, performance benchmarks and analyst task-time studies.

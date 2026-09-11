#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 generate_demo.py
rm -rf output
python3 run_clti.py --network demo/network_observations.xml --blockchain demo/case_blockchain.json --seeds demo/risk_seeds.csv --baseline demo/baseline_blockchain.csv --output output
python3 evaluate.py --k 5
python3 -m unittest discover -s tests -v
test -s output/evidence_passports.json

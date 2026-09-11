.PHONY: demo test run evaluate smoke dashboard
demo:
	python3 generate_demo.py
test: demo
	python3 -m unittest discover -s tests -v
run: demo
	python3 run_clti.py --network demo/network_observations.csv --blockchain demo/case_blockchain.csv --seeds demo/risk_seeds.csv --baseline demo/baseline_blockchain.csv --output output
evaluate: run
	python3 evaluate.py
dashboard: demo
	streamlit run app.py
smoke:
	bash scripts/smoke_test.sh

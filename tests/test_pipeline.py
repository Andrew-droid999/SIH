import csv,tempfile,unittest
from pathlib import Path
import generate_demo
from clti.graph import cluster_addresses,coinjoin_like
from clti.ingestion import load_records
from clti.pipeline import CLTIPipeline
ROOT=Path(__file__).resolve().parents[1];DEMO=ROOT/"demo"
class CLTITests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):generate_demo.main()
 def test_csv_json_xml_equivalence(self):
  for stem,kind in (("network_observations","network"),("case_blockchain","blockchain"),("risk_seeds","seeds")):
   counts=[len(load_records(DEMO/f"{stem}.{ext}",kind).records) for ext in ("csv","json","xml")];self.assertEqual(len(set(counts)),1);self.assertGreater(counts[0],0)
 def test_pipeline_produces_ranked_evidence(self):
  with tempfile.TemporaryDirectory() as target:
   r=CLTIPipeline().run(DEMO/"network_observations.csv",DEMO/"case_blockchain.csv",DEMO/"risk_seeds.csv",DEMO/"baseline_blockchain.csv",target);self.assertEqual(len(r.leads),r.summary["transactions"]);self.assertTrue(all(r.leads[i]["investigation_priority"]>=r.leads[i+1]["investigation_priority"] for i in range(len(r.leads)-1)));self.assertTrue((Path(target)/"evidence_passports.json").is_file());self.assertIn("network_observed",{e["evidence_type"] for e in r.graph.edges})
 def test_coinjoin_guard(self):
  rows=load_records(DEMO/"case_blockchain.csv","blockchain").records;tx=next(r for r in rows if r["txid"]==generate_demo.ident("coinjoin-control"));self.assertTrue(coinjoin_like(tx));mapping,_,guarded=cluster_addresses(rows);self.assertIn(tx["txid"],guarded);self.assertEqual(len({mapping[a] for a in tx["input_addresses"]}),len(tx["input_addresses"]))
 def test_labels_are_separate(self):
  with (DEMO/"case_blockchain.csv").open(encoding="utf-8") as h:headers=next(csv.reader(h))
  self.assertNotIn("is_suspicious",headers);self.assertNotIn("scenario",headers)
 def test_top_five_golden_scenario(self):
  r=CLTIPipeline().run(DEMO/"network_observations.xml",DEMO/"case_blockchain.json",DEMO/"risk_seeds.xml",DEMO/"baseline_blockchain.csv")
  with (DEMO/"ground_truth.csv").open(encoding="utf-8",newline="") as h:positive={x["txid"] for x in csv.DictReader(h) if x["is_suspicious"]=="1"}
  self.assertEqual({x["txid"] for x in r.leads[:5]},positive)
if __name__=="__main__":unittest.main()

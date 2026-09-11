#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--leads",default="output/leads.json");p.add_argument("--truth",default="demo/ground_truth.csv");p.add_argument("--k",type=int,default=5);p.add_argument("--output",default="output/evaluation.json");a=p.parse_args();leads=json.loads(Path(a.leads).read_text(encoding="utf-8"))
 with open(a.truth,encoding="utf-8",newline="") as h:truth={r["txid"]:int(r["is_suspicious"]) for r in csv.DictReader(h)}
 top=leads[:a.k];predicted={r["txid"] for r in top};positives={t for t,label in truth.items() if label};negatives=set(truth)-positives;tp=len(predicted&positives);fp=len(predicted&negatives);fn=len(positives-predicted);tn=len(negatives-predicted);metrics={"k":a.k,"true_positives":tp,"false_positives":fp,"false_negatives":fn,"true_negatives":tn,"precision_at_k":round(tp/len(top),4) if top else 0,"scenario_recall":round(tp/len(positives),4) if positives else 0,"false_positive_rate":round(fp/len(negatives),4) if negatives else 0,"note":"Synthetic demonstration metrics; not evidence of real-world criminal classification performance."};Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(metrics,indent=2),encoding="utf-8");print(json.dumps(metrics,indent=2))
if __name__=="__main__":main()

#!/usr/bin/env python3
import argparse
from clti import CLTIPipeline
def main():
 p=argparse.ArgumentParser(description="CLTI offline cross-layer Bitcoin investigation");p.add_argument("--network",required=True);p.add_argument("--blockchain",required=True);p.add_argument("--seeds",required=True);p.add_argument("--baseline",required=True);p.add_argument("--output",default="output");a=p.parse_args();r=CLTIPipeline().run(a.network,a.blockchain,a.seeds,a.baseline,a.output);print(f"Analysed {r.summary['transactions']} transactions; correlated {r.summary['correlated_transactions']}; outputs in {a.output}")
 for lead in r.leads[:5]:print(f"#{lead['rank']} {lead['txid'][:12]} priority={lead['investigation_priority']} reasons={','.join(lead['reason_codes'])}")
if __name__=="__main__":main()

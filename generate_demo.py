#!/usr/bin/env python3
"""Generate deterministic, internally consistent synthetic CLTI data."""
import csv,hashlib,json,xml.etree.ElementTree as ET
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent/"demo";BASE=datetime(2026,9,1,10,0,tzinfo=timezone.utc)
def ident(label):return hashlib.sha256(label.encode()).hexdigest()
def address(label):return "syn_"+ident(label)[:30]
def transaction(label,minute,input_outpoints,input_addresses,input_amounts,output_addresses,output_amounts,fee=.0002,script="P2WPKH"):
 return {"txid":ident(label),"block_time":(BASE+timedelta(minutes=minute)).isoformat(),"input_outpoints":"|".join(input_outpoints),"input_addresses":"|".join(input_addresses),"input_amounts":"|".join(f"{x:.8f}" for x in input_amounts),"output_addresses":"|".join(output_addresses),"output_amounts":"|".join(f"{x:.8f}" for x in output_amounts),"fee":f"{fee:.8f}","script_type":script,"source_record_id":f"chain-{label}"}
def normal_transactions(prefix,count,start=0):
 rows=[]
 for i in range(count):
  value=1.5+(i%7)*.13;fee=.0002;payment=round(value*.35,8);change=round(value-payment-fee,8)
  rows.append(transaction(f"{prefix}-normal-{i}",start+i*7,[f"external-{prefix}-{i}:0"],[address(f"{prefix}-payer-{i}")],[value],[address(f"{prefix}-merchant-{i%5}"),address(f"{prefix}-change-{i}")],[payment,change],fee))
 return rows
def build_case():
 rows=normal_transactions("case",24);truth=[{"txid":r["txid"],"is_suspicious":"0","scenario":"normal_payment"} for r in rows];seed=address("darknet-seed");chain=[];values=[20,19.5998,19.2496,18.9494];peels=[.4,.35,.3,2];outpoint="external-seed-funding:0";owner=seed
 for i,(value,peel) in enumerate(zip(values,peels)):
  continuation=round(value-peel-.0002,8);row=transaction(f"peel-{i}",200+i*12,[outpoint],[owner],[value],[address(f"peel-recipient-{i}"),address(f"peel-change-{i}")],[peel,continuation]);chain.append(row);outpoint=f"{row['txid']}:1";owner=address(f"peel-change-{i}")
 rows.extend(chain);truth.extend({"txid":r["txid"],"is_suspicious":"1","scenario":"seed_linked_peeling_chain"} for r in chain)
 total=round(values[-1]-peels[-1]-.0002,8);amounts=[round(total/8,8)]*7;amounts.append(round(total-sum(amounts)-.0002,8));fan=transaction("seed-fanout",255,[outpoint],[owner],[total],[address(f"fan-recipient-{i}") for i in range(8)],amounts);rows.append(fan);truth.append({"txid":fan["txid"],"is_suspicious":"1","scenario":"seed_linked_fanout"})
 cj=transaction("coinjoin-control",300,[f"external-cj-{i}:0" for i in range(6)],[address(f"coinjoin-user-{i}") for i in range(6)],[.101]*6,[address(f"coinjoin-output-{i}") for i in range(6)]+[address("coinjoin-fee-change")],[.1]*6+[.0058]);rows.append(cj);truth.append({"txid":cj["txid"],"is_suspicious":"0","scenario":"coinjoin_hard_negative"})
 exchange=transaction("exchange-deposit",320,["external-exchange-user:0"],[address("exchange-user")],[100.0002],[address("known-exchange-service")],[100]);rows.append(exchange);truth.append({"txid":exchange["txid"],"is_suspicious":"0","scenario":"exchange_deposit_hard_negative"})
 consolidation=transaction("merchant-consolidation",340,[f"external-merchant-{i}:0" for i in range(8)],[address(f"merchant-deposit-{i}") for i in range(8)],[1]*8,[address("merchant-treasury")],[7.9998]);rows.append(consolidation);truth.append({"txid":consolidation["txid"],"is_suspicious":"0","scenario":"merchant_consolidation_hard_negative"})
 return rows,truth,seed,{r["txid"] for r in chain+[fan]}
def observations(txs,suspicious):
 rows=[];counter=1
 for i,tx in enumerate(txs):
  count=3 if tx["txid"] in suspicious else 1;peer=f"203.0.113.{20+i%30}" if count==3 else f"198.51.100.{20+i%80}";block=datetime.fromisoformat(tx["block_time"])
  for j in range(count):
   rows.append({"observation_id":f"obs-{counter:04d}","observer_id":f"sensor-{j+1:02d}","observed_at":(block-timedelta(seconds=70-j*8)).isoformat(),"src_ip":peer,"src_port":str(50000+(i*13+j)%14000),"dst_ip":f"192.0.2.{10+j}","dst_port":"8333","txid":tx["txid"],"asn":"AS64500" if count==3 else f"AS{64510+i%5}","geo_country":"ZZ","source_record_id":f"pcap-row-{counter:04d}"});counter+=1
 return rows
def write_csv(path,rows):
 with path.open("w",encoding="utf-8",newline="") as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def write_xml(path,rows):
 root=ET.Element("records")
 for row in rows:
  record=ET.SubElement(root,"record")
  for key,value in row.items():ET.SubElement(record,key).text=str(value)
 ET.ElementTree(root).write(path,encoding="utf-8",xml_declaration=True)
def main():
 ROOT.mkdir(parents=True,exist_ok=True);baseline=normal_transactions("baseline",80);case,truth,seed,suspicious=build_case();network=observations(case,suspicious);seeds=[{"address":seed,"risk_category":"synthetic_darknet_seed","confidence":"1.0","source":"demo_ground_truth"}]
 write_csv(ROOT/"baseline_blockchain.csv",baseline);write_csv(ROOT/"case_blockchain.csv",case);write_csv(ROOT/"network_observations.csv",network);write_csv(ROOT/"risk_seeds.csv",seeds);write_csv(ROOT/"ground_truth.csv",truth)
 for name,records in (("network_observations",network),("case_blockchain",case),("risk_seeds",seeds)):(ROOT/f"{name}.json").write_text(json.dumps({"records":records},indent=2),encoding="utf-8");write_xml(ROOT/f"{name}.xml",records)
 print(f"Generated {len(case)} case transactions, {len(network)} observations and {len(baseline)} baseline transactions")
if __name__=="__main__":main()

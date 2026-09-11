"""End-to-end CLTI evidence-fusion and lead-ranking pipeline."""
from __future__ import annotations
import csv,json,math
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from .graph import EvidenceGraph,build_evidence_graph,cluster_addresses,correlate_observations,detect_peeling_chains,seed_distances
from .ingestion import LoadedRecords,load_records
from .model import ExplainableAnomalyModel
MODEL_VERSION="clti-anomaly-v1.0.0";ALGORITHM_VERSION="clti-evidence-graph-v1.0.0"
@dataclass
class PipelineResult:
    leads:list[dict[str,Any]];graph:EvidenceGraph;passports:list[dict[str,Any]];summary:dict[str,Any]
    def write(self,output_dir):
        target=Path(output_dir);target.mkdir(parents=True,exist_ok=True)
        (target/"leads.json").write_text(json.dumps(self.leads,indent=2),encoding="utf-8")
        (target/"evidence_graph.json").write_text(json.dumps({"nodes":list(self.graph.nodes.values()),"edges":self.graph.edges},indent=2),encoding="utf-8")
        (target/"evidence_passports.json").write_text(json.dumps(self.passports,indent=2),encoding="utf-8")
        (target/"summary.json").write_text(json.dumps(self.summary,indent=2),encoding="utf-8")
        if self.leads:
            fields=["rank","txid","entity_id","investigation_priority","anomaly_percentile","typology_strength","seed_proximity","network_confidence","cluster_confidence","data_completeness","reason_codes","limitations"]
            with (target/"ranked_leads.csv").open("w",encoding="utf-8",newline="") as h:
                w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
                for lead in self.leads:
                    row={k:lead.get(k) for k in fields};row["reason_codes"]="|".join(lead["reason_codes"]);row["limitations"]="|".join(lead["limitations"]);w.writerow(row)
class CLTIPipeline:
    def run(self,network_path,blockchain_path,seed_path,baseline_blockchain_path,output_dir=None):
        network=load_records(network_path,"network");blockchain=load_records(blockchain_path,"blockchain");seeds=load_records(seed_path,"seeds");baseline=load_records(baseline_blockchain_path,"blockchain")
        txs,obs,seed_rows=blockchain.records,network.records,seeds.records
        entity_map,entity_confidence,guarded=cluster_addresses(txs);correlation=correlate_observations(obs,txs);peeling=detect_peeling_chains(txs);proximity=seed_distances(txs,seed_rows);graph=build_evidence_graph(txs,obs,seed_rows,entity_map,entity_confidence)
        features=self._feature_rows(txs,correlation,entity_map,guarded)
        base_map,_,base_guarded=cluster_addresses(baseline.records);base_features=self._feature_rows(baseline.records,correlate_observations([],baseline.records),base_map,base_guarded)
        model=ExplainableAnomalyModel().fit(base_features);model_output=model.score(features);manifest=self._manifest(network,blockchain,seeds,baseline);by_id={t["txid"]:t for t in txs};leads=[];passports=[]
        for i,feature in enumerate(features):
            txid=feature["txid"];tx=by_id[txid];corr=correlation[txid];seed=proximity.get(txid,{"score":0,"hops":None,"path":[],"category":None});anomaly=float(model_output.percentiles[i]);typology,reasons=self._typology(feature,txid,guarded,peeling);seed_score=100*float(seed["score"]);network_score=100*corr["network_confidence"];cluster_score=100*feature["cluster_confidence"];completeness=100*feature["data_completeness"];priority=.35*anomaly+.25*typology+.20*seed_score+.10*network_score+.10*completeness
            if txid in guarded and seed_score==0 and txid not in peeling:priority=max(0,priority-12)
            limitations=["Observed peer IP may be a relay, VPN, Tor, NAT, shared host or cloud endpoint.","Entity grouping is heuristic and is not verified identity.","Investigation priority is not a probability of criminal activity."]
            if txid in guarded:limitations.append("Collaborative-spend pattern detected; common-input clustering was disabled.");reasons.append("COLLABORATIVE_SPEND_WARNING")
            entity=entity_map.get(tx["input_addresses"][0],"entity:unknown") if tx["input_addresses"] else "entity:coinbase"
            lead={"rank":0,"txid":txid,"entity_id":entity,"investigation_priority":round(priority,1),"anomaly_percentile":round(anomaly,1),"typology_strength":round(typology,1),"seed_proximity":round(seed_score,1),"network_confidence":round(network_score,1),"cluster_confidence":round(cluster_score,1),"data_completeness":round(completeness,1),"reason_codes":sorted(set(reasons)),"model_explanation":[{"feature":name,"relative_local_deviation":value} for name,value in model_output.contributions[i]],"evidence_path":seed["path"] or peeling.get(txid,{}).get("path",[]),"observation_ids":corr["observation_ids"],"peer_ips":corr["peer_ips"],"counterfactual":{"without_network_evidence":round(priority-.10*network_score,1),"without_seed_evidence":round(priority-.20*seed_score,1)},"limitations":limitations}
            leads.append(lead);passports.append(self._passport(lead,tx,manifest,model_output.model_name))
        leads.sort(key=lambda x:(-x["investigation_priority"],x["txid"]))
        for rank,lead in enumerate(leads,1):lead["rank"]=rank
        pmap={p["txid"]:p for p in passports};passports=[pmap[l["txid"]] for l in leads]
        summary={"transactions":len(txs),"network_observations":len(obs),"correlated_transactions":sum(1 for v in correlation.values() if v["observation_count"]),"entity_clusters":len(set(entity_map.values())),"collaborative_spend_warnings":len(guarded),"peeling_chain_transactions":len(peeling),"seed_reachable_transactions":len(proximity),"model":model_output.model_name,"model_version":MODEL_VERSION,"generated_at":datetime.now(timezone.utc).isoformat(),"source_manifest":manifest}
        result=PipelineResult(leads,graph,passports,summary)
        if output_dir:result.write(output_dir)
        return result
    def _feature_rows(self,txs,correlation,entity_map,guarded):
        counts={};peers={}
        for tx in txs:
            entity=entity_map.get(tx["input_addresses"][0],"entity:unknown") if tx["input_addresses"] else "entity:coinbase";counts[entity]=counts.get(entity,0)+1;peers.setdefault(entity,set()).update(correlation[tx["txid"]]["peer_ips"])
        rows=[]
        for tx in txs:
            total_in=sum(tx["input_amounts"]);total_out=sum(tx["output_amounts"]);fan_in=len(tx["input_addresses"]);fan_out=len(tx["output_addresses"]);shares=[x/total_out for x in tx["output_amounts"]] if total_out else [];entity=entity_map.get(tx["input_addresses"][0],"entity:unknown") if tx["input_addresses"] else "entity:coinbase";corr=correlation[tx["txid"]];disparity=max(shares)-min(shares) if len(shares)==2 else 0;fields=[tx["txid"],tx["block_time"],tx["input_addresses"],tx["output_addresses"],tx["fee"]];complete=sum(v not in (None,"",[]) for v in fields)/len(fields)
            rows.append({"txid":tx["txid"],"log_total_input":math.log1p(total_in),"log_fee_rate":math.log1p(1_000_000*tx["fee"]/total_in) if total_in else 0,"fan_in":fan_in,"fan_out":fan_out,"output_concentration":sum(s*s for s in shares),"peel_disparity":disparity,"entity_tx_count":counts[entity],"entity_peer_diversity":len(peers[entity]),"observation_count":corr["observation_count"],"observer_count":corr["observer_count"],"peer_count":corr["peer_count"],"network_confidence":corr["network_confidence"],"coinjoin_warning":1 if tx["txid"] in guarded else 0,"cluster_confidence":.85 if fan_in>1 and tx["txid"] not in guarded else .45,"data_completeness":complete})
        return rows
    def _typology(self,feature,txid,guarded,peeling):
        score=0;reasons=[]
        if txid in peeling:score=max(score,90);reasons.extend(["RAPID_MULTI_HOP" if peeling[txid]["rapid"] else "PEELING_CHAIN","HIGH_VALUE_RETENTION"])
        if feature["fan_out"]>=6 and txid not in guarded:score=max(score,55);reasons.append("UNUSUAL_FAN_OUT")
        if feature["fan_in"]>=6 and txid not in guarded:score=max(score,45);reasons.append("MASS_CONSOLIDATION")
        if feature["log_fee_rate"]>math.log1p(5000):score=max(score,35);reasons.append("FEE_RATE_OUTLIER")
        if feature["observer_count"]>=2:reasons.append("MULTI_OBSERVER_CORROBORATION")
        return score,reasons
    def _manifest(self,*sources):return [{"file":Path(s.source_path).name,"sha256":s.sha256,"format":s.format,"records":len(s.records)} for s in sources]
    def _passport(self,lead,tx,manifest,model_name):return {"passport_version":"1.0","txid":lead["txid"],"source_manifest":manifest,"source_record_id":tx["source_record_id"],"source_row":tx["_row_number"],"evidence_types":["blockchain_verified","network_observed","heuristic_derived","model_derived"],"reason_codes":lead["reason_codes"],"model":model_name,"model_version":MODEL_VERSION,"algorithm_version":ALGORITHM_VERSION,"generated_at":datetime.now(timezone.utc).isoformat(),"analyst_disposition":"UNREVIEWED","limitations":lead["limitations"]}

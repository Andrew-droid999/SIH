"""Typed evidence graph, guarded clustering and temporal fund-flow analytics."""
from __future__ import annotations
from collections import defaultdict,deque
from dataclasses import dataclass,field
from datetime import datetime
from typing import Any
@dataclass
class EvidenceGraph:
    nodes:dict[str,dict[str,Any]]=field(default_factory=dict);edges:list[dict[str,Any]]=field(default_factory=list)
    def add_node(self,node_id,node_type,**attrs):self.nodes.setdefault(node_id,{"id":node_id,"type":node_type}).update(attrs)
    def add_edge(self,source,target,edge_type,evidence_type,confidence=1.0,**attrs):self.edges.append({"source":source,"target":target,"type":edge_type,"evidence_type":evidence_type,"confidence":round(float(confidence),3),**attrs})
class UnionFind:
    def __init__(self):self.parent={}
    def add(self,x):self.parent.setdefault(x,x)
    def find(self,x):
        self.add(x)
        while self.parent[x]!=x:self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
        return x
    def union(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b:self.parent[b]=a
def coinjoin_like(tx,tolerance=.01):
    if len(tx["input_addresses"])<5 or len(tx["output_amounts"])<5:return False
    groups=[]
    for amount in sorted(tx["output_amounts"]):
        for group in groups:
            base=max(abs(group[0]),abs(amount),1e-12)
            if abs(group[0]-amount)/base<=tolerance:group.append(amount);break
        else:groups.append([amount])
    largest=max((len(g) for g in groups),default=0)
    return largest>=3 and largest/len(tx["output_amounts"])>=.5
def cluster_addresses(transactions):
    uf=UnionFind();guarded=set()
    for tx in transactions:
        for a in tx["input_addresses"]+tx["output_addresses"]:uf.add(a)
        if coinjoin_like(tx):guarded.add(tx["txid"]);continue
        for a in tx["input_addresses"][1:]:uf.union(tx["input_addresses"][0],a)
    roots=sorted({uf.find(a) for a in uf.parent});ids={r:f"entity:{i:04d}" for i,r in enumerate(roots,1)};mapping={a:ids[uf.find(a)] for a in uf.parent};sizes=defaultdict(int)
    for entity in mapping.values():sizes[entity]+=1
    confidence={entity:(.85 if size>1 else .45) for entity,size in sizes.items()}
    return mapping,confidence,guarded
def build_evidence_graph(transactions,observations,seeds,entity_map,entity_confidence):
    g=EvidenceGraph()
    for tx in transactions:
        txn=f"tx:{tx['txid']}";g.add_node(txn,"transaction",txid=tx["txid"],block_time=tx["block_time"])
        for i,(address,amount) in enumerate(zip(tx["output_addresses"],tx["output_amounts"])):
            an,utxo,entity=f"address:{address}",f"utxo:{tx['txid']}:{i}",entity_map[address];g.add_node(an,"address",address=address);g.add_node(utxo,"utxo",amount=amount,outpoint=f"{tx['txid']}:{i}");g.add_node(entity,"entity",cluster_confidence=entity_confidence[entity]);g.add_edge(txn,utxo,"CREATED","blockchain_verified");g.add_edge(utxo,an,"LOCKED_TO","blockchain_verified");g.add_edge(an,entity,"PROBABLY_CONTROLLED_BY","heuristic_derived",entity_confidence[entity],method="guarded_common_input")
        for outpoint,address,amount in zip(tx["input_outpoints"],tx["input_addresses"],tx["input_amounts"]):
            an,utxo,entity=f"address:{address}",f"utxo:{outpoint}",entity_map[address];g.add_node(an,"address",address=address);g.add_node(utxo,"utxo",amount=amount,outpoint=outpoint);g.add_node(entity,"entity",cluster_confidence=entity_confidence[entity]);g.add_edge(utxo,txn,"SPENT_BY","blockchain_verified");g.add_edge(an,entity,"PROBABLY_CONTROLLED_BY","heuristic_derived",entity_confidence[entity],method="guarded_common_input")
    for obs in observations:
        observer,peer,txn=f"observer:{obs['observer_id']}",f"peer_ip:{obs['src_ip']}",f"tx:{obs['txid']}";g.add_node(observer,"observer",observer_id=obs["observer_id"]);g.add_node(peer,"peer_ip",ip=obs["src_ip"],asn=obs["asn"],geo_country=obs["geo_country"]);g.add_edge(observer,peer,"RECEIVED_FROM","network_observed",1,observation_id=obs["observation_id"],observed_at=obs["observed_at"])
        if txn in g.nodes:g.add_edge(peer,txn,"OBSERVED_ANNOUNCING","network_observed",.35,observation_id=obs["observation_id"],observed_at=obs["observed_at"])
    for seed in seeds:
        an=f"address:{seed['address']}";g.add_node(an,"address",address=seed["address"]);g.nodes[an].update(seed_category=seed["risk_category"],seed_source=seed["source"],seed_confidence=seed["confidence"])
    return g
def correlate_observations(observations,transactions):
    txids={t["txid"] for t in transactions};grouped=defaultdict(list)
    for obs in observations:
        if obs["txid"] in txids:grouped[obs["txid"]].append(obs)
    result={}
    for txid in txids:
        rows=sorted(grouped.get(txid,[]),key=lambda x:x["observed_at"]);observers={r["observer_id"] for r in rows};peers={r["src_ip"] for r in rows};confidence=min(.75,.25+.15*max(0,len(observers)-1)) if rows else 0
        result[txid]={"observation_count":len(rows),"observer_count":len(observers),"peer_count":len(peers),"first_seen":rows[0]["observed_at"] if rows else None,"network_confidence":confidence,"observation_ids":[r["observation_id"] for r in rows],"peer_ips":sorted(peers)}
    return result
def detect_peeling_chains(transactions,min_length=3):
    by={t["txid"]:t for t in transactions};spends={o:t["txid"] for t in transactions for o in t["input_outpoints"]};nxt={};share={}
    for tx in transactions:
        outs=tx["output_amounts"]
        if len(outs)!=2 or sum(outs)<=0:continue
        i=max(range(2),key=lambda j:outs[j]);s=outs[i]/sum(outs);candidate=spends.get(f"{tx['txid']}:{i}")
        if s>=.85 and candidate:nxt[tx["txid"]]=candidate;share[tx["txid"]]=s
    results={};visited=set()
    for start in sorted(nxt):
        if start in visited:continue
        path=[start]
        while path[-1] in nxt and nxt[path[-1]] not in path:path.append(nxt[path[-1]])
        if len(path)>=min_length:
            rapid=_rapid(path,by)
            for txid in path:results[txid]={"path":path,"length":len(path),"rapid":rapid,"retained_share":share.get(txid,0)}
            visited.update(path)
    return results
def _rapid(path,by,hours=2):
    try:
        times=[datetime.fromisoformat(str(by[x]["block_time"]).replace("Z","+00:00")) for x in path];return (max(times)-min(times)).total_seconds()<=hours*3600
    except (ValueError,TypeError):return False
def seed_distances(transactions,seeds,max_hops=4):
    address_to_txs=defaultdict(set);outputs=defaultdict(set)
    for tx in transactions:
        for a in tx["input_addresses"]:address_to_txs[a].add(tx["txid"])
        outputs[tx["txid"]].update(tx["output_addresses"])
    q=deque((s["address"],0,s["confidence"],[s["address"]],s["risk_category"]) for s in seeds);best={};seen={}
    while q:
        address,hops,confidence,path,category=q.popleft()
        if hops>max_hops or hops>=seen.get(address,10**9):continue
        seen[address]=hops
        for txid in address_to_txs.get(address,set()):
            score=confidence*(.65**hops);current=best.get(txid)
            if current is None or score>current["score"]:best[txid]={"hops":hops,"score":score,"path":path+[txid],"category":category}
            if hops<max_hops:
                for out in outputs[txid]:q.append((out,hops+1,confidence,path+[txid,out],category))
    return best

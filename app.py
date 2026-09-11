"""CLTI offline investigation dashboard. Run: streamlit run app.py"""
import json,tempfile,zipfile
from pathlib import Path
import pandas as pd
import streamlit as st
from pyvis.network import Network
from clti import CLTIPipeline
ROOT=Path(__file__).resolve().parent;DEMO=ROOT/"demo"
if not (DEMO/"case_blockchain.csv").is_file():
 import generate_demo;generate_demo.main()
COLORS={"observer":"#22c55e","peer_ip":"#ef4444","transaction":"#f59e0b","utxo":"#94a3b8","address":"#60a5fa","entity":"#a78bfa"}
st.set_page_config(page_title="CLTI — Cross-Layer Transaction Intelligence",page_icon="🔎",layout="wide")
st.markdown("<style>.stApp{background:#090d14;color:#e5e7eb}[data-testid='stMetric']{background:#111827;border:1px solid #253047;padding:14px;border-radius:12px}</style>",unsafe_allow_html=True)
def save_upload(upload,directory):
 target=directory/upload.name;target.write_bytes(upload.getvalue());return target
def focused_graph(result,txid):
 center=f"tx:{txid}";selected={center}
 for _ in range(2):
  for edge in result.graph.edges:
   if edge["source"] in selected or edge["target"] in selected:selected.update((edge["source"],edge["target"]))
 net=Network(height="560px",width="100%",bgcolor="#090d14",font_color="#e5e7eb",directed=True,cdn_resources="in_line")
 for node_id in selected:
  node=result.graph.nodes.get(node_id,{"type":"unknown"});kind=node.get("type","unknown");label=node_id.split(":",1)[-1];label=label[:9]+"…"+label[-6:] if len(label)>18 else label;net.add_node(node_id,label=label,title=json.dumps(node,indent=2),color=COLORS.get(kind,"#64748b"),shape="diamond" if kind=="transaction" else "dot")
 for edge in result.graph.edges:
  if edge["source"] in selected and edge["target"] in selected:net.add_edge(edge["source"],edge["target"],label=edge["type"],title=f"{edge['evidence_type']} · confidence {edge['confidence']}")
 net.set_options('{"physics":{"solver":"forceAtlas2Based","stabilization":{"iterations":150}},"edges":{"font":{"size":9}}}')
 with tempfile.NamedTemporaryFile(suffix=".html",delete=False) as h:path=Path(h.name)
 net.save_graph(str(path));return path.read_text(encoding="utf-8")
st.title("🔎 CLTI — Cross-Layer Transaction Intelligence");st.caption("Offline Bitcoin evidence fusion · facts and inferences remain explicitly separated")
with st.sidebar:
 st.header("Case files");demo=st.toggle("Use bundled synthetic case",value=True);network=st.file_uploader("Network observations",type=["csv","json","xml"],disabled=demo);blockchain=st.file_uploader("Blockchain transactions",type=["csv","json","xml"],disabled=demo);seeds=st.file_uploader("Risk seeds",type=["csv","json","xml"],disabled=demo);baseline=st.file_uploader("Normal model baseline",type=["csv","json","xml"],disabled=demo);run=st.button("Run offline investigation",type="primary",use_container_width=True);st.caption("No cloud model, live blockchain or external font is required at runtime.")
if not run:st.info("Use the synthetic case or upload four evidence files, then run the investigation.");st.stop()
with tempfile.TemporaryDirectory() as name:
 temp=Path(name)
 if demo:npath,bpath,spath,base=DEMO/"network_observations.csv",DEMO/"case_blockchain.csv",DEMO/"risk_seeds.csv",DEMO/"baseline_blockchain.csv"
 else:
  if not all((network,blockchain,seeds,baseline)):st.error("All four files are required.");st.stop()
  npath,bpath,spath,base=[save_upload(x,temp) for x in (network,blockchain,seeds,baseline)]
 output=temp/"output"
 try:
  with st.spinner("Validating evidence, correlating layers and ranking leads…"):result=CLTIPipeline().run(npath,bpath,spath,base,output)
 except Exception as exc:st.error(f"Case validation failed: {exc}");st.stop()
 cols=st.columns(4);cols[0].metric("Transactions",result.summary["transactions"]);cols[1].metric("Observations",result.summary["network_observations"]);cols[2].metric("Correlated TXIDs",result.summary["correlated_transactions"]);cols[3].metric("Peeling-chain TXs",result.summary["peeling_chain_transactions"])
 st.subheader("Ranked investigative leads");table=pd.DataFrame(result.leads);st.dataframe(table[["rank","txid","entity_id","investigation_priority","anomaly_percentile","typology_strength","seed_proximity","network_confidence","reason_codes"]],use_container_width=True,hide_index=True)
 rank=st.selectbox("Inspect lead",[x["rank"] for x in result.leads],format_func=lambda x:f"#{x} · {result.leads[x-1]['txid'][:14]}…");lead=result.leads[rank-1];passport=result.passports[rank-1];left,right=st.columns([1.15,1])
 with left:
  st.subheader(f"Lead #{lead['rank']} · Priority {lead['investigation_priority']}/100");st.warning("Investigation priority is not a probability of criminal activity.");confidence=pd.DataFrame({"dimension":["Anomaly","Typology","Seed","Network","Cluster","Completeness"],"score":[lead["anomaly_percentile"],lead["typology_strength"],lead["seed_proximity"],lead["network_confidence"],lead["cluster_confidence"],lead["data_completeness"]]});st.bar_chart(confidence.set_index("dimension"));st.code("\n".join(lead["reason_codes"]) or "No deterministic typology rule fired");st.dataframe(pd.DataFrame(lead["model_explanation"]),hide_index=True,use_container_width=True)
 with right:
  st.subheader("Counterfactual evidence replay");st.write({"Current priority":lead["investigation_priority"],**lead["counterfactual"]});st.markdown("**Evidence path**");st.code(" → ".join(map(str,lead["evidence_path"])) or "No seed/peeling path");st.markdown("**Limitations**");[st.write("• "+x) for x in lead["limitations"]]
 st.subheader("Typed evidence graph");st.components.v1.html(focused_graph(result,lead["txid"]),height=580,scrolling=False)
 with st.expander("Evidence Passport"):st.json(passport)
 archive=temp/"clti_case_export.zip"
 with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as bundle:
  for file in output.iterdir():bundle.write(file,file.name)
 st.download_button("Download reproducible case export",archive.read_bytes(),"clti_case_export.zip","application/zip",use_container_width=True)

"""
app.py — AI Bitcoin Transaction Monitor (Streamlit Frontend)
=============================================================

Interactive offline dashboard for investigating flagged Bitcoin
transactions. Features a dark-mode bento-box layout, an interactive
pyvis network graph, and a detailed investigation panel.

Officers can upload raw CSV files directly — the AI engine runs
in-app and updates all panels automatically.

Run:
    streamlit run app.py

Dependencies:
    pip install streamlit pyvis pandas scikit-learn
"""

import tempfile
from pathlib import Path
from io import StringIO

import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
import streamlit.components.v1 as components
# pyrefly: ignore [missing-import]
from pyvis.network import Network

# Import the AI engine and cross-chain adapter layer
from ml_engine import run_pipeline_from_df
from transaction_adapter import BitcoinCSVAdapter

# ---------------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Bitcoin Transaction Monitor",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Dark mode + Bento-box grid
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
    /* ── Import premium font ───────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Global dark theme overrides ───────────────────────────── */
    .stApp {
        background: linear-gradient(145deg, #0a0a0f 0%, #0d1117 40%, #0f0b1a 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Hide default Streamlit header/footer */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Dashboard title ───────────────────────────────────────── */
    .dashboard-header {
        text-align: center;
        padding: 2rem 0 0.5rem 0;
    }
    .dashboard-header h1 {
        font-family: 'Inter', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .dashboard-header p {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 0.3rem;
        font-weight: 400;
    }

    /* ── Bento metric cards ────────────────────────────────────── */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.2rem;
        padding: 1.5rem 0;
    }
    .bento-card {
        background: linear-gradient(135deg, rgba(30, 32, 48, 0.9) 0%, rgba(20, 22, 35, 0.95) 100%);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 1rem;
        padding: 1.6rem 1.8rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .bento-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.1);
    }
    .bento-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 1rem 1rem 0 0;
    }
    .bento-card.card-scanned::before {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
    }
    .bento-card.card-flagged::before {
        background: linear-gradient(90deg, #ef4444, #f87171);
    }
    .bento-card.card-risk::before {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
    }
    .bento-card .card-icon {
        font-size: 1.6rem;
        margin-bottom: 0.5rem;
    }
    .bento-card .card-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9ca3af;
        margin-bottom: 0.4rem;
    }
    .bento-card .card-value {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .bento-card.card-scanned .card-value { color: #60a5fa; }
    .bento-card.card-flagged .card-value { color: #f87171; }
    .bento-card.card-risk .card-value    { color: #fbbf24; }
    .bento-card .card-sub {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.5rem;
    }

    /* ── Section titles ────────────────────────────────────────── */
    .section-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #e5e7eb;
        margin: 2rem 0 0.8rem 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .section-title .icon { font-size: 1.4rem; }
    .section-subtitle {
        color: #6b7280;
        font-size: 0.85rem;
        margin-top: -0.4rem;
        margin-bottom: 1rem;
    }

    /* ── Graph container ───────────────────────────────────────── */
    .graph-container {
        background: linear-gradient(135deg, rgba(30, 32, 48, 0.7) 0%, rgba(15, 17, 28, 0.9) 100%);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 1rem;
        padding: 0.5rem;
        overflow: hidden;
    }

    /* ── Investigation table styling ───────────────────────────── */
    .investigation-panel {
        background: linear-gradient(135deg, rgba(30, 32, 48, 0.7) 0%, rgba(15, 17, 28, 0.9) 100%);
        border: 1px solid rgba(239, 68, 68, 0.15);
        border-radius: 1rem;
        padding: 1.2rem;
    }

    /* Streamlit dataframe overrides */
    .stDataFrame {
        border-radius: 0.75rem;
        overflow: hidden;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-critical { background: rgba(239, 68, 68, 0.15); color: #f87171; }
    .badge-normal   { background: rgba(34, 197, 94, 0.15);  color: #4ade80; }

    /* ── Divider ───────────────────────────────────────────────── */
    .fancy-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent);
        margin: 1.5rem 0;
    }

    /* ── Live-pulse indicator ──────────────────────────────────── */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    .live-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #22c55e;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s ease-in-out infinite;
    }

    /* ── Upload success banner ─────────────────────────────────── */
    .upload-banner {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 0.75rem;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        color: #4ade80;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* ── Sidebar styling ───────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #131720 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.1);
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #9ca3af;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Required columns for validation
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "timestamp", "src_ip", "dst_ip", "src_port", "dst_port",
    "txid", "input_addresses", "output_addresses", "input_amounts", "output_amounts", "fee", "script_type", "geo_country",
]


# ---------------------------------------------------------------------------
# Sidebar — File uploader + data source controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0;">
            <span style="font-size: 2rem;">🔗</span>
            <h3 style="color: #e5e7eb; margin: 0.3rem 0 0 0; font-family: Inter, sans-serif;">
                Data Source
            </h3>
            <p style="color: #6b7280; font-size: 0.8rem; margin-top: 0.2rem;">
                Upload raw CSV or use pre-analysed data
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # File uploader
    uploaded_file = st.file_uploader(
        "📂 Upload Bitcoin Traffic CSV",
        type=["csv"],
        help="Upload a raw CSV with columns: timestamp, src_ip, dst_ip, "
             "src_port, dst_port, txid, input_addresses, output_addresses, "
             "input_amounts, output_amounts, fee, script_type, geo_country",
    )

    # Contamination slider — let officers tune sensitivity
    contamination = st.slider(
        "🎚️ Anomaly Sensitivity",
        min_value=0.01,
        max_value=0.20,
        value=0.05,
        step=0.01,
        help="Expected fraction of anomalous transactions. "
             "Higher = more flags, lower = stricter.",
        format="%.0f%%",
    )

    st.markdown("---")

    # Info box
    st.markdown(
        """
        <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2);
                    border-radius: 0.5rem; padding: 0.8rem; margin-top: 0.5rem;">
            <p style="color: #a5b4fc; font-size: 0.75rem; margin: 0; font-weight: 600;">
                ℹ️ HOW IT WORKS
            </p>
            <p style="color: #9ca3af; font-size: 0.72rem; margin: 0.3rem 0 0 0; line-height: 1.4;">
                Upload a raw CSV → the AI engine (IsolationForest) runs
                in real-time → dashboard updates with flagged anomalies,
                risk scores, explanations, and network graph.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Data loading — either from upload or from pre-existing flagged file
# ---------------------------------------------------------------------------

@st.cache_data
def load_preanalysed_data(filepath: str = "flagged_transactions.csv") -> pd.DataFrame:
    """Load a previously analysed dataset (fallback when no upload)."""
    return pd.read_csv(filepath)


# ── Cross-chain adapter (swap this line for a different chain) ──
_adapter = BitcoinCSVAdapter()


def run_ai_on_upload(raw_df: pd.DataFrame, contamination: float) -> pd.DataFrame:
    """
    Run the full AI pipeline on an uploaded DataFrame via the
    polymorphic adapter.  Swapping ``_adapter`` to an
    ``EthereumAdapter`` would make this function work on ETH
    data with zero changes.
    """
    enriched_df, _model = _adapter.run_pipeline_from_df(
        raw_df, contamination=contamination,
    )
    return enriched_df


# Determine data source and load
data_source = "pre-analysed"  # Track which source is active

if uploaded_file is not None:
    # ── Officer uploaded a new CSV ──
    try:
        raw_df = pd.read_csv(uploaded_file)

        # Validate required columns
        missing = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
        if missing:
            st.error(
                f"❌ **Missing columns:** {', '.join(missing)}\n\n"
                f"Required: {', '.join(REQUIRED_COLUMNS)}"
            )
            st.stop()

        # Run AI pipeline with a spinner
        with st.spinner("🧠 AI Engine running — detecting anomalies..."):
            df = run_ai_on_upload(raw_df, contamination)
            data_source = "uploaded"

        # Show success in sidebar
        with st.sidebar:
            st.markdown(
                f'<div class="upload-banner">'
                f"✅ Analysed <b>{len(raw_df)}</b> transactions · "
                f"<b>{(df['is_anomaly'].sum())}</b> flagged"
                f"</div>",
                unsafe_allow_html=True,
            )

    except Exception as e:
        import traceback
        st.error(f"❌ **Error processing file:** {e}\n\n```python\n{traceback.format_exc()}\n```")
        st.stop()
else:
    st.warning("📁 Please upload a Bitcoin transaction CSV file in the sidebar to begin analysis.")
    st.stop()


# ---------------------------------------------------------------------------
# Compute metrics from the active dataset
# ---------------------------------------------------------------------------

total_tx = len(df)
flagged_df = df[df["is_anomaly"] == True].copy()
total_flagged = len(flagged_df)
max_risk = df["risk_score"].max() if total_flagged > 0 else 0.0


# ---------------------------------------------------------------------------
# Dashboard header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="dashboard-header">
        <h1>🔗 AI Bitcoin Transaction Monitor</h1>
        <p><span class="live-dot"></span>Offline Analysis Engine &nbsp;·&nbsp; IsolationForest Anomaly Detection &nbsp;·&nbsp; Network Intelligence</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Show data source indicator
if data_source == "uploaded":
    source_label = f"📂 Live analysis of uploaded file ({total_tx} transactions)"
    source_color = "#4ade80"
else:
    source_label = f"💾 Pre-analysed dataset (flagged_transactions.csv)"
    source_color = "#60a5fa"

st.markdown(
    f'<p style="text-align:center; color:{source_color}; font-size:0.8rem; '
    f'font-weight:500; margin-top:-0.5rem;">{source_label}</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Bento metric cards
# ---------------------------------------------------------------------------

anomaly_pct = (total_flagged / total_tx * 100) if total_tx > 0 else 0.0

st.markdown(
    f"""
    <div class="bento-grid">
        <div class="bento-card card-scanned">
            <div class="card-icon">📡</div>
            <div class="card-label">Total Scanned Transactions</div>
            <div class="card-value">{total_tx:,}</div>
            <div class="card-sub">Bitcoin network traffic captured</div>
        </div>
        <div class="bento-card card-flagged">
            <div class="card-icon">🚨</div>
            <div class="card-label">Total Flagged Threats</div>
            <div class="card-value">{total_flagged}</div>
            <div class="card-sub">{anomaly_pct:.1f}% anomaly detection rate</div>
        </div>
        <div class="bento-card card-risk">
            <div class="card-icon">⚠️</div>
            <div class="card-label">Max Risk Score</div>
            <div class="card-value">{max_risk:.1f}%</div>
            <div class="card-sub">Highest threat confidence level</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Interactive network graph (pyvis)
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="section-title">
        <span class="icon">🕸️</span> Entity / Transaction Network Graph
    </div>
    <p class="section-subtitle">
        Anomalous entities and their immediate connections &nbsp;·&nbsp;
        <span style="color:#ef4444; font-weight:600;">● Red = flagged anomalies</span> &nbsp;·&nbsp;
        <span style="color:#f59e0b; font-weight:600;">◆ Amber = transactions</span> &nbsp;·&nbsp;
        <span style="color:#9b59b6; font-weight:600;">■ Purple = wallet entities</span> &nbsp;·&nbsp;
        <span style="color:#3b82f6; font-weight:600;">● Blue = context nodes</span>
    </p>
    """,
    unsafe_allow_html=True,
)

# ── Graph mode toggle ────────────────────────────────────────────────
toggle_col1, toggle_col2 = st.columns([1, 3])
with toggle_col1:
    threats_only = st.toggle(
        "🔍 Threat-Centric Mode",
        value=True,
        help="ON = show only flagged threats and their direct connections. "
             "OFF = include surrounding normal traffic for full context.",
    )
with toggle_col2:
    if threats_only:
        st.markdown(
            '<p style="color:#f87171; font-size:0.82rem; margin-top:0.5rem; font-weight:500;">'
            '🚨 Showing <b>flagged anomalies only</b> — threats and their immediate IP/Entity neighbours</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p style="color:#60a5fa; font-size:0.82rem; margin-top:0.5rem; font-weight:500;">'
            '📡 Showing <b>all traffic context</b> — threats highlighted within broader network activity</p>',
            unsafe_allow_html=True,
        )

MAX_CONTEXT_NORMAL = 50   # neighbours of threats shown in both modes
MAX_CLEAN_SAMPLE = 40     # fully-clean normal nodes shown only in "all traffic" mode


def build_network_graph(graph_df: pd.DataFrame, threats_only: bool = True) -> str:
    """
    Build a focused, intelligence-style tripartite network graph.

    Two modes controlled by threats_only:
      True  (Threat-Centric) — Only anomalous rows + their immediate
            context neighbours (normal rows sharing an IP/Entity).
      False (All Traffic)    — Same as above PLUS a random sample of
            fully-clean normal traffic to show the broader network shape.
    """
    net = Network(
        height="580px",
        width="100%",
        bgcolor="#0d1117",
        font_color="#e5e7eb",
        directed=True,
        notebook=False,
    )

    # Tuned physics: strong repulsion + long springs = spread-out layout
    net.set_options("""
    {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -120,
                "centralGravity": 0.005,
                "springLength": 280,
                "springConstant": 0.02,
                "damping": 0.6,
                "avoidOverlap": 0.8
            },
            "solver": "forceAtlas2Based",
            "stabilization": { "iterations": 200 },
            "minVelocity": 0.75
        },
        "nodes": {
            "font": { "size": 11, "face": "Inter, sans-serif" },
            "borderWidth": 2,
            "borderWidthSelected": 3
        },
        "edges": {
            "smooth": { "type": "curvedCW", "roundness": 0.12 },
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.5 } },
            "width": 1
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragView": true
        }
    }
    """)

    # ── 1. Collect ALL anomaly rows ──────────────────────────────────
    anom_rows = graph_df[graph_df["is_anomaly"] == True]

    # Gather IPs and entities directly involved in anomalies
    anom_ips = set(anom_rows["src_ip"].unique())
    anom_entities = set()
    if "entity_id" in anom_rows.columns:
        anom_entities = set(anom_rows["entity_id"].unique())

    # ── 2. Pick context normal rows (neighbours of anomaly nodes) ───
    normal_rows = graph_df[graph_df["is_anomaly"] == False]
    ip_mask = normal_rows["src_ip"].isin(anom_ips)
    entity_mask = (
        normal_rows["entity_id"].isin(anom_entities)
        if "entity_id" in normal_rows.columns
        else pd.Series(False, index=normal_rows.index)
    )
    context_candidates = normal_rows[ip_mask | entity_mask]
    context_rows = context_candidates.sort_values(
        "risk_score", ascending=False
    ).head(MAX_CONTEXT_NORMAL)

    # ── 3. Optionally add clean-traffic sample (All Traffic mode) ───
    if not threats_only:
        already_selected = set(context_rows.index)
        clean_pool = normal_rows[~normal_rows.index.isin(already_selected)]
        clean_sample = clean_pool.sample(
            n=min(MAX_CLEAN_SAMPLE, len(clean_pool)), random_state=42
        )
        plot_df = pd.concat([anom_rows, context_rows, clean_sample]).drop_duplicates()
    else:
        plot_df = pd.concat([anom_rows, context_rows]).drop_duplicates()

    # ── 4. Build the graph ──────────────────────────────────────────
    added_nodes: set = set()

    for _, row in plot_df.iterrows():
        is_anom = bool(row["is_anomaly"])
        src_ip = str(row["src_ip"])
        txid = str(row["txid"])
        entity = str(row.get("entity_id", "Unknown"))
        amount = row.get("total_amount_btc", sum(float(a) for a in str(row.get("input_amounts", "0")).split("|") if a.strip()))
        risk = row["risk_score"]
        country = row.get("geo_country", "")

        # ─── IP node ───
        if src_ip not in added_nodes:
            if is_anom or src_ip in anom_ips:
                ip_color = "#ef4444"
                ip_size = 24
                ip_title = f"⚠️ SUSPICIOUS IP: {src_ip}"
            else:
                ip_color = "#3b82f6"
                ip_size = 14
                ip_title = f"IP: {src_ip}"
            net.add_node(
                src_ip, label=src_ip,
                color=ip_color, size=ip_size, shape="dot",
                title=ip_title,
            )
            added_nodes.add(src_ip)

        # ─── TX node ───
        if txid not in added_nodes:
            tx_label = f"{txid[:6]}…{txid[-4:]}"
            if is_anom:
                tx_color = "#f59e0b"
                tx_size = 16
                tx_title = (
                    f"🚨 FLAGGED TX: {txid}\n"
                    f"Amount: {amount} BTC\n"
                    f"Risk: {risk}%\nFirst-Seen Node: {country}"
                )
            else:
                tx_color = "#6b7280"
                tx_size = 8
                tx_title = f"TX: {txid}\nAmount: {amount} BTC"
            net.add_node(
                txid, label=tx_label,
                color=tx_color, size=tx_size, shape="diamond",
                title=tx_title,
            )
            added_nodes.add(txid)

        # ─── Entity node ───
        if entity not in added_nodes:
            if is_anom or entity in anom_entities:
                ent_color = "#9b59b6"
                ent_size = 30
                ent_title = f"⚠️ HIGH-RISK ENTITY: {entity}"
            else:
                ent_color = "#9b59b6"
                ent_size = 22
                ent_title = f"Entity Cluster: {entity}"
            net.add_node(
                entity, label=entity,
                color=ent_color, size=ent_size, shape="square",
                title=ent_title,
                borderWidth=3,
                font={"size": 14, "color": "#ffffff", "bold": True},
            )
            added_nodes.add(entity)

        # ─── Edges ───
        if is_anom:
            edge_color = "#ef4444"
            edge_width = 2.5
        else:
            edge_color = "rgba(107, 114, 128, 0.35)"
            edge_width = 0.7

        net.add_edge(
            src_ip, txid, color=edge_color, width=edge_width,
            title=f"Propagation node: {country}",
        )
        net.add_edge(
            entity, txid, color=edge_color, width=edge_width,
            title="Inputs owned by entity",
        )

    # ── 5. Render to HTML string ────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w")
    net.save_graph(tmp.name)

    with open(tmp.name, "r") as f:
        html_content = f.read()

    return html_content


st.markdown('<div class="graph-container">', unsafe_allow_html=True)
graph_html = build_network_graph(df, threats_only=threats_only)
components.html(graph_html, height=600, scrolling=False)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Investigation panel — flagged transactions table
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="section-title">
        <span class="icon">🔍</span> Investigation Panel
    </div>
    <p class="section-subtitle">
        {total_flagged} flagged transactions requiring analyst review &nbsp;·&nbsp;
        Sorted by Risk Score (descending)
    </p>
    """,
    unsafe_allow_html=True,
)

if total_flagged > 0:
    # Prepare display table
    display_df = flagged_df[
        [
            "timestamp",
            "src_ip",
            "entity_id",
            "input_addresses",
            "total_amount_btc",
            "fee",
            "script_type",
            "geo_country",
            "risk_score",
            "explanation",
        ]
    ].copy()

    # Format arrays for cleaner display
    display_df["input_addresses"] = display_df["input_addresses"].apply(
        lambda x: str(x).replace("|", ", ")[:30] + "..." if len(str(x)) > 30 else str(x).replace("|", ", ")
    )

    display_df = display_df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    display_df.columns = [
        "Timestamp",
        "Source IP",
        "Entity ID",
        "Inputs (Sample)",
        "Total Vol (BTC)",
        "Fee",
        "Script",
        "First-Seen Propagation Node",
        "Risk Score (%)",
        "Explanation",
    ]

    # Render with Streamlit's dataframe (full width, themed)
    st.markdown('<div class="investigation-panel">', unsafe_allow_html=True)

    st.dataframe(
        display_df.style
        .background_gradient(subset=["Risk Score (%)"], cmap="YlOrRd", vmin=50, vmax=100)
        .format({"Amount (BTC)": "{:.6f}", "Risk Score (%)": "{:.1f}%"}),
        use_container_width=True,
        height=480,
        hide_index=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # Download button for results
    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

    csv_export = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Flagged Results as CSV",
        data=csv_export,
        file_name="flagged_transactions.csv",
        mime="text/csv",
        use_container_width=True,
    )

else:
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem; color: #4ade80;">
            <span style="font-size: 3rem;">✅</span>
            <h3 style="color: #4ade80; margin-top: 0.5rem;">No Anomalies Detected</h3>
            <p style="color: #6b7280;">All transactions appear within normal parameters.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="fancy-divider"></div>
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <p style="color: #4b5563; font-size: 0.78rem; font-weight: 400;">
            AI Bitcoin Transaction Monitor &nbsp;·&nbsp; IsolationForest Anomaly Detection &nbsp;·&nbsp;
            Offline Analysis System &nbsp;·&nbsp; Built for SIH 2026
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

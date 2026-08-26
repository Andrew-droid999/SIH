"""
ml_engine.py — Graph-Aware AI Anomaly Detection Engine
======================================================

Implements a full data pipeline:
1. Constructs an Entity/Transaction graph using NetworkX.
2. Performs Wallet Clustering via Common-Input-Ownership (Union-Find).
3. Extracts graph-level and network-layer correlation features.
4. Trains an IsolationForest to detect anomalous graph behavior (layering).
5. Generates human-readable explanations (XAI) for flagged threats.

Can be run standalone via CLI or imported into Streamlit.
"""

import warnings
from typing import Tuple, List, Dict

import pandas as pd
import numpy as np
import networkx as nx
# pyrefly: ignore [missing-import]
from sklearn.ensemble import IsolationForest
# pyrefly: ignore [missing-import]
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings("ignore", category=UserWarning)

import builtins as _builtins
_print = _builtins.print  # capture real print before any overrides

def _log(msg: str) -> None:
    """Safe print wrapper — silently ignores I/O errors (e.g. inside Streamlit)."""
    try:
        _print(msg)
    except OSError:
        pass

INPUT_CSV = "bitcoin_traffic.csv"
OUTPUT_CSV = "flagged_transactions.csv"
CONTAMINATION = 0.05

HIGH_RISK_COUNTRIES = {"RU", "CN", "IR", "KP", "SY", "VE"}
MICRO_TX_THRESHOLD = 0.006

# ═══════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

def load_data(filepath: str = INPUT_CSV) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    _log(f"[*] Loaded {len(df)} transactions from {filepath}")
    return df

# ═══════════════════════════════════════════════════════════════════════════
# 2. GRAPH CONSTRUCTION & WALLET CLUSTERING
# ═══════════════════════════════════════════════════════════════════════════

def build_entity_graph(df: pd.DataFrame) -> Tuple[nx.Graph, Dict[str, str]]:
    """
    Builds the Entity-Transaction graph and clusters wallets using the 
    Common-Input-Ownership heuristic.
    """
    _log("[*] Building Entity/Transaction graph with NetworkX ...")
    
    # Bipartite mapping to cluster addresses
    address_graph = nx.Graph()
    
    for idx, row in df.iterrows():
        inputs = str(row["input_addresses"]).split("|")
        # Link all co-inputs together in the address graph to form entities
        for i in range(len(inputs)):
            address_graph.add_node(inputs[i])
            for j in range(i + 1, len(inputs)):
                address_graph.add_edge(inputs[i], inputs[j])
                    
    # Union Find (Connected Components) for entity clustering
    _log("[*] Running Union-Find wallet clustering (Common-Input-Ownership) ...")
    entity_map = {}
    components = list(nx.connected_components(address_graph))
    for entity_id, comp in enumerate(components):
        for addr in comp:
            entity_map[addr] = f"Entity_{entity_id}"
            
    _log(f"[*] Clustered {len(address_graph.nodes)} addresses into {len(components)} entities.")
    return address_graph, entity_map

def _frequency_encode(series: pd.Series) -> pd.Series:
    freq_map = series.value_counts(normalize=True)
    return series.map(freq_map)

# ═══════════════════════════════════════════════════════════════════════════
# 3. FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════

def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform raw transaction data into graph-aware numeric features.
    """
    _, entity_map = build_entity_graph(df)
    
    # Assign Entity ID to each transaction (based on first input)
    entities = []
    for inputs in df["input_addresses"].str.split("|"):
        if len(inputs) > 0 and inputs[0] in entity_map:
            entities.append(entity_map[inputs[0]])
        else:
            entities.append("UnknownEntity")
    df["entity_id"] = entities

    features = pd.DataFrame(index=df.index)

    # --- Graph Correlation Features ---
    # For each entity, how many distinct IPs does it use? (High = anonymization)
    entity_ip_counts = df.groupby("entity_id")["src_ip"].nunique()
    features["entity_ip_diversity"] = df["entity_id"].map(entity_ip_counts).fillna(1)
    
    # For each IP, how many distinct entities is it broadcasting for?
    ip_entity_counts = df.groupby("src_ip")["entity_id"].nunique()
    features["ip_entity_diversity"] = df["src_ip"].map(ip_entity_counts).fillna(1)

    features["entity_tx_freq"] = _frequency_encode(df["entity_id"])

    # --- Standard Network & Geography Features ---
    features["src_ip_freq"] = _frequency_encode(df["src_ip"])
    features["geo_freq"] = _frequency_encode(df["geo_country"])
    features["is_high_risk_geo"] = df["geo_country"].isin(HIGH_RISK_COUNTRIES).astype(int)

    # Calculate total input amount for each transaction
    def calc_total(amount_str):
        try:
            return sum(float(a) for a in str(amount_str).split("|") if a.strip())
        except:
            return 0.0
    
    df["total_amount_btc"] = df["input_amounts"].apply(calc_total)

    # --- Amount & Port Features ---
    scaler = MinMaxScaler()
    features["amount_btc_scaled"] = scaler.fit_transform(df[["total_amount_btc"]])
    if "fee" in df.columns:
        features["fee_scaled"] = scaler.fit_transform(df[["fee"]])
    features["is_micro_tx"] = (df["total_amount_btc"] < MICRO_TX_THRESHOLD).astype(int)
    
    # Script type frequency encoding
    if "script_type" in df.columns:
        features["script_type_freq"] = _frequency_encode(df["script_type"])
    
    standard_ports = {8332, 8333, 8334, 18332, 18333}
    features["src_port_is_std"] = df["src_port"].isin(standard_ports).astype(int)

    _log(f"[*] Engineered {features.shape[1]} features: {list(features.columns)}")
    return features, df

# ═══════════════════════════════════════════════════════════════════════════
# 4. MODEL TRAINING & PREDICTION
# ═══════════════════════════════════════════════════════════════════════════

def train_model(features: pd.DataFrame, contamination: float = CONTAMINATION) -> Tuple[IsolationForest, np.ndarray, np.ndarray]:
    _log(f"[*] Training IsolationForest (n_estimators=200, contamination={contamination}) …")
    model = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination=contamination,
        random_state=42,
        n_jobs=1
    )
    model.fit(features)
    predictions = model.predict(features)
    raw_scores = model.decision_function(features)
    
    num_anomalies = (predictions == -1).sum()
    _log(f"[*] Flagged {num_anomalies} transactions as anomalies ({num_anomalies / len(features) * 100:.1f}%)")
    return model, predictions, raw_scores

def compute_risk_scores(raw_scores: np.ndarray) -> np.ndarray:
    inverted = -raw_scores
    min_score = inverted.min()
    max_score = inverted.max()
    
    if max_score > min_score:
        scaled = (inverted - min_score) / (max_score - min_score)
        risk_pct = scaled * 100.0
    else:
        risk_pct = np.zeros_like(inverted)
        
    return np.clip(risk_pct, 0, 100).round(1)

# ═══════════════════════════════════════════════════════════════════════════
# 5. EXPLAINABLE AI (XAI)
# ═══════════════════════════════════════════════════════════════════════════

def generate_explanation(row_features: pd.Series, risk_score: float, original_row: pd.Series) -> str:
    if risk_score < 50.0:
        return "Normal network traffic behavior."

    reasons = []
    
    if row_features["entity_ip_diversity"] > 2:
        reasons.append(f"Entity uses multiple distinct IPs ({int(row_features['entity_ip_diversity'])} IPs), suggesting anonymization")
        
    if row_features["ip_entity_diversity"] > 2:
        reasons.append(f"IP {original_row['src_ip']} broadcasts for multiple distinct entities, acting as a high-traffic node")
        
    if row_features["src_ip_freq"] > 0.05:
        reasons.append("High-frequency IP broadcast pattern")
        
    if row_features["is_micro_tx"] == 1:
        reasons.append(f"Micro-transaction detected ({original_row.get('total_amount_btc', 0):.4f} BTC)")
        
    if row_features["is_high_risk_geo"] == 1:
        reasons.append(f"Originates from high-risk jurisdiction ({original_row['geo_country']})")

    if not reasons:
        reasons.append("Anomalous structural graph relationships detected by ML")

    return "Risk indicators: " + "; ".join(reasons) + "."

def generate_all_explanations(df: pd.DataFrame, features: pd.DataFrame, predictions: np.ndarray, risk_scores: np.ndarray) -> pd.DataFrame:
    _log("[*] Generating graph-aware risk explanations …")
    result = df.copy()
    result["is_anomaly"] = (predictions == -1)
    result["risk_score"] = risk_scores
    
    explanations = []
    for idx, row in result.iterrows():
        if row["is_anomaly"]:
            feat_row = features.iloc[idx]
            exp = generate_explanation(feat_row, row["risk_score"], row)
            explanations.append(exp)
        else:
            explanations.append("Normal.")
            
    result["explanation"] = explanations
    return result

# ═══════════════════════════════════════════════════════════════════════════
# 6. EXPORT
# ═══════════════════════════════════════════════════════════════════════════

def export_results(df: pd.DataFrame, filepath: str = OUTPUT_CSV) -> str:
    df.to_csv(filepath, index=False)
    _log(f"[*] Results saved to {filepath}")
    return filepath

# ═══════════════════════════════════════════════════════════════════════════
# 7. FULL PIPELINE ENTRIES
# ═══════════════════════════════════════════════════════════════════════════

def run_pipeline(
    input_csv: str = INPUT_CSV,
    output_csv: str = OUTPUT_CSV,
    contamination: float = CONTAMINATION,
) -> Tuple[pd.DataFrame, IsolationForest]:
    _log("=" * 60)
    _log("  Bitcoin Graph Anomaly Detection Engine")
    _log("=" * 60)

    df = load_data(input_csv)
    features, df = engineer_features(df)
    model, predictions, raw_scores = train_model(features, contamination=contamination)
    risk_scores = compute_risk_scores(raw_scores)
    enriched_df = generate_all_explanations(df, features, predictions, risk_scores)
    export_results(enriched_df, output_csv)

    anomaly_df = enriched_df[enriched_df["is_anomaly"]]
    _log(f"\n{'─' * 60}")
    _log(f"  Summary")
    _log(f"{'─' * 60}")
    _log(f"  Total transactions:     {len(enriched_df)}")
    _log(f"  Flagged anomalies:      {len(anomaly_df)}")
    _log(f"  Avg risk (anomalies):   {anomaly_df['risk_score'].mean():.1f}%")
    _log(f"  Max risk score:         {anomaly_df['risk_score'].max():.1f}%")
    _log(f"  Output:                 {output_csv}")
    _log(f"{'─' * 60}")
    _log(f"  [✓] Pipeline complete.\n")

    return enriched_df, model

def run_pipeline_from_df(
    df: pd.DataFrame,
    contamination: float = CONTAMINATION,
) -> Tuple[pd.DataFrame, IsolationForest]:
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    features, df = engineer_features(df)
    model, predictions, raw_scores = train_model(features, contamination=contamination)
    risk_scores = compute_risk_scores(raw_scores)
    enriched_df = generate_all_explanations(df, features, predictions, risk_scores)

    return enriched_df, model

if __name__ == "__main__":
    run_pipeline()

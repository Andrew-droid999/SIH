<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-1.62-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Scikit--Learn-IsolationForest-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" />
  <img src="https://img.shields.io/badge/NetworkX-Graph_Clustering-3399FF?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Linux%20(Offline)-FCC624?style=for-the-badge&logo=linux&logoColor=black" />
  <img src="https://img.shields.io/badge/SIH-2026-00C853?style=for-the-badge" />
</p>

<h1 align="center">🔗 AI-Powered Monitoring & Analysis of<br>Bitcoin Transaction Traffic</h1>

<p align="center">
  <b>An offline, Linux-native intelligence system that fuses network-layer (IP/port/geo) and blockchain-layer (wallet/TXID/amount) data using graph-aware unsupervised ML to detect Bitcoin laundering, ransomware payments, and layering patterns — with full explainability and interactive threat isolation.</b>
</p>

<p align="center">
  <i>Built for Smart India Hackathon 2026</i>
</p>

---

## 📋 Table of Contents

| # | Section |
|---|---------|
| 1 | [Problem Statement & Motivation](#-problem-statement--motivation) |
| 2 | [Key Features](#-key-features) |
| 3 | [System Architecture & Data Flow](#-system-architecture--data-flow) |
| 4 | [Tech Stack & Design Rationale](#-tech-stack--design-rationale) |
| 5 | [Dataset Schema](#-dataset-schema) |
| 6 | [AI/ML Pipeline Deep Dive](#-aiml-pipeline-deep-dive) |
| 7 | [Explainable AI (XAI)](#-explainable-ai-xai) |
| 8 | [Dashboard & Visualization Guide](#-dashboard--visualization-guide) |
| 9 | [Project Structure](#-project-structure) |
| 10 | [Installation & Usage](#-installation--usage) |
| 11 | [SIH Compliance Matrix](#-sih-compliance-matrix) |
| 12 | [Future Roadmap](#-future-roadmap) |

---

## 🎯 Problem Statement & Motivation

### The Challenge (SIH 2026)

Bitcoin's pseudonymous, peer-to-peer design lets criminal actors move, layer, and cash out illicit funds — **ransomware payments, darknet-market proceeds, extortion, and money laundering** — while evading traditional financial surveillance.

Law enforcement needs tools that can **operate entirely offline on air-gapped Linux machines** while still providing AI-grade detection, entity clustering, and graph analysis capabilities.

### Objective

Design and build a **complete offline system** that:
1. **Ingests** bulk Bitcoin transaction/network metadata (CSV).
2. **Correlates** network-layer observations (IP/port/timing) with blockchain-layer data (wallet/TXID/amount).
3. **Applies AI/ML** to detect anomalies, cluster entities, and generate prioritised, explainable investigative leads.
4. **Presents** findings via an interactive dashboard with link-analysis visualisation.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔒 **Fully Offline** | Zero cloud dependencies. Runs on air-gapped Linux machines with offline GeoIP (`GeoLite2-Country.mmdb`). |
| 🧠 **Unsupervised AI/ML** | `IsolationForest` trained on 11 graph-derived correlation features — discovers anomalies without pre-labelled fraud data. |
| 🔗 **Graph-Aware Clustering** | Wallet clustering via Common-Input-Ownership heuristic using NetworkX Union-Find (connected components). |
| 🕸️ **Interactive Tripartite Graph** | Pyvis-powered physics-based network visualisation linking **IPs ↔ Transactions ↔ Wallet Entities**. |
| 🔍 **Threat-Centric Mode Toggle** | Dynamic UI switch to isolate flagged threats only or view them within broader network context. |
| 📊 **Ranked Alert List** | Every flagged transaction scored 0–100% with human-readable risk explanations (XAI). |
| 🎚️ **Tunable Sensitivity** | Officers can adjust the anomaly detection threshold (1%–20%) via a live slider. |
| 📥 **CSV Export** | One-click download of enriched results with all AI predictions and explanations. |

---

## ⚙ System Architecture & Data Flow

The system operates as a **three-stage pipeline**:

```
┌─────────────────────┐      ┌─────────────────────┐      ┌───────────────────────┐
│   STAGE 1            │      │   STAGE 2            │      │   STAGE 3              │
│   DATA INGESTION     │─────▶│   AI/ML ENGINE       │─────▶│   DASHBOARD            │
│                      │      │                      │      │                        │
│   data_generator.py  │      │   ml_engine.py       │      │   app.py               │
│                      │      │                      │      │                        │
│   • Synthetic data   │      │   • Graph building   │      │   • Bento metric cards  │
│   • Entity sim       │      │   • Wallet clustering│      │   • Pyvis network graph │
│   • GeoIP lookup     │      │   • Feature eng.     │      │   • Investigation table │
│   • CSV output       │      │   • IsolationForest  │      │   • Threat toggle       │
│                      │      │   • XAI explanations │      │   • CSV export          │
│   ▼                  │      │   ▼                  │      │                        │
│   bitcoin_traffic    │      │   flagged_           │      │   Interactive offline   │
│   .csv               │      │   transactions.csv   │      │   Streamlit dashboard   │
└─────────────────────┘      └─────────────────────┘      └───────────────────────┘
```

### Data Flow

1. **`data_generator.py`** creates a synthetic dataset of 2,000 Bitcoin transactions with realistic entity ownership, co-spending inputs, and offline GeoIP country codes.
2. **`ml_engine.py`** ingests the CSV, builds a NetworkX graph, clusters wallets into entities, engineers 11 correlation features, trains an `IsolationForest` model, and outputs ranked, explained alerts.
3. **`app.py`** provides a Streamlit dashboard where officers upload CSVs, triggering the AI engine in real-time. Results are displayed via metric cards, an interactive network graph, and a sortable investigation table.

---

## 🛠 Tech Stack & Design Rationale

| Technology | Role | Why This Choice |
|---|---|---|
| **Python 3.10+** | Core language | Industry standard for ML/data pipelines; runs natively on Linux |
| **Pandas + NumPy** | Data manipulation | Efficient DataFrame operations for CSV ingestion and feature computation |
| **NetworkX** | Graph construction & clustering | Builds the tripartite IP-TX-Entity graph; Union-Find via `connected_components()` |
| **Scikit-Learn** | ML engine (`IsolationForest`) | Battle-tested unsupervised anomaly detection; works fully offline |
| **Streamlit** | Interactive dashboard | Rapid prototyping of data apps with zero frontend boilerplate; Python-native |
| **Pyvis** | Network graph visualisation | Interactive, physics-based graphs rendered in-browser; reveals transaction topology |
| **GeoIP2** | Geographic mapping | True offline IP-to-Country lookups using `GeoLite2-Country.mmdb` (~8 MB) |
| **Faker** | Synthetic data generation | Realistic IP addresses, timestamps, and transaction hashes for testing |

---

## 📊 Dataset Schema

The synthetic dataset (`bitcoin_traffic.csv`) models real Bitcoin P2P/transaction fields. All fields match the SIH problem statement requirements:

| Column | Type | Description | Example |
|---|---|---|---|
| `timestamp` | datetime | ISO-8601 date/time of the transaction | `2026-08-15 14:23:01` |
| `src_ip` | string | Source IP address (sender's node) | `185.220.101.42` |
| `dst_ip` | string | Destination IP address (receiver's node) | `142.93.177.141` |
| `src_port` | int | Source port number | `8333` |
| `dst_port` | int | Destination port number | `18333` |
| `txid` | string | 64-char SHA-256 transaction hash | `fc5a006...` |
| `input_addresses` | string[] | Pipe-delimited sender wallet addresses | `1o7C...\|bc1q...` |
| `output_addresses` | string[] | Pipe-delimited receiver wallet addresses | `3Gmo...\|1Xw...` |
| `input_amounts` | float[] | Pipe-delimited input amounts in BTC | `0.0005\|0.0005` |
| `output_amounts` | float[] | Pipe-delimited output amounts in BTC | `0.0009` |
| `fee` | float | Transaction network fee in BTC | `0.0001` |
| `script_type` | string | Bitcoin script type (P2PKH/P2SH/P2WPKH/P2TR) | `P2WPKH` |
| `geo_country` | string | ISO country code from offline GeoIP lookup | `RU` |

---

## 🧠 AI/ML Pipeline Deep Dive

### Stage 1: Wallet Clustering — Common-Input-Ownership Heuristic

The engine parses `input_addresses[]` for every transaction. If multiple addresses appear as inputs to the same transaction, they are mathematically controlled by the same entity (they must all sign the transaction). These addresses are grouped via **NetworkX connected components** (Union-Find algorithm).

```
Transaction A: inputs = [addr1, addr2, addr3]  →  Entity_0
Transaction B: inputs = [addr2, addr4]          →  Entity_0 (addr2 links them)
Transaction C: inputs = [addr5]                 →  Entity_1 (separate cluster)
```

### Stage 2: Graph-Aware Feature Engineering

The ML model extracts **11 correlation features** from the network graph:

| Feature | What It Captures |
|---------|-----------------|
| `entity_ip_diversity` | Number of distinct IPs an entity uses (high = anonymization/VPN/Tor) |
| `ip_entity_diversity` | Number of distinct entities an IP broadcasts for (high = relay/botnet) |
| `entity_tx_freq` | Frequency of transactions by this entity cluster |
| `src_ip_freq` | Frequency of this source IP across all transactions |
| `geo_freq` | How common this geographic origin is |
| `is_high_risk_geo` | Binary flag for sanctioned/high-risk jurisdictions (RU, CN, IR, KP, SY, VE) |
| `amount_btc_scaled` | MinMax-scaled total transaction volume |
| `fee_scaled` | MinMax-scaled transaction fee |
| `is_micro_tx` | Binary flag for micro-transactions below 0.006 BTC (layering indicator) |
| `script_type_freq` | Frequency encoding of the Bitcoin script type used |
| `src_port_is_std` | Whether the source port is a standard Bitcoin port |

### Stage 3: IsolationForest Anomaly Detection

An unsupervised `IsolationForest` (200 estimators) evaluates transactions by building random isolation trees. Points that are isolated with fewer splits are mathematical outliers. The model requires **zero labelled fraud data** — it discovers anomalies independently.

- **Input:** 11-feature matrix (2,000 × 11)
- **Output:** Binary anomaly flag + `decision_function` score → normalised to 0–100% risk score
- **Contamination:** Configurable via UI slider (default 5%)

---

## 🔍 Explainable AI (XAI)

Every flagged transaction receives a **human-readable explanation** mapping the ML decision back to specific risk indicators:

### Example Output

```
Risk indicators: Entity uses multiple distinct IPs (4 IPs), suggesting
anonymization; IP 185.220.101.42 broadcasts for multiple distinct entities,
acting as a high-traffic node; Micro-transaction detected (0.0010 BTC);
Originates from high-risk jurisdiction (RU).
```

### How It Works

The `generate_explanation()` function inspects the feature vector for each flagged transaction and translates threshold breaches into natural-language sentences:

| Feature Condition | Explanation Generated |
|---|---|
| `entity_ip_diversity > 2` | "Entity uses multiple distinct IPs (N IPs), suggesting anonymization" |
| `ip_entity_diversity > 2` | "IP X broadcasts for multiple distinct entities, acting as a high-traffic node" |
| `src_ip_freq > 0.05` | "High-frequency IP broadcast pattern" |
| `is_micro_tx == 1` | "Micro-transaction detected (X BTC)" |
| `is_high_risk_geo == 1` | "Originates from high-risk jurisdiction (CC)" |

---

## 🖥 Dashboard & Visualization Guide

### Header & Metrics

The dashboard opens with three **bento-box metric cards** showing:
- **Total Scanned Transactions** — complete dataset size
- **Total Flagged Threats** — anomalies detected by IsolationForest
- **Max Risk Score** — highest confidence level among all flags

### Network Graph — Tripartite Visualization

An interactive Pyvis physics-based graph renders three node types:

| Node Shape | Color | Meaning |
|---|---|---|
| ● Circle | 🔴 **Red** `#ef4444` | Suspicious/flagged IP address |
| ● Circle | 🔵 **Blue** `#3b82f6` | Normal context IP address |
| ◆ Diamond | 🟡 **Amber** `#f59e0b` | Flagged transaction |
| ◆ Diamond | ⚫ **Gray** `#6b7280` | Normal context transaction |
| ■ Square | 🟣 **Purple** `#9b59b6` | Wallet entity cluster |

### 🔍 Threat-Centric Mode Toggle

A dynamic toggle switch above the graph controls the view:

| Mode | Description |
|---|---|
| **ON — Threats Only** | Shows only flagged anomalous nodes + their immediate IP/Entity neighbours. Clean, focused view for investigation. |
| **OFF — All Traffic** | Adds a sample of normal traffic nodes to provide broader network context. Threats remain highlighted with red edges. |

### Investigation Panel

A sortable data table showing all flagged transactions ranked by risk score (descending), with columns:
- Timestamp, Source IP, Entity ID, Input Addresses, Total Volume (BTC), Fee, Script Type, Country, Risk Score (%), Explanation

### Export

A **Download CSV** button exports the complete enriched dataset including all AI predictions and explanations.

---

## 📁 Project Structure

```text
SIH-2026-2/
│
├── data_generator.py          # Stage 1: Synthetic dataset generator + GeoIP download
├── ml_engine.py               # Stage 2: Graph builder + wallet clustering + AI engine
├── app.py                     # Stage 3: Streamlit dashboard + Pyvis visualisation
│
├── bitcoin_traffic.csv        # Generated: Raw transaction data (2,000 rows, 13 columns)
├── flagged_transactions.csv   # Generated: Enriched data with AI predictions + XAI
│
├── GeoLite2-Country.mmdb      # Offline GeoIP database (~8 MB)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🚀 Installation & Usage

### Prerequisites

| Requirement | Details |
|---|---|
| **OS** | Linux (Ubuntu 20.04+ / Kali / any distro) — fully offline-capable |
| **Python** | 3.10 or higher |
| **Internet** | Required **only once** for initial `pip install` and GeoIP database download |

### Step 1: Clone & Setup

```bash
git clone https://github.com/devansh2007-ruikar/SIH.git
cd SIH-2026-2
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Generate the Synthetic Dataset

```bash
python data_generator.py
```

This will:
- Auto-download `GeoLite2-Country.mmdb` if not present (~8 MB, one-time)
- Generate `bitcoin_traffic.csv` with 2,000 transactions (5% injected anomalies)

### Step 3: (Optional) Run ML Engine Standalone

```bash
python ml_engine.py
```

This processes `bitcoin_traffic.csv` through the full AI pipeline and outputs `flagged_transactions.csv`.

### Step 4: Launch the Dashboard

```bash
streamlit run app.py
```

1. Open **http://localhost:8501** in your browser.
2. **Upload** `bitcoin_traffic.csv` using the sidebar uploader.
3. The AI engine runs automatically — dashboard populates with:
   - Metric cards (total scanned, flagged, max risk)
   - Interactive network graph (toggle Threat-Centric Mode)
   - Ranked investigation table with explanations
4. **Download** enriched results via the CSV export button.

---

## ✅ SIH Compliance Matrix

| SIH Requirement | Our Implementation | Status |
|---|---|---|
| Offline Linux solution | Python + Scikit-Learn + NetworkX + offline GeoIP | ✅ |
| Ingest bulk CSV metadata | Pandas CSV parser with column validation | ✅ |
| Required fields (timestamp, IP, port, TXID, addresses[], amounts[], fee, script_type, geo) | All 13 fields implemented in `data_generator.py` | ✅ |
| Entity/transaction graph linking IPs, wallets, transactions | NetworkX tripartite graph + Pyvis visualisation | ✅ |
| AI/ML detection with working model (not just rules) | `IsolationForest` with 11 graph-derived features | ✅ |
| Wallet clustering | Common-Input-Ownership via `nx.connected_components()` | ✅ |
| Ranked, explainable alert list with confidence scores | Risk scores (0–100%) + human-readable explanations | ✅ |
| Dashboard / link-analysis visualisation | Streamlit + Pyvis with Threat-Centric toggle | ✅ |
| Working prototype code repo | Complete 3-file pipeline, reproducible | ✅ |
| Technical write-up | This README | ✅ |

---

## 🗺 Future Roadmap

| Feature | Status | Description |
|---|---|---|
| Real-time packet capture | 🔲 Planned | Replace CSV ingestion with live `tcpdump` / `tshark` pipeline |
| Deep learning (Autoencoder) | 🔲 Planned | Add a second ML model for temporal sequence anomaly detection |
| PDF report export | 🔲 Planned | One-click investigation report for law enforcement filing |
| Multi-cryptocurrency | 🔲 Planned | Extend to Ethereum, Monero, and Tether (USDT) |
| ASN / BGP enrichment | 🔲 Planned | Integrate ASN data for deeper network-layer correlation |
| Temporal velocity features | 🔲 Planned | Detect burst-sending patterns via sliding-window analysis |

---

<p align="center">
  <b>Built for Smart India Hackathon 2026</b><br>
  <sub>AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic</sub>
</p>

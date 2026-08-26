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
  <b>An offline, Linux-native, graph-aware intelligence system that uses NetworkX wallet clustering and unsupervised machine learning to detect Bitcoin laundering, ransomware payments, and layering patterns — with full explainability for investigating officers.</b>
</p>

---

## 📋 Table of Contents

| # | Section |
|---|---------|
| 1 | [Project Overview](#-project-overview) |
| 2 | [Tech Stack & Design Rationale](#-tech-stack--design-rationale) |
| 3 | [How The System Works (Step-by-Step)](#-how-the-system-works-step-by-step) |
| 4 | [Explainable AI (XAI)](#-explainable-ai-xai) |
| 5 | [Project Structure](#-project-structure) |
| 6 | [Installation & Usage Guide](#-installation--usage-guide) |
| 7 | [Future Roadmap](#-future-roadmap) |

---

## 🎯 Project Overview

### The Problem

Cryptocurrency — particularly Bitcoin — has become a preferred vehicle for **ransomware payments, money laundering, and terrorist financing**. Criminals exploit the pseudonymous nature of blockchain networks to move illicit funds across borders through techniques like:

- **Layering** — rapidly splitting funds across dozens of wallets in small, identical amounts to obscure the money trail.
- **Micro-structuring** — sending amounts just below detection thresholds.
- **Proxy relay networks** — routing transactions through Tor exit nodes and compromised IPs to hide geographic origin.

Law enforcement and cybersecurity agencies need tools that can **operate entirely offline on air-gapped Linux machines** (for security compliance) while still providing AI-grade detection capabilities, entity clustering, and graph analysis.

### Our Solution

This system is a **fully offline, Linux-native graph-aware AI pipeline** that:

1. **Ingests** raw Bitcoin network traffic data (CSV format) and integrates with offline GeoIP databases.
2. **Clusters** wallets into Entities using the **Common-Input-Ownership** heuristic via NetworkX Union-Find algorithms.
3. **Detects** anomalous transactions using an **unsupervised IsolationForest ML model** enhanced with network-layer correlation features — no pre-labelled fraud data required.
4. **Explains** every flagged transaction with a human-readable risk assessment and confidence score.
5. **Visualises** the transaction network as an interactive Tripartite graph, revealing entity clusters and suspicious relay patterns.

> **Key Differentiator:** The AI engine merges the blockchain layer (transactions/wallets) with the network layer (IPs). It actively clusters wallets into entities and scores anomalies based on structural correlation patterns (e.g., An entity using multiple distinct IPs for anonymization).

---

## 🛠 Tech Stack & Design Rationale

| Technology | Role | Why This Choice |
|---|---|---|
| **Python 3.10+** | Core language | Industry standard for ML/data pipelines; vast ecosystem |
| **Pandas** | Data ingestion & manipulation | Efficient DataFrame operations for CSV processing at scale |
| **NetworkX** | Graph & Clustering | Builds the Bipartite IP-Transaction graph and clusters wallets using Union-Find algorithms |
| **Scikit-Learn** | ML engine (IsolationForest) | Battle-tested unsupervised anomaly detection; works offline with zero external API calls |
| **Streamlit** | Interactive dashboard | Rapid prototyping of data apps with zero frontend boilerplate; Python-native |
| **Pyvis** | Graph visualisation | Interactive, physics-based network graphs rendered in-browser; reveals transaction topology |
| **GeoIP2** | Geographic Mapping | True offline IP-to-Country lookups using `GeoLite2-Country.mmdb` |

---

## ⚙ How The System Works (Step-by-Step)

The system operates as a **three-stage pipeline**, with each stage producing a tangible output:

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  DATA INGESTION  │────▶│   AI ENGINE     │────▶│   DASHBOARD      │
│  data_generator  │     │   ml_engine     │     │   app.py         │
│                  │     │                 │     │                  │
│  bitcoin_traffic │     │  flagged_       │     │  Tripartite      │
│  .csv            │     │  transactions   │     │  Network Graph   │
│                  │     │  .csv           │     │  + Investigation │
└─────────────────┘     └─────────────────┘     └──────────────────┘
```

---

### Stage 1: Data Ingestion — `data_generator.py`

#### What It Does

Generates a synthetic dataset of **2,000 Bitcoin transactions** that closely mimics real-world network traffic captured from Bitcoin full nodes. It simulates realistic entity ownership, co-spending inputs, and uses offline IP lookups.

#### The Data Columns

| Column | Description | Example |
|---|---|---|
| `timestamp` | ISO-8601 date/time of the transaction | `2026-08-15 14:23:01` |
| `src_ip` | Source IP address (sender's node) | `185.220.101.42` |
| `dst_ip` | Destination IP address (receiver's node) | `142.93.177.141` |
| `src_port` | Source port number | `8333` |
| `dst_port` | Destination port number | `18333` |
| `txid` | 64-char hex transaction hash (SHA-256) | `fc5a00603d8f...` |
| `input_addresses` | Array of Bitcoin wallet addresses (sender) | `1o7C...\|bc1q...` |
| `output_addresses` | Array of Bitcoin wallet addresses (receiver) | `3Gmo...\|1Xw...` |
| `input_amounts` | Array of input amounts in BTC | `0.0005\|0.0005` |
| `output_amounts` | Array of output amounts in BTC | `0.0009` |
| `fee` | Transaction network fee in BTC | `0.0001` |
| `script_type` | Type of Bitcoin script used | `P2WPKH` |
| `geo_country` | ISO country code of the source IP | `RU` |

#### Offline GeoIP Integration
The script automatically downloads the `GeoLite2-Country.mmdb` (~8MB) and uses it to map generated IPs to actual countries, satisfying the strict SIH offline requirement.

---

### Stage 2: Graph-Aware AI Engine — `ml_engine.py`

This is the heart of the system. It transforms raw CSV data into actionable intelligence.

#### 2.1 Wallet Clustering (Union-Find)
The engine parses the `input_addresses` array for every transaction. If multiple addresses are used as inputs to the same transaction, they are grouped into the same `Entity_ID` via NetworkX connected components. This implements the **Common-Input-Ownership** heuristic to cluster addresses into wallets.

#### 2.2 Feature Engineering
The ML model extracts **correlation features** from the network graph:
- `entity_ip_diversity`: Flags entities that use many different IPs (anonymization/layering).
- `ip_entity_diversity`: Flags IPs that broadcast transactions for many distinct entities (botnets/nodes).
- Geographic frequencies, port checks, and transaction magnitude scalings are also computed.

#### 2.3 Model Training — IsolationForest
An unsupervised `IsolationForest` model evaluates the transactions. It builds isolation trees and mathematically flags points that are statistical outliers across the engineered features. The AI does not read a "fraud" column; it discovers anomalies independently.

#### 2.4 Output
The engine appends `is_anomaly`, `risk_score` (0-100%), and a text `explanation` to the original data, saved as `flagged_transactions.csv`.

---

### Stage 3: Dashboard — `app.py`

The Streamlit dashboard requires an investigating officer to upload the CSV file (mandatory upload). It then renders an **intelligence-focused Tripartite network graph**:

#### Node Types
- 📡 **IPs** (Dots)
- 🔗 **Transactions** (Diamonds)
- 💼 **Entities** (Boxes - representing clustered wallets)

#### Graph Filtering
To prevent visual clutter, the physics graph strictly filters the view to:
1. **ALL anomalous transactions, entities, and IPs.**
2. A capped set of **immediate context nodes** (highest-risk normal transactions connected to anomalous IPs/Entities).

This layout immediately exposes relay networks, botnets, and proxy obfuscation patterns.

---

## 🧠 Explainable AI (XAI)

A core requirement of the SIH problem statement is that the system must not be a black box. Every flagged transaction receives a **human-readable explanation** detailing exactly why it was flagged.

### Example Explanation

```
🔴 Critical risk: Entity uses multiple distinct IPs (4 IPs), suggesting 
anonymization; IP 185.220.101.42 broadcasts for multiple distinct entities, 
acting as a high-traffic node; Micro-transaction detected (0.001 BTC); 
Originates from high-risk jurisdiction (RU).
```

---

## 📁 Project Structure

```text
SIH-2026-2/
│
├── data_generator.py          # Stage 1: Synthetic dataset generator & GeoIP DB download
├── ml_engine.py               # Stage 2: Graph builder & AI anomaly detection engine
├── app.py                     # Stage 3: Streamlit dashboard frontend
│
├── bitcoin_traffic.csv        # Generated: Raw transaction data (2,000 rows)
├── flagged_transactions.csv   # Generated: Enriched data with AI predictions
│
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🚀 Installation & Usage Guide

### Prerequisites
- **OS:** Linux (Ubuntu 20.04+ / Kali / any distro) — fully offline-capable
- **Python:** 3.10 or higher
- **Internet:** Required only once for initial `pip install`

### Step 1: Clone & Setup
```bash
git clone <repository-url>
cd SIH-2026-2
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Generate the Synthetic Dataset
```bash
python data_generator.py
```
*Note: This will automatically download the GeoLite2 database if not present.*

### Step 3: Run the Dashboard
```bash
streamlit run app.py
```
Open **http://localhost:8501** in your browser.
**Upload** the `bitcoin_traffic.csv` using the sidebar uploader. The AI model will run dynamically in the background and populate the investigation dashboard!

---

## 🗺 Future Roadmap

| Feature | Status | Description |
|---|---|---|
| Real-time packet capture | 🔲 Planned | Replace CSV ingestion with live `tcpdump` / `tshark` pipeline |
| Deep learning (Autoencoder) | 🔲 Planned | Add a second ML model for temporal sequence anomaly detection |
| PDF report export | 🔲 Planned | One-click investigation report for law enforcement filing |
| Multi-cryptocurrency | 🔲 Planned | Extend to Ethereum, Monero, and Tether (USDT) |

---

<p align="center">
  <b>Built for Smart India Hackathon 2026</b><br>
  <sub>AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic</sub>
</p>
# SIH

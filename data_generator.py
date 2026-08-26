"""
data_generator.py — Synthetic Bitcoin Transaction Dataset Generator
===================================================================

Generates a CSV of synthetic Bitcoin transactions with realistic
network and blockchain metadata, including true entity clustering
(multiple inputs co-spent) and offline GeoIP lookups.

Dependencies:
    pip install faker pandas requests geoip2

Output:
    bitcoin_traffic.csv
"""

import hashlib
import random
import string
import os
from datetime import datetime, timedelta

import requests
import pandas as pd
# pyrefly: ignore [missing-import]
import geoip2.database
# pyrefly: ignore [missing-import]
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOTAL_TRANSACTIONS = 2_000
ANOMALY_RATE = 0.05
NUM_ANOMALIES = int(TOTAL_TRANSACTIONS * ANOMALY_RATE)
NUM_NORMAL = TOTAL_TRANSACTIONS - NUM_ANOMALIES

SEED = 42
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

END_TIME = datetime(2026, 8, 26, 12, 0, 0)
START_TIME = END_TIME - timedelta(days=30)
BITCOIN_PORTS = [8333, 18333, 8332, 8334, 18332]

# ---------------------------------------------------------------------------
# GeoIP Setup
# ---------------------------------------------------------------------------

MMDB_FILENAME = "GeoLite2-Country.mmdb"
MMDB_URL = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"

def download_geoip_db():
    if not os.path.exists(MMDB_FILENAME):
        print(f"[*] Downloading {MMDB_FILENAME} (approx 8MB) ...")
        r = requests.get(MMDB_URL, stream=True)
        r.raise_for_status()
        with open(MMDB_FILENAME, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("[*] Download complete.")

# ---------------------------------------------------------------------------
# Entity Simulation (for Wallet Clustering)
# ---------------------------------------------------------------------------

def random_btc_address() -> str:
    prefix = random.choice(["1", "3", "bc1q"])
    length = 33 if prefix in ("1", "3") else 38
    body = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{prefix}{body}"

# Pre-generate entities: A user (entity) controls multiple addresses.
# When they transact, they co-spend these addresses.
print("[*] Generating entities for realistic clustering ...")
NORMAL_ENTITIES = []
for _ in range(500): # 500 normal entities
    # Each entity controls 2 to 8 addresses
    addrs = [random_btc_address() for _ in range(random.randint(2, 8))]
    NORMAL_ENTITIES.append(addrs)

ANOMALY_ENTITIES = []
for _ in range(10): # 10 anomalous entities doing the layering
    addrs = [random_btc_address() for _ in range(random.randint(5, 15))]
    ANOMALY_ENTITIES.append(addrs)

SUSPICIOUS_SRC_IPS = [
    "185.220.101.42",
    "185.220.101.55",
    "91.219.237.99",
    "193.56.28.103",
]
ANOMALY_AMOUNTS = [0.001, 0.002, 0.005, 0.0001, 0.0005]


# ---------------------------------------------------------------------------
# Transaction Generators
# ---------------------------------------------------------------------------

def random_timestamp() -> str:
    delta = END_TIME - START_TIME
    offset = random.random() * delta.total_seconds()
    ts = START_TIME + timedelta(seconds=offset)
    return ts.strftime("%Y-%m-%d %H:%M:%S")

def random_txid() -> str:
    return fake.sha256()

def get_country(ip: str, reader: geoip2.database.Reader) -> str:
    try:
        response = reader.country(ip)
        return response.country.iso_code or "Unknown"
    except geoip2.errors.AddressNotFoundError:
        return "Unknown"

def generate_transaction(is_anomaly: bool, reader: geoip2.database.Reader) -> dict:
    if is_anomaly:
        entity = random.choice(ANOMALY_ENTITIES)
        src_ip = random.choice(SUSPICIOUS_SRC_IPS)
        amount = random.choice(ANOMALY_AMOUNTS)
    else:
        entity = random.choice(NORMAL_ENTITIES)
        src_ip = fake.ipv4_public()
        amount = round(random.uniform(0.01, 5.0), 8)
    
    # Co-spend 1 to 4 addresses from the entity's wallet
    num_inputs = min(len(entity), random.randint(1, 4))
    inputs = random.sample(entity, num_inputs)
    
    # Outputs are usually random (sent to others or change address)
    num_outputs = random.randint(1, 3)
    outputs = [random_btc_address() for _ in range(num_outputs)]
    
    # Optional: in anomalies, they sometimes fan out heavily or use same outputs
    if is_anomaly and random.random() < 0.3:
        num_outputs = random.randint(5, 10)
        outputs = [random_btc_address() for _ in range(num_outputs)]

    country = get_country(src_ip, reader)
    
    return {
        "timestamp": random_timestamp(),
        "src_ip": src_ip,
        "dst_ip": fake.ipv4_public(),
        "src_port": random.choice(BITCOIN_PORTS + list(range(49152, 65535))),
        "dst_port": random.choice(BITCOIN_PORTS),
        "txid": random_txid(),
        "input_addresses": "|".join(inputs),
        "output_addresses": "|".join(outputs),
        "amount_btc": amount,
        "geo_country": country,
    }


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def main():
    download_geoip_db()
    
    # Open GeoIP Reader
    with geoip2.database.Reader(MMDB_FILENAME) as reader:
        print(f"[*] Generating {NUM_NORMAL} normal transactions …")
        normal_rows = [generate_transaction(False, reader) for _ in range(NUM_NORMAL)]

        print(f"[*] Injecting {NUM_ANOMALIES} anomalous transactions (layering) …")
        anomaly_rows = [generate_transaction(True, reader) for _ in range(NUM_ANOMALIES)]

    all_rows = normal_rows + anomaly_rows
    random.shuffle(all_rows)

    df = pd.DataFrame(all_rows)
    df.sort_values(by="timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)

    output_path = "bitcoin_traffic.csv"
    df.to_csv(output_path, index=False)

    print(f"\n{'=' * 55}")
    print(f"  Dataset saved to: {output_path}")
    print(f"  Total transactions:   {len(df)}")
    print(f"  Normal transactions:  {NUM_NORMAL}")
    print(f"  Anomalous (5%):       {NUM_ANOMALIES}")
    print(f"  Columns:              {list(df.columns)}")
    print(f"  Date range:           {df['timestamp'].min()}  →  {df['timestamp'].max()}")
    print(f"{'=' * 55}")
    print(f"\n[✓] Done.\n")


if __name__ == "__main__":
    main()

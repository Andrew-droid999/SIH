"""Strict offline ingestion for CLTI CSV, JSON and XML case files."""
from __future__ import annotations
import csv, hashlib, json, xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
NETWORK_FIELDS={"observation_id","observer_id","observed_at","src_ip","src_port","dst_ip","dst_port","txid","asn","geo_country","source_record_id"}
BLOCKCHAIN_FIELDS={"txid","block_time","input_outpoints","input_addresses","input_amounts","output_addresses","output_amounts","fee","script_type","source_record_id"}
SEED_FIELDS={"address","risk_category","confidence","source"}
class DataValidationError(ValueError): pass
@dataclass(frozen=True)
class LoadedRecords:
    records:list[dict[str,Any]]; source_path:str; sha256:str; format:str
def sha256_file(path):
    d=hashlib.sha256()
    with open(path,"rb") as h:
        for chunk in iter(lambda:h.read(1024*1024),b""): d.update(chunk)
    return d.hexdigest()
def _load_csv(p):
    with p.open("r",encoding="utf-8-sig",newline="") as h:return [dict(r) for r in csv.DictReader(h)]
def _load_json(p):
    with p.open("r",encoding="utf-8") as h:x=json.load(h)
    if isinstance(x,dict):x=x.get("records")
    if not isinstance(x,list) or not all(isinstance(r,dict) for r in x):raise DataValidationError("JSON must be an array of objects or {'records': [...]}")
    return [dict(r) for r in x]
def _load_xml(p):
    rows=[{c.tag:(c.text or "").strip() for c in e} for e in ET.parse(p).getroot().findall(".//record")]
    if not rows:raise DataValidationError("XML must contain one or more <record> elements")
    return rows
def load_records(path,kind):
    source=Path(path)
    if not source.is_file():raise FileNotFoundError(source)
    loaders={".csv":_load_csv,".json":_load_json,".xml":_load_xml}; suffix=source.suffix.lower()
    if suffix not in loaders:raise DataValidationError(f"Unsupported format {suffix}; use CSV, JSON or XML")
    rows=loaders[suffix](source)
    if not rows:raise DataValidationError(f"{source.name} contains no records")
    required={"network":NETWORK_FIELDS,"blockchain":BLOCKCHAIN_FIELDS,"seeds":SEED_FIELDS}.get(kind)
    if required is None:raise DataValidationError(f"Unknown record kind: {kind}")
    missing=sorted(required-set(rows[0]))
    if missing:raise DataValidationError(f"{source.name} missing fields: {', '.join(missing)}")
    normal=[_normalise(r,kind,i+1,source.name) for i,r in enumerate(rows)];_validate_unique_ids(normal,kind)
    return LoadedRecords(normal,str(source),sha256_file(source),suffix[1:])
def _tokens(v):
    if v is None or v=="":return []
    if isinstance(v,list):return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v).split("|") if x.strip()]
def _floats(v,field):
    try:values=[float(x) for x in _tokens(v)]
    except ValueError as e:raise DataValidationError(f"Invalid numeric list in {field}: {v}") from e
    if any(x<0 for x in values):raise DataValidationError(f"Negative amount in {field}")
    return values
def _normalise(row,kind,number,source_name):
    out={str(k).strip():v for k,v in row.items()};out.update(_source_file=source_name,_row_number=number)
    if kind=="network":
        for f in ("observation_id","observer_id","txid","src_ip","dst_ip"):out[f]=str(out[f]).strip()
        for f in ("src_port","dst_port"):
            try:out[f]=int(out[f])
            except (TypeError,ValueError) as e:raise DataValidationError(f"Invalid {f} at row {number}") from e
            if not 0<=out[f]<=65535:raise DataValidationError(f"Out-of-range {f} at row {number}")
        out["asn"]=str(out.get("asn","")).strip();out["geo_country"]=str(out.get("geo_country","")).strip().upper()
    elif kind=="blockchain":
        out["txid"]=str(out["txid"]).strip();out["input_outpoints"]=_tokens(out["input_outpoints"]);out["input_addresses"]=_tokens(out["input_addresses"]);out["input_amounts"]=_floats(out["input_amounts"],"input_amounts");out["output_addresses"]=_tokens(out["output_addresses"]);out["output_amounts"]=_floats(out["output_amounts"],"output_amounts")
        try:out["fee"]=float(out["fee"])
        except (TypeError,ValueError) as e:raise DataValidationError(f"Invalid fee at row {number}") from e
        if out["fee"]<0:raise DataValidationError(f"Negative fee at row {number}")
        if len(out["input_addresses"])!=len(out["input_amounts"]):raise DataValidationError(f"Input address/amount count mismatch at row {number}")
        if len(out["output_addresses"])!=len(out["output_amounts"]):raise DataValidationError(f"Output address/amount count mismatch at row {number}")
        if out["input_outpoints"] and len(out["input_outpoints"])!=len(out["input_addresses"]):raise DataValidationError(f"Input outpoint/address count mismatch at row {number}")
        a,b=sum(out["input_amounts"]),sum(out["output_amounts"])
        if a and abs(a-b-out["fee"])>1e-7:raise DataValidationError(f"Value conservation failed at row {number}: inputs={a}, outputs={b}, fee={out['fee']}")
    else:
        out["address"]=str(out["address"]).strip()
        try:out["confidence"]=float(out["confidence"])
        except (TypeError,ValueError) as e:raise DataValidationError(f"Invalid seed confidence at row {number}") from e
        if not 0<=out["confidence"]<=1:raise DataValidationError(f"Seed confidence must be within [0,1] at row {number}")
    return out
def _validate_unique_ids(rows,kind):
    key={"network":"observation_id","blockchain":"txid"}.get(kind)
    if key:
        values=[r[key] for r in rows]
        if len(values)!=len(set(values)):raise DataValidationError(f"Duplicate {key} values detected")

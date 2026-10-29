#!/usr/bin/env python3
"""Retrieve REAL two-horizontal strong-motion accelerations from official SCEDC FDSN.

2019 Ridgecrest or independent 2020 Lone Pine event. THIS IS AN INPUT-QC
DEMONSTRATION, NOT Jiayu site compatible or PEER NGA-West2 RSN authenticated.
Requires numpy, requests, obspy, existing s05_ground_motion_pair_qc.py.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import requests
from obspy import read, read_inventory, UTCDateTime
from s05_ground_motion_pair_qc import inspect

BASES = [
    "https://service.scedc.caltech.edu/fdsnws",
    "https://service.iris.edu/fdsnws",
]
# SCIENCE: event identity independently USGS ci38457511, origin UTC 2019-07-06T03:19:53
# Event origin metadata from USGS/SCEC catalog; data requests are NOT proof of waveform availability.
EVENTS = {
    "ridgecrest2019": {
        "usgs_id": "ci38457511", "event_name": "Ridgecrest", "magnitude_mw": 7.1,
        "event_utc": "2019-07-06T03:19:53Z",
        "start": "2019-07-06T03:19:20", "end": "2019-07-06T03:22:40",
        "stations": ["CLC", "WRC", "WCS", "RVR", "PASC"],
        "catalog": "https://earthquake.usgs.gov/earthquakes/eventpage/ci38457511",
    },
    "lonepine2020": {
        "usgs_id": "ci39493944", "event_name": "Lone_Pine", "magnitude_mw": 5.8,
        "event_utc": "2020-06-24T17:40:49Z",
        "start": "2020-06-24T17:40:20", "end": "2020-06-24T17:43:40",
        "stations": ["CLC", "WRC", "WCS", "RVR", "PASC"],
        "catalog": "https://earthquake.usgs.gov/earthquakes/eventpage/ci39493944",
    },
}
NETWORK = "CI"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def get(service, params, *, timeout=30):
    failures = []
    for base in BASES:
        url = f"{base}/{service}/1/query"
        try:
            r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": "WindTowerResearch-S05/1.0 (academic noncommercial reproducibility)"})
            if r.status_code == 200 and len(r.content) >= 80:
                return r.content, r.url, failures
            failures.append({"url": r.url, "http": r.status_code, "bytes": len(r.content)})
        except requests.RequestException as e:
            failures.append({"url": url, "error": str(e)[:250]})
    raise RuntimeError(f"No official FDSN response for {service}: {failures}")


def get_channel(inv, trace):
    for nw in inv:
        if nw.code != trace.stats.network:
            continue
        for sta in nw:
            if sta.code != trace.stats.station:
                continue
            for ch in sta:
                if ch.code == trace.stats.channel and ch.location_code == trace.stats.location:
                    return ch, sta
    raise ValueError("NO_INVENTORY_CHANNEL " + trace.id)


def normalized_acceleration(trace, inv, ch):
    if abs(float(ch.dip)) > 15:
        raise ValueError("NOT_HORIZONTAL")
    if trace.stats.channel[1] != "N":
        raise ValueError("NOT_ACCELEROMETER_HN")
    response = inv.get_response(trace.id, trace.stats.starttime)
    sens = response.instrument_sensitivity
    unit = sens.input_units.upper().replace(" ", "")
    factors = {
        "M/S**2": 1.0, "M/S^2": 1.0, "M/S/S": 1.0, "M/S2": 1.0,
        "CM/S**2": 0.01, "CM/S^2": 0.01,
    }
    if unit not in factors:
        raise ValueError("UNKNOWN_ACCEL_UNITS " + str(sens.input_units))
    if not math.isfinite(sens.value) or sens.value == 0:
        raise ValueError("BAD_INSTRUMENT_SENSITIVITY")
    values = np.asarray(trace.data, dtype=np.float64) * (factors[unit] / float(sens.value))
    if len(values) < 1000 or not np.isfinite(values).all():
        raise ValueError("INVALID_ACCELERATION")
    # We do NOT detrend, filter, baseline-correct, clip, time-scale or spectrally match the originals.
    return values, {"input_units": sens.input_units, "counts_per_input_unit": float(sens.value), "azimuth_deg": float(ch.azimuth), "dip_deg": float(ch.dip), "sample_rate_Hz": float(trace.stats.sampling_rate)}


def recover(out, station, event_key):
    cfg = EVENTS[event_key]
    begin, end = UTCDateTime(cfg["start"]), UTCDateTime(cfg["end"])
    par = {"net": NETWORK, "sta": station, "loc": "*", "cha": "HN*", "starttime": cfg["start"], "endtime": cfg["end"]}
    sta_data, sta_url, sta_errors = get("station", dict(par, level="response", format="xml"))
    inv = read_inventory(io.BytesIO(sta_data), format="STATIONXML")
    wave_data, wave_url, wave_errors = get("dataselect", par)
    stream = read(io.BytesIO(wave_data), format="MSEED")
    # Select continuous horizontal HN accelerometer channels, reject gaps and clipping later.
    candidates = []
    rejected = []
    for tr in stream:
        try:
            ch, sta = get_channel(inv, tr)
            tr.trim(begin, end, pad=False)
            v, meta = normalized_acceleration(tr, inv, ch)
            if hasattr(tr.data, "mask") and np.any(tr.data.mask):
                raise ValueError("GAP_IN_MSEED")
            candidates.append((tr, v, meta, sta))
        except Exception as e:
            rejected.append({"trace": tr.id, "reason": str(e)})
    candidates.sort(key=lambda c: (-len(c[1]), c[0].id))
    pair = None
    for i, a in enumerate(candidates):
        for b in candidates[i+1:]:
            ta, tb = a[0], b[0]
            if ta.stats.channel == tb.stats.channel:
                continue
            az_diff = abs((a[2]["azimuth_deg"] - b[2]["azimuth_deg"]) % 180)
            if min(az_diff, 180 - az_diff) < 65:
                continue
            if abs(float(ta.stats.delta) - float(tb.stats.delta)) > 1e-9:
                continue
            ta0, tb0 = ta.stats.starttime, tb.stats.starttime
            t0 = max(ta0, tb0)
            t1 = min(ta.stats.endtime, tb.stats.endtime)
            dt = float(ta.stats.delta)
            n = int((t1 - t0) / dt + 0.5) + 1
            if n < 1000:
                continue
            ia, ib = int(round((t0-ta0)/dt)), int(round((t0-tb0)/dt))
            if abs((ta0+ia*dt)-t0) > dt*0.0001 or abs((tb0+ib*dt)-t0) > dt*0.0001:
                continue
            aa, bb = a[1][ia:ia+n], b[1][ib:ib+n]
            if len(aa) != n or len(bb) != n:
                continue
            pair = (a, b, aa, bb, str(t0), dt)
            break
        if pair:
            break
    if pair is None:
        raise ValueError("NO_COMPLETE_COPLANAR_PAIR " + str(rejected))
    a, b, aa, bb, iso, dt = pair
    out.mkdir(parents=True, exist_ok=True)
    rawdir = out / "original"
    rawdir.mkdir(exist_ok=True)
    (rawdir / "CI_station_response.xml").write_bytes(sta_data)
    (rawdir / "CI_waveform_counts.mseed").write_bytes(wave_data)
    meta_pair = []
    for item, values in [(a, aa), (b, bb)]:
        tr, _, meta, sta = item
        filename = "CI_" + station + "_" + tr.stats.channel + "_accel_mps2.csv"
        p = out / filename
        with p.open("w", encoding="utf-8", newline="") as fd:
            w = csv.writer(fd, lineterminator="\n")
            w.writerow(["time_s", "accel"])
            for i, x in enumerate(values):
                w.writerow([f"{i*dt:.8f}", f"{float(x):.12g}"])
        meta_pair.append({
            "file": filename, "sha256": digest(p.read_bytes()), "rsn": "NOT_PEER_RSN",
            "event": "USGS_" + cfg["usgs_id"] + "_" + cfg["event_name"], "station": "CI." + station, "component": tr.stats.channel,
            "unit": "m/s2", "dt_s": dt,
        })
    m = {
        "source_database": "SCEDC_or_EarthScope_official_FDSN_raw_MSEED",
        "source_accession": "USGS:" + cfg["usgs_id"] + ";FDSN:CI." + station + ":HN*:" + cfg["event_utc"][:10],
        "damping_ratio": 0.05,
        "periods_s": [0.1,0.2,0.4,0.6,0.8,1.0,1.5,2.0,3.0,4.0,6.0,8.0,10.0],
        "horizontal_components": meta_pair,
    }
    mp = out / "manifest.json"
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    qc = inspect(mp)
    (out / "pair_qc.json").write_text(json.dumps(qc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary = {
        "input_type":"REAL_RECORDED_GROUND_ACCELERATION_OFFICIAL_STATION_PILOT_NOT_SITE_MATCHED",
        "source_record_is_not_peer_nga_rsn":True,
        "event_catalog":cfg["catalog"], "event_utc":cfg["event_utc"],
        "event_id":cfg["usgs_id"], "event_key":event_key, "event_magnitude_mw":cfg["magnitude_mw"],
        "station_network":NETWORK, "station":station,
        "station_latitude":sta.latitude, "station_longitude":sta.longitude,
        "station_elevation_m":sta.elevation,
        "official_stationxml_url":sta_url,
        "official_mseed_url":wave_url,
        "stationxml_sha256": digest(sta_data),
        "raw_mseed_sha256": digest(wave_data),
        "raw_mseed_bytes":len(wave_data),
        "stationxml_bytes":len(sta_data),
        "window_request_utc":[cfg["start"],cfg["end"]],
        "common_start_utc":iso, "common_npts":len(aa), "common_dt_s":dt,
        "channels":[
            {"seed_id":item[0].id, **item[2], "csv":m0["file"],"csv_sha256":m0["sha256"],"pga_g":v["pga_g"]}
            for item,m0,v in zip([a,b],meta_pair,qc["components"])
        ],
        "software":{"python":sys.version.split()[0],"obspy":__import__("obspy").__version__,"numpy":np.__version__},
        "station_errors":sta_errors,"wave_errors":wave_errors,
        "rejected_channels":rejected,
        "npts_matches":len(aa)==len(bb),
        "source_is_window_not_complete_earthquake_record":True,
        "raw_counts_instrument_sensitivity_only_no_baseline_correction":True,
        "reliability_flags":{
            "usable_low_frequency_not_verified":True,
            "site_target_spectrum_not_available":True,
            "Jiayu_site_class_geotechnical_not_verified":True,
            "site_match_PASS":False,
            "PEER_RSN_verified":False,
            "Abaqus_RUN":False,
            "S05_PASS":False,
        },
        "files_SHA256":{},
    }
    for p in sorted(out.rglob("*")):
        if p.is_file():
            summary["files_SHA256"][str(p.relative_to(out))]=digest(p.read_bytes())
    (out / "source_receipt.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("REAL_FDSN_PAIR_QC_CREATED",station,"NPTS",len(aa),"DT",dt,"PGA_g",[v["pga_g"] for v in qc["components"]],flush=True)
    return summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--station",default="")
    ap.add_argument("--event",choices=sorted(EVENTS),default="ridgecrest2019")
    args=ap.parse_args()
    stations=[args.station] if args.station else EVENTS[args.event]["stations"]
    failures=[]
    for station in stations:
        try:
            recover(pathlib.Path(args.output_dir),station,args.event)
            return
        except Exception as e:
            print("OFFICIAL_STATION_NOT_USABLE",station,repr(e),flush=True)
            failures.append({"station":station,"error":str(e)[:600]})
    out=pathlib.Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    (out/"recovery_failures.json").write_text(json.dumps({"status":"HOLD_NO_REAL_PAIR","attempts":failures,"event":EVENTS[args.event],"earthquake_RUN":0},indent=2)+"\n")
    raise SystemExit("NO_OFFICIAL_REAL_ACCELERATION_PAIR; reasons saved in recovery_failures.json")

if __name__=="__main__":
    main()

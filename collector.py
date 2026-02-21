"""collector.py - Wi-Fi環境ベンチマーク 計測・記録エンジン"""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import speedtest as speedtest_module

DEFAULT_COUNT = 3
DEFAULT_INTERVAL = 10
JST = timezone(timedelta(hours=9))
AIRPORT_CMD = (
    "/System/Library/PrivateFrameworks/Apple80211.framework"
    "/Versions/Current/Resources/airport"
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Wi-Fi環境ベンチマーク 計測エンジン")
    parser.add_argument(
        "--ssids", nargs="+", required=True, help="計測対象のSSIDリスト"
    )
    parser.add_argument(
        "--count", type=int, default=DEFAULT_COUNT, help="1SSIDあたりの計測回数"
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL, help="SSID切り替え後の安定待機秒数"
    )
    return parser.parse_args(argv)


def get_current_ssid(interface="en0"):
    result = subprocess.run(
        ["networksetup", "-getairportnetwork", interface],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"networksetup failed: {result.stdout.strip()}")
    output = result.stdout.strip()
    prefix = "Current Wi-Fi Network: "
    if not output.startswith(prefix):
        raise RuntimeError(f"Not associated with any network: {output}")
    return output[len(prefix):]


def get_physical_metrics():
    import re
    result = subprocess.run(
        [AIRPORT_CMD, "-I"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"airport command failed: {result.stdout.strip()}")
    output = result.stdout

    def _parse(pattern):
        m = re.search(pattern, output)
        return int(m.group(1)) if m else None

    return {
        "rssi":      _parse(r"agrCtlRSSI:\s*(-?\d+)"),
        "noise":     _parse(r"agrCtlNoise:\s*(-?\d+)"),
        "mcs_index": _parse(r"\bMCS:\s*(\d+)"),
    }


def run_speedtest():
    try:
        st = speedtest_module.Speedtest()
        st.get_best_server()
        st.download()
        st.upload()
        result = st.results.dict()
    except Exception as e:
        raise RuntimeError(f"speedtest failed: {e}") from e
    return {
        "download_mbps": round(result["download"] / 1_000_000, 1),
        "upload_mbps":   round(result["upload"]   / 1_000_000, 1),
        "ping_ms":       result["ping"],
    }


def build_record(ssid, physical_metrics, speed_metrics):
    return {
        "timestamp": datetime.now(JST).isoformat(),
        "ssid": ssid,
        **physical_metrics,
        **speed_metrics,
    }


def append_log(record, log_path):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def switch_ssid(ssid, interface="en0", wait_sec=0):
    pass

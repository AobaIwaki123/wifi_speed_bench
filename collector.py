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
AIRPORT_CMD = ["system_profiler", "SPAirPortDataType"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Wi-Fi環境ベンチマーク 計測エンジン")
    parser.add_argument(
        "--ssids", nargs="+", required=True, help="計測対象のSSIDリスト"
    )
    parser.add_argument(
        "--count", type=int, default=DEFAULT_COUNT, help="1SSIDあたりの計測回数"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help="SSID切り替え後の安定待機秒数",
    )
    return parser.parse_args(argv)


def get_physical_metrics():
    import re

    result = subprocess.run(AIRPORT_CMD, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"system_profiler failed: {result.stdout.strip()}")
    output = result.stdout

    def _parse_int(pattern):
        m = re.search(pattern, output)
        return int(m.group(1)) if m else None

    # Signal / Noise: -57 dBm / -101 dBm
    rssi = _parse_int(r"Signal / Noise:\s*(-?\d+)\s*dBm")
    noise = _parse_int(r"Signal / Noise:\s*-?\d+\s*dBm\s*/\s*(-?\d+)\s*dBm")
    mcs = _parse_int(r"MCS Index:\s*(\d+)")

    # Channel: 140 (5GHz, 20MHz)
    ch_m = re.search(r"Channel:\s*(\d+)\s*\(([^,)]+)", output)
    channel = int(ch_m.group(1)) if ch_m else None
    if ch_m:
        freq = ch_m.group(2)  # "5GHz" / "2GHz" / "6GHz"
        band = (
            "6GHz"
            if "6GHz" in freq
            else "5GHz"
            if "5GHz" in freq
            else "2.4GHz"
            if "2GHz" in freq
            else None
        )
    else:
        band = None

    return {
        "rssi": rssi,
        "noise": noise,
        "mcs_index": mcs,
        "channel": channel,
        "band": band,
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
        "upload_mbps": round(result["upload"] / 1_000_000, 1),
        "ping_ms": result["ping"],
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


def switch_ssid(ssid, interface="en0", wait_sec=DEFAULT_INTERVAL):
    try:
        result = subprocess.run(
            ["networksetup", "-setairportnetwork", interface, ssid],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"networksetup not found: {e}") from e
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to switch SSID to '{ssid}': {result.stdout.strip()}"
        )
    time.sleep(wait_sec)


DEFAULT_LOG_PATH = Path("logs/benchmark.jsonl")


def main():
    args = parse_args()
    log_path = DEFAULT_LOG_PATH

    total = len(args.ssids) * args.count
    done = 0

    for ssid in args.ssids:
        print(f"\n[→] Switching to SSID: {ssid}")
        try:
            switch_ssid(ssid, wait_sec=args.interval)
        except RuntimeError as e:
            print(f"[ERROR] SSID切り替え失敗、スキップします: {e}")
            continue

        for i in range(1, args.count + 1):
            done += 1
            print(f"[{ssid}  {i}/{args.count}] 計測中... ({done}/{total})")
            try:
                physical = get_physical_metrics()
                speed = run_speedtest()
                record = build_record(ssid, physical, speed)
                append_log(record, log_path)
                print(
                    f"  RSSI:{physical['rssi']} dBm  "
                    f"CH:{physical['channel']}({physical['band']})  "
                    f"MCS:{physical['mcs_index']}  "
                    f"↓{speed['download_mbps']} Mbps  "
                    f"↑{speed['upload_mbps']} Mbps  "
                    f"ping:{speed['ping_ms']} ms"
                )
            except RuntimeError as e:
                print(f"  [WARN] 計測失敗、スキップします: {e}")

    print(f"\n[✓] 完了 — ログ: {log_path.resolve()}")


if __name__ == "__main__":
    main()

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
    pass


def get_physical_metrics():
    pass


def run_speedtest():
    pass


def build_record(ssid, physical_metrics, speed_metrics):
    pass


def append_log(record, log_path):
    pass


def switch_ssid(ssid, interface="en0", wait_sec=0):
    pass

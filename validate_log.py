"""validate_log.py - benchmark.jsonl のバリデーションツール

SSIDとbandの対応マップ (ssid_band_map.json) を参照し、
ログの各レコードが期待値と一致するかを検証する。
"""

import argparse
import json
from pathlib import Path

REQUIRED_FIELDS = [
    "timestamp",
    "ssid",
    "rssi",
    "noise",
    "mcs_index",
    "channel",
    "band",
    "download_mbps",
    "upload_mbps",
    "ping_ms",
]

DEFAULT_LOG_PATH = Path("logs/benchmark.jsonl")
DEFAULT_MAP_PATH = Path("ssid_band_map.json")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="benchmark.jsonl バリデーター")
    parser.add_argument(
        "--log", type=Path, default=DEFAULT_LOG_PATH, help="検証するJSONLログファイル"
    )
    parser.add_argument(
        "--map",
        type=Path,
        default=DEFAULT_MAP_PATH,
        help="SSIDとbandの対応JSONファイル",
    )
    return parser.parse_args(argv)


def load_map(map_path: Path) -> dict:
    with map_path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_record(record: dict, ssid_band_map: dict, line_no: int) -> list[str]:
    """1レコードを検証し、エラーメッセージのリストを返す。"""
    errors = []

    # 必須フィールドの存在確認
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"  [line {line_no}] 必須フィールド欠損: '{field}'")

    if errors:
        return errors  # 以降のチェックはフィールドが揃っている前提

    ssid = record["ssid"]
    actual_band = record["band"]

    # SSIDがマップに存在するか
    if ssid not in ssid_band_map:
        errors.append(f"  [line {line_no}] SSID '{ssid}' がマップに未登録")
    else:
        expected_band = ssid_band_map[ssid]
        if actual_band != expected_band:
            errors.append(
                f"  [line {line_no}] SSID '{ssid}': band不一致 "
                f"(期待: {expected_band}, 実際: {actual_band})"
            )

    # 数値フィールドの型チェック
    for field in ("rssi", "noise", "mcs_index", "channel"):
        if not isinstance(record[field], (int, float)):
            errors.append(
                f"  [line {line_no}] '{field}' が数値でない: {record[field]!r}"
            )

    for field in ("download_mbps", "upload_mbps", "ping_ms"):
        if not isinstance(record[field], (int, float)):
            errors.append(
                f"  [line {line_no}] '{field}' が数値でない: {record[field]!r}"
            )

    return errors


def validate(log_path: Path, ssid_band_map: dict) -> bool:
    """ログ全体を検証する。問題なければ True を返す。"""
    if not log_path.exists():
        print(f"[ERROR] ログファイルが見つかりません: {log_path}")
        return False

    all_errors = []
    total = 0
    ssid_counts: dict[str, int] = {}

    with log_path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(f"  [line {line_no}] JSON解析エラー: {e}")
                continue

            ssid_counts[record.get("ssid", "<unknown>")] = (
                ssid_counts.get(record.get("ssid", "<unknown>"), 0) + 1
            )
            all_errors.extend(validate_record(record, ssid_band_map, line_no))

    print(f"検証対象: {log_path}  ({total} レコード)")
    print("SSID別レコード数:")
    for ssid, count in ssid_counts.items():
        expected_band = ssid_band_map.get(ssid, "?")
        print(f"  {ssid:30s}  {count:>3} 件  (期待band: {expected_band})")

    if all_errors:
        print(f"\n[NG] {len(all_errors)} 件のエラーが見つかりました:")
        for msg in all_errors:
            print(msg)
        return False
    else:
        print(f"\n[OK] 全レコード正常")
        return True


def main():
    args = parse_args()
    try:
        ssid_band_map = load_map(args.map)
    except FileNotFoundError:
        print(f"[ERROR] マップファイルが見つかりません: {args.map}")
        raise SystemExit(1)

    ok = validate(args.log, ssid_band_map)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()

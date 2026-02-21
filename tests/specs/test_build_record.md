# テスト仕様: test_build_record

## 対応する関数
`collector.build_record(ssid, physical_metrics, speed_metrics)`

## 対応するpytestファイル・関数
- ファイル: `tests/test_collector.py`
- 関数:
  - `test_build_record_contains_all_required_fields`
  - `test_build_record_timestamp_format`
  - `test_build_record_ssid_matches_input`

---

## テストケース

### 入力サンプル
```python
ssid = "MyNet_5GHz"
physical_metrics = {"rssi": -55, "noise": -95, "mcs_index": 9}
speed_metrics = {"download_mbps": 412.3, "upload_mbps": 89.1, "ping_ms": 12.4}
```

### 期待するJSONLレコード構造
```json
{
  "timestamp": "2026-02-22T10:00:00+09:00",
  "ssid": "MyNet_5GHz",
  "rssi": -55,
  "noise": -95,
  "mcs_index": 9,
  "download_mbps": 412.3,
  "upload_mbps": 89.1,
  "ping_ms": 12.4
}
```

### 正常系

| #   | テスト関数名                                     | 期待結果                                                               |
| --- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| 1   | `test_build_record_contains_all_required_fields` | 上記8フィールドが全て存在する                                          |
| 2   | `test_build_record_timestamp_format`             | `timestamp` が ISO 8601形式（`datetime.fromisoformat()` でパース可能） |
| 3   | `test_build_record_ssid_matches_input`           | `record["ssid"] == "MyNet_5GHz"`                                       |
| 4   | `test_build_record_metrics_are_merged`           | `physical_metrics` と `speed_metrics` の値が正しく含まれる             |

---

## 備考
- `datetime.now()` はモック化（`freezegun` 等）して決定論的なテストにすること
- `timestamp` はタイムゾーン付き（JST: `+09:00`）で出力すること

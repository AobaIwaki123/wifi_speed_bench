# 追加仕様 (SPEC)

テスト設計フェーズにおいて新たに定めた仕様をまとめる。

---

## collector.py - モジュール構成

| 関数                                                  | 役割                                                       |
| ----------------------------------------------------- | ---------------------------------------------------------- |
| `parse_args(argv)`                                    | CLIの引数を解析して返す                                    |
| `get_current_ssid(interface)`                         | 現在接続中のSSIDを文字列で返す                             |
| `get_physical_metrics()`                              | 物理層メトリクス（RSSI / Noise / MCS）を取得して辞書で返す |
| `run_speedtest()`                                     | speedtestを実行し、速度・pingを辞書で返す                  |
| `build_record(ssid, physical_metrics, speed_metrics)` | 1件分のJSONLレコード（辞書）を構築して返す                 |
| `append_log(record, log_path)`                        | レコードをJSONL形式でファイルに追記する                    |
| `switch_ssid(ssid, interface, wait_sec)`              | SSIDを切り替え、安定待機する                               |

---

## CLIインターフェース

```bash
python collector.py --ssids <SSID1> [SSID2 ...] [--count N] [--interval SEC]
```

| 引数         | 型              | デフォルト | 説明                         |
| ------------ | --------------- | ---------- | ---------------------------- |
| `--ssids`    | `str` (1つ以上) | 必須       | 計測対象のSSIDリスト         |
| `--count`    | `int`           | `3`        | 1SSIDあたりの計測回数        |
| `--interval` | `int`           | `10`       | SSID切り替え後の安定待機秒数 |

---

## データ仕様

### 速度の単位変換
- `speedtest-cli` の出力（bps）を Mbps に変換して記録する
- 変換式: `Mbps = bps ÷ 1_000_000`（小数第1位で丸め）

### タイムスタンプ
- ISO 8601形式、タイムゾーン付き（JST: `+09:00`）
- 例: `2026-02-22T10:00:00+09:00`

### ログ未存在時の動作
- `logs/` ディレクトリが存在しない場合は自動作成する
- ログファイルが存在しない場合は新規作成する（追記モード）

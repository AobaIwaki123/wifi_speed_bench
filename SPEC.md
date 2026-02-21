# 追加仕様 (SPEC)

テスト設計フェーズにおいて新たに定めた仕様をまとめる。

---

## collector.py - モジュール構成

| 関数                                                  | 役割                                                                        |
| ----------------------------------------------------- | --------------------------------------------------------------------------- |
| `parse_args(argv)`                                    | CLIの引数を解析して返す                                                     |
| `get_physical_metrics()`                              | 物理層メトリクス（RSSI / Noise / MCS / Channel / Band）を取得して辞書で返す |
| `run_speedtest()`                                     | speedtestを実行し、速度・pingを辞書で返す                                   |
| `build_record(ssid, physical_metrics, speed_metrics)` | 1件分のJSONLレコード（辞書）を構築して返す                                  |
| `append_log(record, log_path)`                        | レコードをJSONL形式でファイルに追記する                                     |
| `switch_ssid(ssid, interface, wait_sec)`              | SSIDを切り替え、安定待機する                                                |

---

## CLIインターフェース

```bash
python collector.py --ssids <SSID1> [SSID2 ...] [--count N] [--interval SEC] [--passwords [PW1 ...]]
```

| 引数          | 型              | デフォルト | 説明                                                                       |
| ------------- | --------------- | ---------- | -------------------------------------------------------------------------- |
| `--ssids`     | `str` (1つ以上) | 必須       | 計測対象のSSIDリスト                                                       |
| `--count`     | `int`           | `3`        | 1SSIDあたりの計測回数                                                      |
| `--interval`  | `int`           | `10`       | SSID切り替え後の安定待機秒数                                               |
| `--passwords` | `str` (0つ以上) | `[]`       | SSIDに対応するパスワードリスト（`--ssids` と同順。不足分は最後の値を複製） |

---

## データ仕様

### 物理層メトリクス
| フィールド  | 取得元                          | 備考                             |
| ----------- | ------------------------------- | -------------------------------- |
| `rssi`      | `Signal / Noise` の前半値 (dBm) | 負の整数                         |
| `noise`     | `Signal / Noise` の後半値 (dBm) | 負の整数                         |
| `mcs_index` | `MCS Index`                     | 0以上の整数                      |
| `channel`   | `Channel`                       | チャンネル番号（正の整数）       |
| `band`      | `Channel` の括弧内              | `"2.4GHz"` / `"5GHz"` / `"6GHz"` |

> **Note**: macOS 14以降、Location Services の制限によりSSIDはredactされるため取得不可。
> `main()` はCLI引数で指定したSSID文字列をそのままログの `ssid` フィールドに記録する。
> 帯域の識別は `band` フィールド（`system_profiler` 経由で取得）で行う。

### 速度の単位変換
- `speedtest-cli` の出力（bps）を Mbps に変換して記録する
- 変換式: `Mbps = bps ÷ 1_000_000`（小数第1位で丸め）

### タイムスタンプ
- ISO 8601形式、タイムゾーン付き（JST: `+09:00`）
- 例: `2026-02-22T10:00:00+09:00`

### ログ未存在時の動作
- `logs/` ディレクトリが存在しない場合は自動作成する
- ログファイルが存在しない場合は新規作成する（追記モード）

# 実行例

```bash
# パスワードなし（オープンネットワーク）
python collector.py --ssids ShareHaimu-2.4G-iii ShareHaimu-5G-iii --count 5 --interval 20

# 全SSIDで同じパスワードを使用（1つ指定すれば全SSIDに複製される）
python collector.py --ssids ShareHaimu-2.4G-iii ShareHaimu-5G-iii --count 5 --interval 20 --passwords mypassword

# SSIDごとに異なるパスワードを指定
python collector.py --ssids ShareHaimu-2.4G-iii ShareHaimu-5G-iii --count 5 --interval 20 --passwords pass_2g pass_5g

# 一部のSSIDにのみパスワードを指定（不足分は最後の値を複製）
python collector.py --ssids SSID_A SSID_B SSID_C --count 3 --passwords pass_a pass_bc
```
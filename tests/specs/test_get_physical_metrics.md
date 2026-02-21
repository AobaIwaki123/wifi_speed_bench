# テスト仕様: test_get_physical_metrics

## 対応する関数
`collector.get_physical_metrics()`

## 対応するpytestファイル・関数
- ファイル: `tests/test_collector.py`
- 関数:
  - `test_get_physical_metrics_returns_expected_keys`
  - `test_get_physical_metrics_parses_rssi`
  - `test_get_physical_metrics_parses_noise`
  - `test_get_physical_metrics_parses_mcs_index`
  - `test_get_physical_metrics_when_command_fails`

---

## テストケース

### 正常系

`system_profiler SPAirPortDataType` の出力サンプル（モック用）:
```
Wi-Fi:

      Interfaces:
        en0:
          Status: Connected
          Current Network Information:
            MyNet_5GHz:
              PHY Mode: 802.11ax
              Channel: 100 (5GHz, 80MHz)
              Signal / Noise: -55 dBm / -95 dBm
              Transmit Rate: 780
              MCS Index: 9
```

| #   | テスト関数名                                      | 期待結果                                              |
| --- | ------------------------------------------------- | ----------------------------------------------------- |
| 1   | `test_get_physical_metrics_returns_expected_keys` | `{"rssi", "noise", "mcs_index"}` のキーが全て存在する |
| 2   | `test_get_physical_metrics_parses_rssi`           | `rssi == -55`                                         |
| 3   | `test_get_physical_metrics_parses_noise`          | `noise == -95`                                        |
| 4   | `test_get_physical_metrics_parses_mcs_index`      | `mcs_index == 9`                                      |

### 異常系

| #   | テスト関数名                                   | 入力（モック戻り値） | 期待結果                       |
| --- | ---------------------------------------------- | -------------------- | ------------------------------ |
| 5   | `test_get_physical_metrics_when_command_fails` | `returncode=1`       | `RuntimeError` が raise される |
| 6   | `test_get_physical_metrics_missing_field`      | MCS行が欠落した出力  | 欠落フィールドが `None` になる |

---

## 使用コマンド
```bash
system_profiler SPAirPortDataType
```

> **Note**: macOS 15以降で `airport` コマンドが廃止されたため `system_profiler` を使用する。

## 備考
- `subprocess` をモック化してOS依存を排除すること
- 各フィールドは正規表現またはスペース区切りでパースする

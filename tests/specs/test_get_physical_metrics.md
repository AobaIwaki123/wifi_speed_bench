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

`airport -I` の出力サンプル（モック用）:
```
     agrCtlRSSI: -55
     agrExtRSSI: 0
    agrCtlNoise: -95
    agrExtNoise: 0
          state: running
        op mode: station
     lastTxRate: 780
        maxRate: 780
lastAssocStatus: 0
    802.11 auth: open
      link auth: wpa2-psk
          BSSID: xx:xx:xx:xx:xx:xx
           SSID: MyNet_5GHz
            MCS: 9
        channel: 100,80
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
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I
```

## 備考
- `subprocess` をモック化してOS依存を排除すること
- 各フィールドは正規表現またはスペース区切りでパースする

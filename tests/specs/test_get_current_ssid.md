# テスト仕様: test_get_current_ssid

## 対応する関数
`collector.get_current_ssid()`

## 対応するpytestファイル・関数
- ファイル: `tests/test_collector.py`
- 関数:
  - `test_get_current_ssid_returns_string`
  - `test_get_current_ssid_when_disconnected_raises_error`

---

## テストケース

### 正常系

| #   | テスト関数名                           | モック対象       | 入力（モック戻り値）                  | 期待結果              |
| --- | -------------------------------------- | ---------------- | ------------------------------------- | --------------------- |
| 1   | `test_get_current_ssid_returns_string` | `subprocess.run` | `"Current Wi-Fi Network: MyNet_5GHz"` | `"MyNet_5GHz"` が返る |

### 異常系

| #   | テスト関数名                                           | モック対象       | 入力（モック戻り値）                                | 期待結果                       |
| --- | ------------------------------------------------------ | ---------------- | --------------------------------------------------- | ------------------------------ |
| 2   | `test_get_current_ssid_when_disconnected_raises_error` | `subprocess.run` | `"You are not associated with an AirPort network."` | `RuntimeError` が raise される |
| 3   | `test_get_current_ssid_when_command_fails`             | `subprocess.run` | `returncode=1`                                      | `RuntimeError` が raise される |

---

## 使用コマンド
```bash
networksetup -getairportnetwork en0
```

## 備考
- `subprocess` をモック化してOS依存を排除すること
- インターフェース名 `en0` はデフォルト値として関数引数で上書き可能にすることが望ましい

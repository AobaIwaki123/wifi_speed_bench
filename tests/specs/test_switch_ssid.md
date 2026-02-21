# テスト仕様: test_switch_ssid

## 対応する関数
`collector.switch_ssid(ssid, interface, wait_sec)`

## 対応するpytestファイル・関数
- ファイル: `tests/test_collector.py`
- 関数:
  - `test_switch_ssid_calls_correct_command`
  - `test_switch_ssid_waits_after_switch`
  - `test_switch_ssid_raises_on_unknown_ssid`

---

## テストケース

### 正常系

| #   | テスト関数名                               | モック対象       | 確認内容                                                    |
| --- | ------------------------------------------ | ---------------- | ----------------------------------------------------------- |
| 1   | `test_switch_ssid_calls_correct_command`   | `subprocess.run` | `networksetup -setairportnetwork en0 MyNet_5GHz` が呼ばれる |
| 2   | `test_switch_ssid_waits_after_switch`      | `time.sleep`     | `sleep(wait_sec)` が1回呼ばれる                             |
| 3   | `test_switch_ssid_default_wait_is_nonzero` | `time.sleep`     | デフォルトの `wait_sec` が `> 0`                            |

### 異常系

| #   | テスト関数名                                   | モック対象       | 入力（モック戻り値）         | 期待結果                       |
| --- | ---------------------------------------------- | ---------------- | ---------------------------- | ------------------------------ |
| 4   | `test_switch_ssid_raises_on_unknown_ssid`      | `subprocess.run` | `returncode=4`（未知のSSID） | `RuntimeError` が raise される |
| 5   | `test_switch_ssid_raises_on_command_not_found` | `subprocess.run` | `FileNotFoundError`          | `RuntimeError` が raise される |

---

## 使用コマンド
```bash
networksetup -setairportnetwork <interface> <ssid>
```

## 備考
- `subprocess` と `time.sleep` の両方をモック化してOS依存・待ち時間を排除すること
- `networksetup` は保存済みのSSIDプロファイルのみ切り替え可能（パスワード不要）
- `wait_sec` のデフォルト値は10秒程度を推奨

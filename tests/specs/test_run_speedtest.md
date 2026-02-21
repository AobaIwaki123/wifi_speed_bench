# テスト仕様: test_run_speedtest

## 対応する関数
`collector.run_speedtest()`

## 対応するpytestファイル・関数
- ファイル: `tests/test_collector.py`
- 関数:
  - `test_run_speedtest_returns_expected_keys`
  - `test_run_speedtest_values_are_positive`
  - `test_run_speedtest_on_network_error`

---

## テストケース

### 正常系

`speedtest-cli --json` の出力サンプル（モック用）:
```json
{
  "download": 432399360.0,
  "upload": 93478912.0,
  "ping": 12.4,
  "server": {"name": "Tokyo"},
  "timestamp": "2026-02-22T10:00:00Z"
}
```

| #   | テスト関数名                               | 期待結果                                                           |
| --- | ------------------------------------------ | ------------------------------------------------------------------ |
| 1   | `test_run_speedtest_returns_expected_keys` | `{"download_mbps", "upload_mbps", "ping_ms"}` のキーが全て存在する |
| 2   | `test_run_speedtest_converts_to_mbps`      | `download_mbps == 432.4`（bps → Mbps 変換確認）                    |
| 3   | `test_run_speedtest_values_are_positive`   | 全ての値が `> 0`                                                   |

### 異常系

| #   | テスト関数名                          | モック内容                                      | 期待結果                       |
| --- | ------------------------------------- | ----------------------------------------------- | ------------------------------ |
| 4   | `test_run_speedtest_on_network_error` | `speedtest.Speedtest()` が `Exception` を raise | `RuntimeError` が raise される |

---

## 備考
- `speedtest.Speedtest()` をモック化して実際の通信を行わないこと
- ダウンロード速度の単位変換: bps ÷ 1_000_000 = Mbps（小数第1位で丸め）

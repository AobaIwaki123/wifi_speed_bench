# テスト仕様: test_parse_args

## 対応する関数
`collector.parse_args()`

## 対応するpytestファイル・関数
- ファイル: `tests/test_collector.py`
- 関数:
  - `test_parse_args_with_valid_ssids`
  - `test_parse_args_default_count`
  - `test_parse_args_default_interval`
  - `test_parse_args_missing_ssids_raises_error`

---

## テストケース

### 正常系

| #   | テスト関数名                       | 入力                      | 期待結果                              |
| --- | ---------------------------------- | ------------------------- | ------------------------------------- |
| 1   | `test_parse_args_with_valid_ssids` | `--ssids A B`             | `args.ssids == ["A", "B"]`            |
| 2   | `test_parse_args_default_count`    | `--ssids A` のみ          | `args.count == 3`（デフォルト値）     |
| 3   | `test_parse_args_default_interval` | `--ssids A` のみ          | `args.interval == 10`（デフォルト値） |
| 4   | `test_parse_args_custom_count`     | `--ssids A --count 5`     | `args.count == 5`                     |
| 5   | `test_parse_args_custom_interval`  | `--ssids A --interval 30` | `args.interval == 30`                 |

### 異常系

| #   | テスト関数名                                 | 入力     | 期待結果                     |
| --- | -------------------------------------------- | -------- | ---------------------------- |
| 6   | `test_parse_args_missing_ssids_raises_error` | 引数なし | `SystemExit` が raise される |

---

## 備考
- `argparse` の `parse_known_args` ではなく `parse_args` を使うこと
- `--count`, `--interval` は `int` 型で受け取ること

# テスト仕様: test_append_log

## 対応する関数
`collector.append_log(record, log_path)`

## 対応するpytestファイル・関数
- ファイル: `tests/test_collector.py`
- 関数:
  - `test_append_log_creates_file_if_not_exists`
  - `test_append_log_writes_valid_json`
  - `test_append_log_appends_multiple_records`
  - `test_append_log_creates_directory_if_not_exists`

---

## テストケース

### 正常系

| #   | テスト関数名                                      | 前提条件                         | 期待結果                                         |
| --- | ------------------------------------------------- | -------------------------------- | ------------------------------------------------ |
| 1   | `test_append_log_creates_file_if_not_exists`      | ファイルが存在しない             | ファイルが新規作成される                         |
| 2   | `test_append_log_writes_valid_json`               | 任意のレコード                   | 書き込まれた行が `json.loads()` でパース可能     |
| 3   | `test_append_log_appends_multiple_records`        | 2回呼び出し                      | ファイルに2行存在する                            |
| 4   | `test_append_log_creates_directory_if_not_exists` | `logs/` ディレクトリが存在しない | ディレクトリが自動作成されファイルが書き込まれる |

### 異常系

| #   | テスト関数名                       | 前提条件                     | 期待結果                          |
| --- | ---------------------------------- | ---------------------------- | --------------------------------- |
| 5   | `test_append_log_permission_error` | ファイルの書き込み権限がない | `PermissionError` が raise される |

---

## 備考
- `tmp_path` (pytest fixture) を使って一時ディレクトリにログを書き込み、テスト後に自動クリーンアップすること
- 1レコード = 1行（改行で区切られたJSONL形式）であることを確認すること

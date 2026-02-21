# 開発環境

- conda: 25.11.1
  - env: wifi-bench
- Python: 3.13
- 主要ライブラリ
  - speedtest-cli
  - matplotlib
  - pandas
  - numpy
  
# テスト設計

`tests/specs`に、テスト計画を記載したMarkdownファイルを配置しています。各テスト関数に対応するテストケースや期待結果を明確に定義しています。これにより、テストの網羅性と品質を確保し、将来的なコード変更に対してもテストが有効であることを保証します。

# Macの制限

1. `airport`はdeprecatedされた
2. SSIDはプライバシーの問題で`sudo`なしでは取得できない。帯域を取り、ログに残すことで後から分析できるようにする。
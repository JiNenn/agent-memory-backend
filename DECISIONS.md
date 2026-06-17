# 設計判断ログ

## 000. MySQL を memory の正本にし、VectorDB は検索 index に限定する

- 日付: 2026-06-17
- 状態: 採用
- 背景: VectorDB は semantic search に向いているが、memory 本体の完全性・更新履歴・失敗時の再処理を担わせるには責務が広すぎる。
- 判断: memory 本体は MySQL に保存し、VectorDB は検索用の派生 index として扱う。
- 影響: VectorDB への反映に失敗しても、正本である MySQL から再処理できる。一方で検索結果から MySQL を引き直す処理が必要になる。
- 記事価値: 高い。VectorDB を便利な保存先ではなく index として扱う設計の意味を説明しやすい。


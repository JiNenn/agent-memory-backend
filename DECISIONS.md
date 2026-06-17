# 設計判断ログ

## 000. MySQL を memory の正本にし、VectorDB は検索 index に限定する

- 日付: 2026-06-17
- 状態: 採用
- 背景: VectorDB は semantic search に向いているが、memory 本体の完全性・更新履歴・失敗時の再処理を担わせるには責務が広すぎる。
- 判断: memory 本体は MySQL に保存し、VectorDB は検索用の派生 index として扱う。
- 影響: VectorDB への反映に失敗しても、正本である MySQL から再処理できる。一方で検索結果から MySQL を引き直す処理が必要になる。
- 記事価値: 高い。VectorDB を便利な保存先ではなく index として扱う設計の意味を説明しやすい。

## 001. schema migration は後続に回し、初期実装は SQLAlchemy の create_all にする

- 日付: 2026-06-17
- 状態: 採用
- 背景: 最初の読者向けコミットでは、outbox と worker の流れを見やすくしたい。
- 判断: 起動時に `Base.metadata.create_all()` を実行する。Alembic は schema が固まってから追加する。
- 影響: 本番相当の migration 検証はまだできない。
- 記事価値: 中。小さく始める代わりに、どこから migration が必要になるかを後続記事の論点にできる。

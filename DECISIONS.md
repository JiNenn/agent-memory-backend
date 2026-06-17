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

## 002. API は MySQL 保存までを同期処理に限定する

- 日付: 2026-06-17
- 状態: 採用
- 背景: API が MySQL と VectorDB に同時書き込みすると、片方だけ成功する dual-write 問題が起きる。
- 判断: API は MySQL transaction 内で `memories` と `outbox_events` を保存するところまでを担当する。
- 影響: API レスポンスは非同期処理の受付完了になり、VectorDB 反映状態は task API で確認する。
- 記事価値: 高い。Outbox Pattern を採用する動機を実装前に示せる。

## 003. 初期 embedding は外部 API ではなく決定的なローカル実装にする

- 日付: 2026-06-17
- 状態: 採用
- 背景: 今回の目的は LLM アプリ構築ではなく、memory の保存・非同期反映・検索 index の責務分離を検証すること。
- 判断: 文字 n-gram を hashing して固定長ベクトルを作る簡易 embedding を使う。
- 影響: 検索品質は限定的だが、Docker Compose だけで再現できる。後続で OpenAI などの embedding provider に差し替えやすい。
- 記事価値: 中。外部 AI 依存を外してアーキテクチャの検証範囲を狭める判断として説明しやすい。

## 004. 検索結果は VectorDB から得た ID で MySQL を引き直す

- 日付: 2026-06-17
- 状態: 採用
- 背景: VectorDB を memory の正本にしないため、payload だけで API レスポンスを組み立てると正本とずれる可能性がある。
- 判断: VectorDB は memory id と score を返す index として使い、本文や metadata は MySQL から取得する。
- 影響: 検索 API は VectorDB と MySQL の両方に触る。削除済み・未反映の index があっても MySQL 側で落とせる。
- 記事価値: 高い。VectorDB を正本にしない設計が API 実装にどう表れるかを示せる。

## 005. 初期実装では Redis Queue を使わず DB polling にする

- 日付: 2026-06-17
- 状態: 採用
- 背景: outbox pattern の効果を検証する段階では、Queue を追加すると失敗箇所と観察対象が増える。
- 判断: `outbox_events` を worker が直接 polling する。Redis Queue は後続で比較検証する。
- 影響: Compose の初期構成は `api` / `worker` / `mysql` / `qdrant` に絞る。
- 記事価値: 高い。Redis Queue が本当に必要かを、実装後に比較する軸を作れる。

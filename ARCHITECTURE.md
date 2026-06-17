# Agent Memory Backend：設計メモ

## 1. 目的

AI Agent の会話履歴や長期記憶を保存し，あとから意味検索できる Memory Backend を小さく実装する。

主な目的は，LLM アプリそのものを作ることではなく，Memory を安定して保存・検索するためのバックエンド構成を検証することである。

## 2. 基本構成

基本構成は以下とする。

```text
Client
  ↓
FastAPI
  ↓
MySQL
  ↓
Outbox Events
  ↓
Queue / Worker
  ↓
Embedding
  ↓
VectorDB
```

各コンポーネントの責務は以下。

| コンポーネント        | 役割                                     |
| -------------- | -------------------------------------- |
| FastAPI        | API リクエストを受ける                          |
| MySQL          | memory，message，outbox_event などの正本を保存する |
| Queue          | Worker に処理を渡す                          |
| Worker         | embedding 生成と VectorDB 反映を行う           |
| VectorDB       | semantic search 用のベクトルを保存する            |
| Docker Compose | ローカル再現環境を作る                            |

## 3. データ保存方針

Memory の正本は MySQL に保存する。

VectorDB は検索用 index として扱い，memory 本体の正本にはしない。

```text
MySQL
  = memory の正本

VectorDB
  = semantic search 用 index
```

この方針により，VectorDB への反映に失敗しても，memory 本体は MySQL に残る。

## 4. Outbox Pattern

API 内では MySQL と VectorDB に直接同時書き込みしない。

理由は，片方だけ成功し，片方だけ失敗する dual-write 問題を避けるためである。

採用する流れは以下。

```text
POST /memories
  ↓
MySQL transaction
  ├── memories に保存
  └── outbox_events に保存
  ↓
API は受付完了を返す
```

この段階では，API の責務を MySQL への保存までに限定する。

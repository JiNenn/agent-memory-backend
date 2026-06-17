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

初期実装では，Queue は Redis ではなく MySQL の outbox_events を Worker が polling する形にする。

理由は，最初に検証したい対象が「MySQL を正本にし，VectorDB を検索 index として非同期反映する構成」だからである。Redis Queue は後続で追加し，DB polling と比較する。

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

outbox_event の状態は以下とする。

```text
pending
processing
completed
failed
```

Worker 実装で検証する論点は以下。

| 論点          | 内容                                   |
| ----------- | ------------------------------------ |
| retry       | 一時的な失敗を再試行する                         |
| retry_count | 失敗回数を保存する                            |
| idempotency | 同じイベントを再実行しても壊れないようにする               |
| failed      | 最大回数を超えたら失敗状態にする                     |
| 二重実行対策      | 複数 Worker が同じ event を処理しても破綻しないようにする |

## 5. Worker の責務

Worker は，重い処理・失敗しやすい処理を担当する。

主な処理は以下。

```text
outbox_event を取得する
embedding を生成する
VectorDB に保存する
処理状態を更新する
失敗したら retry する
```

API の責務は MySQL への保存までとし，VectorDB 反映は Worker に任せる。

## 6. 最小 API

最小実装では，まず以下の API を作る。

| API             | 役割                             |
| --------------- | ------------------------------ |
| POST /memories  | memory を保存し，outbox_event を作成する |
| GET /tasks/{id} | 非同期処理の状態を確認する                  |
| GET /memories/search | VectorDB を使って関連 memory を検索する   |

検索 API は VectorDB から得た memory id を使い，最終的な memory 本体を MySQL から取得する。

この3つで，保存，非同期処理，検索，失敗時の状態確認を検証する。

## 7. 実行環境

実装・検証は Docker Compose で行う。

```text
Docker Compose
  ├── api
  ├── worker
  ├── mysql
  └── vectordb
```

Redis は初期実装では含めない。Queue が必要になる条件を観察してから追加する。

クラウド構成や Kubernetes 移行は，今回の最小設計には含めない。

## 8. 最小到達ライン

最低限，以下が動けばよい。

```text
FastAPI で memory 作成 API を作る
MySQL に memory / outbox_event を保存する
Worker が outbox_event を処理する
embedding を生成する
VectorDB に embedding を保存する
memory search API で関連 memory を取得する
Worker 失敗時の retry を確認する
Docker Compose で再現可能にする
```

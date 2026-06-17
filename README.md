# Agent Memory Backend

AI Agent の memory を MySQL に正本として保存し、outbox worker が embedding を生成して Qdrant に反映する最小実装です。

## 起動

```bash
docker compose up --build
```

API は `http://localhost:8000` で起動します。

## API

### memory を作成する

```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{"content":"ユーザーは Kubernetes の volume permission に関心がある","role":"user"}'
```

レスポンスの `task_id` は outbox event の ID です。

### 非同期処理の状態を見る

```bash
curl http://localhost:8000/tasks/{task_id}
```

### semantic search する

```bash
curl "http://localhost:8000/memories/search?q=Kubernetes%20permission&limit=5"
```

## ローカル開発

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -e ".[dev]"
pytest
```

Docker Compose では MySQL と Qdrant を使います。直接 `uvicorn` で起動する場合は `.env.example` を参考に `DATABASE_URL` と `QDRANT_URL` を設定してください。

Compose の MySQL はホスト側 `3307` に公開しています。ローカルに既存の MySQL がいても衝突しにくくするためです。

# Test Log

各ロジックコミットで実行した最小テストを記録する。

書式:

```text
## コミット名

command:
<実行コマンド>

result:
<短い結果>
```

## memory 保存時に outbox event を作成

command:
`python -m pytest tests/test_memory_service.py`

result:
`1 passed`

## memory 作成 API を追加

command:
`python -m pytest tests/test_api_memories.py`

first result:
`ERROR ModuleNotFoundError: No module named 'pymysql'`

fix:
テスト import 前に `DATABASE_URL=sqlite+pysqlite:///:memory:` を設定した。

result:
`1 passed, 2 warnings`

## task 状態確認 API を追加

command:
`python -m pytest tests/test_api_tasks.py`

result:
`1 passed, 2 warnings`

## hashing embedding を追加

command:
`python -m pytest tests/test_embeddings.py`

result:
`2 passed`

## memory 検索 API を追加

command:
`python -m pytest tests/test_api_search.py`

first result:
`ERROR ModuleNotFoundError: No module named 'qdrant_client'`

fix:
`.venv` を作成して `pip install -e ".[dev]"` を実行した。

command:
`.venv\Scripts\python -m pytest tests/test_api_search.py`

result:
`1 passed, 2 warnings`

## pending outbox event を claim する

command:
`.venv\Scripts\python -m pytest tests/test_outbox_claim.py`

result:
`1 passed`

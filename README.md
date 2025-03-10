### Init python virtaul environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### Measure pip version is up-to-date
```bash
pip install --upgrade pip
```

### If you don’t yet have poetry installed, start by running:
```bash
pip install poetry deepeval starlette
```

### Init poetry
```bash
poetry init
```

### Install dependency
```bash
poetry add "fastapi[standard]" fastcrud pymongo \
confluent-kafka PyPDF2 pinecone pinecone-plugin-assistant \
flask transformers torch pdfkit instructor InstructorEmbedding ollama \
sentence_transformers eval_type_backport pytest pytest-asyncio
```

## Docker Compose
1. From the project root folder, use **docker compose** to start the docker containers.
    ```shell
    docker compose up -d
    ```
2. To terminate all docker containers.
    ```shell
    docker compose down --remove-orphans
    ```
3. To reset data and rebuild all docker containers.
    ```bash
    docker compose down --volumes
    docker compose up -d --build
    ```

### Run the project
```bash
poetry run fastapi run
```

### [Optional] Run local LLM
```bash
deepeval set-local-model --model-name=llama3.1 \
    --base-url="http://localhost:11434/v1/" \
    --api-key="ollama"
```

### Run test cases
```bash
export PYTHONPATH=$(pwd)
pytest /path/<filename>.py
```

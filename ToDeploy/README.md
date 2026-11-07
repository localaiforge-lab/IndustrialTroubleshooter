# LUMEEI AI Mind – deploy package (önálló)

Ez a mappa a **Cloud Run / Docker / helyi** szerver teljes csomagja. A Flutter telefon csak UI + online Hu↔En fordítás; minden nehéz munka itt fut.

```
Telefon  --HTTPS-->  Cloud Run / géped
                       ├─ DistilUSE ONNX
                       ├─ Tananyag index (data/materials)
                       ├─ Web search (DuckDuckGo)
                       └─ Qwen2.5 GGUF (llama.cpp)  ← válaszgenerálás
```

A telefonos MediaPipe `.task` **nem** fut szerveren. Ugyanabból a Qwen2.5-1.5B családból **GGUF** kell (`llama-cpp-python`). Cloud Run **ad CPU-t és RAM-ot** – ajánlott **4–8 vCPU**, **8–16 GiB**, `concurrency=1`.

## Követelmények

| Komponens | Hol van | Megjegyzés |
|-----------|---------|------------|
| FastAPI + uvicorn | `requirements.txt` | HTTP API |
| ONNX Runtime + DistilUSE | `data/embedding/` | Embedding |
| Tananyag corpus | `data/materials/` | RAG |
| Qwen GGUF | `models/*.gguf` | Kötelező a chathez (`llmReady`) |
| llama-cpp-python | `requirements-llm.txt` | Windows: gyakran kell MSVC Build Tools |

## 1) Qwen GGUF letöltése (egyszer)

```bash
cd ToDeploy
mkdir -p models
# ~1.1 GB – Qwen2.5 1.5B Instruct Q4_K_M
wget -O models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
```

Windows PowerShell: töltsd le böngészővel / `Invoke-WebRequest`-tel ugyanerre az útvonalra.

## 2) Futtatás (Linux / géped)

```bash
cd ToDeploy
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-llm.txt   # llama-cpp-python

export LLM_MODEL_PATH="$PWD/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Ellenőrzés:

```bash
curl http://127.0.0.1:8080/health
```

Az üzemi hibakereső böngészőből, ugyanerről a szerverről:

`http://127.0.0.1:8080/plant/`

Ide kerülnek a gyári dokumentumok (PDF, Word, Excel, PowerPoint, szöveg, CSV, zip). A válasz csak a feltöltött anyagból készül. A tudástár a `data/plant_library` mappába íródik; tartós tároláshoz a `PLANT_DIR` mutasson egy megmaradó lemezre. A nyelvi modell nélkül is a talált dokumentumrészt mutatja. Ha a GGUF be van töltve, a választ abból fogalmazza meg.

Várt mezők: `"ok": true`, `"ragReady": true`, `"llmReady": true`.

Flutter `cloudBaseUrl`:

- LAN demó: `http://192.168.x.x:8080` (a gép LAN IP-je, **nem** `127.0.0.1` a telefonról)
- Prod: `https://lumeei-ai-mind-270606217294.europe-west1.run.app`

## 3) Docker / Cloud Run

```bash
# GGUF legyen a models/ mappában a build előtt, VAGY mountold futáskor:
docker build -t lumeei-ai-mind-api .
docker run --rm -p 8080:8080 \
  -e LLM_MODEL_PATH=/app/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -v "$PWD/models:/app/models:ro" \
  lumeei-ai-mind-api
```

Cloud Run javasolt flag-ek: `--cpu 4 --memory 8Gi --concurrency 1 --timeout 300`.

A `Dockerfile` alapból a `LLM_MODEL_PATH=/app/models/qwen2.5-1.5b-instruct-q4_k_m.gguf` útvonalat várja.

## 4) API

| Metódus | Útvonal | Leírás |
|---------|---------|--------|
| `GET` | `/health` | `ok`, `uptimeSec`, `ragReady`, `llmReady`, `books` |
| `GET` | `/v1/books` | Katalógus |
| `POST` | `/v1/translate` | Hu↔En (Firebase / böngésző tesztelő) |
| `POST` | `/v1/chat` | Kérdés → angol válasz |
| `GET` | `/plant/` | Üzemi hibakereső (feltöltés, kérdés, áttekintés) |
| `POST` | `/v1/plant/documents` | Dokumentumok feltöltése |
| `POST` | `/v1/plant/ask` | Kérdés a feltöltött gyári anyagból |

### Fordítás (web tesztelő)

```json
{ "text": "Ki volt Koppány?", "source": "hu", "target": "en" }
```

A Flutter telefon továbbra is helyben fordít; a `/v1/translate` a böngészős `web_tester` / Firebase Hosting kliensnek van (CORS-barát).

### Chat kérés

A kliens **angol** `question`-t küld (fordítás a telefonon vagy `/v1/translate`-en), opcionális `hungarianQuestion` a lexikai boosthoz. A válasz **angol**; a kliens fordítja magyarra.

```json
{
  "question": "What is force in physics?",
  "hungarianQuestion": "Mi az erő a fizikában?",
  "documentId": null
}
```

### Válaszfolyamat (szerver)

1. RAG retrieve (angol embedding + magyar lexical boost)
2. Ha kevés a találat → DuckDuckGo curriculum web search a kontextusba
3. Qwen GGUF generál angol választ a kontextusból
4. Debug mező: találatok, search terms, `web_used`

### Környezeti változók (fontosabbak)

| Változó | Alapértelmezés | Szerep |
|---------|----------------|--------|
| `LLM_MODEL_PATH` | (üres / Docker path) | GGUF fájl |
| `MATERIALS_DIR` | `data/materials` | Tananyag |
| `EMBEDDING_ONNX` | `data/embedding/model.onnx` | DistilUSE |
| `EMBEDDING_VOCAB` | `data/embedding/vocab.txt` | Vocab |
| `LLM_N_CTX` | `1024` | Kontextusablak |
| `LLM_N_THREADS` | `4` | CPU szálak |
| `LLM_MAX_TOKENS` | `256` | Max válasz token |
| `CORS_ORIGINS` | `*` | CORS |
| `PLANT_DIR` | `data/plant_library` | Üzemi tudástár |

## 5) Forrásstruktúra

```
ToDeploy/
  app/
    main.py          # FastAPI: /health, /v1/books, /v1/chat
    config.py        # Settings (env)
    embedder.py      # DistilUSE ONNX
    rag_store.py     # Retrieve
    rag_index.py     # Index építés / betöltés
    web_search.py    # DuckDuckGo curriculum search
    llm.py           # llama.cpp GGUF wrapper
  data/
    materials/       # Tananyag corpus
    embedding/       # model.onnx + vocab.txt
  models/            # *.gguf (lásd models/README.md)
  Dockerfile
  requirements.txt
  requirements-llm.txt
```

## Hibaelhárítás

| Tünet | Tipikus ok |
|-------|------------|
| `llmReady: false` | Hiányzó / rossz `LLM_MODEL_PATH`, GGUF nincs betöltve |
| Telefon: „nem elérhető” | Rossz `cloudBaseUrl`, firewall, Cloud Run cold start |
| `pip install` llama-cpp fail (Windows) | MSVC Build Tools hiányzik |
| Echo / üres válasz a régi kliensben | Régi offline út – használd a vékony cloud klienst |

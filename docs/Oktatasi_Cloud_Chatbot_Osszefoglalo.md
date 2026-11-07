# Oktatási Cloud Chatbot  
## Technikai és projektösszefoglaló

**LUMEEI AI Mind** · Flutter vékony kliens · Cloud Run RAG + Qwen GGUF · Android  

**Verzió:** app 2.0.0 · API 2.1.0 · 2026

---

## 1. Cél és áttekintés

Az alkalmazás egy magyar nyelvű, oktatási célú chatbot. A felhasználó telefonon beszélget; a **tananyagkeresés (RAG)**, a **webes mélykeresés** és a **nagy nyelvi modell (Qwen)** a **Google Cloud Run** szerveren fut.

- **Célközönség:** magyar iskolai tananyag (OH tankönyvek) – fizika, matek, irodalom, magyar nyelv.
- **Platform:** elsősorban Android (Flutter); a szerver Linux konténer (Cloud Run / Docker).
- **Brand / csomag:** LUMEEI AI Mind (`educational_chatbot`).
- **Internet:** kötelező – a chat a Cloud Run API-t hívja; a Hu↔En fordítás is online (Google Translate a telefonon).

A korábbi **on-device** (MediaPipe `.task` + helyi ObjectBox RAG) architektúra **elavult**. Az APK már nem tartalmaz LLM-et, embedding ONNX-ot és tananyag-indexet.

---

## 2. Végfelhasználói adatfolyam

Egy tipikus kérdés útja:

1. A felhasználó **magyarul** kérdez a chat UI-ban.
2. **TranslationService** (telefon): Hu→En (Google Translate; névvédő sablonok).
3. **HTTPS** `POST /v1/chat` a Cloud Run felé (`question` angol, opcionális `hungarianQuestion`).
4. **Szerver RAG:** DistilUSE embedding + lexikális boost a tananyag-chunkokon.
5. Ha kevés a találat → **DuckDuckGo** curriculum web search a kontextusba.
6. **Qwen2.5 GGUF** (llama.cpp): angol rendszerprompt + kontextus → angol válasz.
7. **TranslationService** (telefon): En→Hu → magyar válasz a felületen.

A rendszerprompt angolul kéri, hogy a modell a megadott tananyag-/web-kontextusból válaszoljon, röviden.

---

## 3. Architektúra

```
[Telefon UI + online fordítás]
        │  HTTPS
        ▼
[Cloud Run: RAG + web search + Qwen GGUF]
```

### Telefon (Flutter)

| Réteg | Feladat | Fő komponensek |
|-------|---------|----------------|
| Bootstrap / DI | Konfig, cloud kliens, fordító | `bootstrap.dart`, `service_locator.dart` |
| Chat UI | Üzenetek, splash, újrapróbálás | `lumeei_ai_mind_chat_screen.dart`, `home_screen.dart` |
| Chat API kliens | Health + `/v1/chat` | `CloudChatService` |
| Fordítás | Online Hu↔En | `TranslationService` |
| Konfig | Cloud URL | `assets/config/app_config.json` → `cloudBaseUrl` |

### Szerver (`ToDeploy/`)

| Réteg | Feladat | Fő komponensek |
|-------|---------|----------------|
| API | FastAPI végpontok | `app/main.py` |
| Embedding | DistilUSE ONNX | `app/embedder.py` |
| RAG | Retrieve + index | `app/rag_store.py`, `rag_index.py` |
| Web | Curriculum keresés | `app/web_search.py` |
| LLM | Qwen GGUF | `app/llm.py` (`llama-cpp-python`) |

Indítási sorrend (app): `ServiceLocator` → `AppConfig` → fordító + `CloudChatService` → health check → fő UI.

---

## 4. Használt technológiák

### 4.1 Alkalmazásréteg (telefon)

| Technológia | Szerep |
|-------------|--------|
| Flutter / Dart (SDK ^3.9) | UI és vékony kliens |
| `http` | Cloud Run hívások |
| `translator` | Hu↔En (Google Translate) |
| `flutter_tts` | Felolvasás |
| `flutter_riverpod` | ProviderScope héj |
| `shared_preferences`, `path_provider`, `uuid`, `equatable` | Segédtárolás / ID-k |

**Nincs** a kliensben: MediaPipe / flutter_gemma, ObjectBox, ONNX Runtime, helyi tananyag-assetek, GGUF.

### 4.2 Szerver LLM

| Technológia | Szerep |
|-------------|--------|
| `llama-cpp-python` | GGUF futtatás CPU-n |
| Qwen2.5 1.5B Instruct Q4_K_M (`.gguf`) | Alapértelmezett modell (~1,1 GB) |

Ajánlott Cloud Run: 4–8 vCPU, 8–16 GiB, `concurrency=1`, timeout ~300 s.  
Alap: `n_ctx=1024`, `max_tokens=256`, `temperature=0.3`.

### 4.3 Szerver RAG

| Technológia | Szerep |
|-------------|--------|
| DistilUSE multilingual (ONNX) | Mondat-embedding |
| `onnxruntime` | Embedding futás a szerveren |
| Előreépített / fájl alapú tananyag index | `data/materials/` |

Hibrid jelleg: vektoros retrieve + lexikális boost (magyar kérdés opcionális). Ha kevés a találat, web search egészíti ki a kontextust.

### 4.4 Fordítás

- Telefon: `translator` → Google Translate.
- Névvédő sablonok (pl. „Ki volt Koppány?”).
- A szerver **nem** fordít (a kliens felelős a nyelvváltásért).

### 4.5 Deploy

| Eszköz | Szerep |
|--------|--------|
| `ToDeploy/Dockerfile` | Image build |
| Google Cloud Run | Prod hosting |
| `requirements.txt` + `requirements-llm.txt` | Python függőségek |

---

## 5. API

| Metódus | Útvonal | Szerep |
|---------|---------|--------|
| `GET` | `/health` | `ok`, `ragReady`, `llmReady`, `books`, `uptimeSec` |
| `GET` | `/v1/books` | Tananyagkatalógus |
| `POST` | `/v1/chat` | Kérdés → angol válasz (+ debug) |

Példa chat body:

```json
{
  "question": "Who was Koppany?",
  "hungarianQuestion": "Ki volt Koppány?"
}
```

Élő Cloud Run URL (konfigban is):  
`https://lumeei-ai-mind-270606217294.europe-west1.run.app`

---

## 6. Miért angol belső pipeline?

A kis (1.5B) Qwen modell magyarul gyengébben teljesít. Az angol tananyag-kontextus + angol generálás stabilabb. A UI magyar marad: a telefon fordít oda-vissza.

---

## 7. Korlátok és ismert tényezők

- Kis LLM: korlátozott érvelés; rövid válaszok; `maxTokens` 256.
- **Internet kötelező** (API + fordítás).
- Cloud Run cold start / alacsony CPU → lassabb első válasz.
- GGUF nélkül a chat 503 (`LLM not loaded`) – `llmReady` legyen `true`.
- Web search csak akkor lép be, ha a tananyag-RAG gyenge.
- Windows helyi `llama-cpp-python` telepítéshez gyakran MSVC Build Tools kell.
- A Dart forrás soronként kommentelt a könnyebb olvashatóságért (nagy fájlméret).

---

## 8. Fontos fájlok

| Útvonal | Jelentőség |
|---------|------------|
| `pubspec.yaml` | Kliens függőségek, assetek |
| `assets/config/app_config.json` | `cloudBaseUrl` |
| `lib/bootstrap.dart` | Indítás |
| `lib/core/di/service_locator.dart` | DI (cloud-only) |
| `lib/features/chat/data/cloud_chat_service.dart` | HTTP chat orkesztráció |
| `lib/features/translation/data/translation_service.dart` | Hu↔En |
| `ToDeploy/app/main.py` | FastAPI |
| `ToDeploy/app/llm.py` | GGUF LLM |
| `ToDeploy/app/rag_store.py` | RAG retrieve |
| `ToDeploy/app/web_search.py` | DDG keresés |
| `ToDeploy/Dockerfile` | Cloud image |
| `ToDeploy/README.md` | Deploy útmutató |
| `README.md` | Projekt belépő |

---

## 9. Összefoglaló folyamat

**Futásidő:**  
UI (HU) → Google Translate (Hu→En) → Cloud Run RAG (+ opcionális web) → Qwen2.5 GGUF → Google Translate (En→Hu) → UI (HU)

**Deploy:**  
Tananyag + DistilUSE + Qwen GGUF → `ToDeploy` image → Cloud Run → Flutter `cloudBaseUrl` beállítás → `flutter run` / APK.

---

Ez a dokumentum az `educational_chatbot` kódbázis **cloud-only** állapotáról készült (`app_config.json`, `lib/`, `ToDeploy/` alapján).  
A korábbi offline összefoglaló (`Oktatasi_Offline_Chatbot_Osszefoglalo`) elavult.

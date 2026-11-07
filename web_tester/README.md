# LUMEEI AI Mind – böngészős tesztelő (Firebase Hosting)

Statikus web UI a Cloud Run API kipróbálásához **asztali böngészőből** (nem kell APK / telefon).

```
[Böngésző: web_tester]
   │  /v1/translate  (Hu↔En)
   │  /v1/chat       (RAG + Qwen)
   ▼
[Cloud Run]
```

## Helyi próba

Bármilyen statikus szerver a `web_tester` mappán:

```powershell
cd web_tester
# Python 3:
python -m http.server 5500
```

Nyisd: http://127.0.0.1:5500  

Az API URL mező alapból a Cloud Run címet tölti; mentés `localStorage`-ba kerül.

## Firebase deploy

1. Telepítsd a Firebase CLI-t és jelentkezz be:

```bash
npm install -g firebase-tools
firebase login
```

2. Állítsd be a projekt ID-t a gyökér `.firebaserc` fájlban (`YOUR_FIREBASE_PROJECT_ID`).

3. Deploy:

```bash
# a repo gyökeréből (ahol a firebase.json van)
firebase deploy --only hosting
```

A Hosting URL után a chat ugyanarra a Cloud Run-ra beszél, mint a mobil (`cloudBaseUrl`).

## Szerver követelmény

A web tesztelő hívja:

| Végpont | Szerep |
|---------|--------|
| `GET /health` | Készültség |
| `POST /v1/translate` | Hu↔En (böngésző CORS-barát) |
| `POST /v1/chat` | Kérdés → angol válasz + debug |

A `/v1/translate` a `ToDeploy` API része – **redeploy** kell a Cloud Runra, ha még a régi image fut fordítás nélkül.

CORS: a szerveren alapból `*` – a Firebase domainről is megy a `fetch`.

## Mit nem csinál?

- Nem Flutter build
- Nincs TTS / mobil-specifikus UI
- Nem helyettesíti a host-app integrációs tesztet – gyors smoke + debug panelhez való

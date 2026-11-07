# LUMEEI AI Mind – bekötés meglévő Flutter appba

**Célközönség:** Flutter-t ismerő fejlesztő  
**Csomag:** `educational_chatbot` (vékony HTTP kliens)  
**Szerver:** Cloud Run (RAG + Qwen) – a telefonon nincs helyi LLM  

**Verzió:** app 2.0.0 · 2026

---

## Mit kapsz a bekötéssel?

A host appból egy gombbal / route-tal megnyílik a LUMEEI tananyag-chat.  
A host feladata: függőség + assetek + `initialize` + chat megnyitás.  
A válaszokat a Cloud Run adja; a Hu↔En fordítás a telefonon fut (internet kell).

Publikus API (egy import):

```dart
import 'package:educational_chatbot/lumeei_ai_mind.dart';

await LumeeiAiMind.initialize(onProgress: ...);
LumeeiAiMind.openChat(context);
// vagy: LumeeiAiMind.chatScreen(showBackButton: true)
```

---

## Előfeltételek

1. Flutter SDK kompatibilis a csomaggal (`sdk: ^3.9.2` a csomag `pubspec.yaml`-jában).
2. A Cloud Run szolgáltatás elérhető (prod URL a csomag `assets/config/app_config.json`-jában, vagy saját URL-t állítasz be).
3. A host appnak van **internetes** hozzáférése (Android `INTERNET` permission).
4. A chatbot csomag forráskódja elérhető a gépeden (path dependency) vagy később git/path publish szerint.

Jelenlegi alapértelmezett szerver:

`https://lumeei-ai-mind-270606217294.europe-west1.run.app`

---

## 1. lépés – Csomag hozzáadása a host `pubspec.yaml`-hoz

A legegyszerűbb mód: **path dependency** (a chatbot mappa relatív/abszolút útvonala):

```yaml
dependencies:
  flutter:
    sdk: flutter
  # ... meglévő függőségeid ...
  educational_chatbot:
    path: ../educational_chatbot   # igazítsd a saját könyvtárszerkezetedhez
```

Majd:

```bash
flutter pub get
```

**Megjegyzés:** A csomag függőségei (`http`, `translator`, `flutter_tts`, `shared_preferences`, stb.) automatikusan feloldódnak. Nem kell őket külön felsorolnod, hacsak a host maga is használja őket.

---

## 2. lépés – Assetek a host appban

A csomag kódja **gyökér asset útvonalakat** tölt (`assets/config/...`, `assets/branding/...`), nem `packages/educational_chatbot/...` formát.  
Ezért a host projektben is legyenek ezek a fájlok, és a host `pubspec.yaml` deklarálja őket.

### 2.1 Másold át a fájlokat

A chatbot repóból a hostba:

| Forrás (chatbot) | Cél (host) |
|------------------|------------|
| `assets/config/app_config.json` | `assets/config/app_config.json` |
| `assets/branding/LUMEEiAi.png` (és a branding mappa) | `assets/branding/` |

### 2.2 Host `pubspec.yaml` – assets szekció

```yaml
flutter:
  uses-material-design: true
  assets:
    - assets/config/
    - assets/branding/
    # ... meglévő assetjeid ...
```

### 2.3 Szerver URL beállítása

Szerkeszd a host `assets/config/app_config.json` fájlját:

```json
{
  "cloudBaseUrl": "https://lumeei-ai-mind-270606217294.europe-west1.run.app"
}
```

Helyi demóhoz (LAN): `http://192.168.x.x:8080`  
Fizikai telefonon **ne** `127.0.0.1`-et használj.

Ellenőrzés: böngészőben / `curl`-lel `GET {cloudBaseUrl}/health` → `ok`, `ragReady`, `llmReady` legyen igaz.

---

## 3. lépés – Android jogosultság

A host `android/app/src/main/AndroidManifest.xml` fájlban legyen:

```xml
<uses-permission android:name="android.permission.INTERNET"/>
```

(Általában már megvan Flutter appokban.)  
iOS-en App Transport Security: HTTPS Cloud Run URL-lel nincs külön teendő; HTTP LAN demóhoz ATS kivétel kellhet.

---

## 4. lépés – Inicializálás

`LumeeiAiMind.initialize()` betölti a konfigot, előkészíti a fordítót, és pingeli a Cloud Run `/health` végpontot.  
Ha a szerver nem elérhető / `llmReady` false, **kivételt** dob – kezeld a UI-ban (splash / dialógus / Újrapróbálás).

### Eager init (ajánlott splash / indítás végén)

```dart
import 'package:educational_chatbot/lumeei_ai_mind.dart';
import 'package:flutter/material.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyHostApp());
}

// A splash State-jében:
Future<void> _prepareAiMind() async {
  await LumeeiAiMind.initialize(
    onProgress: (status, progress) {
      // opcionális: státusz szöveg + LinearProgressIndicator
    },
  );
}
```

### Lazy init (első chat nyitás előtt)

```dart
Future<void> openAiMind(BuildContext context) async {
  if (!LumeeiAiMind.isInitialized) {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
    try {
      await LumeeiAiMind.initialize();
    } finally {
      if (context.mounted) Navigator.of(context).pop();
    }
  }
  if (!context.mounted) return;
  await LumeeiAiMind.openChat(context);
}
```

**Fontos:** `initialize` előtt hívj `WidgetsFlutterBinding.ensureInitialized()`-t (általában a `main`-ben).

---

## 5. lépés – Chat megnyitása

### A) Navigátor push (legegyszerűbb)

```dart
await LumeeiAiMind.openChat(context);
// vissza gombbal a chat AppBar-ján:
await LumeeiAiMind.openChat(context, showBackButton: true);
```

### B) Saját route / go_router / AutoRoute

```dart
// Route builder – initialize MÁR lefutott:
Widget buildAiMindPage(BuildContext context) {
  assert(LumeeiAiMind.isInitialized);
  return LumeeiAiMind.chatScreen(showBackButton: true);
}
```

Példa go_router:

```dart
GoRoute(
  path: '/ai-mind',
  builder: (context, state) => LumeeiAiMind.chatScreen(showBackButton: true),
),
```

A route elérése előtt győződj meg, hogy `LumeeiAiMind.isInitialized == true`.

### C) Beágyazott képernyő (tab / nested navigator)

```dart
Scaffold(
  body: LumeeiAiMind.chatScreen(showBackButton: false),
)
```

`showBackButton: false`, ha nincs „vissza” a host stacken.

---

## 6. lépés – UI illesztés (opcionális)

- **Téma:** `LumeeiAiMind.theme` – sötét LUMEEI kinézet. A chat saját színeket használ; a host MaterialApp témáját nem kötelező átírni.
- **Gomb a host UI-ban:** FAB, menüpont, drawer – bármi, ami `openChat`-et hív.
- **Riverpod:** a chatbot saját `ProviderScope`-ot **nem** követel a `openChat` / `chatScreen` útvonalon. A standalone app splashje használ Riverpodot; a hostnak emiatt nem kell wrapping.

---

## 7. lépés – Teljes minimál példa (FAB a saját home-on)

```dart
import 'package:educational_chatbot/lumeei_ai_mind.dart';
import 'package:flutter/material.dart';

class HostHome extends StatelessWidget {
  const HostHome({super.key});

  Future<void> _openChat(BuildContext context) async {
    try {
      if (!LumeeiAiMind.isInitialized) {
        await LumeeiAiMind.initialize();
      }
      if (!context.mounted) return;
      await LumeeiAiMind.openChat(context);
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chatbot nem elérhető: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Host alkalmazás')),
      body: const Center(child: Text('Saját tartalom')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openChat(context),
        icon: const Icon(Icons.auto_awesome),
        label: const Text('Tananyag chat'),
      ),
    );
  }
}
```

További minták a chatbot repóban:

- `examples/host_simple_main.dart` – teljes app = chat  
- `examples/host_complex_integration.dart` – FAB + lazy init + route builder  

---

## 8. lépés – Ellenőrzőlista (átadás előtt)

| # | Ellenőrzés |
|---|------------|
| 1 | `flutter pub get` hibamentes |
| 2 | Hostban van `assets/config/app_config.json` helyes `cloudBaseUrl`-lel |
| 3 | Hostban van `assets/branding/` (logo) |
| 4 | Host `pubspec.yaml` deklarálja a fenti asset mappákat |
| 5 | Android `INTERNET` permission |
| 6 | `GET {cloudBaseUrl}/health` → `llmReady: true` |
| 7 | `initialize()` lefut (eager vagy lazy) |
| 8 | `openChat` / `chatScreen` megnyílik, magyar kérdésre válasz érkezik |
| 9 | Offline / rossz URL esetén érthető hibaüzenet a host UI-ban |

---

## 9. Gyakori hibák

| Tünet | Ok / megoldás |
|-------|----------------|
| `Unable to load asset: assets/config/app_config.json` | Nincs átmásolva / nincs a host `pubspec` assets listájában → `flutter pub get` + hot restart |
| `cloudBaseUrl hiányzik` | Üres vagy hibás JSON |
| `CloudUnavailableException` / „nem elérhető” | Rossz URL, nincs net, Cloud Run down, vagy `llmReady: false` |
| Chat üres / timeout | Ellenőrizd a `/health`-et és a Cloud Run logokat |
| `127.0.0.1` telefonról | Használj LAN IP-t vagy a Cloud Run HTTPS URL-t |
| `initialize` kétszer | Ártalmatlan: a DI idempotens (`isInitialized` után return) |
| Hot restart után furcsa állapot | `await LumeeiAiMind.dispose()` tesztekhez; normal app lifecycle-ben ritkán kell |

---

## 10. API rövid referencia

| Tag | Szerep |
|-----|--------|
| `LumeeiAiMind.initialize({onProgress})` | Konfig + fordító + health ping |
| `LumeeiAiMind.isInitialized` | bool – kész-e a DI |
| `LumeeiAiMind.openChat(context, {showBackButton})` | Push navigáció a chatre |
| `LumeeiAiMind.chatScreen({showBackButton})` | Widget route-hoz / embedhez |
| `LumeeiAiMind.theme` | Sötét ThemeData |
| `LumeeiAiMind.dispose()` | Erőforrások elengedése (teszt / újrainítás) |

Egyetlen import:

`package:educational_chatbot/lumeei_ai_mind.dart`

---

## 11. Architektúra emlékeztető (host szemszög)

```
[Host Flutter app]
   │  LumeeiAiMind.initialize / openChat
   ▼
[educational_chatbot csomag]
   │  Hu↔En fordítás (telefon) + HTTPS
   ▼
[Cloud Run: RAG + web search + Qwen GGUF]
```

A host **nem** telepít MediaPipe-ot, ONNX-ot, GGUF-et vagy tananyag-indexet az APK-ba.

---

## 12. Kapcsolódó dokumentumok

- Projekt áttekintés: `README.md`
- Technikai összefoglaló: `docs/Oktatasi_Cloud_Chatbot_Osszefoglalo.md`
- Szerver deploy: `ToDeploy/README.md`

---

**Összefoglalva:** path dependency → assetek átmásolása + `cloudBaseUrl` → INTERNET → `initialize` → `openChat` / `chatScreen`.

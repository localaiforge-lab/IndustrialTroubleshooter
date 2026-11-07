/// Külső (host) appok számára egyetlen import-pont.
///
/// Használat:
/// ```dart
/// import 'package:educational_chatbot/lumeei_ai_mind.dart';
/// await LumeeiAiMind.initialize();
/// LumeeiAiMind.openChat(context);
/// ```
library; // Könyvtár jelölő: ez a fájl csak exportál.

// A publikus LumeeiAiMind API (initialize, openChat…).
export 'package:educational_chatbot/integration/lumeei_ai_mind.dart';
// A chat képernyő widget közvetlen használathoz.
export 'package:educational_chatbot/features/chat/presentation/screens/lumeei_ai_mind_chat_screen.dart';
// A téma tokenek (színek, ThemeData).
export 'package:educational_chatbot/features/chat/presentation/theme/lumeei_theme.dart';
// ServiceLocator – ritkán kell hostnak, de elérhető.
export 'package:educational_chatbot/core/di/service_locator.dart';

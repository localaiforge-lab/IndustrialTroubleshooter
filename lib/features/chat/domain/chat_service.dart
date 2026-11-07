// ChatMessage entitás a history listához.
import 'package:educational_chatbot/features/chat/domain/entities/chat_message.dart';

/// Chat absztrakció: a UI csak ezt látja (nem a Cloud HTTP részleteit).
///
/// A konkrét implementáció [ChangeNotifier], hogy a képernyő figyelhesse.
abstract class ChatService {
  /// Az aktuális beszélgetés üzenetei (memóriában).
  List<ChatMessage> get messages;

  /// true, amíg a szerver válaszát várjuk / streameljük.
  bool get isGenerating;

  /// Kiválasztott tankönyv documentId (RAG szűrés a szerveren).
  String? get selectedDocumentId;
  // Setter: UI könyvválasztó hívja.
  set selectedDocumentId(String? value);

  /// Felhasználói kérdés elküldése; a válasz a [messages]-ben jelenik meg.
  ///
  /// [documentId] opcionálisan felülírja a kiválasztott könyvet erre a körre.
  Future<void> sendMessage(
    // Szöveges mező vagy változó.
    String text, {
    // Igaz/hamis mező vagy változó.
    bool useRag = true, // Megtartva kompatibilitás miatt (szerver mindig RAG-ol).
    // Widget / hívás paraméterlista folytatása.
    String? documentId,
  // Blokk / szerkezet zárójele.
  });

  /// Folyamatban lévő válasz megszakítása.
  Future<void> stopGeneration();

  /// UI history törlése (szerver oldali indexet nem bántja).
  void clearHistory();
// Blokk / osztály vége.
}

// Equatable: érték-egyenlőség a listák újrarajzolásához.
import 'package:equatable/equatable.dart';

/// Ki írta az üzenetet.
enum ChatRole { user, assistant, system }

/// Egy RAG találat előnézete (opcionális debug / citáció).
class RagSourcePreview extends Equatable {
  // Minden mező kötelező a megjelenítéshez.
  const RagSourcePreview({
    // Kódsor: részlet a fenti logikából.
    required this.documentTitle, // Tankönyv címe.
    // Kódsor: részlet a fenti logikából.
    required this.chunkIndex, // Chunk sorszám.
    // Kódsor: részlet a fenti logikából.
    required this.text, // Részlet szövege.
    // Kódsor: részlet a fenti logikából.
    required this.score, // Relevancia (kisebb/nagyobb a szerver szerint).
    // Kódsor: részlet a fenti logikából.
    required this.usedInPrompt, // Belement-e a LLM promptba.
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final String documentTitle; // Pl. "Töri 5.".
  // Változó / mező: egyszer állítható érték.
  final int chunkIndex; // Index a packben.
  // Változó / mező: egyszer állítható érték.
  final String text; // Truncált passage.
  // Változó / mező: egyszer állítható érték.
  final double score; // Távolság / score.

  /// false, ha a maxContextChars miatt kimaradt a promptból.
  final bool usedInPrompt;

  // Felülírja a szülő/interfész metódusát.
  @override
  // Equatable összehasonlítás mezői.
  List<Object?> get props =>
      // Utasítás vége.
      [documentTitle, chunkIndex, text, score, usedInPrompt];
// Blokk / osztály vége.
}

/// Egy chat üzenet a listában (immutable).
class ChatMessage extends Equatable {
  // Fordítási idejű konstans.
  const ChatMessage({
    // Kódsor: részlet a fenti logikából.
    required this.id, // Egyedi UUID.
    // Kódsor: részlet a fenti logikából.
    required this.role, // user / assistant / system.
    // Kódsor: részlet a fenti logikából.
    required this.content, // Megjelenő szöveg.
    // Kódsor: részlet a fenti logikából.
    required this.createdAt, // Időbélyeg.
    // Értékadás / mezőkitöltés.
    this.isStreaming = false, // true = még írja a választ.
    // Értékadás / mezőkitöltés.
    this.ragSources = const [], // Chunk ID-k (debug).
    // Értékadás / mezőkitöltés.
    this.ragPreviews = const [], // Emberi előnézetek.
    // Értékadás / mezőkitöltés.
    this.ragContextBlock = '', // Promptba került kontextus.
    // Értékadás / mezőkitöltés.
    this.ragSearchQuery = '', // Angol keresőkérdés.
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final String id;
  // Változó / mező: egyszer állítható érték.
  final ChatRole role;
  // Változó / mező: egyszer állítható érték.
  final String content;
  // Változó / mező: egyszer állítható érték.
  final DateTime createdAt;
  // Változó / mező: egyszer állítható érték.
  final bool isStreaming;

  /// RAG chunk azonosítók.
  final List<String> ragSources;

  /// Olvasható találatlista.
  final List<RagSourcePreview> ragPreviews;

  /// A szerver által összeállított context string.
  final String ragContextBlock;

  /// Angol query (fordítás után).
  final String ragSearchQuery;

  /// Új példány módosított mezőkkel (immutability minta).
  ChatMessage copyWith({
    // Widget / hívás paraméterlista folytatása.
    String? id,
    // Widget / hívás paraméterlista folytatása.
    ChatRole? role,
    // Widget / hívás paraméterlista folytatása.
    String? content,
    // Widget / hívás paraméterlista folytatása.
    DateTime? createdAt,
    // Widget / hívás paraméterlista folytatása.
    bool? isStreaming,
    // Widget / hívás paraméterlista folytatása.
    List<String>? ragSources,
    // Widget / hívás paraméterlista folytatása.
    List<RagSourcePreview>? ragPreviews,
    // Widget / hívás paraméterlista folytatása.
    String? ragContextBlock,
    // Widget / hívás paraméterlista folytatása.
    String? ragSearchQuery,
  // Blokk / szerkezet zárójele.
  }) {
    // null = tartsd az eredeti értéket.
    return ChatMessage(
      // Widget / hívás paraméterlista folytatása.
      id: id ?? this.id,
      // Widget / hívás paraméterlista folytatása.
      role: role ?? this.role,
      // Widget / hívás paraméterlista folytatása.
      content: content ?? this.content,
      // Widget / hívás paraméterlista folytatása.
      createdAt: createdAt ?? this.createdAt,
      // Widget / hívás paraméterlista folytatása.
      isStreaming: isStreaming ?? this.isStreaming,
      // Widget / hívás paraméterlista folytatása.
      ragSources: ragSources ?? this.ragSources,
      // Widget / hívás paraméterlista folytatása.
      ragPreviews: ragPreviews ?? this.ragPreviews,
      // Widget / hívás paraméterlista folytatása.
      ragContextBlock: ragContextBlock ?? this.ragContextBlock,
      // Widget / hívás paraméterlista folytatása.
      ragSearchQuery: ragSearchQuery ?? this.ragSearchQuery,
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  // Equatable: mely mezők számítanak egyenlőségnél.
  List<Object?> get props => [
        // Widget / hívás paraméterlista folytatása.
        id,
        // Widget / hívás paraméterlista folytatása.
        role,
        // Widget / hívás paraméterlista folytatása.
        content,
        // Widget / hívás paraméterlista folytatása.
        createdAt,
        // Widget / hívás paraméterlista folytatása.
        isStreaming,
        // Widget / hívás paraméterlista folytatása.
        ragSources,
        // Widget / hívás paraméterlista folytatása.
        ragPreviews,
        // Widget / hívás paraméterlista folytatása.
        ragContextBlock,
        // Widget / hívás paraméterlista folytatása.
        ragSearchQuery,
      // Utasítás vége.
      ];
// Blokk / osztály vége.
}

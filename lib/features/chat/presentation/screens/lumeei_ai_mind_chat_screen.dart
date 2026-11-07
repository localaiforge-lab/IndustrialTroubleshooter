// Import: külső/csomag függőség betöltése.
import 'dart:async';

// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/core/di/service_locator.dart';
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/core/platform/tts_install_platform.dart';
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/core/utils/diagnostic_log.dart';
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/features/chat/data/cloud_chat_service.dart';
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/features/chat/domain/chat_service.dart';
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/features/chat/domain/entities/chat_message.dart';
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/features/chat/presentation/theme/lumeei_theme.dart';
// Import: külső/csomag függőség betöltése.
import 'package:flutter/material.dart';
// Import: külső/csomag függőség betöltése.
import 'package:flutter_tts/flutter_tts.dart';

// Fordítási idejű konstans.
const _kBrandAsset = 'assets/branding/LUMEEiAi.png';

// Osztály definíció kezdete.
class TextbookOption {
  // Fordítási idejű konstans.
  const TextbookOption({required this.documentId, required this.title});
  // Változó / mező: egyszer állítható érték.
  final String documentId;
  // Változó / mező: egyszer állítható érték.
  final String title;
// Blokk / osztály vége.
}

/// Cloud-only chat UI: HTTP → Cloud Run (RAG + web + Qwen).
// Osztály definíció kezdete.
class LumeeiAiMindChatScreen extends StatefulWidget {
  // Fordítási idejű konstans.
  const LumeeiAiMindChatScreen({
    // Szülő osztály metódusának hívása.
    super.key,
    // Widget / hívás paraméterlista folytatása.
    this.showBackButton = true,
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final bool showBackButton;

  // Felülírja a szülő/interfész metódusát.
  @override
  // Értékadás / mezőkitöltés.
  State<LumeeiAiMindChatScreen> createState() => _LumeeiAiMindChatScreenState();
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _LumeeiAiMindChatScreenState extends State<LumeeiAiMindChatScreen>
    // Widget / hívás paraméterlista folytatása.
    with WidgetsBindingObserver {
  // Osztályszintű (példány nélküli) tag.
  static const _prefsKeyBook = 'lumeei.selected_document_id';

  // Utasítás vége.
  late final ChatService _chat;
  // Utasítás vége.
  late final ChangeNotifier _chatListenable;
  // Változó / mező: egyszer állítható érték.
  final _inputController = TextEditingController();
  // Változó / mező: egyszer állítható érték.
  final _scrollController = ScrollController();
  // Változó / mező: egyszer állítható érték.
  final _focusNode = FocusNode();
  // Változó / mező: egyszer állítható érték.
  final _tts = FlutterTts();

  // Értékadás / mezőkitöltés.
  List<TextbookOption> _books = const [];
  // Utasítás vége.
  String? _selectedBookId;
  // Utasítás vége.
  bool? _hungarianTtsAvailable;
  // Igaz/hamis mező vagy változó.
  bool _ttsSpeaking = false;
  // Utasítás vége.
  String? _speakingMessageId;
  // Igaz/hamis mező vagy változó.
  bool _sendInFlight = false;
  // Igaz/hamis mező vagy változó.
  bool _busyLeaveDialogOpen = false;

  // Igaz/hamis mező vagy változó.
  bool get _interactionLocked => _sendInFlight || _chat.isGenerating;

  // Felülírja a szülő/interfész metódusát.
  @override
  // Nincs visszatérési érték.
  void initState() {
    // Szülő osztály metódusának hívása.
    super.initState();
    // Utasítás vége.
    WidgetsBinding.instance.addObserver(this);
    // Értékadás / mezőkitöltés.
    _chat = ServiceLocator.chat;
    // Értékadás / mezőkitöltés.
    _chatListenable = chatAsListenable(_chat);
    // Utasítás vége.
    _chatListenable.addListener(_onChatChanged);
    // Utasítás vége.
    _loadBooks();
    // Utasítás vége.
    _initTts();
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  // Nincs visszatérési érték.
  void dispose() {
    // Utasítás vége.
    WidgetsBinding.instance.removeObserver(this);
    // Utasítás vége.
    _chatListenable.removeListener(_onChatChanged);
    // Feltételes elágazás.
    if (_chat.isGenerating) {
      // Fut a háttérben, nem várjuk meg.
      unawaited(_chat.stopGeneration());
    // Blokk / osztály vége.
    }
    // Utasítás vége.
    _tts.stop();
    // Utasítás vége.
    _inputController.dispose();
    // Utasítás vége.
    _scrollController.dispose();
    // Utasítás vége.
    _focusNode.dispose();
    // Szülő osztály metódusának hívása.
    super.dispose();
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  // Nincs visszatérési érték.
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Feltételes elágazás.
    if (state == AppLifecycleState.resumed) {
      // Fut a háttérben, nem várjuk meg.
      unawaited(_refreshHungarianTtsAvailability());
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<void> _initTts() async {
    // Hibakezelés kezdete (try).
    try {
      // Változó / mező: egyszer állítható érték.
      final available = await _detectHungarianTts();
      // Feltételes elágazás.
      if (available) {
        // Aszinkron művelet megvárása.
        await _tts.setLanguage('hu-HU');
        // Aszinkron művelet megvárása.
        await _tts.setSpeechRate(0.45);
        // Aszinkron művelet megvárása.
        await _tts.setPitch(1.0);
      // Blokk / osztály vége.
      }
      // Widget / hívás paraméterlista folytatása.
      _tts.setCompletionHandler(() {
        // Feltételes elágazás.
        if (!mounted) return;
        // UI újrarajzolás kérése állapotváltozás után.
        setState(() {
          // Értékadás / mezőkitöltés.
          _ttsSpeaking = false;
          // Értékadás / mezőkitöltés.
          _speakingMessageId = null;
        // Blokk / szerkezet zárójele.
        });
      // Blokk / szerkezet zárójele.
      });
      // Widget / hívás paraméterlista folytatása.
      _tts.setCancelHandler(() {
        // Feltételes elágazás.
        if (!mounted) return;
        // UI újrarajzolás kérése állapotváltozás után.
        setState(() {
          // Értékadás / mezőkitöltés.
          _ttsSpeaking = false;
          // Értékadás / mezőkitöltés.
          _speakingMessageId = null;
        // Blokk / szerkezet zárójele.
        });
      // Blokk / szerkezet zárójele.
      });
      // Feltételes elágazás.
      if (mounted) setState(() => _hungarianTtsAvailable = available);
    // Blokk / szerkezet zárójele.
    } catch (e, st) {
      // Utasítás vége.
      DiagnosticLog.log('LumeeiUI', 'TTS init failed: $e\n$st');
      // Feltételes elágazás.
      if (mounted) setState(() => _hungarianTtsAvailable = false);
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<bool> _detectHungarianTts() async {
    // Hibakezelés kezdete (try).
    try {
      // Változó / mező: egyszer állítható érték.
      final langs = await _tts.getLanguages;
      // Feltételes elágazás.
      if (langs is List) {
        // Visszatérési érték a hívónak.
        return langs.any(
          // Widget / hívás paraméterlista folytatása.
          (l) => l.toString().toLowerCase().startsWith('hu'),
        // Utasítás vége.
        );
      // Blokk / osztály vége.
      }
    // Blokk / szerkezet zárójele.
    } catch (_) {}
    // Visszatérési érték a hívónak.
    return false;
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<void> _refreshHungarianTtsAvailability() async {
    // Változó / mező: egyszer állítható érték.
    final available = await _detectHungarianTts();
    // Feltételes elágazás.
    if (!mounted) return;
    // UI újrarajzolás kérése állapotváltozás után.
    setState(() => _hungarianTtsAvailable = available);
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<void> _speakAnswer(ChatMessage message) async {
    // Változó / mező: egyszer állítható érték.
    final text = message.content.trim();
    // Feltételes elágazás.
    if (text.isEmpty) return;

    // Feltételes elágazás.
    if (_hungarianTtsAvailable != true) {
      // Változó / mező: egyszer állítható érték.
      final opened = await TtsInstallPlatform.openVoiceInstall();
      // Feltételes elágazás.
      if (!mounted) return;
      // Widget / hívás paraméterlista folytatása.
      ScaffoldMessenger.of(context).showSnackBar(
        // Widget / hívás paraméterlista folytatása.
        SnackBar(
          // Widget / hívás paraméterlista folytatása.
          content: Text(
            // Értékadás / mezőkitöltés.
            opened != null && opened != 'failed'
                // Kódsor: részlet a fenti logikából.
                ? 'Telepíts magyar TTS hangot a rendszerbeállításokban.'
                // Widget / hívás paraméterlista folytatása.
                : 'Nincs telepítve magyar felolvasó hang.',
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ),
      // Utasítás vége.
      );
      // Utasítás vége.
      return;
    // Blokk / osztály vége.
    }

    // Feltételes elágazás.
    if (_ttsSpeaking && _speakingMessageId == message.id) {
      // Aszinkron művelet megvárása.
      await _tts.stop();
      // Feltételes elágazás.
      if (!mounted) return;
      // UI újrarajzolás kérése állapotváltozás után.
      setState(() {
        // Értékadás / mezőkitöltés.
        _ttsSpeaking = false;
        // Értékadás / mezőkitöltés.
        _speakingMessageId = null;
      // Blokk / szerkezet zárójele.
      });
      // Utasítás vége.
      return;
    // Blokk / osztály vége.
    }

    // Aszinkron művelet megvárása.
    await _tts.stop();
    // Feltételes elágazás.
    if (!mounted) return;
    // UI újrarajzolás kérése állapotváltozás után.
    setState(() {
      // Értékadás / mezőkitöltés.
      _ttsSpeaking = true;
      // Értékadás / mezőkitöltés.
      _speakingMessageId = message.id;
    // Blokk / szerkezet zárójele.
    });
    // Változó / mező: egyszer állítható érték.
    final result = await _tts.speak(text);
    // Feltételes elágazás.
    if (result != 1 && mounted) {
      // UI újrarajzolás kérése állapotváltozás után.
      setState(() {
        // Értékadás / mezőkitöltés.
        _ttsSpeaking = false;
        // Értékadás / mezőkitöltés.
        _speakingMessageId = null;
      // Blokk / szerkezet zárójele.
      });
      // Widget / hívás paraméterlista folytatása.
      ScaffoldMessenger.of(context).showSnackBar(
        // Fordítási idejű konstans.
        const SnackBar(content: Text('Nem sikerült elindítani a felolvasást.')),
      // Utasítás vége.
      );
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Nincs visszatérési érték.
  void _onChatChanged() {
    // Feltételes elágazás.
    if (!mounted) return;
    // UI újrarajzolás kérése állapotváltozás után.
    setState(() {});
    // Utasítás vége.
    _scrollToBottom();
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<void> _loadBooks() async {
    // Értékadás / mezőkitöltés.
    List<TextbookOption> books = const [];
    // Változó / mező: egyszer állítható érték.
    final chat = _chat;
    // Feltételes elágazás.
    if (chat is CloudChatService) {
      // Hibakezelés kezdete (try).
      try {
        // Változó / mező: egyszer állítható érték.
        final remote = await chat.fetchBooks();
        // Értékadás / mezőkitöltés.
        books = [
          // Ciklus a listán / tartományon.
          for (final b in remote)
            // Widget / hívás paraméterlista folytatása.
            TextbookOption(documentId: b.documentId, title: b.title),
        // Utasítás vége.
        ];
      // Blokk / szerkezet zárójele.
      } catch (e) {
        // Utasítás vége.
        DiagnosticLog.log('LumeeiUI', 'fetchBooks failed: $e');
        // Feltételes elágazás.
        if (mounted) {
          // Widget / hívás paraméterlista folytatása.
          ScaffoldMessenger.of(context).showSnackBar(
            // Fordítási idejű konstans.
            const SnackBar(
              // Widget / hívás paraméterlista folytatása.
              content: Text(
                // Kódsor: részlet a fenti logikából.
                'A tankönyvlista nem tölthető le a felhőből. '
                // Widget / hívás paraméterlista folytatása.
                'Ellenőrizd az internetet.',
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Utasítás vége.
          );
        // Blokk / osztály vége.
        }
      // Blokk / osztály vége.
      }
    // Blokk / osztály vége.
    }
    // Változó / mező: egyszer állítható érték.
    final prefs = ServiceLocator.prefs;
    // Lokális változó.
    var selected = prefs.getString(_prefsKeyBook);
    // Feltételes elágazás.
    if (selected != null && books.every((b) => b.documentId != selected)) {
      // Értékadás / mezőkitöltés.
      selected = null;
    // Blokk / osztály vége.
    }
    // Értékadás / mezőkitöltés.
    selected ??= books.isNotEmpty ? books.first.documentId : null;
    // Feltételes elágazás.
    if (!mounted) return;
    // UI újrarajzolás kérése állapotváltozás után.
    setState(() {
      // Értékadás / mezőkitöltés.
      _books = books;
      // Értékadás / mezőkitöltés.
      _selectedBookId = selected;
    // Blokk / szerkezet zárójele.
    });
    // Értékadás / mezőkitöltés.
    _chat.selectedDocumentId = selected;
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<void> _selectBook(String documentId) async {
    // Feltételes elágazás.
    if (_selectedBookId == documentId || _interactionLocked) return;
    // UI újrarajzolás kérése állapotváltozás után.
    setState(() => _selectedBookId = documentId);
    // Értékadás / mezőkitöltés.
    _chat.selectedDocumentId = documentId;
    // Aszinkron művelet megvárása.
    await ServiceLocator.prefs.setString(_prefsKeyBook, documentId);
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<void> _send() async {
    // Változó / mező: egyszer állítható érték.
    final text = _inputController.text.trim();
    // Feltételes elágazás.
    if (text.isEmpty || _interactionLocked) return;

    // UI újrarajzolás kérése állapotváltozás után.
    setState(() => _sendInFlight = true);
    // Utasítás vége.
    _focusNode.unfocus();
    // Utasítás vége.
    _inputController.clear();
    // Hibakezelés kezdete (try).
    try {
      // Aszinkron művelet megvárása.
      await _chat.sendMessage(
        // Widget / hívás paraméterlista folytatása.
        text,
        // Widget / hívás paraméterlista folytatása.
        useRag: true,
        // Widget / hívás paraméterlista folytatása.
        documentId: _selectedBookId,
      // Utasítás vége.
      );
    // Blokk / szerkezet zárójele.
    } finally {
      // Feltételes elágazás.
      if (mounted) {
        // UI újrarajzolás kérése állapotváltozás után.
        setState(() => _sendInFlight = false);
      // Az if hamis ága.
      } else {
        // Értékadás / mezőkitöltés.
        _sendInFlight = false;
      // Blokk / osztály vége.
      }
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Aszinkron függvény / Future típus.
  Future<void> _handleBackRequest() async {
    // Feltételes elágazás.
    if (!_interactionLocked) {
      // Feltételes elágazás.
      if (mounted) Navigator.of(context).maybePop();
      // Utasítás vége.
      return;
    // Blokk / osztály vége.
    }
    // Feltételes elágazás.
    if (_busyLeaveDialogOpen) return;

    // Értékadás / mezőkitöltés.
    _busyLeaveDialogOpen = true;
    // Változó / mező: egyszer állítható érték.
    final action = await showDialog<_BusyLeaveAction>(
      // Widget / hívás paraméterlista folytatása.
      context: context,
      // Widget / hívás paraméterlista folytatása.
      barrierDismissible: false,
      // Widget / hívás paraméterlista folytatása.
      builder: (ctx) {
        // Visszatérési érték a hívónak.
        return AlertDialog(
          // Widget / hívás paraméterlista folytatása.
          backgroundColor: const Color(0xFF161A2A),
          // Widget / hívás paraméterlista folytatása.
          title: const Text(
            // Widget / hívás paraméterlista folytatása.
            'Válasz folyamatban',
            // Widget / hívás paraméterlista folytatása.
            style: TextStyle(color: LumeeiTheme.textPrimary),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Widget / hívás paraméterlista folytatása.
          content: const Text(
            // Kódsor: részlet a fenti logikából.
            'Az asszisztens még a tananyag alapján dolgozik. '
            // Widget / hívás paraméterlista folytatása.
            'Várd meg a választ, vagy szakítsd meg és lépj vissza.',
            // Widget / hívás paraméterlista folytatása.
            style: TextStyle(
              // Widget / hívás paraméterlista folytatása.
              color: LumeeiTheme.textPrimary,
              // Widget / hívás paraméterlista folytatása.
              fontSize: 15,
              // Widget / hívás paraméterlista folytatása.
              height: 1.4,
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Kódsor: részlet a fenti logikából.
          actions: [
            // Widget / hívás paraméterlista folytatása.
            TextButton(
              // Widget / hívás paraméterlista folytatása.
              onPressed: () => Navigator.of(ctx).pop(_BusyLeaveAction.stay),
              // Widget / hívás paraméterlista folytatása.
              child: const Text(
                // Widget / hívás paraméterlista folytatása.
                'Várok',
                // Widget / hívás paraméterlista folytatása.
                style: TextStyle(color: LumeeiTheme.textSecondary),
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
            // Widget / hívás paraméterlista folytatása.
            TextButton(
              // Értékadás / mezőkitöltés.
              onPressed: () =>
                  // Képernyőnavigáció.
                  Navigator.of(ctx).pop(_BusyLeaveAction.cancelAndLeave),
              // Widget / hívás paraméterlista folytatása.
              child: const Text(
                // Widget / hívás paraméterlista folytatása.
                'Megszakítás',
                // Widget / hívás paraméterlista folytatása.
                style: TextStyle(
                  // Widget / hívás paraméterlista folytatása.
                  color: LumeeiTheme.cyan,
                  // Widget / hívás paraméterlista folytatása.
                  fontWeight: FontWeight.w700,
                // Widget / hívás paraméterlista folytatása.
                ),
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ],
        // Utasítás vége.
        );
      // Blokk / szerkezet zárójele.
      },
    // Utasítás vége.
    );
    // Értékadás / mezőkitöltés.
    _busyLeaveDialogOpen = false;

    // Feltételes elágazás.
    if (!mounted || action != _BusyLeaveAction.cancelAndLeave) return;

    // Aszinkron művelet megvárása.
    await _tts.stop();
    // Aszinkron művelet megvárása.
    await _chat.stopGeneration();
    // Feltételes elágazás.
    if (!mounted) return;
    // UI újrarajzolás kérése állapotváltozás után.
    setState(() {
      // Értékadás / mezőkitöltés.
      _sendInFlight = false;
      // Értékadás / mezőkitöltés.
      _ttsSpeaking = false;
      // Értékadás / mezőkitöltés.
      _speakingMessageId = null;
    // Blokk / szerkezet zárójele.
    });
    // Képernyőnavigáció.
    Navigator.of(context).pop();
  // Blokk / osztály vége.
  }

  // Nincs visszatérési érték.
  void _scrollToBottom() {
    // Widget / hívás paraméterlista folytatása.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Feltételes elágazás.
      if (!_scrollController.hasClients) return;
      // Widget / hívás paraméterlista folytatása.
      _scrollController.animateTo(
        // Widget / hívás paraméterlista folytatása.
        _scrollController.position.maxScrollExtent,
        // Widget / hívás paraméterlista folytatása.
        duration: const Duration(milliseconds: 260),
        // Widget / hívás paraméterlista folytatása.
        curve: Curves.easeOutCubic,
      // Utasítás vége.
      );
    // Blokk / szerkezet zárójele.
    });
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return PopScope(
      // Widget / hívás paraméterlista folytatása.
      canPop: !_interactionLocked,
      // Widget / hívás paraméterlista folytatása.
      onPopInvokedWithResult: (didPop, result) {
        // Feltételes elágazás.
        if (didPop) return;
        // Fut a háttérben, nem várjuk meg.
        unawaited(_handleBackRequest());
      // Blokk / szerkezet zárójele.
      },
      // Widget / hívás paraméterlista folytatása.
      child: Theme(
        // Widget / hívás paraméterlista folytatása.
        data: LumeeiTheme.dark(),
        // Widget / hívás paraméterlista folytatása.
        child: Scaffold(
          // Widget / hívás paraméterlista folytatása.
          backgroundColor: LumeeiTheme.voidBlack,
          // Widget / hívás paraméterlista folytatása.
          body: DecoratedBox(
            // Widget / hívás paraméterlista folytatása.
            decoration: const BoxDecoration(
              // Widget / hívás paraméterlista folytatása.
              gradient: LinearGradient(
                // Widget / hívás paraméterlista folytatása.
                begin: Alignment.topCenter,
                // Widget / hívás paraméterlista folytatása.
                end: Alignment.bottomCenter,
                // Kódsor: részlet a fenti logikából.
                colors: [
                  // Widget / hívás paraméterlista folytatása.
                  Color(0xFF0C1020),
                  // Widget / hívás paraméterlista folytatása.
                  LumeeiTheme.voidBlack,
                  // Widget / hívás paraméterlista folytatása.
                  Color(0xFF0A0614),
                // Widget / hívás paraméterlista folytatása.
                ],
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
            // Widget / hívás paraméterlista folytatása.
            child: SafeArea(
              // Widget / hívás paraméterlista folytatása.
              child: Column(
                // Kódsor: részlet a fenti logikából.
                children: [
                  // Widget / hívás paraméterlista folytatása.
                  _HeaderBar(
                    // Widget / hívás paraméterlista folytatása.
                    showBack: widget.showBackButton,
                    // Widget / hívás paraméterlista folytatása.
                    onBack: _handleBackRequest,
                    // Kódsor: részlet a fenti logikából.
                    onClear: _interactionLocked
                        // Kódsor: részlet a fenti logikából.
                        ? null
                        // Widget / hívás paraméterlista folytatása.
                        : () async {
                            // Aszinkron művelet megvárása.
                            await _tts.stop();
                            // Feltételes elágazás.
                            if (!mounted) return;
                            // UI újrarajzolás kérése állapotváltozás után.
                            setState(() {
                              // Értékadás / mezőkitöltés.
                              _ttsSpeaking = false;
                              // Értékadás / mezőkitöltés.
                              _speakingMessageId = null;
                            // Blokk / szerkezet zárójele.
                            });
                            // Utasítás vége.
                            _chat.clearHistory();
                          // Blokk / szerkezet zárójele.
                          },
                  // Widget / hívás paraméterlista folytatása.
                  ),
                  // Feltételes elágazás.
                  if (_books.isNotEmpty)
                    // Widget / hívás paraméterlista folytatása.
                    _BookPicker(
                      // Widget / hívás paraméterlista folytatása.
                      books: _books,
                      // Widget / hívás paraméterlista folytatása.
                      selectedId: _selectedBookId,
                      // Widget / hívás paraméterlista folytatása.
                      enabled: !_interactionLocked,
                      // Widget / hívás paraméterlista folytatása.
                      onSelected: _selectBook,
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  Expanded(
                    // Widget / hívás paraméterlista folytatása.
                    child: _ChatBody(
                      // Widget / hívás paraméterlista folytatása.
                      messages: _chat.messages,
                      // Widget / hívás paraméterlista folytatása.
                      scrollController: _scrollController,
                      // Widget / hívás paraméterlista folytatása.
                      speakingMessageId: _speakingMessageId,
                      // Widget / hívás paraméterlista folytatása.
                      onSpeak: _speakAnswer,
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  ),
                  // Feltételes elágazás.
                  if (_interactionLocked) const _ThinkingBar(),
                  // Widget / hívás paraméterlista folytatása.
                  _Composer(
                    // Widget / hívás paraméterlista folytatása.
                    controller: _inputController,
                    // Widget / hívás paraméterlista folytatása.
                    focusNode: _focusNode,
                    // Widget / hívás paraméterlista folytatása.
                    enabled: !_interactionLocked,
                    // Widget / hívás paraméterlista folytatása.
                    onSend: _send,
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ],
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ),
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Enum (felsorolás) típus.
enum _BusyLeaveAction { stay, cancelAndLeave }

// Osztály definíció kezdete.
class _BookPicker extends StatelessWidget {
  // Fordítási idejű konstans.
  const _BookPicker({
    // Widget / hívás paraméterlista folytatása.
    required this.books,
    // Widget / hívás paraméterlista folytatása.
    required this.selectedId,
    // Widget / hívás paraméterlista folytatása.
    required this.enabled,
    // Widget / hívás paraméterlista folytatása.
    required this.onSelected,
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final List<TextbookOption> books;
  // Változó / mező: egyszer állítható érték.
  final String? selectedId;
  // Változó / mező: egyszer állítható érték.
  final bool enabled;
  // Változó / mező: egyszer állítható érték.
  final ValueChanged<String> onSelected;

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return Padding(
      // Widget / hívás paraméterlista folytatása.
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
      // Widget / hívás paraméterlista folytatása.
      child: Column(
        // Widget / hívás paraméterlista folytatása.
        crossAxisAlignment: CrossAxisAlignment.start,
        // Kódsor: részlet a fenti logikából.
        children: [
          // Fordítási idejű konstans.
          const Text(
            // Widget / hívás paraméterlista folytatása.
            'Tankönyv / év',
            // Widget / hívás paraméterlista folytatása.
            style: TextStyle(
              // Widget / hívás paraméterlista folytatása.
              color: LumeeiTheme.textSecondary,
              // Widget / hívás paraméterlista folytatása.
              fontSize: 12,
              // Widget / hívás paraméterlista folytatása.
              fontWeight: FontWeight.w600,
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Fordítási idejű konstans.
          const SizedBox(height: 8),
          // Widget / hívás paraméterlista folytatása.
          SingleChildScrollView(
            // Widget / hívás paraméterlista folytatása.
            scrollDirection: Axis.horizontal,
            // Widget / hívás paraméterlista folytatása.
            child: Row(
              // Kódsor: részlet a fenti logikából.
              children: [
                // Ciklus a listán / tartományon.
                for (final book in books) ...[
                  // Widget / hívás paraméterlista folytatása.
                  _BookChip(
                    // Widget / hívás paraméterlista folytatása.
                    label: book.title,
                    // Widget / hívás paraméterlista folytatása.
                    selected: book.documentId == selectedId,
                    // Widget / hívás paraméterlista folytatása.
                    enabled: enabled,
                    // Widget / hívás paraméterlista folytatása.
                    onTap: () => onSelected(book.documentId),
                  // Widget / hívás paraméterlista folytatása.
                  ),
                  // Fordítási idejű konstans.
                  const SizedBox(width: 8),
                // Widget / hívás paraméterlista folytatása.
                ],
              // Widget / hívás paraméterlista folytatása.
              ],
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ],
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _BookChip extends StatelessWidget {
  // Fordítási idejű konstans.
  const _BookChip({
    // Widget / hívás paraméterlista folytatása.
    required this.label,
    // Widget / hívás paraméterlista folytatása.
    required this.selected,
    // Widget / hívás paraméterlista folytatása.
    required this.enabled,
    // Widget / hívás paraméterlista folytatása.
    required this.onTap,
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final String label;
  // Változó / mező: egyszer állítható érték.
  final bool selected;
  // Változó / mező: egyszer állítható érték.
  final bool enabled;
  // Változó / mező: egyszer állítható érték.
  final VoidCallback onTap;

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return Opacity(
      // Widget / hívás paraméterlista folytatása.
      opacity: enabled ? 1 : 0.5,
      // Widget / hívás paraméterlista folytatása.
      child: Material(
        // Widget / hívás paraméterlista folytatása.
        color: Colors.transparent,
        // Widget / hívás paraméterlista folytatása.
        child: InkWell(
          // Widget / hívás paraméterlista folytatása.
          onTap: enabled ? onTap : null,
          // Widget / hívás paraméterlista folytatása.
          borderRadius: BorderRadius.circular(22),
          // Widget / hívás paraméterlista folytatása.
          child: Ink(
            // Widget / hívás paraméterlista folytatása.
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            // Widget / hívás paraméterlista folytatása.
            decoration: BoxDecoration(
              // Widget / hívás paraméterlista folytatása.
              borderRadius: BorderRadius.circular(22),
              // Widget / hívás paraméterlista folytatása.
              gradient: selected ? LumeeiTheme.brandGradient : null,
              // Widget / hívás paraméterlista folytatása.
              color: selected ? null : LumeeiTheme.surfaceElevated,
              // Widget / hívás paraméterlista folytatása.
              border: Border.all(
                // Kódsor: részlet a fenti logikából.
                color:
                    // Widget / hívás paraméterlista folytatása.
                    selected ? Colors.transparent : const Color(0x33FFFFFF),
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
            // Widget / hívás paraméterlista folytatása.
            child: Text(
              // Widget / hívás paraméterlista folytatása.
              label,
              // Widget / hívás paraméterlista folytatása.
              style: TextStyle(
                // Widget / hívás paraméterlista folytatása.
                color: selected ? Colors.white : LumeeiTheme.textSecondary,
                // Widget / hívás paraméterlista folytatása.
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                // Widget / hívás paraméterlista folytatása.
                fontSize: 13,
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ),
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _HeaderBar extends StatelessWidget {
  // Fordítási idejű konstans.
  const _HeaderBar({
    // Widget / hívás paraméterlista folytatása.
    required this.showBack,
    // Widget / hívás paraméterlista folytatása.
    required this.onBack,
    // Widget / hívás paraméterlista folytatása.
    required this.onClear,
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final bool showBack;
  // Változó / mező: egyszer állítható érték.
  final VoidCallback onBack;
  // Változó / mező: egyszer állítható érték.
  final VoidCallback? onClear;

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return Padding(
      // Widget / hívás paraméterlista folytatása.
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 4),
      // Widget / hívás paraméterlista folytatása.
      child: Row(
        // Kódsor: részlet a fenti logikából.
        children: [
          // Feltételes elágazás.
          if (showBack)
            // Widget / hívás paraméterlista folytatása.
            IconButton(
              // Widget / hívás paraméterlista folytatása.
              onPressed: onBack,
              // Widget / hívás paraméterlista folytatása.
              icon: const Icon(Icons.arrow_back_rounded),
              // Widget / hívás paraméterlista folytatása.
              color: LumeeiTheme.textPrimary,
            // Kódsor: részlet a fenti logikából.
            )
          // Kódsor: részlet a fenti logikából.
          else
            // Fordítási idejű konstans.
            const SizedBox(width: 12),
          // Widget / hívás paraméterlista folytatása.
          ClipRRect(
            // Widget / hívás paraméterlista folytatása.
            borderRadius: BorderRadius.circular(12),
            // Widget / hívás paraméterlista folytatása.
            child: Image.asset(
              // Widget / hívás paraméterlista folytatása.
              _kBrandAsset,
              // Widget / hívás paraméterlista folytatása.
              width: 40,
              // Widget / hívás paraméterlista folytatása.
              height: 40,
              // Widget / hívás paraméterlista folytatása.
              fit: BoxFit.cover,
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Fordítási idejű konstans.
          const SizedBox(width: 12),
          // Fordítási idejű konstans.
          const Expanded(
            // Widget / hívás paraméterlista folytatása.
            child: Column(
              // Widget / hívás paraméterlista folytatása.
              crossAxisAlignment: CrossAxisAlignment.start,
              // Kódsor: részlet a fenti logikából.
              children: [
                // Widget / hívás paraméterlista folytatása.
                Text(
                  // Widget / hívás paraméterlista folytatása.
                  'LUMEEI AI Mind',
                  // Widget / hívás paraméterlista folytatása.
                  style: TextStyle(
                    // Widget / hívás paraméterlista folytatása.
                    color: LumeeiTheme.textPrimary,
                    // Widget / hívás paraméterlista folytatása.
                    fontSize: 18,
                    // Widget / hívás paraméterlista folytatása.
                    fontWeight: FontWeight.w700,
                    // Widget / hívás paraméterlista folytatása.
                    letterSpacing: 0.2,
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ),
                // Widget / hívás paraméterlista folytatása.
                Text(
                  // Widget / hívás paraméterlista folytatása.
                  'Tananyag-asszisztens',
                  // Widget / hívás paraméterlista folytatása.
                  style: TextStyle(
                    // Widget / hívás paraméterlista folytatása.
                    color: LumeeiTheme.textSecondary,
                    // Widget / hívás paraméterlista folytatása.
                    fontSize: 12,
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ),
              // Widget / hívás paraméterlista folytatása.
              ],
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Widget / hívás paraméterlista folytatása.
          IconButton(
            // Widget / hívás paraméterlista folytatása.
            tooltip: 'Új beszélgetés',
            // Widget / hívás paraméterlista folytatása.
            onPressed: onClear,
            // Widget / hívás paraméterlista folytatása.
            icon: const Icon(Icons.refresh_rounded),
            // Widget / hívás paraméterlista folytatása.
            color: LumeeiTheme.textSecondary,
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ],
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _ChatBody extends StatelessWidget {
  // Fordítási idejű konstans.
  const _ChatBody({
    // Widget / hívás paraméterlista folytatása.
    required this.messages,
    // Widget / hívás paraméterlista folytatása.
    required this.scrollController,
    // Widget / hívás paraméterlista folytatása.
    required this.speakingMessageId,
    // Widget / hívás paraméterlista folytatása.
    required this.onSpeak,
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final List<ChatMessage> messages;
  // Változó / mező: egyszer állítható érték.
  final ScrollController scrollController;
  // Változó / mező: egyszer állítható érték.
  final String? speakingMessageId;
  // Változó / mező: egyszer állítható érték.
  final ValueChanged<ChatMessage> onSpeak;

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Feltételes elágazás.
    if (messages.isEmpty) return const _EmptyState();
    // Visszatérési érték a hívónak.
    return ListView.builder(
      // Widget / hívás paraméterlista folytatása.
      controller: scrollController,
      // Widget / hívás paraméterlista folytatása.
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      // Widget / hívás paraméterlista folytatása.
      itemCount: messages.length,
      // Widget / hívás paraméterlista folytatása.
      itemBuilder: (context, index) {
        // Változó / mező: egyszer állítható érték.
        final message = messages[index];
        // Visszatérési érték a hívónak.
        return _MessageBubble(
          // Widget / hívás paraméterlista folytatása.
          message: message,
          // Widget / hívás paraméterlista folytatása.
          isSpeaking: speakingMessageId == message.id,
          // Értékadás / mezőkitöltés.
          onSpeak: message.role == ChatRole.assistant &&
                  // Kódsor: részlet a fenti logikából.
                  !message.isStreaming &&
                  // Kódsor: részlet a fenti logikából.
                  message.content.trim().isNotEmpty
              // Értékadás / mezőkitöltés.
              ? () => onSpeak(message)
              // Widget / hívás paraméterlista folytatása.
              : null,
        // Utasítás vége.
        );
      // Blokk / szerkezet zárójele.
      },
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _EmptyState extends StatelessWidget {
  // Fordítási idejű konstans.
  const _EmptyState();

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return Center(
      // Widget / hívás paraméterlista folytatása.
      child: Padding(
        // Widget / hívás paraméterlista folytatása.
        padding: const EdgeInsets.symmetric(horizontal: 36),
        // Widget / hívás paraméterlista folytatása.
        child: Column(
          // Widget / hívás paraméterlista folytatása.
          mainAxisAlignment: MainAxisAlignment.center,
          // Kódsor: részlet a fenti logikából.
          children: [
            // Widget / hívás paraméterlista folytatása.
            Container(
              // Widget / hívás paraméterlista folytatása.
              padding: const EdgeInsets.all(18),
              // Widget / hívás paraméterlista folytatása.
              decoration: BoxDecoration(
                // Widget / hívás paraméterlista folytatása.
                shape: BoxShape.circle,
                // Widget / hívás paraméterlista folytatása.
                gradient: LumeeiTheme.softGlow,
                // Widget / hívás paraméterlista folytatása.
                border: Border.all(color: const Color(0x33FFFFFF)),
              // Widget / hívás paraméterlista folytatása.
              ),
              // Widget / hívás paraméterlista folytatása.
              child: Image.asset(_kBrandAsset, width: 88, height: 88),
            // Widget / hívás paraméterlista folytatása.
            ),
            // Fordítási idejű konstans.
            const SizedBox(height: 24),
            // Widget / hívás paraméterlista folytatása.
            ShaderMask(
              // Értékadás / mezőkitöltés.
              shaderCallback: (bounds) =>
                  // Widget / hívás paraméterlista folytatása.
                  LumeeiTheme.brandGradient.createShader(bounds),
              // Widget / hívás paraméterlista folytatása.
              child: const Text(
                // Widget / hívás paraméterlista folytatása.
                'Kérdezz nyugodtan a tananyagról',
                // Widget / hívás paraméterlista folytatása.
                textAlign: TextAlign.center,
                // Widget / hívás paraméterlista folytatása.
                style: TextStyle(
                  // Widget / hívás paraméterlista folytatása.
                  color: Colors.white,
                  // Widget / hívás paraméterlista folytatása.
                  fontSize: 20,
                  // Widget / hívás paraméterlista folytatása.
                  fontWeight: FontWeight.w700,
                // Widget / hívás paraméterlista folytatása.
                ),
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
            // Fordítási idejű konstans.
            const SizedBox(height: 10),
            // Fordítási idejű konstans.
            const Text(
              // Kódsor: részlet a fenti logikából.
              'Például: „Ki volt a bölcsesség istennője?” vagy '
              // Widget / hívás paraméterlista folytatása.
              '„Mikor volt az első olimpia?”',
              // Widget / hívás paraméterlista folytatása.
              textAlign: TextAlign.center,
              // Widget / hívás paraméterlista folytatása.
              style: TextStyle(
                // Widget / hívás paraméterlista folytatása.
                color: LumeeiTheme.textSecondary,
                // Widget / hívás paraméterlista folytatása.
                height: 1.4,
              // Widget / hívás paraméterlista folytatása.
              ),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ],
        // Widget / hívás paraméterlista folytatása.
        ),
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _MessageBubble extends StatelessWidget {
  // Fordítási idejű konstans.
  const _MessageBubble({
    // Widget / hívás paraméterlista folytatása.
    required this.message,
    // Widget / hívás paraméterlista folytatása.
    required this.isSpeaking,
    // Widget / hívás paraméterlista folytatása.
    this.onSpeak,
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final ChatMessage message;
  // Változó / mező: egyszer állítható érték.
  final bool isSpeaking;
  // Változó / mező: egyszer állítható érték.
  final VoidCallback? onSpeak;

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Változó / mező: egyszer állítható érték.
    final isUser = message.role == ChatRole.user;
    // Változó / mező: egyszer állítható érték.
    final text = message.content.isEmpty && message.isStreaming
        // Kódsor: részlet a fenti logikából.
        ? '…'
        // Utasítás vége.
        : message.content;

    // Visszatérési érték a hívónak.
    return Align(
      // Widget / hívás paraméterlista folytatása.
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      // Widget / hívás paraméterlista folytatása.
      child: ConstrainedBox(
        // Widget / hívás paraméterlista folytatása.
        constraints: BoxConstraints(
          // Widget / hívás paraméterlista folytatása.
          maxWidth: MediaQuery.sizeOf(context).width * 0.86,
        // Widget / hívás paraméterlista folytatása.
        ),
        // Widget / hívás paraméterlista folytatása.
        child: Container(
          // Widget / hívás paraméterlista folytatása.
          margin: const EdgeInsets.only(bottom: 12),
          // Widget / hívás paraméterlista folytatása.
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          // Widget / hívás paraméterlista folytatása.
          decoration: BoxDecoration(
            // Kódsor: részlet a fenti logikából.
            gradient: isUser
                // Widget / hívás paraméterlista folytatása.
                ? const LinearGradient(
                    // Widget / hívás paraméterlista folytatása.
                    colors: [Color(0xFF1E3A5F), Color(0xFF2A1B4A)],
                  // Kódsor: részlet a fenti logikából.
                  )
                // Widget / hívás paraméterlista folytatása.
                : null,
            // Widget / hívás paraméterlista folytatása.
            color: isUser ? null : LumeeiTheme.surfaceElevated,
            // Widget / hívás paraméterlista folytatása.
            borderRadius: BorderRadius.only(
              // Widget / hívás paraméterlista folytatása.
              topLeft: const Radius.circular(20),
              // Widget / hívás paraméterlista folytatása.
              topRight: const Radius.circular(20),
              // Widget / hívás paraméterlista folytatása.
              bottomLeft: Radius.circular(isUser ? 20 : 6),
              // Widget / hívás paraméterlista folytatása.
              bottomRight: Radius.circular(isUser ? 6 : 20),
            // Widget / hívás paraméterlista folytatása.
            ),
            // Widget / hívás paraméterlista folytatása.
            border: Border.all(
              // Kódsor: részlet a fenti logikából.
              color: isUser
                  // Kódsor: részlet a fenti logikából.
                  ? const Color(0x4400E5FF)
                  // Widget / hívás paraméterlista folytatása.
                  : const Color(0x22FFFFFF),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Widget / hívás paraméterlista folytatása.
          child: Column(
            // Widget / hívás paraméterlista folytatása.
            crossAxisAlignment: CrossAxisAlignment.start,
            // Kódsor: részlet a fenti logikából.
            children: [
              // Widget / hívás paraméterlista folytatása.
              Text(
                // Widget / hívás paraméterlista folytatása.
                text,
                // Widget / hívás paraméterlista folytatása.
                style: const TextStyle(
                  // Widget / hívás paraméterlista folytatása.
                  color: LumeeiTheme.textPrimary,
                  // Widget / hívás paraméterlista folytatása.
                  height: 1.4,
                  // Widget / hívás paraméterlista folytatása.
                  fontSize: 15.5,
                // Widget / hívás paraméterlista folytatása.
                ),
              // Widget / hívás paraméterlista folytatása.
              ),
              // Feltételes elágazás.
              if (!isUser && onSpeak != null) ...[
                // Fordítási idejű konstans.
                const SizedBox(height: 8),
                // Widget / hívás paraméterlista folytatása.
                Align(
                  // Widget / hívás paraméterlista folytatása.
                  alignment: Alignment.centerRight,
                  // Widget / hívás paraméterlista folytatása.
                  child: Material(
                    // Widget / hívás paraméterlista folytatása.
                    color: Colors.transparent,
                    // Widget / hívás paraméterlista folytatása.
                    child: InkWell(
                      // Widget / hívás paraméterlista folytatása.
                      onTap: onSpeak,
                      // Widget / hívás paraméterlista folytatása.
                      borderRadius: BorderRadius.circular(20),
                      // Widget / hívás paraméterlista folytatása.
                      child: Ink(
                        // Widget / hívás paraméterlista folytatása.
                        decoration: BoxDecoration(
                          // Widget / hívás paraméterlista folytatása.
                          borderRadius: BorderRadius.circular(20),
                          // Widget / hívás paraméterlista folytatása.
                          border: Border.all(
                            // Kódsor: részlet a fenti logikából.
                            color: isSpeaking
                                // Kódsor: részlet a fenti logikából.
                                ? LumeeiTheme.cyan.withValues(alpha: 0.7)
                                // Widget / hívás paraméterlista folytatása.
                                : const Color(0x33FFFFFF),
                          // Widget / hívás paraméterlista folytatása.
                          ),
                        // Widget / hívás paraméterlista folytatása.
                        ),
                        // Widget / hívás paraméterlista folytatása.
                        child: Padding(
                          // Widget / hívás paraméterlista folytatása.
                          padding: const EdgeInsets.symmetric(
                            // Widget / hívás paraméterlista folytatása.
                            horizontal: 10,
                            // Widget / hívás paraméterlista folytatása.
                            vertical: 6,
                          // Widget / hívás paraméterlista folytatása.
                          ),
                          // Widget / hívás paraméterlista folytatása.
                          child: Row(
                            // Widget / hívás paraméterlista folytatása.
                            mainAxisSize: MainAxisSize.min,
                            // Kódsor: részlet a fenti logikából.
                            children: [
                              // Widget / hívás paraméterlista folytatása.
                              Icon(
                                // Kódsor: részlet a fenti logikából.
                                isSpeaking
                                    // Kódsor: részlet a fenti logikából.
                                    ? Icons.stop_circle_outlined
                                    // Widget / hívás paraméterlista folytatása.
                                    : Icons.volume_up_rounded,
                                // Widget / hívás paraméterlista folytatása.
                                size: 18,
                                // Widget / hívás paraméterlista folytatása.
                                color: LumeeiTheme.cyan,
                              // Widget / hívás paraméterlista folytatása.
                              ),
                              // Fordítási idejű konstans.
                              const SizedBox(width: 6),
                              // Widget / hívás paraméterlista folytatása.
                              Text(
                                // Widget / hívás paraméterlista folytatása.
                                isSpeaking ? 'Leállítás' : 'Felolvasás',
                                // Widget / hívás paraméterlista folytatása.
                                style: const TextStyle(
                                  // Widget / hívás paraméterlista folytatása.
                                  color: LumeeiTheme.textSecondary,
                                  // Widget / hívás paraméterlista folytatása.
                                  fontSize: 12.5,
                                  // Widget / hívás paraméterlista folytatása.
                                  fontWeight: FontWeight.w600,
                                // Widget / hívás paraméterlista folytatása.
                                ),
                              // Widget / hívás paraméterlista folytatása.
                              ),
                            // Widget / hívás paraméterlista folytatása.
                            ],
                          // Widget / hívás paraméterlista folytatása.
                          ),
                        // Widget / hívás paraméterlista folytatása.
                        ),
                      // Widget / hívás paraméterlista folytatása.
                      ),
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ),
              // Widget / hívás paraméterlista folytatása.
              ],
            // Widget / hívás paraméterlista folytatása.
            ],
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ),
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _ThinkingBar extends StatelessWidget {
  // Fordítási idejű konstans.
  const _ThinkingBar();

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return const Padding(
      // Widget / hívás paraméterlista folytatása.
      padding: EdgeInsets.fromLTRB(24, 0, 24, 8),
      // Widget / hívás paraméterlista folytatása.
      child: Row(
        // Kódsor: részlet a fenti logikából.
        children: [
          // Widget / hívás paraméterlista folytatása.
          SizedBox(
            // Widget / hívás paraméterlista folytatása.
            width: 14,
            // Widget / hívás paraméterlista folytatása.
            height: 14,
            // Widget / hívás paraméterlista folytatása.
            child: CircularProgressIndicator(
              // Widget / hívás paraméterlista folytatása.
              strokeWidth: 2,
              // Widget / hívás paraméterlista folytatása.
              color: LumeeiTheme.cyan,
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Widget / hívás paraméterlista folytatása.
          SizedBox(width: 10),
          // Widget / hívás paraméterlista folytatása.
          Text(
            // Widget / hívás paraméterlista folytatása.
            'Gondolkodom a tananyag alapján…',
            // Widget / hívás paraméterlista folytatása.
            style: TextStyle(
              // Widget / hívás paraméterlista folytatása.
              color: LumeeiTheme.textSecondary,
              // Widget / hívás paraméterlista folytatása.
              fontSize: 12.5,
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ],
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

// Osztály definíció kezdete.
class _Composer extends StatelessWidget {
  // Fordítási idejű konstans.
  const _Composer({
    // Widget / hívás paraméterlista folytatása.
    required this.controller,
    // Widget / hívás paraméterlista folytatása.
    required this.focusNode,
    // Widget / hívás paraméterlista folytatása.
    required this.enabled,
    // Widget / hívás paraméterlista folytatása.
    required this.onSend,
  // Blokk / szerkezet zárójele.
  });

  // Változó / mező: egyszer állítható érték.
  final TextEditingController controller;
  // Változó / mező: egyszer állítható érték.
  final FocusNode focusNode;
  // Változó / mező: egyszer állítható érték.
  final bool enabled;
  // Változó / mező: egyszer állítható érték.
  final VoidCallback onSend;

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return Padding(
      // Widget / hívás paraméterlista folytatása.
      padding: const EdgeInsets.fromLTRB(14, 4, 14, 14),
      // Widget / hívás paraméterlista folytatása.
      child: Row(
        // Widget / hívás paraméterlista folytatása.
        crossAxisAlignment: CrossAxisAlignment.end,
        // Kódsor: részlet a fenti logikából.
        children: [
          // Widget / hívás paraméterlista folytatása.
          Expanded(
            // Widget / hívás paraméterlista folytatása.
            child: TextField(
              // Widget / hívás paraméterlista folytatása.
              controller: controller,
              // Widget / hívás paraméterlista folytatása.
              focusNode: focusNode,
              // Widget / hívás paraméterlista folytatása.
              enabled: enabled,
              // Widget / hívás paraméterlista folytatása.
              minLines: 1,
              // Widget / hívás paraméterlista folytatása.
              maxLines: 5,
              // Widget / hívás paraméterlista folytatása.
              textInputAction: TextInputAction.send,
              // Widget / hívás paraméterlista folytatása.
              style: const TextStyle(color: LumeeiTheme.textPrimary),
              // Widget / hívás paraméterlista folytatása.
              decoration: const InputDecoration(
                // Widget / hívás paraméterlista folytatása.
                hintText: 'Kérdezz a tananyagról…',
              // Widget / hívás paraméterlista folytatása.
              ),
              // Widget / hívás paraméterlista folytatása.
              onSubmitted: (_) => onSend(),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Fordítási idejű konstans.
          const SizedBox(width: 10),
          // Widget / hívás paraméterlista folytatása.
          DecoratedBox(
            // Widget / hívás paraméterlista folytatása.
            decoration: BoxDecoration(
              // Widget / hívás paraméterlista folytatása.
              shape: BoxShape.circle,
              // Widget / hívás paraméterlista folytatása.
              gradient: enabled ? LumeeiTheme.brandGradient : null,
              // Widget / hívás paraméterlista folytatása.
              color: enabled ? null : const Color(0xFF2A2A36),
            // Widget / hívás paraméterlista folytatása.
            ),
            // Widget / hívás paraméterlista folytatása.
            child: IconButton(
              // Widget / hívás paraméterlista folytatása.
              onPressed: enabled ? onSend : null,
              // Widget / hívás paraméterlista folytatása.
              icon: const Icon(Icons.send_rounded),
              // Widget / hívás paraméterlista folytatása.
              color: Colors.white,
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ],
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

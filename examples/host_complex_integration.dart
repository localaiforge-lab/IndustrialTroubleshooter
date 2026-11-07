/// Példa: komplex host (saját shell + FAB + lazy/eager init).
///
/// Illeszd a saját Routered / DI-d mellé – a lényeg a három hívás:
/// 1) `LumeeiAiMind.initialize`
/// 2) `LumeeiAiMind.openChat` vagy `chatScreen`
/// 3) host INTERNET + assets/config + assets/branding (lásd docs/Lumeei_AI_Mind_Integracio.md)
library;

import 'package:educational_chatbot/lumeei_ai_mind.dart';
import 'package:flutter/material.dart';

/// Hívd a host splash végén VAGY az első chat nyitás előtt.
Future<void> ensureAiMindReady(
  void Function(String status, double? progress)? onProgress,
) {
  return LumeeiAiMind.initialize(onProgress: onProgress);
}

class HostHomeWithAiMindFab extends StatelessWidget {
  const HostHomeWithAiMindFab({super.key});

  Future<void> _onFab(BuildContext context) async {
    if (!LumeeiAiMind.isInitialized) {
      showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (_) => const Center(child: CircularProgressIndicator()),
      );
      try {
        await ensureAiMindReady(null);
      } finally {
        if (context.mounted) Navigator.of(context).pop();
      }
    }
    if (!context.mounted) return;
    await LumeeiAiMind.openChat(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('LUMEEI host példa')),
      body: const Center(
        child: Text('A FAB megnyitja a tananyag-chatbotot.'),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _onFab(context),
        child: const Icon(Icons.auto_awesome),
      ),
    );
  }
}

/// go_router / AutoRoute stílusú route builder.
Widget aiMindRouteBuilder(BuildContext context, {bool showBack = true}) {
  assert(
    LumeeiAiMind.isInitialized,
    'Hívd LumeeiAiMind.initialize()-t a route elé.',
  );
  return LumeeiAiMind.chatScreen(showBackButton: showBack);
}

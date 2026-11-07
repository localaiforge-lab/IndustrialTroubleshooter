/// Példa: legegyszerűbb host – a LUMEEI AI Mind a teljes app.
///
/// Használat demóként (másold `lib/main.dart` helyére ideiglenesen),
/// vagy másold a mintát a saját host `main.dart`-jába.
library;

import 'package:educational_chatbot/lumeei_ai_mind.dart';
import 'package:flutter/material.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  runApp(const _Boot());
}

class _Boot extends StatefulWidget {
  const _Boot();

  @override
  State<_Boot> createState() => _BootState();
}

class _BootState extends State<_Boot> {
  String _status = 'Indítás…';
  double? _progress;
  Object? _error;
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    try {
      await LumeeiAiMind.initialize(
        onProgress: (s, p) {
          if (!mounted) return;
          setState(() {
            _status = s;
            _progress = p;
          });
        },
      );
      if (!mounted) return;
      setState(() => _ready = true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return MaterialApp(
        home: Scaffold(body: Center(child: Text('Hiba: $_error'))),
      );
    }
    if (!_ready) {
      return MaterialApp(
        home: Scaffold(
          body: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (_progress != null)
                  SizedBox(
                    width: 240,
                    child: LinearProgressIndicator(value: _progress),
                  ),
                const SizedBox(height: 16),
                Text(_status),
              ],
            ),
          ),
        ),
      );
    }

    // Egyszerű: egyből a chat.
    return MaterialApp(
      theme: LumeeiAiMind.theme,
      home: LumeeiAiMind.chatScreen(showBackButton: false),
    );
  }
}

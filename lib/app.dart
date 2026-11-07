// A fő képernyő (HomeScreen) importja – innen indul a demo shell UI.
import 'package:educational_chatbot/features/chat/presentation/screens/home_screen.dart';
// A sötét LUMEEI téma (színek, InputDecoration stb.).
import 'package:educational_chatbot/features/chat/presentation/theme/lumeei_theme.dart';
// Flutter Material widgetek (MaterialApp, ThemeMode…).
import 'package:flutter/material.dart';

/// Az alkalmazás gyökér widgetje a splash után.
class EducationalChatbotApp extends StatelessWidget {
  // Állapot nélküli widget; a key a Flutter fa azonosításhoz kell.
  const EducationalChatbotApp({super.key});

  // Felülírja a szülő/interfész metódusát.
  @override
  // A UI felépítése: egy MaterialApp a HomeScreennel.
  Widget build(BuildContext context) {
    // MaterialApp: navigáció, téma, kezdő route.
    return MaterialApp(
      // Kódsor: részlet a fenti logikából.
      title: 'LUMEEI AI Mind', // Feladatkezelőben megjelenő név.
      // Kódsor: részlet a fenti logikából.
      debugShowCheckedModeBanner: false, // Elrejti a DEBUG szalagot.
      // Kódsor: részlet a fenti logikából.
      theme: LumeeiTheme.dark(), // Világos módban is a sötét témát használjuk.
      // Kódsor: részlet a fenti logikából.
      darkTheme: LumeeiTheme.dark(), // Rendszer-sötét mód esetén ugyanez.
      // Kódsor: részlet a fenti logikából.
      themeMode: ThemeMode.dark, // Mindig sötét megjelenés.
      // Kódsor: részlet a fenti logikából.
      home: const HomeScreen(), // Első képernyő: host demo + FAB.
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

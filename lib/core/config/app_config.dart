// JSON dekódoláshoz (app_config.json).
import 'dart:convert';

// rootBundle: asset fájlok olvasása a csomagolt APK-ból.
import 'package:flutter/services.dart';

/// Futásidejű beállítások az [assets/config/app_config.json]-ból.
class AppConfig {
  // Csak a Cloud Run alap URL kell a vékony klienshez.
  const AppConfig({required this.cloudBaseUrl});

  // JSON Map → AppConfig objektum.
  factory AppConfig.fromJson(Map<String, dynamic> json) {
    // cloudBaseUrl kiolvasása, trim, üres esetén ''.
    final url = (json['cloudBaseUrl'] as String?)?.trim() ?? '';
    // Üres URL esetén azonnal hibát dobunk – az app nem tudna hová csatlakozni.
    if (url.isEmpty) {
      // Kivétel dobása.
      throw StateError('app_config.json: cloudBaseUrl hiányzik');
    // Blokk / osztály vége.
    }
    // Sikeres parse után visszaadjuk a konfigot.
    return AppConfig(cloudBaseUrl: url);
  // Blokk / osztály vége.
  }

  // Assetből betölti és parse-olja a JSON-t.
  static Future<AppConfig> load() async {
    // A JSON szöveg beolvasása a Flutter asset bundle-ből.
    final raw = await rootBundle.loadString('assets/config/app_config.json');
    // Szöveg → Map → AppConfig.
    return AppConfig.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  // Blokk / osztály vége.
  }

  // A Cloud Run (vagy helyi) szolgáltatás HTTPS címe.
  final String cloudBaseUrl;
// Blokk / osztály vége.
}

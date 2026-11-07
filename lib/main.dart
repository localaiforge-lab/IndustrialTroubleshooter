// Belépési pont: ez a fájl indul el először az app indításakor.
import 'package:educational_chatbot/bootstrap.dart'; // A bootstrap() függvényt innen hívjuk.

// Az Android/iOS/desktop a main()-t futtatja; továbbadjuk a vezérlést a bootstrapnak.
Future<void> main() => bootstrap(); // Aszinkron indítás, splash + Cloud Run ping.

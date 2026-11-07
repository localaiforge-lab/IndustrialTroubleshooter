package hu.educational.educational_chatbot

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine

class MainActivity : FlutterActivity() {

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        BundledModelChannel(this).register(flutterEngine.dartExecutor.binaryMessenger)
        NativeLibraryChannel(this).register(flutterEngine.dartExecutor.binaryMessenger)
        DeviceMemoryChannel(this).register(flutterEngine.dartExecutor.binaryMessenger)
        DiagnosticExportChannel(this).register(flutterEngine.dartExecutor.binaryMessenger)
        TtsInstallChannel(this).register(flutterEngine.dartExecutor.binaryMessenger)
    }
}

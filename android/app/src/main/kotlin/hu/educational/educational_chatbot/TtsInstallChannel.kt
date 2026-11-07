package hu.educational.educational_chatbot

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.speech.tts.TextToSpeech
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * Opens the system UI so the user can download TTS language packs
 * (e.g. Hungarian for Google Text-to-speech).
 */
class TtsInstallChannel(private val context: Context) :
    MethodChannel.MethodCallHandler {

    fun register(messenger: io.flutter.plugin.common.BinaryMessenger) {
        MethodChannel(messenger, CHANNEL).setMethodCallHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "openTtsVoiceInstall" -> {
                result.success(openTtsVoiceInstall())
            }
            else -> result.notImplemented()
        }
    }

    private fun openTtsVoiceInstall(): String {
        // 1) Official voice-data installer (engine-specific language packs).
        if (startSafe(Intent(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA))) {
            return "install_tts_data"
        }
        // 2) System TTS settings – user can manage / download voices.
        if (startSafe(Intent("com.android.settings.TTS_SETTINGS"))) {
            return "tts_settings"
        }
        // 3) Google Text-to-speech app on Play Store.
        val market = Intent(
            Intent.ACTION_VIEW,
            Uri.parse("market://details?id=com.google.android.tts"),
        ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (startSafe(market)) {
            return "play_store"
        }
        val web = Intent(
            Intent.ACTION_VIEW,
            Uri.parse(
                "https://play.google.com/store/apps/details?id=com.google.android.tts",
            ),
        ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (startSafe(web)) {
            return "web_store"
        }
        return "failed"
    }

    private fun startSafe(intent: Intent): Boolean {
        return try {
            val launch = Intent(intent).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(launch)
            true
        } catch (_: ActivityNotFoundException) {
            false
        } catch (_: Exception) {
            false
        }
    }

    companion object {
        private const val CHANNEL = "hu.educational.educational_chatbot/tts_install"
    }
}

package hu.educational.educational_chatbot

import android.content.ContentValues
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class DiagnosticExportChannel(private val activity: MainActivity) :
    MethodChannel.MethodCallHandler {

    fun register(messenger: io.flutter.plugin.common.BinaryMessenger) {
        MethodChannel(messenger, CHANNEL).setMethodCallHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "exportToDownloads" -> {
                val sourcePath = call.argument<String>("sourcePath")
                if (sourcePath.isNullOrBlank()) {
                    result.error("ARG", "sourcePath required", null)
                    return
                }
                try {
                    result.success(exportToDownloads(sourcePath))
                } catch (e: Exception) {
                    result.error("EXPORT", e.message, null)
                }
            }
            else -> result.notImplemented()
        }
    }

    private fun exportToDownloads(sourcePath: String): String {
        val source = File(sourcePath)
        if (!source.exists()) {
            throw IllegalArgumentException("Log file not found: $sourcePath")
        }

        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val displayName = "educational_chatbot_diag_$stamp.log"

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val resolver = activity.contentResolver
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, displayName)
                put(MediaStore.Downloads.MIME_TYPE, "text/plain")
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
                put(MediaStore.Downloads.IS_PENDING, 1)
            }
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: throw IllegalStateException("MediaStore insert failed")

            resolver.openOutputStream(uri)?.use { out ->
                source.inputStream().use { it.copyTo(out) }
            } ?: throw IllegalStateException("Cannot open output stream")

            values.clear()
            values.put(MediaStore.Downloads.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
            return "Letöltések/$displayName"
        }

        @Suppress("DEPRECATION")
        val downloadsDir =
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        if (!downloadsDir.exists()) downloadsDir.mkdirs()
        val dest = File(downloadsDir, displayName)
        source.copyTo(dest, overwrite = true)
        return dest.absolutePath
    }

    companion object {
        private const val CHANNEL =
            "hu.educational.educational_chatbot/diagnostic_export"
    }
}

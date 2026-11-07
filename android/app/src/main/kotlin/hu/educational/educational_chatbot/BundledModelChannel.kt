package hu.educational.educational_chatbot

import android.content.Context
import android.util.Log
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.FileOutputStream

/**
 * Streams large GGUF files from APK assets to app-internal storage (first launch).
 * Avoids loading multi-GB files into the Dart heap.
 */
class BundledModelChannel(private val context: Context) :
    MethodChannel.MethodCallHandler,
    EventChannel.StreamHandler {

    private var progressSink: EventChannel.EventSink? = null

    fun register(messenger: io.flutter.plugin.common.BinaryMessenger) {
        MethodChannel(messenger, METHOD_CHANNEL).setMethodCallHandler(this)
        EventChannel(messenger, PROGRESS_CHANNEL).setStreamHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "assetExists" -> {
                val assetPath = call.argument<String>("assetPath")
                if (assetPath.isNullOrBlank()) {
                    result.error("invalid_args", "assetPath required", null)
                    return
                }
                result.success(assetExists(assetPath))
            }
            "getAssetSize" -> {
                val assetPath = call.argument<String>("assetPath")
                if (assetPath.isNullOrBlank()) {
                    result.error("invalid_args", "assetPath required", null)
                    return
                }
                result.success(assetLength(assetPath))
            }
            "extractAsset" -> {
                val assetPath = call.argument<String>("assetPath")
                val destPath = call.argument<String>("destPath")
                if (assetPath.isNullOrBlank() || destPath.isNullOrBlank()) {
                    result.error("invalid_args", "assetPath and destPath required", null)
                    return
                }
                Thread {
                    try {
                        val path = extractAsset(assetPath, destPath)
                        context.mainExecutor.execute { result.success(path) }
                    } catch (e: Exception) {
                        Log.e(TAG, "extractAsset failed", e)
                        context.mainExecutor.execute {
                            result.error("extract_failed", e.message, null)
                        }
                    }
                }.start()
            }
            else -> result.notImplemented()
        }
    }

    private fun assetExists(assetPath: String): Boolean {
        return try {
            context.assets.open(assetPath).use { true }
        } catch (_: Exception) {
            false
        }
    }

    private fun extractAsset(assetPath: String, destPath: String): String {
        val dest = File(destPath)
        dest.parentFile?.mkdirs()

        val totalBytes = assetLength(assetPath)
        if (dest.exists()) {
            val existing = dest.length()
            if (totalBytes > 0 && existing == totalBytes) {
                emitProgress(1.0)
                return dest.absolutePath
            }
            if (existing > 0) {
                Log.w(TAG, "Deleting incomplete model: $existing bytes, expected $totalBytes")
                dest.delete()
            }
        }

        var copied = 0L

        context.assets.open(assetPath).use { input ->
            FileOutputStream(dest).use { output ->
                val buffer = ByteArray(BUFFER_SIZE)
                while (true) {
                    val read = input.read(buffer)
                    if (read <= 0) break
                    output.write(buffer, 0, read)
                    copied += read
                    if (totalBytes > 0) {
                        emitProgress(copied.toDouble() / totalBytes.toDouble())
                    }
                }
                output.fd.sync()
            }
        }

        val finalSize = dest.length()
        if (totalBytes > 0 && finalSize != totalBytes) {
            dest.delete()
            throw IllegalStateException(
                "Extract size mismatch: got $finalSize bytes, expected $totalBytes"
            )
        }

        emitProgress(1.0)
        Log.i(TAG, "Extracted $assetPath -> $destPath (${dest.length()} bytes)")
        return dest.absolutePath
    }

    private fun assetLength(assetPath: String): Long {
        return try {
            context.assets.openFd(assetPath).use { it.length }
        } catch (_: Exception) {
            -1L
        }
    }

    private fun emitProgress(value: Double) {
        context.mainExecutor.execute {
            progressSink?.success(value.coerceIn(0.0, 1.0))
        }
    }

    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        progressSink = events
    }

    override fun onCancel(arguments: Any?) {
        progressSink = null
    }

    companion object {
        private const val TAG = "BundledModelChannel"
        private const val METHOD_CHANNEL = "hu.educational.educational_chatbot/bundled_models"
        private const val PROGRESS_CHANNEL =
            "hu.educational.educational_chatbot/bundled_models_progress"
        private const val BUFFER_SIZE = 8 * 1024 * 1024
    }
}

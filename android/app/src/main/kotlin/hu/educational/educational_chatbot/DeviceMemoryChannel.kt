package hu.educational.educational_chatbot

import android.app.Activity
import android.app.ActivityManager
import android.content.Context
import android.os.PowerManager
import android.view.WindowManager
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class DeviceMemoryChannel(private val activity: Activity) :
    MethodChannel.MethodCallHandler {

    private var wakeLock: PowerManager.WakeLock? = null

    fun register(messenger: io.flutter.plugin.common.BinaryMessenger) {
        MethodChannel(messenger, CHANNEL).setMethodCallHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "getMemoryInfo" -> result.success(readMemoryInfo())
            "acquireCpuWakeLock" -> {
                acquireWakeLock()
                result.success(true)
            }
            "releaseCpuWakeLock" -> {
                releaseWakeLock()
                result.success(true)
            }
            "setKeepScreenOn" -> {
                val enabled = call.argument<Boolean>("enabled") ?: false
                activity.runOnUiThread {
                    if (enabled) {
                        activity.window.addFlags(
                            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                        )
                    } else {
                        activity.window.clearFlags(
                            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                        )
                    }
                }
                result.success(true)
            }
            else -> result.notImplemented()
        }
    }

    private fun readMemoryInfo(): Map<String, Any> {
        val am =
            activity.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val info = ActivityManager.MemoryInfo()
        am.getMemoryInfo(info)
        return mapOf(
            "availBytes" to info.availMem,
            "totalBytes" to info.totalMem,
            "thresholdBytes" to info.threshold,
            "lowMemory" to info.lowMemory,
        )
    }

    private fun acquireWakeLock() {
        if (wakeLock?.isHeld == true) return
        val pm = activity.getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "educational_chatbot::LlmInference",
        ).apply {
            setReferenceCounted(false)
            // Long enough for model unpack / translator / one answer turn.
            acquire(30 * 60 * 1000L)
        }
    }

    private fun releaseWakeLock() {
        wakeLock?.let {
            if (it.isHeld) it.release()
        }
        wakeLock = null
    }

    companion object {
        private const val CHANNEL = "hu.educational.educational_chatbot/device_memory"
    }
}

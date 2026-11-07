package hu.educational.educational_chatbot

import android.content.Context
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class NativeLibraryChannel(context: Context) : MethodChannel.MethodCallHandler {
    private val nativeLibraryDir = context.applicationInfo.nativeLibraryDir

    fun register(messenger: io.flutter.plugin.common.BinaryMessenger) {
        MethodChannel(messenger, CHANNEL).setMethodCallHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "getNativeLibraryDir" -> result.success(nativeLibraryDir)
            else -> result.notImplemented()
        }
    }

    companion object {
        private const val CHANNEL = "hu.educational.educational_chatbot/native_library"
    }
}

# Flutter
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Google Play Core (deferred components)
-keep class com.google.android.play.core.** { *; }
-dontwarn com.google.android.play.core.**

# MediaPipe (.task inference via flutter_gemma_mediapipe)
-keep class com.google.mediapipe.** { *; }
-dontwarn com.google.mediapipe.**
-dontwarn com.google.mediapipe.proto.CalculatorProfileProto*
-dontwarn com.google.mediapipe.proto.GraphTemplateProto*

# Protocol Buffers
-keep class com.google.protobuf.** { *; }
-dontwarn com.google.protobuf.**

# AutoValue (referenced by MediaPipe image API)
-dontwarn com.google.auto.value.extension.memoized.Memoized

# Kotlin coroutines
-keep class kotlinx.coroutines.** { *; }
-dontwarn kotlinx.coroutines.**

# ONNX Runtime (embedding) – R8 strips JNI bindings → silent freeze/crash in release
-keep class ai.onnxruntime.** { *; }
-keepclassmembers class ai.onnxruntime.** { *; }
-dontwarn ai.onnxruntime.**

# ObjectBox
-keep class io.objectbox.** { *; }
-dontwarn io.objectbox.**

# flutter_gemma / LiteRT / MediaPipe GenAI
-keep class com.google.ai.edge.** { *; }
-keep class com.google.android.libraries.aicore.** { *; }
-dontwarn com.google.ai.edge.**

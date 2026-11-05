plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}
val gstRoot = providers.gradleProperty("gstreamerRoot").orElse(providers.environmentVariable("GSTREAMER_ROOT_ANDROID"))
val gstAbis = providers.gradleProperty("gstAbis").orElse("armeabi-v7a").get().split(',')
android {
    namespace = "com.metrixneo.tv"
    compileSdk = 36
    ndkVersion = "25.2.9519653"
    defaultConfig {
        applicationId = "com.metrixneo.tv"
        minSdk = 26
        targetSdk = 35
        versionCode = 22
        versionName = "0.8.3-alpha"
        ndk { abiFilters.addAll(gstAbis) }
        externalNativeBuild {
            ndkBuild {
                arguments += "GSTREAMER_ROOT_ANDROID=${gstRoot.get()}"
                arguments += "GSTREAMER_JAVA_SRC_DIR=${project.layout.buildDirectory.dir("native-gstreamer/java").get().asFile.absolutePath.replace('\\', '/')}"
                arguments += "GSTREAMER_ASSETS_DIR=${project.layout.buildDirectory.dir("native-gstreamer/assets").get().asFile.absolutePath.replace('\\', '/')}"
            }
        }
    }
    buildFeatures { compose = true }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = true
            isShrinkResources = true
            // Local sideload keeps the existing app identity/data. Not a publishing key.
            signingConfig = signingConfigs.getByName("debug")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    packaging { resources { excludes += "/META-INF/{AL2.0,LGPL2.1}" } }
    externalNativeBuild { ndkBuild { path = file("src/main/jni/Android.mk") } }
    sourceSets.getByName("main") {
        java.srcDir(layout.buildDirectory.dir("generated/gstreamer/java"))
        assets.srcDir(layout.buildDirectory.dir("generated/gstreamer/assets"))
    }
}
// Generate Java and assets before Kotlin/resource tasks, independent of native task ordering.
val prepareGStreamerSupport = tasks.register("prepareGStreamerSupport") {
    val sdk = file(gstRoot.get()).resolve("armv7")
    val support = sdk.resolve("share/gst-android/ndk-build")
    val output = layout.buildDirectory.dir("generated/gstreamer")
    inputs.dir(support); inputs.dir(sdk.resolve("share/licenses")); inputs.file(sdk.resolve("etc/ssl/certs/ca-certificates.crt"))
    outputs.dir(output)
    doLast {
        val destination = output.get().asFile
        val javaDir = destination.resolve("java/org/freedesktop/gstreamer").apply { mkdirs() }
        javaDir.resolve("GStreamer.java").writeText(support.resolve("GStreamer.java").readText()
            .replace("//copyFonts", "copyFonts").replace("//copyCaCertificates", "copyCaCertificates"))
        copy { from(support); include("androidmedia/*.java"); into(javaDir) }
        val assets = destination.resolve("assets")
        copy { from(support.resolve("fontconfig/fonts.conf")); into(assets.resolve("fontconfig")) }
        copy { from(support.resolve("fontconfig/fonts/Ubuntu-R.ttf")); into(assets.resolve("fontconfig/fonts/truetype")) }
        copy { from(sdk.resolve("etc/ssl/certs/ca-certificates.crt")); into(assets.resolve("ssl/certs")) }
        copy { from(sdk.resolve("share/licenses")); into(assets.resolve("gstreamer/licenses")) }
    }
}
tasks.named("preBuild") { dependsOn(prepareGStreamerSupport) }
dependencies {
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
    implementation(platform("androidx.compose:compose-bom:2025.04.00"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.tv:tv-material:1.1.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("androidx.media3:media3-exoplayer:1.8.0")
    implementation("androidx.media3:media3-exoplayer-hls:1.8.0")
    implementation("androidx.media3:media3-ui:1.8.0")
}

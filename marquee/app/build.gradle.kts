plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

// Signing keys stay outside the repo and their passwords in the Mac keychain. Builds for our own TVs use the everyday
// key; public builds (-PpublicRelease) use the release key, whose keychain item asks before every read.
// Without the key the release build comes out unsigned
val signingName = if (hasProperty("publicRelease")) "homeboard-release" else "homeboard-everyday"
val signingKey = file("${System.getProperty("user.home")}/.homeboard/$signingName.jks")

android {
    namespace = "com.evofactory.homeboard"
    compileSdk = 37

    defaultConfig {
        // Its own id: installs next to stock HomeBoard rather than over it
        applicationId = "com.grimbelch.marquee"
        minSdk = 25 // Android 7.1: Fire OS 6 (Fire TV Stick 4K, 2018)
        targetSdk = 36
        versionCode = 1
        versionName = "1.0-deco"
        buildConfigField("long", "BUILD_TIME", "${System.currentTimeMillis()}L")
    }

    signingConfigs {
        if (signingKey.exists()) {
            val password = providers.exec {
                commandLine("security", "find-generic-password", "-a", "homeboard", "-s", signingName, "-w")
            }.standardOutput.asText.get().trim()
            create("release") {
                storeFile = signingKey
                storePassword = password
                keyAlias = "homeboard"
                keyPassword = password
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
            signingConfig = signingConfigs.findByName("release")
        }
    }

    // java.time on Android 7.1 (Fire OS 6)
    compileOptions {
        isCoreLibraryDesugaringEnabled = true
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.09.00")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.tv:tv-material:1.1.0")
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.core:core-ktx:1.19.1")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.11.0")
    implementation("androidx.media3:media3-exoplayer:1.11.1")
    implementation("androidx.media3:media3-exoplayer-rtsp:1.11.1")
    implementation("androidx.media3:media3-datasource-okhttp:1.11.1")
    implementation("androidx.media3:media3-ui:1.11.1")
    implementation("com.squareup.okhttp3:okhttp:5.5.1")
    implementation("org.conscrypt:conscrypt-android:2.8.0")
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")
    testImplementation("junit:junit:4.13.2")
}

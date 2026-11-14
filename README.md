# Atlas Android

This repository packages the existing Atlas analysis engine as a native Android application.

## Architecture

- Native Kotlin interface; no embedded terminal/TUI.
- The original Python analysis modules are bundled locally with Chaquopy.
- Bybit public market data is fetched over HTTPS; no API key is required for market-data analysis.
- No order placement, Telegram integration, or AI module is included in the Android build.
- The Atlas source repository remains separate and is not modified by this project.

## Build

The GitHub Actions workflow at `.github/workflows/android-apk.yml` imports the current Python engine from `12baro1/Atlas`, checks Python syntax, and builds a debug APK.

After a successful workflow run, download the `Atlas-Android-debug` artifact from the run's **Artifacts** section. Install `app-debug.apk` on an Android device (Android 7.0/API 24 or later).

## Compatibility note

The Android app uses Chaquopy to embed Python 3.11. The Android build is the compatibility gate: packages or engine code which rely on unsupported native dependencies must be adapted without changing Atlas's trading decisions. The first build and runtime analysis test are required before calling the APK production-ready.

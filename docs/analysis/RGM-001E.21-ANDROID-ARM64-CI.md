# RGM-001E.21 — Android ARM64 CI Build Verification

**Date:** 2026-11-20 (Asia/Jakarta)  
**Repository:** `yogiags56/StarlightGaiden`  
**Branch:** `work/rgm-001e3-bootstrap`  
**Commit:** `571258f4303274665a7216af5592145e66eba712`  
**Workflow:** Upstream desktop integration, run #40 (`44599996449`)

## Result

The GitHub Actions desktop and Android ARM64 jobs both completed successfully.

Android job gates:
- Android SDK setup: passed.
- Pinned NDK 26.2.11394342 and CMake 3.22.1 installation: passed.
- Guarded RGM integration application: passed.
- Gradle `assembleDebug`: passed.
- ARM64 APK verification: passed.
- Artifact upload: passed.

Desktop job and executable artifact upload also passed.

## Android artifact

Download from [successful GitHub Actions run #40](https://github.com/yogiags56/StarlightGaiden/actions/runs/44599996449) under Artifacts; select `starlightgaiden-android-arm64-debug`.

- Artifact name: `starlightgaiden-android-arm64-debug`
- Artifact ID: `14569130500`
- ZIP size: 28,696,744 bytes
- APK inside ZIP: `app-debug.apk`
- APK size: 73,409,428 bytes
- Artifact SHA-256 (GitHub ZIP): `39207e965fc51a9666e9314f61b3d40fc0a91ec22937c1e1afad44235a29dd26`
- Extracted APK SHA-256: `39b4537f88eea3614f59adbed91c94d23699368a07c0eab5c7add05f62e0915e`
- Artifact expiration: 2026-12-03 19:50:10 UTC (check GitHub Actions if downloading later).

APK archive inspection confirmed:
- `lib/arm64-v8a/libmain.so` exists (67,420,224 bytes).
- `lib/arm64-v8a/libSDL2.so` exists (1,513,368 bytes).
- `AndroidManifest.xml` exists.
- `classes.dex` and application assets exist.

This verifies package structure and ARM64 native libraries, not successful installation or runtime behavior on a physical phone.

## Runtime capture integration

The build includes the guarded RGM adapter, Android JNI CMake registration, touch-menu capture request and app-specific external-storage destination. Session and capture identifiers are generated to avoid collisions. Initial labels remain `unlabeled`, `unclassified`, and `unknown` until the operator verifies them.

## Explicitly not verified

- No physical Android device installation or launch.
- No ROM was supplied to the CI job; no game session was run.
- No real state/graphics capture has been collected.
- Touch capture behavior, Android storage permissions and output contents still need device validation.
- This is a debug APK, not a release-signed distribution build.

## Next gate

Install the APK on the user's Android phone, verify first launch and the Diagnostics/touch capture flow, then collect one legally sourced gameplay capture and validate the paired state/graphics bundle. Do not begin room-fingerprint calibration until real captures are available.

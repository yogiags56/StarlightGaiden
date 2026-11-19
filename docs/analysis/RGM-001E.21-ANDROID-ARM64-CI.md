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

## RGM-001E.22 — Physical Android Smoke Test

**Operator report:** The user installed and launched the APK on a physical Android phone, confirmed that the ROM runs, and reported that all on-screen buttons work. A screenshot supplied on 2026-11-20 shows the game scene rendered in landscape with the character and environment visible, plus the on-screen D-pad and action buttons.

### Verified by operator
- APK installs and launches on the physical Android device.
- A game ROM starts and renders a playable scene.
- User reports all touch buttons function.

### Still pending
- Exact device model, Android version and APK build identity have not yet been recorded.
- Diagnostics capture action and app-specific storage output have not yet been verified.
- No paired real state/graphics capture bundle has been received or inspected.
- Screenshot visibly contains a checkerboard-like pattern over large portions of the game view; its origin is unknown and must be investigated from a clean capture. Do not assume it is a game asset or transparency bug yet.
- This remains a debug APK, not a release-signed distribution build.

## Next gate

Open the runtime menu/Diagnostics, request one RGM bundle capture while the game is in the visible Starlight scene, then share the generated bundle (or its files). Verify the .bin, .txt, graphics PNGs, metadata and SHA-256 values before classifying the room or calibrating fingerprints.

#!/usr/bin/env python3
"""Add Android public-Downloads export for one RGM capture directory."""
from pathlib import Path
import argparse

MARKER = "RGM_ANDROID_PUBLIC_EXPORT"

def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("upstream", type=Path)
    args = ap.parse_args()
    root = args.upstream.resolve()
    game = root / "android/app/src/main/java/com/capcom/regaiden/GameActivity.java"
    header = root / "src/recompiled/runtime/include/platform_sdl.h"
    platform = root / "src/recompiled/runtime/src/platform_sdl.cpp"
    main_c = root / "src/recompiled/Resident_Evil_Gaiden__USA__main.c"
    g, h, p, m = game.read_text(), header.read_text(), platform.read_text(), main_c.read_text()
    if MARKER in g or MARKER in h or MARKER in p or MARKER in m:
        print("Android public export already applied.")
        return

    g = once(g, "import android.content.DialogInterface;\n",
        "import android.content.DialogInterface;\n"
        "import android.content.ContentValues;\n"
        "import android.os.Environment;\n"
        "import android.provider.MediaStore;\n"
        "import java.io.BufferedInputStream;\n"
        "import java.io.BufferedOutputStream;\n"
        "import java.security.MessageDigest;\n"
        "import java.util.zip.ZipEntry;\n"
        "import java.util.zip.ZipOutputStream;\n", "Java imports")
    g = once(g, "    private static final int REQUEST_CODE_PICK_ROM = 1002;\n",
        "    private static final int REQUEST_CODE_PICK_ROM = 1002;\n"
        "    private static final int REQUEST_CODE_EXPORT_RGM = 1003; // " + MARKER + "\n"
        "    private File mPendingRgmZip = null;\n", "export state")
    methods = r"""

    // " + MARKER + r": export from app-private Android/data to user-visible Downloads.
    public static void exportRgmCaptureFromNative(final String captureDir) {
        final GameActivity activity = sInstance;
        if (activity == null || captureDir == null) return;
        activity.runOnUiThread(new Runnable() {
            @Override public void run() { activity.exportRgmCapture(captureDir); }
        });
    }

    private void exportRgmCapture(String captureDir) {
        File source = new File(captureDir);
        if (!source.isDirectory()) {
            Toast.makeText(this, "RGM capture folder not found", Toast.LENGTH_LONG).show();
            return;
        }
        File zip = new File(getCacheDir(), "RGM-" + source.getName() + "-" + System.currentTimeMillis() + ".zip");
        try {
            try (ZipOutputStream out = new ZipOutputStream(new BufferedOutputStream(new FileOutputStream(zip)))) {
                zipRgmDirectory(source, source.getName(), out);
            }
            if (Build.VERSION.SDK_INT >= 29) exportRgmWithMediaStore(zip);
            else {
                mPendingRgmZip = zip;
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/zip");
                intent.putExtra(Intent.EXTRA_TITLE, zip.getName());
                startActivityForResult(intent, REQUEST_CODE_EXPORT_RGM);
            }
        } catch (Exception e) {
            Log.e(TAG, "RGM ZIP export failed", e);
            Toast.makeText(this, "RGM export failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
            zip.delete();
        }
    }

    private void zipRgmDirectory(File root, String relative, ZipOutputStream out) throws java.io.IOException {
        File[] children = root.listFiles();
        if (children == null) throw new java.io.IOException("Cannot read capture directory");
        java.util.Arrays.sort(children, (a, b) -> a.getName().compareTo(b.getName()));
        if (children.length == 0) {
            out.putNextEntry(new ZipEntry(relative + "/"));
            out.closeEntry();
            return;
        }
        byte[] buffer = new byte[32768];
        for (File child : children) {
            String name = relative + "/" + child.getName();
            if (child.isDirectory()) {
                zipRgmDirectory(child, name, out);
            } else if (child.isFile()) {
                out.putNextEntry(new ZipEntry(name));
                try (BufferedInputStream in = new BufferedInputStream(new FileInputStream(child))) {
                    int count;
                    while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
                }
                out.closeEntry();
            }
        }
    }

    private String sha256File(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[32768];
            int count;
            while ((count = in.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        StringBuilder value = new StringBuilder();
        for (byte b : digest.digest()) value.append(String.format(java.util.Locale.ROOT, "%02x", b & 0xff));
        return value.toString();
    }

    private long copyRgmZip(File zip, OutputStream out) throws java.io.IOException {
        long total = 0;
        try (InputStream in = new FileInputStream(zip)) {
            byte[] buffer = new byte[32768];
            int count;
            while ((count = in.read(buffer)) != -1) {
                out.write(buffer, 0, count);
                total += count;
            }
            out.flush();
        }
        if (total != zip.length()) throw new java.io.IOException("ZIP size verification failed");
        return total;
    }

    private void exportRgmWithMediaStore(File zip) throws Exception {
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, zip.getName());
        values.put(MediaStore.Downloads.MIME_TYPE, "application/zip");
        values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/StarlightGaiden");
        values.put(MediaStore.Downloads.IS_PENDING, 1);
        Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new java.io.IOException("MediaStore could not create Downloads entry");
        try {
            long copied;
            try (OutputStream out = getContentResolver().openOutputStream(uri)) {
                if (out == null) throw new java.io.IOException("Could not open exported ZIP");
                copied = copyRgmZip(zip, out);
            }
            ContentValues ready = new ContentValues();
            ready.put(MediaStore.Downloads.IS_PENDING, 0);
            getContentResolver().update(uri, ready, null, null);
            String hash = sha256File(zip);
            Log.i(TAG, "RGM export verified: " + uri + ", bytes=" + copied + ", sha256=" + hash);
            Toast.makeText(this, "RGM ZIP saved to Downloads/StarlightGaiden", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            getContentResolver().delete(uri, null, null);
            throw e;
        } finally {
            zip.delete();
        }
    }

"""
    g = once(g, "    // JNI Native Call: called from ImGui settings menu if user taps",
             methods + "    // JNI Native Call: called from ImGui settings menu if user taps",
             "Java export methods")
    g = once(g, "        if (requestCode == REQUEST_CODE_PICK_ROM) {",
        "        if (requestCode == REQUEST_CODE_EXPORT_RGM) {\n"
        "            if (resultCode == RESULT_OK && data != null && data.getData() != null && mPendingRgmZip != null) {\n"
        "                try (OutputStream out = getContentResolver().openOutputStream(data.getData())) {\n"
        "                    if (out == null) throw new java.io.IOException(\"Could not open destination\");\n"
        "                    long copied = copyRgmZip(mPendingRgmZip, out);\n"
        "                    Log.i(TAG, \"RGM SAF export verified, bytes=\" + copied + \", sha256=\" + sha256File(mPendingRgmZip));\n"
        "                    Toast.makeText(this, \"RGM ZIP exported successfully\", Toast.LENGTH_LONG).show();\n"
        "                } catch (Exception e) {\n"
        "                    Log.e(TAG, \"SAF RGM export failed\", e);\n"
        "                    Toast.makeText(this, \"RGM export failed\", Toast.LENGTH_LONG).show();\n"
        "                }\n"
        "            }\n"
        "            if (mPendingRgmZip != null) mPendingRgmZip.delete();\n"
        "            mPendingRgmZip = null;\n"
        "        } else if (requestCode == REQUEST_CODE_PICK_ROM) {", "SAF result handler")

    h = once(h, "bool gb_platform_consume_rgm_capture_request(void);\n",
        "bool gb_platform_consume_rgm_capture_request(void);\n"
        "/* Export a completed capture to user-visible Android Downloads. */\n"
        "void gb_platform_export_rgm_bundle(const char* capture_dir); // " + MARKER + "\n",
        "platform export declaration")
    p += r"""

#ifdef __ANDROID__
/* " + MARKER + r": bridge native capture output to the app's Java MediaStore/SAF exporter. */
extern "C" void gb_platform_export_rgm_bundle(const char* capture_dir) {
    if (!capture_dir || !capture_dir[0]) return;
    JNIEnv* env = (JNIEnv*)SDL_AndroidGetJNIEnv();
    if (!env) return;
    jclass activity = env->FindClass("com/capcom/regaiden/GameActivity");
    if (!activity) {
        if (env->ExceptionCheck()) env->ExceptionClear();
        return;
    }
    jmethodID method = env->GetStaticMethodID(
        activity, "exportRgmCaptureFromNative", "(Ljava/lang/String;)V");
    if (method) {
        jstring path = env->NewStringUTF(capture_dir);
        if (path) {
            env->CallStaticVoidMethod(activity, method, path);
            env->DeleteLocalRef(path);
        }
    }
    if (env->ExceptionCheck()) env->ExceptionClear();
    env->DeleteLocalRef(activity);
}
#else
extern "C" void gb_platform_export_rgm_bundle(const char* capture_dir) {
    (void)capture_dir;
}
#endif
"""
    m = once(m,
        '                fprintf(stderr, "[RGM] %s\\n", rgm_status[0] ? rgm_status : (rgm_ok ? "capture complete" : "capture failed"));\n',
        '                fprintf(stderr, "[RGM] %s\\n", rgm_status[0] ? rgm_status : (rgm_ok ? "capture complete" : "capture failed"));\n'
        '#ifdef __ANDROID__\n'
        '                if (rgm_ok) gb_platform_export_rgm_bundle(rgm_capture_dir);\n'
        '#endif\n',
        "invoke Android exporter after successful capture")
    game.write_text(g)
    header.write_text(h)
    platform.write_text(p)
    main_c.write_text(m)
    print("Applied Android RGM public Downloads export.")
    
if __name__ == "__main__":
    main()

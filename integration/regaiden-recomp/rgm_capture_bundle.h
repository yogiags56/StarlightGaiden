#ifndef RGM_CAPTURE_BUNDLE_H
#define RGM_CAPTURE_BUNDLE_H

#include <stdbool.h>
#include <stddef.h>
#include "gbrt.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Call only on the emulator thread after a guest frame has completed and
 * before the next gb_run_frame()/gb_run_cycles() execution begins.
 *
 * capture_dir must be a unique FP-<capture_id> directory for this capture.
 * This wrapper writes the existing state dump, the existing graphics dump,
 * and capture_metadata.json. It does not alter emulated guest state.
 *
 * SHA-256 values are added afterward by tools/rgm_capture_finalize.py.
 */
bool rgm_capture_bundle(
    GBContext* ctx,
    const char* capture_dir,
    const char* session_id,
    const char* capture_id,
    const char* experiment_id,
    const char* checkpoint,
    unsigned repeat,
    const char* location_label,
    const char* activity,
    const char* character,
    const char* speaker,
    char* out_status,
    size_t status_size
);

#ifdef __cplusplus
}
#endif
#endif

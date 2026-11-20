#ifndef TEST_ASSET_DUMP_H
#define TEST_ASSET_DUMP_H
#include <stdbool.h>
#include <stddef.h>
#include "gbrt.h"
#ifdef __cplusplus
extern "C" {
#endif
bool asset_dump_capture(const GBContext* ctx,const char* output_dir,char* status,size_t size);
#ifdef __cplusplus
}
#endif
#endif

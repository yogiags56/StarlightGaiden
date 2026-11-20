#ifndef TEST_STATE_DUMP_H
#define TEST_STATE_DUMP_H
#include <stdbool.h>
#include <stddef.h>
#include "gbrt.h"
#ifdef __cplusplus
extern "C" {
#endif
void state_dump_set_output_dir(const char* dir);
const char* state_dump_output_dir(void);
int state_dump_count(void);
bool state_dump_capture(GBContext* ctx,const char* label,char* status,size_t size);
#ifdef __cplusplus
}
#endif
#endif

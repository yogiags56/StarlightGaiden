#include "rgm_capture_bundle.h"
#include "state_dump.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

namespace fs = std::filesystem;
static std::string output_dir = ".";
static int dump_count = 0;
static bool advance_frame_in_graphics = false;

extern "C" void state_dump_set_output_dir(const char* dir) {
    if (dir && *dir) output_dir = dir;
}
extern "C" const char* state_dump_output_dir(void) { return output_dir.c_str(); }
extern "C" int state_dump_count(void) { return dump_count; }

static bool write_file(const fs::path& p, const char* bytes) {
    std::ofstream out(p, std::ios::binary);
    out << bytes;
    return out.good();
}
extern "C" bool state_dump_capture(GBContext*, const char*, char* status, size_t size) {
    ++dump_count;
    const fs::path root(output_dir);
    const std::string n = std::to_string(dump_count);
    if (!write_file(root / ("state_0" + n + ".bin"), "state") ||
        !write_file(root / ("state_0" + n + ".txt"), "summary")) return false;
    if (status && size) std::snprintf(status, size, "state ok");
    return true;
}
extern "C" bool asset_dump_capture(const GBContext* const_ctx,const char* dir,char* status,size_t size) {
    GBContext* ctx = const_cast<GBContext*>(const_ctx);
    const fs::path graphics = fs::path(dir) / ("capture_000" + std::to_string(dump_count));
    fs::create_directories(graphics);
    for (const char* n : {"framebuffer.png","map_9800.png","map_9c00.png","manifest.txt"}) {
        if (!write_file(graphics / n, "fixture")) return false;
    }
    if (advance_frame_in_graphics) ++ctx->completed_frames;
    if (status && size) std::snprintf(status, size, "Graphics captured: %s", graphics.string().c_str());
    return true;
}

static std::string read(const fs::path& p) {
    std::ifstream in(p);
    return std::string(std::istreambuf_iterator<char>(in), {});
}

int main() {
    const fs::path base = fs::temp_directory_path() / "rgm-cpp-adapter-smoke";
    std::error_code ec; fs::remove_all(base, ec);
    const fs::path session = base / "SESSION-TEST";
    fs::create_directories(session);
    GBContext ctx{42};
    char status[512] = {};
    const fs::path first = session / "FP-CAP-001";
    assert(rgm_capture_bundle(&ctx, first.string().c_str(), "SESSION-TEST", "CAP-001",
        "EXP-01", "stationary", 1, "Observed corridor", "exploration",
        "Barry", "none", status, sizeof(status)));
    assert(fs::is_regular_file(first / "capture_metadata.json"));
    assert(read(first / "capture_metadata.json").find("\"same_completed_frame\": true") != std::string::npos);
    assert(output_dir == ".");

    const fs::path second = session / "FP-CAP-002";
    advance_frame_in_graphics = true;
    assert(rgm_capture_bundle(&ctx, second.string().c_str(), "SESSION-TEST", "CAP-002",
        "EXP-01", "stationary", 2, "Observed corridor", "exploration",
        "Barry", "none", status, sizeof(status)));
    assert(read(second / "capture_metadata.json").find("\"same_completed_frame\": false") != std::string::npos);
    assert(output_dir == ".");

    const fs::path wrong = session / "wrong-name";
    assert(!rgm_capture_bundle(&ctx, wrong.string().c_str(), "SESSION-TEST", "CAP-003",
        "EXP-01", "stationary", 3, "Observed corridor", "exploration",
        "Barry", "none", status, sizeof(status)));
    std::cout << "RGM C++ adapter smoke tests passed; fixture bundle: " << first << "\n";
    return 0;
}

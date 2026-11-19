#include "rgm_capture_bundle.h"

#include "state_dump.h"
#include "asset_dump.h"

#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>

namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;

static uint64_t rgm_now_ns() {
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(
            Clock::now().time_since_epoch()).count());
}

static std::string rgm_json_escape(const char* value) {
    std::ostringstream out;
    const unsigned char* p = reinterpret_cast<const unsigned char*>(
        value ? value : "");
    for (; *p; ++p) {
        switch (*p) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\b': out << "\\b"; break;
            case '\f': out << "\\f"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (*p < 0x20) {
                    out << "\\u" << std::hex << std::setw(4)
                        << std::setfill('0') << static_cast<unsigned>(*p)
                        << std::dec;
                } else {
                    out << static_cast<char>(*p);
                }
        }
    }
    return out.str();
}

static bool rgm_write_metadata(
    const fs::path& root,
    const char* session_id,
    const char* capture_id,
    const char* experiment_id,
    const char* checkpoint,
    unsigned repeat,
    const char* location_label,
    const char* activity,
    const char* character,
    const char* speaker,
    const std::string& state_file,
    const std::string& state_summary,
    const std::string& graphics_dir,
    uint64_t state_start_ns,
    uint64_t state_end_ns,
    uint64_t graphics_start_ns,
    uint64_t graphics_end_ns,
    uint64_t state_frame_start,
    uint64_t state_frame_end,
    uint64_t graphics_frame_start,
    uint64_t graphics_frame_end) {

    const bool state_stable = state_frame_start == state_frame_end;
    const bool graphics_stable = graphics_frame_start == graphics_frame_end;
    const bool same_frame = state_frame_start == graphics_frame_start &&
                            state_stable && graphics_stable;
    const fs::path tmp = root / "capture_metadata.json.tmp";
    const fs::path dst = root / "capture_metadata.json";
    std::ofstream out(tmp, std::ios::binary | std::ios::trunc);
    if (!out) return false;

    out << "{\n"
        << "  \"schema_version\": 1,\n"
        << "  \"session_id\": \"" << rgm_json_escape(session_id) << "\",\n"
        << "  \"capture_id\": \"" << rgm_json_escape(capture_id) << "\",\n"
        << "  \"experiment_id\": \"" << rgm_json_escape(experiment_id) << "\",\n"
        << "  \"checkpoint\": \"" << rgm_json_escape(checkpoint) << "\",\n"
        << "  \"repeat\": " << repeat << ",\n"
        << "  \"observed\": {\n"
        << "    \"location_label\": \"" << rgm_json_escape(location_label) << "\",\n"
        << "    \"activity\": \"" << rgm_json_escape(activity) << "\",\n"
        << "    \"character\": \"" << rgm_json_escape(character) << "\",\n"
        << "    \"speaker\": \"" << rgm_json_escape(speaker) << "\"\n"
        << "  },\n"
        << "  \"capture\": {\n"
        << "    \"state_file\": \"" << rgm_json_escape(state_file.c_str()) << "\",\n"
        << "    \"state_summary\": \"" << rgm_json_escape(state_summary.c_str()) << "\",\n"
        << "    \"graphics_directory\": \"" << rgm_json_escape(graphics_dir.c_str()) << "\"\n"
        << "  },\n"
        << "  \"capture_timing\": {\n"
        << "    \"clock_id\": \"steady_clock:process\",\n"
        << "    \"clock_source\": \"std::chrono::steady_clock\",\n"
        << "    \"state_dump_started_ns\": " << state_start_ns << ",\n"
        << "    \"state_dump_completed_ns\": " << state_end_ns << ",\n"
        << "    \"graphics_dump_started_ns\": " << graphics_start_ns << ",\n"
        << "    \"graphics_dump_completed_ns\": " << graphics_end_ns << ",\n"
        << "    \"game_frame_at_state\": " << state_frame_start << ",\n"
        << "    \"game_frame_at_graphics\": " << graphics_frame_start << ",\n"
        << "    \"state_frame_stable\": " << (state_stable ? "true" : "false") << ",\n"
        << "    \"graphics_frame_stable\": " << (graphics_stable ? "true" : "false") << ",\n"
        << "    \"same_completed_frame\": " << (same_frame ? "true" : "false") << "\n"
        << "  },\n"
        << "  \"source_sha256\": {}\n"
        << "}\n";
    out.flush();
    const bool written = out.good();
    out.close();
    if (!written || out.fail()) {
        std::error_code ec;
        fs::remove(tmp, ec);
        return false;
    }
    std::error_code ec;
    fs::rename(tmp, dst, ec);
    if (ec) {
        fs::remove(tmp, ec);
        return false;
    }
    return true;
}

extern "C" bool rgm_capture_bundle(
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
    size_t status_size) {

    auto fail = [&](const char* message) {
        if (out_status && status_size) std::snprintf(out_status, status_size, "%s", message);
        return false;
    };
    if (!ctx || !capture_dir || !capture_dir[0] ||
        !session_id || !session_id[0] ||
        !capture_id || !capture_id[0] ||
        !experiment_id || !experiment_id[0] ||
        !checkpoint || !checkpoint[0] || repeat == 0) {
        return fail("RGM capture failed: invalid identity or runtime context");
    }
    if (!Clock::is_steady) {
        return fail("RGM capture failed: steady clock is not monotonic on this platform");
    }

    std::error_code ec;
    const fs::path root(capture_dir);
    fs::create_directories(root, ec);
    if (ec || !fs::is_directory(root)) {
        return fail("RGM capture failed: cannot create capture directory");
    }

    const int state_index = state_dump_count() + 1;
    char state_name[40], summary_name[40];
    std::snprintf(state_name, sizeof(state_name), "state_%02d.bin", state_index);
    std::snprintf(summary_name, sizeof(summary_name), "state_%02d.txt", state_index);

    state_dump_set_output_dir(root.string().c_str());
    const uint64_t state_frame_start = ctx->completed_frames;
    const uint64_t state_start_ns = rgm_now_ns();
    char state_status[512] = {};
    const bool state_ok = state_dump_capture(ctx, capture_id, state_status, sizeof(state_status));
    const uint64_t state_end_ns = rgm_now_ns();
    const uint64_t state_frame_end = ctx->completed_frames;
    if (!state_ok) return fail(state_status[0] ? state_status : "RGM capture failed: state dump failed");

    const fs::path state_path = root / state_name;
    const fs::path summary_path = root / summary_name;
    if (!fs::is_regular_file(state_path) || !fs::is_regular_file(summary_path)) {
        return fail("RGM capture incomplete: state dump or summary file missing");
    }

    const uint64_t graphics_frame_start = ctx->completed_frames;
    const uint64_t graphics_start_ns = rgm_now_ns();
    char graphics_status[512] = {};
    const bool graphics_ok = asset_dump_capture(
        ctx, root.string().c_str(), graphics_status, sizeof(graphics_status));
    const uint64_t graphics_end_ns = rgm_now_ns();
    const uint64_t graphics_frame_end = ctx->completed_frames;
    if (!graphics_ok) {
        return fail(graphics_status[0] ? graphics_status : "RGM capture failed: graphics dump failed");
    }

    const std::string prefix = "Graphics captured: ";
    const std::string status_text(graphics_status);
    if (status_text.rfind(prefix, 0) != 0) {
        return fail("RGM capture incomplete: graphics output path was not reported");
    }
    const fs::path graphics_path(status_text.substr(prefix.size()));
    if (!fs::is_directory(graphics_path)) {
        return fail("RGM capture incomplete: graphics directory missing");
    }
    const fs::path absolute_root = fs::absolute(root, ec).lexically_normal();
    if (ec) return fail("RGM capture failed: cannot resolve capture root");
    const fs::path absolute_graphics = fs::absolute(graphics_path, ec).lexically_normal();
    if (ec) return fail("RGM capture failed: cannot resolve graphics directory");
    const std::string graphics_relative =
        absolute_graphics.lexically_relative(absolute_root).generic_string();
    if (graphics_relative.empty() || graphics_relative == "." ||
        graphics_relative == ".." || graphics_relative.rfind("../", 0) == 0) {
        return fail("RGM capture failed: graphics directory is outside capture root");
    }

    const bool same_frame =
        state_frame_start == state_frame_end &&
        graphics_frame_start == graphics_frame_end &&
        state_frame_start == graphics_frame_start;
    if (!rgm_write_metadata(
            root, session_id, capture_id, experiment_id, checkpoint, repeat,
            location_label, activity, character, speaker,
            state_name, summary_name, graphics_relative,
            state_start_ns, state_end_ns, graphics_start_ns, graphics_end_ns,
            state_frame_start, state_frame_end, graphics_frame_start, graphics_frame_end)) {
        return fail("RGM capture incomplete: cannot write capture_metadata.json");
    }

    if (out_status && status_size) {
        std::snprintf(out_status, status_size,
            "RGM bundle captured: %s (frame=%llu, same_frame=%s; finalize SHA-256)",
            capture_dir, static_cast<unsigned long long>(state_frame_start),
            same_frame ? "yes" : "no");
    }
    return true;
}

/* aegentix_fast.c - bare-metal oriented hot-path helpers for AEGENTIX
 * Build (Windows/MSVC): cl /LD /O2 /W3 /DNDEBUG native\aegentix_fast.c /Fe:native\aegentix_fast.dll
 * Build (MinGW/clang/gcc): cc -O3 -shared -fPIC -o native/aegentix_fast.dll native/aegentix_fast.c
 * ABI: C (ctypes-friendly). No Python headers required.
 */
#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32)
  #define AEGX_API __declspec(dllexport)
#else
  #define AEGX_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Matches RingBufferAdapter checksum: s = ((s*31)+b) & 0xFFFFFFFF */
AEGX_API uint32_t aegx_checksum32(const uint8_t *data, size_t len) {
    uint32_t s = 0u;
    if (!data) return 0u;
    for (size_t i = 0; i < len; ++i) {
        s = ((s * 31u) + (uint32_t)data[i]) & 0xFFFFFFFFu;
    }
    return s;
}

/* Score lowercase text against terms separated by \n/\x1f/space/tab; +2 if exact contains. */
AEGX_API int32_t aegx_score_terms(const char *hay, size_t hay_len,
                                  const char *terms, size_t terms_len,
                                  const char *exact, size_t exact_len) {
    int32_t score = 0;
    if (!hay || !terms) return 0;
    if (exact && exact_len > 0 && hay_len >= exact_len) {
        for (size_t i = 0; i + exact_len <= hay_len; ++i) {
            size_t j = 0;
            while (j < exact_len && hay[i + j] == exact[j]) ++j;
            if (j == exact_len) { score += 2; break; }
        }
    }
    size_t i = 0;
    while (i < terms_len) {
        while (i < terms_len && (terms[i]=='\n' || terms[i]=='\x1f' || terms[i]==' ' || terms[i]=='\t' || terms[i]=='\r')) ++i;
        size_t s = i;
        while (i < terms_len && !(terms[i]=='\n' || terms[i]=='\x1f' || terms[i]=='\r')) ++i;
        size_t tlen = (i > s) ? (i - s) : 0;
        if (tlen == 0) continue;
        if (hay_len >= tlen) {
            for (size_t h = 0; h + tlen <= hay_len; ++h) {
                size_t j = 0;
                while (j < tlen && hay[h + j] == terms[s + j]) ++j;
                if (j == tlen) { score += 1; break; }
            }
        }
    }
    return score;
}

AEGX_API uint32_t aegx_abi_version(void) { return 1u; }

#ifdef __cplusplus
}
#endif

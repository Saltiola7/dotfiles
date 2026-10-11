/* Exercise the real upstream configuration readers under a small FD limit. */
#include <assert.h>
#include <dirent.h>
#include <sys/resource.h>
#include <unistd.h>
#include "config.h"
#include "os.h"
#include "xmem.h"

static int fd_count(void) {
    DIR *dir = opendir("/proc/self/fd");
    assert(dir);
    int count = 0;
    while (readdir(dir)) ++count;
    closedir(dir);
    return count;
}

int main(void) {
    struct rlimit limit = {256, 256};
    assert(setrlimit(RLIMIT_NOFILE, &limit) == 0);
    char directory[] = "/tmp/waynergy-config-test.XXXXXX";
    assert(mkdtemp(directory));
    osConfigPathOverride = directory;
    char *path;
    xasprintf(&path, "%s/fingerprint", directory);
    FILE *file = fopen(path, "w");
    assert(file);
    fputs("test-fingerprint\n", file);
    fclose(file);
    int before = fd_count();
    for (int i = 0; i < 10000; ++i) {
        char *value = configReadFile("fingerprint");
        assert(value && strcmp(value, "test-fingerprint\n") == 0);
        free(value);
        char **lines = configReadLines("fingerprint");
        assert(lines && lines[0] && !lines[1]);
        assert(strcmp(lines[0], "test-fingerprint\n") == 0);
        strfreev(lines);
    }
    int after = fd_count();
    printf("20000 configuration reads: descriptors before=%d after=%d\n", before, after);
    assert(before == after);
    assert(unlink(path) == 0);
    assert(rmdir(directory) == 0);
    free(path);
    return 0;
}

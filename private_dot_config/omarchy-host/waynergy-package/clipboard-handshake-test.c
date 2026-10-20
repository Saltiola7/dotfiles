/* Real poll/clipboard/protocol paths, using only AF_UNIX socketpairs and synthetic
 * text. No compositor, clipboard program, TLS peer, or external connection.
 * Compile after meson compile:
 * cc -D_GNU_SOURCE -DUSYNERGY_LITTLE_ENDIAN -Iinclude \
 *   -Ibuild/protocol/libclient_protos.a.p clipboard-handshake-test.c \
 *   src/net.c src/clip.c src/uSynergy.c src/sig.c src/ssp.c src/config.c \
 *   src/os.c src/log.c -ltls -o clipboard-handshake-test
 * The server enforces HelloBack -> QINF/DINF -> CIAK before clipboard traffic,
 * as ClientProxyUnknown and ClientProxy1_0::parseHandshakeMessage require. */
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "net.h"

struct wlContext wlContext;
uSynergyContext synContext;
struct synNetContext synNetContext = {.fd = -1};
static const char text[] = "synthetic clipboard fixture";
static char *test_argv[] = {"clipboard-handshake-test", NULL};
static bool update_geometry;
static pid_t worker = -1;

/* The sole integration stub can deliver the same resolution callback that
 * wlPollProc invokes. Deliberately doing it during prepare also tests callers
 * outside the poll dispatch guard. Production wlPrepareFd currently only
 * returns the Wayland descriptor. The actual clipboard socket parser is used. */
int wlPrepareFd(struct wlContext *context)
{
    (void)context;
    if (update_geometry) {
        update_geometry = false;
        uSynergyUpdateRes(&synContext, 1200, 800);
    }
    return -1;
}
void wlPollProc(struct wlContext *context, short events) { (void)context; (void)events; }
void wlClose(struct wlContext *context) { (void)context; }
void wlIdleInhibit(struct wlContext *context, bool on) { (void)context; (void)on; }

#define CHILD_CHECK(condition) do { if (!(condition)) _exit(90); } while (0)
#define CHECK(condition) do { if (!(condition)) { \
    fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, #condition); \
    goto done; \
} } while (0)

static uint32_t be32(const unsigned char *p)
{
    return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 |
           (uint32_t)p[2] << 8 | p[3];
}

static bool ready(int fd, int milliseconds)
{
    struct pollfd pfd = {.fd = fd, .events = POLLIN};
    return poll(&pfd, 1, milliseconds) == 1 && (pfd.revents & POLLIN);
}

static bool read_bytes(int fd, void *buffer, size_t size)
{
    unsigned char *p = buffer;
    while (size) {
        if (!ready(fd, 1500)) return false;
        ssize_t count = read(fd, p, size);
        if (count <= 0) return false;
        p += count;
        size -= count;
    }
    return true;
}

static int read_frame(int fd, unsigned char *body, size_t capacity)
{
    unsigned char header[4];
    if (!read_bytes(fd, header, sizeof(header))) return -1;
    uint32_t size = be32(header);
    if (size > capacity || !read_bytes(fd, body, size)) return -1;
    return (int)size;
}

static bool send_command(int fd, const char command[4])
{
    unsigned char frame[8] = {0, 0, 0, 4};
    memcpy(frame + 4, command, 4);
    return write(fd, frame, sizeof(frame)) == sizeof(frame);
}

static void queue_clipboard(int fd)
{
    char id = 'c';
    size_t length = sizeof(text) - 1;
    CHILD_CHECK(write(fd, &id, sizeof(id)) == sizeof(id));
    CHILD_CHECK(write(fd, &length, sizeof(length)) == sizeof(length));
    CHILD_CHECK(write(fd, text, length) == (ssize_t)length);
}

static bool fake_connect(uSynergyCookie cookie) { (void)cookie; return true; }

static bool previous_ack(uSynergyCookie cookie, uint8_t *buffer, int capacity, int *length)
{
    (void)cookie;
    const unsigned char frame[] = {0, 0, 0, 4, 'C', 'I', 'A', 'K'};
    CHILD_CHECK(capacity >= (int)sizeof(frame));
    memcpy(buffer, frame, sizeof(frame));
    *length = sizeof(frame);
    return true;
}

enum scenario { QUEUED_CLIPBOARD, GEOMETRY, CACHED_CLIPBOARD, RESIZE_CLIPBOARD, RECONNECT };

static void client(int network, int clipboard, enum scenario scenario)
{
    CHILD_CHECK(logInit(LOG_ERR, NULL));
    clipMonitorFd = -1;
    clipMonitorPid[0] = clipMonitorPid[1] = -1;
    sigHandleInit(test_argv);
    uSynergyInit(&synContext);
    synContext.m_clientName = "clipboard-handshake-test";
    synContext.m_clientWidth = 1920;
    synContext.m_clientHeight = 1080;
    CHILD_CHECK(synNetInit(&synNetContext, &synContext, "unused", "0", false, false));
    synNetContext.fd = network;
    synContext.m_connected = true;
    synContext.m_lastMessageTime = synContext.m_getTimeFunc();
    netPollInit();
    netPollFd[POLLFD_CLIP_UPDATER].fd = clipboard;
    if (scenario == GEOMETRY) update_geometry = true;
    if (scenario == CACHED_CLIPBOARD)
        uSynergyUpdateClipBuf(&synContext, SYNERGY_CLIPBOARD_CLIPBOARD, sizeof(text) - 1, text);
    if (scenario == RECONNECT) {
        /* A nonfatal raw transport disconnect can leave old protocol state.
         * Re-enter through the actual reconnect path, without creating TCP. */
        synContext.m_hasReceivedHello = true;
        uSynergyReceiveFunc receive = synContext.m_receiveFunc;
        synContext.m_receiveFunc = previous_ack;
        uSynergyUpdate(&synContext);
        synContext.m_receiveFunc = receive;
        CHILD_CHECK(synContext.m_infoCurrent);
        synContext.m_connected = false;
        synContext.m_receiveOfs = 2;
        synContext.m_replyCur += 7;
        synContext.m_connectFunc = fake_connect;
        uSynergyUpdate(&synContext);
        CHILD_CHECK(synContext.m_connected);
        CHILD_CHECK(!synContext.m_hasReceivedHello);
        CHILD_CHECK(!synContext.m_infoCurrent);
        CHILD_CHECK(synContext.m_receiveOfs == 0);
        CHILD_CHECK(synContext.m_replyCur == synContext.m_replyBuffer + 4);
    }
    netPoll(&synNetContext, &wlContext);
    _exit(91);
}

static bool run_case(enum scenario scenario)
{
    int network[2] = {-1, -1}, clipboard[2] = {-1, -1};
    unsigned char frame[4096];
    bool ok = false;
    CHECK(socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, network) == 0);
    CHECK(socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, clipboard) == 0);
    if (scenario == QUEUED_CLIPBOARD || scenario == RECONNECT)
        queue_clipboard(clipboard[1]);
    pid_t owner = getpid();
    worker = fork();
    CHECK(worker >= 0);
    if (!worker) {
        CHILD_CHECK(prctl(PR_SET_PDEATHSIG, SIGKILL) == 0);
        CHILD_CHECK(getppid() == owner);
        close(network[1]);
        close(clipboard[1]);
        client(network[0], clipboard[0], scenario);
    }
    close(network[0]); network[0] = -1;
    close(clipboard[0]); clipboard[0] = -1;
    /* The original implementation emits CCLP or DINF here, before the server
     * has even sent its greeting. Such a frame cannot parse as HelloBack. */
    if (ready(network[1], 200)) {
        int early = read_frame(network[1], frame, sizeof(frame));
        fprintf(stderr, "unexpected pre-greeting client frame: %.*s (length %d)\n",
                early > 0 ? (early < 7 ? early : 7) : 0, frame, early);
        goto done;
    }
    const unsigned char hello[] = {0, 0, 0, 11, 'S', 'y', 'n', 'e', 'r', 'g', 'y', 0, 1, 0, 8};
    CHECK(write(network[1], hello, 2) == 2);
    CHECK(!ready(network[1], 100));
    CHECK(write(network[1], hello + 2, sizeof(hello) - 2) == sizeof(hello) - 2);
    int length = read_frame(network[1], frame, sizeof(frame));
    const char name[] = "clipboard-handshake-test";
    CHECK(length == 15 + sizeof(name) - 1);
    CHECK(!memcmp(frame, "Synergy\0\1\0\6", 11));
    CHECK(be32(frame + 11) == sizeof(name) - 1);
    CHECK(!memcmp(frame + 15, name, sizeof(name) - 1));
    /* ClientProxy1_0's initial parser accepts DINF/CNOP, not CCLP. */
    CHECK(!ready(network[1], 100));
    CHECK(send_command(network[1], "QINF"));
    CHECK(read_frame(network[1], frame, sizeof(frame)) == 18);
    CHECK(!memcmp(frame, "DINF", 4));
    CHECK((frame[8] || frame[9]) && (frame[10] || frame[11]));
    if (scenario == GEOMETRY) {
        CHECK(frame[8] == 0x04 && frame[9] == 0xb0);
        CHECK(frame[10] == 0x03 && frame[11] == 0x20);
    }
    CHECK(!ready(network[1], 100));
    CHECK(send_command(network[1], "CIAK"));
    if (scenario == QUEUED_CLIPBOARD || scenario == CACHED_CLIPBOARD || scenario == RECONNECT) {
        CHECK(read_frame(network[1], frame, sizeof(frame)) == 9);
        CHECK(!memcmp(frame, "CCLP\0", 5));
        CHECK(send_command(network[1], "COUT"));
        bool found = false;
        for (int i = 0; i < 3; ++i) {
            length = read_frame(network[1], frame, sizeof(frame));
            CHECK(length >= 10 && !memcmp(frame, "DCLP", 4));
            if (memmem(frame, length, text, sizeof(text) - 1)) found = true;
        }
        CHECK(found);
        CHECK(read_frame(network[1], frame, sizeof(frame)) == 4);
        CHECK(!memcmp(frame, "CNOP", 4));
    } else if (scenario == RESIZE_CLIPBOARD) {
        /* DINF can be awaiting a later CIAK in a healthy session. Clipboard
         * ownership and data must still survive COUT during that interval. */
        CHECK(send_command(network[1], "QINF"));
        CHECK(read_frame(network[1], frame, sizeof(frame)) == 18);
        CHECK(!memcmp(frame, "DINF", 4));
        queue_clipboard(clipboard[1]);
        CHECK(read_frame(network[1], frame, sizeof(frame)) == 9);
        CHECK(!memcmp(frame, "CCLP\0", 5));
        CHECK(send_command(network[1], "COUT"));
        bool found = false;
        for (int i = 0; i < 3; ++i) {
            length = read_frame(network[1], frame, sizeof(frame));
            CHECK(length >= 10 && !memcmp(frame, "DCLP", 4));
            if (memmem(frame, length, text, sizeof(text) - 1)) found = true;
        }
        CHECK(found);
        CHECK(read_frame(network[1], frame, sizeof(frame)) == 4);
        CHECK(!memcmp(frame, "CNOP", 4));
        CHECK(send_command(network[1], "CIAK"));
        CHECK(!ready(network[1], 100));
    }
    ok = true;
done:
    if (worker > 0) {
        kill(worker, SIGTERM);
        int status;
        waitpid(worker, &status, 0);
        if (ok && (!WIFEXITED(status) || WEXITSTATUS(status) != 0)) {
            fprintf(stderr, "client exited unexpectedly: %d\n", status);
            ok = false;
        }
        worker = -1;
    }
    for (int i = 0; i < 2; ++i) {
        if (network[i] >= 0) close(network[i]);
        if (clipboard[i] >= 0) close(clipboard[i]);
    }
    return ok;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    const char *names[] = {"queued clipboard waits for initial CIAK",
                          "pre-hello geometry is cached for QINF",
                          "cached clipboard is replayed after initial CIAK",
                          "clipboard survives a later information acknowledgement",
                          "nonfatal reconnect resets greeting and receive state"};
    int failed = 0;
    for (int scenario = QUEUED_CLIPBOARD; scenario <= RECONNECT; ++scenario) {
        bool ok = run_case(scenario);
        printf("%s: %s\n", ok ? "PASS" : "FAIL", names[scenario]);
        failed += !ok;
    }
    return failed ? EXIT_FAILURE : EXIT_SUCCESS;
}

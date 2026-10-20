/* Exercise the real network/protocol/signal code without a compositor or Mac.
 * Compile after generating the protocol headers (normally meson compile):
 * cc -D_GNU_SOURCE -DUSYNERGY_LITTLE_ENDIAN -Iinclude -Ibuild/protocol/libclient_protos.a.p \
 *   network-recovery-test.c src/net.c src/uSynergy.c src/sig.c src/ssp.c \
 *   src/config.c src/os.c src/log.c -Wl,--wrap=tls_handshake -ltls -lcrypto \
 *   -o network-recovery-test
 * Keep the production 10-second timeout: all cases run concurrently. */
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
#include <tls.h>
#include <openssl/ec.h>
#include <openssl/pem.h>
#include <openssl/x509.h>
#include "net.h"
#include "sig.h"
#include "os.h"

struct wlContext wlContext;
uSynergyContext synContext;
struct synNetContext synNetContext = {.fd = -1};
int clipMonitorFd = -1;
struct sockaddr_un clipMonitorAddr;
pid_t clipMonitorPid[2] = {-1, -1};
static int wayland_fd = -1;
static int reconnects;
static int handshake_wants;
static int handshake_calls;

int __real_tls_handshake(struct tls *context);
int __wrap_tls_handshake(struct tls *context)
{
    ++handshake_calls;
    /* Force both documented retry results before a real successful handshake.
     * Every other case calls the actual libtls function without injection. */
    if (handshake_wants == 2) {
        --handshake_wants;
        return TLS_WANT_POLLIN;
    }
    if (handshake_wants == 1) {
        --handshake_wants;
        return TLS_WANT_POLLOUT;
    }
    return __real_tls_handshake(context);
}
static char *test_argv[] = {"network-recovery-test", NULL};

/* Only compositor/clipboard integration is replaced. Poll, TCP, TLS, protocol
 * parsing, timeout classification, fatal checks, and exit cleanup are real. */
int wlPrepareFd(struct wlContext *context) { (void)context; return wayland_fd; }
void wlPollProc(struct wlContext *context, short events) { (void)context; (void)events; }
void wlClose(struct wlContext *context) { (void)context; }
void wlIdleInhibit(struct wlContext *context, bool on) { (void)context; (void)on; }
void clipMonitorPollProc(struct pollfd *fd) { (void)fd; }

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, #condition); \
        _exit(EXIT_FAILURE); \
    } \
} while (0)

static uint64_t monotonic_ms(void)
{
    struct timespec now;
    CHECK(clock_gettime(CLOCK_MONOTONIC, &now) == 0);
    return (uint64_t)now.tv_sec * 1000 + now.tv_nsec / 1000000;
}

static void sleep_ms(unsigned milliseconds)
{
    struct timespec delay = {.tv_sec = milliseconds / 1000,
                             .tv_nsec = (milliseconds % 1000) * 1000000L};
    while (nanosleep(&delay, &delay) < 0) CHECK(errno == EINTR);
}

static void initialize(bool fatal, const char *port, bool tls)
{
    CHECK(logInit(LOG_ERR, NULL));
    sigHandleInit(test_argv);
    uSynergyInit(&synContext);
    synContext.m_clientName = "network-recovery-test";
    synContext.m_errorIsFatal[USYNERGY_ERROR_TIMEOUT] = fatal;
    CHECK(synNetInit(&synNetContext, &synContext, "127.0.0.1", port, tls, true));
    netPollInit();
}

static int connected_pair(bool fatal)
{
    int sockets[2];
    CHECK(socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, sockets) == 0);
    initialize(fatal, "0", false);
    synNetContext.fd = sockets[0];
    synContext.m_connected = true;
    synContext.m_hasReceivedHello = true;
    synContext.m_lastMessageTime = synContext.m_getTimeFunc();
    return sockets[1];
}

static bool reconnect(uSynergyCookie cookie)
{
    (void)cookie;
    ++reconnects;
    return true;
}

static void verify_disconnect(bool fatal)
{
    CHECK(!synContext.m_connected);
    CHECK(synNetContext.fd == -1);
    CHECK(synContext.m_lastError == USYNERGY_ERROR_TIMEOUT);
    synContext.m_connectFunc = reconnect;
    uSynergyUpdate(&synContext);
    /* Fatal mode must exit through the actual protocol fatal check. */
    CHECK(!fatal);
    CHECK(reconnects == 1);
    CHECK(synContext.m_connected);
}

static void poll_stall(bool fatal)
{
    int peer = connected_pair(fatal);
    netPoll(&synNetContext, &wlContext);
    verify_disconnect(fatal);
    close(peer);
}

static void fatal_poll_stall(void) { poll_stall(true); }
static void nonfatal_poll_stall(void) { poll_stall(false); }

static void stale_messages(bool fatal)
{
    int pipefd[2];
    int peer = connected_pair(fatal);
    CHECK(pipe2(pipefd, O_CLOEXEC) == 0);
    wayland_fd = pipefd[0];
    CHECK(write(pipefd[1], "x", 1) == 1);
    /* A ready unrelated descriptor must not hide a stalled Synergy stream. */
    synContext.m_lastMessageTime -= USYNERGY_IDLE_TIMEOUT + 1;
    netPoll(&synNetContext, &wlContext);
    verify_disconnect(fatal);
    close(pipefd[0]);
    close(pipefd[1]);
    close(peer);
}

static void fatal_stale_messages(void) { stale_messages(true); }
static void nonfatal_stale_messages(void) { stale_messages(false); }

static pid_t helper_fork(void)
{
    pid_t owner = getpid();
    pid_t child = fork();
    CHECK(child >= 0);
    if (!child) {
        /* Helpers cannot outlive a failed test or its time limit. */
        CHECK(prctl(PR_SET_PDEATHSIG, SIGKILL) == 0);
        CHECK(getppid() == owner);
    }
    return child;
}

static void healthy_heartbeats(void)
{
    int peer = connected_pair(true);
    pid_t receiver = getpid();
    if (!helper_fork()) {
        const unsigned char keepalive[] = {0, 0, 0, 4, 'C', 'A', 'L', 'V'};
        close(synNetContext.fd);
        uint64_t deadline = monotonic_ms() + USYNERGY_IDLE_TIMEOUT + 2000;
        do {
            CHECK(write(peer, keepalive, sizeof(keepalive)) == sizeof(keepalive));
            sleep_ms(500);
        } while (monotonic_ms() < deadline);
        CHECK(kill(receiver, SIGTERM) == 0);
        _exit(EXIT_SUCCESS);
    }
    close(peer);
    netPoll(&synNetContext, &wlContext);
    /* Only the helper's clean SIGTERM should end this case; no input events
     * occur, but actual CALV packets keep the connection alive beyond 10s. */
    CHECK(false);
}

static int loopback_socket(char port[6], bool listening)
{
    struct sockaddr_in address = {.sin_family = AF_INET,
                                 .sin_addr.s_addr = htonl(INADDR_LOOPBACK)};
    socklen_t length = sizeof(address);
    int fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    CHECK(fd >= 0);
    CHECK(bind(fd, (struct sockaddr *)&address, sizeof(address)) == 0);
    CHECK(getsockname(fd, (struct sockaddr *)&address, &length) == 0);
    CHECK(snprintf(port, 6, "%u", ntohs(address.sin_port)) > 0);
    if (listening) CHECK(listen(fd, 1) == 0);
    return fd;
}

static void tls_stall(bool fatal)
{
    char port[6];
    int listener = loopback_socket(port, true);
    initialize(fatal, port, true);
    if (!helper_fork()) {
        int peer = accept4(listener, NULL, NULL, SOCK_CLOEXEC);
        CHECK(peer >= 0);
        close(listener);
        /* TCP is accepted, but no TLS response is sent. The real SIGALRM
         * handler must interrupt the actual libtls handshake after 10s. */
        for (;;) pause();
    }
    close(listener);
    uSynergyUpdate(&synContext);
    CHECK(!synContext.m_connected);
    CHECK(synNetContext.fd == -1);
    CHECK(synContext.m_lastError == USYNERGY_ERROR_TIMEOUT);
    synContext.m_connectFunc = reconnect;
    uSynergyUpdate(&synContext);
    CHECK(!fatal);
    CHECK(reconnects == 1);
}

static void fatal_tls_stall(void) { tls_stall(true); }
static void nonfatal_tls_stall(void) { tls_stall(false); }

static void ordinary_rejection(void)
{
    char port[6];
    /* Keeping the port bound but not listening makes ECONNREFUSED local and
     * deterministic. It must remain a retryable failure, not an alarm. */
    int reserved = loopback_socket(port, false);
    initialize(true, port, true);
    uSynergyUpdate(&synContext);
    CHECK(!synContext.m_connected);
    CHECK(synNetContext.fd == -1);
    CHECK(synContext.m_lastError == USYNERGY_ERROR__INIT);
    synContext.m_connectFunc = reconnect;
    uSynergyUpdate(&synContext);
    CHECK(reconnects == 1);
    close(reserved);
}

static struct tls *ephemeral_tls_server(void)
{
    /* Generate test-only key material in memory; no pairing key is read or
     * written. The certificate lives only as long as this test process. */
    EVP_PKEY_CTX *key_context = EVP_PKEY_CTX_new_id(EVP_PKEY_EC, NULL);
    EVP_PKEY *key = NULL;
    CHECK(key_context);
    CHECK(EVP_PKEY_keygen_init(key_context) == 1);
    CHECK(EVP_PKEY_CTX_set_ec_paramgen_curve_nid(key_context, NID_X9_62_prime256v1) == 1);
    CHECK(EVP_PKEY_keygen(key_context, &key) == 1);
    EVP_PKEY_CTX_free(key_context);
    X509 *certificate = X509_new();
    CHECK(certificate);
    CHECK(X509_set_version(certificate, 2) == 1);
    CHECK(ASN1_INTEGER_set(X509_get_serialNumber(certificate), 1) == 1);
    CHECK(X509_gmtime_adj(X509_getm_notBefore(certificate), -60));
    CHECK(X509_gmtime_adj(X509_getm_notAfter(certificate), 3600));
    CHECK(X509_set_pubkey(certificate, key) == 1);
    X509_NAME *name = X509_get_subject_name(certificate);
    CHECK(X509_NAME_add_entry_by_txt(name, "CN", MBSTRING_ASC,
                                     (const unsigned char *)"localhost", -1, -1, 0) == 1);
    CHECK(X509_set_issuer_name(certificate, name) == 1);
    CHECK(X509_sign(certificate, key, EVP_sha256()) > 0);
    BIO *cert_memory = BIO_new(BIO_s_mem());
    BIO *key_memory = BIO_new(BIO_s_mem());
    CHECK(cert_memory && key_memory);
    CHECK(PEM_write_bio_X509(cert_memory, certificate) == 1);
    CHECK(PEM_write_bio_PrivateKey(key_memory, key, NULL, NULL, 0, NULL, NULL) == 1);
    struct tls_config *config = tls_config_new();
    struct tls *server = tls_server();
    CHECK(config && server);
    char *data = NULL;
    long length = BIO_get_mem_data(cert_memory, &data);
    CHECK(length > 0);
    CHECK(tls_config_set_cert_mem(config, (const uint8_t *)data, (size_t)length) == 0);
    length = BIO_get_mem_data(key_memory, &data);
    CHECK(length > 0);
    CHECK(tls_config_set_key_mem(config, (const uint8_t *)data, (size_t)length) == 0);
    CHECK(tls_configure(server, config) == 0);
    tls_config_free(config);
    BIO_free(cert_memory);
    BIO_free(key_memory);
    X509_free(certificate);
    EVP_PKEY_free(key);
    return server;
}

static void handshake_want_retries(void)
{
    char port[6];
    int listener = loopback_socket(port, true);
    initialize(true, port, true);
    struct tls *server = ephemeral_tls_server();
    if (!helper_fork()) {
        int peer = accept4(listener, NULL, NULL, SOCK_CLOEXEC);
        struct tls *connection = NULL;
        CHECK(peer >= 0);
        close(listener);
        CHECK(tls_accept_socket(server, &connection, peer) == 0);
        int result;
        do {
            result = __real_tls_handshake(connection);
        } while (result == TLS_WANT_POLLIN || result == TLS_WANT_POLLOUT);
        CHECK(result == 0);
        unsigned char ignored;
        /* Wait for the client's orderly close after successful negotiation. */
        do {
            result = (int)tls_read(connection, &ignored, 1);
        } while (result == TLS_WANT_POLLIN || result == TLS_WANT_POLLOUT);
        tls_close(connection);
        tls_free(connection);
        tls_free(server);
        close(peer);
        _exit(EXIT_SUCCESS);
    }
    close(listener);
    tls_free(server);
    handshake_wants = 2;
    uSynergyUpdate(&synContext);
    CHECK(synContext.m_connected);
    CHECK(handshake_wants == 0 && handshake_calls >= 3);
    CHECK(synContext.m_lastError == USYNERGY_ERROR__INIT);
    CHECK(synNetDisconnect(&synNetContext));
}

static void restart_cancels_alarm(void)
{
    initialize(false, "0", false);
    char *restart_argv[] = {"/proc/self/exe", "--check-no-inherited-alarm", NULL};
    sigHandleInit(restart_argv);
    alarm(USYNERGY_IDLE_TIMEOUT / 1000);
    Restart(SES_SUCCESS);
    CHECK(false);
}

struct test_case {
    const char *name;
    void (*run)(void);
    int expected_status;
    unsigned minimum_ms;
    pid_t pid;
    uint64_t started;
    bool complete;
};

int main(int argc, char **argv)
{
    /* Reached through the real Restart()/execvp() path, before creating any
     * test configuration or arming a new timer in the replacement process. */
    if (argc == 2 && strcmp(argv[1], "--check-no-inherited-alarm") == 0)
        return alarm(0) == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
    char configuration[] = "/tmp/waynergy-network-test.XXXXXX";
    CHECK(mkdtemp(configuration));
    /* No real pairing hashes, client keys, or user configuration are read. */
    osConfigPathOverride = configuration;
    struct test_case tests[] = {
        {"fatal poll stall", fatal_poll_stall, SES_ERROR_SYN, USYNERGY_IDLE_TIMEOUT},
        {"nonfatal poll stall", nonfatal_poll_stall, 0, USYNERGY_IDLE_TIMEOUT},
        {"fatal stale stream with unrelated events", fatal_stale_messages, SES_ERROR_SYN, 0},
        {"nonfatal stale stream with unrelated events", nonfatal_stale_messages, 0, 0},
        {"healthy CALV heartbeats without input", healthy_heartbeats, 0, USYNERGY_IDLE_TIMEOUT + 1000},
        {"fatal stalled TLS handshake", fatal_tls_stall, SES_ERROR_SYN, USYNERGY_IDLE_TIMEOUT},
        {"nonfatal stalled TLS handshake", nonfatal_tls_stall, 0, USYNERGY_IDLE_TIMEOUT},
        {"ordinary connection rejection remains retryable", ordinary_rejection, 0, 0},
        {"TLS WANT_READ and WANT_WRITE complete real handshake", handshake_want_retries, 0, 0},
        {"restart does not inherit previous alarm", restart_cancels_alarm, 0, 0},
    };
    size_t count = sizeof(tests) / sizeof(tests[0]);
    for (size_t i = 0; i < count; ++i) {
        tests[i].started = monotonic_ms();
        tests[i].pid = fork();
        CHECK(tests[i].pid >= 0);
        if (!tests[i].pid) {
            CHECK(setpgid(0, 0) == 0);
            tests[i].run();
            _exit(EXIT_SUCCESS);
        }
        CHECK(setpgid(tests[i].pid, tests[i].pid) == 0 || errno == EACCES || errno == ESRCH);
    }
    size_t remaining = count;
    unsigned failures = 0;
    while (remaining) {
        for (size_t i = 0; i < count; ++i) {
            struct test_case *test = &tests[i];
            if (test->complete) continue;
            int status = 0;
            pid_t done = waitpid(test->pid, &status, WNOHANG);
            CHECK(done >= 0);
            uint64_t elapsed = monotonic_ms() - test->started;
            bool overdue = elapsed > USYNERGY_IDLE_TIMEOUT + 10000;
            if (!done && !overdue) continue;
            if (overdue && !done) {
                CHECK(kill(-test->pid, SIGKILL) == 0);
                CHECK(waitpid(test->pid, &status, 0) == test->pid);
            }
            /* Also reap helper groups if the tested process exited early. */
            if (kill(-test->pid, SIGKILL) < 0) CHECK(errno == ESRCH);
            bool passed = !overdue && WIFEXITED(status) &&
                          WEXITSTATUS(status) == test->expected_status &&
                          elapsed >= test->minimum_ms;
            printf("%s: %s (%llu ms, status %d)\n", passed ? "PASS" : "FAIL",
                   test->name, (unsigned long long)elapsed,
                   WIFEXITED(status) ? WEXITSTATUS(status) : -1);
            if (!passed) ++failures;
            test->complete = true;
            --remaining;
        }
        if (remaining) sleep_ms(20);
    }
    /* The successful TOFU test writes only its public certificate hash. */
    char generated[PATH_MAX];
    CHECK(snprintf(generated, sizeof(generated), "%s/tls/hash/127.0.0.1", configuration) > 0);
    CHECK(unlink(generated) == 0 || errno == ENOENT);
    CHECK(snprintf(generated, sizeof(generated), "%s/tls/hash", configuration) > 0);
    CHECK(rmdir(generated) == 0 || errno == ENOENT);
    CHECK(snprintf(generated, sizeof(generated), "%s/tls", configuration) > 0);
    CHECK(rmdir(generated) == 0 || errno == ENOENT);
    CHECK(rmdir(configuration) == 0);
    printf("Network recovery: %zu cases, %u failures\n", count, failures);
    return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}

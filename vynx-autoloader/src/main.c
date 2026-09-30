/*
 * Vynx.dev Autoloader Installer - Main Entry Point
 *
 * This is a native PS5 ELF that starts a temporary HTTP server, opens the
 * browser to cache a page (or set of pages), installs the homescreen shortcut
 * once the cache is complete (via the /install route), then exits. On
 * subsequent launches from the homescreen, the cached content loads offline.
 *
 * This file handles: process init, signal setup, MHD lifecycle, shutdown.
 */

#include <microhttpd.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <sys/sysctl.h>
#include <unistd.h>

#include "vynx.h"
#include "http_server.h"
#include "ps5_launcher.h"

static pid_t find_pid(const char *name) {
    int mib[4] = {1, 14, 8, 0};
    pid_t mypid = getpid();
    pid_t pid = -1;
    size_t buf_size;
    uint8_t *buf;

    if (sysctl(mib, 4, 0, &buf_size, 0, 0)) {
        vynxi_log("[VYNXI] sysctl failed\n");
        return -1;
    }

    if (!(buf = malloc(buf_size))) {
        vynxi_log("[VYNXI] malloc failed\n");
        return -1;
    }

    if (sysctl(mib, 4, buf, &buf_size, 0, 0)) {
        vynxi_log("[VYNXI] sysctl failed\n");
        free(buf);
        return -1;
    }

    /* KERN_PROC_ALL scan — raw offsets into FreeBSD 12's struct kinfo_proc
     * as exposed by the PS5 kernel: ki_pid at offset 72, ki_tdname at 447
     * (matches the layout used by the ps5-payload-dev SDK's klib). These
     * are ABI-specific; re-check if the kernel struct ever changes. */
    for (uint8_t *ptr = buf; ptr < (buf + buf_size);) {
        int ki_structsize = *(int *)ptr;
        pid_t ki_pid = *(pid_t *)&ptr[72];
        char *ki_tdname = (char *)&ptr[447];

        ptr += ki_structsize;
        if (!strcmp(name, ki_tdname) && ki_pid != mypid) {
            pid = ki_pid;
        }
    }

    free(buf);
    return pid;
}

/* PS5 System Calls (Internal) */
extern int sceNetCtlInit();
extern int sceUserServiceInitialize(void *);
extern int sceUserServiceGetForegroundUser(int *);

__attribute__((used)) volatile const char vynxi_version_sig[] =
    "VYNXI_VER:" VYNX_FULL_VERSION;

int main(void) {
    struct MHD_Daemon *daemon;
    pid_t pid;

    syscall(SYS_thr_set_name, -1, VYNXI_THREAD_NAME);

    /* Kill previous installer instances */
    while ((pid = find_pid(VYNXI_THREAD_NAME)) > 0) {
        if (kill(pid, SIGKILL)) {
            vynxi_log("[VYNXI] kill failed\n");
            return EXIT_FAILURE;
        }
        sleep(1);
    }

    vynxi_log("[VYNXI] Vynx.dev Autoloader Installer v%s by Vynx Developments (built %s) starting on port %d...\n",
                   VYNX_FULL_VERSION, VYNX_BUILD_TIME, VYNXI_PORT);

    /* Initialize PS5 System Services */
    int err;
    if ((err = sceNetCtlInit()) == 0) {
        vynxi_log("[VYNXI] Network Controller initialized.\n");
    } else {
        vynxi_log("[VYNXI] sceNetCtlInit failed: 0x%08X\n", err);
    }

    int user_prio = 256;
    if ((err = sceUserServiceInitialize(&user_prio)) == 0) {
        vynxi_log("[VYNXI] User Service initialized.\n");
    } else {
        vynxi_log("[VYNXI] sceUserServiceInitialize failed: 0x%08X\n", err);
    }

    /* The homescreen app is installed/updated only AFTER the browser has
     * finished caching (via the /install route), so a shortcut is never
     * created for a partial cache. Nothing app-related happens at startup. */
    signal(SIGPIPE, SIG_IGN);
    signal(SIGHUP, SIG_IGN);
    signal(SIGTERM, SIG_IGN);

    /* Start the MHD daemon using a thread pool to handle concurrent AppCache requests. */
    daemon = MHD_start_daemon(MHD_USE_INTERNAL_POLLING_THREAD | MHD_USE_DEBUG,
                              VYNXI_PORT, NULL, NULL, &http_on_request,
                              NULL, 
                              MHD_OPTION_THREAD_POOL_SIZE, (unsigned int)8,
                              MHD_OPTION_END);

    if (NULL == daemon) {
        vynxi_log("[VYNXI] Failed to start HTTP daemon!\n");
        vynxi_notify("Vynx.dev Autoloader Installer: Error\nHTTP server failed to start");
        return 1;
    }

    vynxi_log("[VYNXI] Server running. Waiting for the browser to cache content...\n");

    /* Query foreground user ID to pass to the frontend URL so the UI can
     * display the exact /user/home/<userid>/webkit/shell/ path in prompts. */
    int uid = -1;
    char uid_param[32] = "";
    if (sceUserServiceGetForegroundUser(&uid) == 0 && uid > 0) {
        snprintf(uid_param, sizeof(uid_param), "&uid=%08x", (unsigned int)uid);
    }

    /* Launch the browser at a versioned URL so the old AppCache master entry
     * for "/" is never served from the previous install. */
    char browser_url[256];
    snprintf(browser_url, sizeof(browser_url),
             "http://127.0.0.1:%d/?v=%s%s", VYNXI_PORT, VYNX_FULL_VERSION, uid_param);
    ps5_launch_browser(browser_url);

    /* Main loop — runs until /install succeeds (which also installs the
     * homescreen app) and sets http_keep_running to 0 */
    int webkit_clear_attempts = 0;

    while (atomic_load(&http_keep_running)) {
        /* Check if the frontend requested a WebKit data clear */
        if (atomic_load(&webkit_data_cleared)) {
            atomic_store(&webkit_data_cleared, 0);
            webkit_clear_attempts++;

            if (webkit_clear_attempts <= 1) {
                /* Give the HTTP response time to flush before re-launching */
                usleep(500000);
                vynxi_log("[VYNXI] Re-launching browser after WebKit data clear (attempt %d)...\n",
                          webkit_clear_attempts);
                char retry_url[256];
                snprintf(retry_url, sizeof(retry_url),
                         "http://127.0.0.1:%d/?v=%s%s&retry=1",
                         VYNXI_PORT, VYNX_FULL_VERSION, uid_param);
                ps5_launch_browser(retry_url);
            } else {
                vynxi_log("[VYNXI] WebKit clear already attempted %d time(s), not re-launching.\n",
                          webkit_clear_attempts);
            }
        }
        usleep(100000); /* 100ms sleep */
    }

    if (atomic_load(&install_completed)) {
        vynxi_notify("Vynx.dev Autoloader v%s cached successfully!", VYNX_FULL_VERSION);
    }
    vynxi_log_wakeup();

    /* Give the /logs thread half a second to wake up and flush the final logs 
     * over the network before we aggressively kill the MHD daemon and all sockets. */
    usleep(500000); 

    if (daemon)
        MHD_stop_daemon(daemon);

    sleep(1);

    return 0;
}

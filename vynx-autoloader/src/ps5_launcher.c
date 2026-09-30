#include <stdio.h>

#include "vynx.h"
#include "ps5_launcher.h"

extern int sceSystemServiceLaunchWebBrowser(const char *uri);

int ps5_launch_browser(const char *uri) {
  vynxi_log("[VYNXI] Launching browser: %s\n", uri);
  if (sceSystemServiceLaunchWebBrowser(uri) != 0) {
    vynxi_notify("VYNXI: Failed to launch browser.");
    return -1;
  }
  return 0;
}

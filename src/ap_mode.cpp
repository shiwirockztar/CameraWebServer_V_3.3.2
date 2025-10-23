#include "ap_mode.h"
#include <WiFi.h>

static IPAddress _apIP;

bool apModeStart(const char *ssid, const char *pass) {
  if (!ssid) return false;
  bool ok;
  if (pass && strlen(pass) > 0) {
    ok = WiFi.softAP(ssid, pass);
  } else {
    ok = WiFi.softAP(ssid);
  }
  if (!ok) return false;
  delay(200);
  _apIP = WiFi.softAPIP();
  return true;
}

void apModeStop() {
  WiFi.softAPdisconnect(true);
}

const char *apModeIP() {
  static char buf[32];
  IPAddress ip = _apIP;
  if (ip) {
    snprintf(buf, sizeof(buf), "%u.%u.%u.%u", ip[0], ip[1], ip[2], ip[3]);
  } else {
    snprintf(buf, sizeof(buf), "0.0.0.0");
  }
  return buf;
}

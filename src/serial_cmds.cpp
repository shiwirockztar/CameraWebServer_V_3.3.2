#include "serial_cmds.h"
#include "esp_camera.h"
#include <WiFi.h>
#include <Preferences.h>

extern String wifi_ssid;
extern String wifi_password;
extern Preferences prefs;

static String incoming = "";

void serialCmdsBegin() {
  // nothing to init currently
}

static void saveCredentials() {
  prefs.begin("wifi", false);
  prefs.putString("ssid", wifi_ssid);
  prefs.putString("pass", wifi_password);
  prefs.end();
  Serial.println("Credentials saved to NVS");
}

static void eraseCredentials() {
  prefs.begin("wifi", false);
  prefs.remove("ssid");
  prefs.remove("pass");
  prefs.end();
  Serial.println("Credentials removed from NVS");
}

static bool connectWiFi(unsigned long timeoutMs = 15000) {
  Serial.printf("Connecting to WiFi '%s'...\n", wifi_ssid.c_str());
  WiFi.disconnect(true);
  WiFi.begin(wifi_ssid.c_str(), wifi_password.c_str());
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < timeoutMs) {
    delay(500);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    return true;
  }
  Serial.println("WiFi connection failed");
  return false;
}

void serialCmdsPrintHelp() {
  Serial.println("Serial commands:");
  Serial.println("  setssid <ssid>    - Set SSID and save");
  Serial.println("  setpass <pass>    - Set password and save");
  Serial.println("  showcreds         - Show current SSID and masked password");
  Serial.println("  showip            - Show current IP if connected");
  Serial.println("  connect           - Attempt to connect using current credentials");
  Serial.println("  erasecreds        - Remove saved credentials from NVS (resets to defaults)");
  Serial.println("  help              - Show this message");
}

void handleSerialCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  if (cmd.equalsIgnoreCase("help")) {
    serialCmdsPrintHelp();
    return;
  }
  if (cmd.startsWith("setssid ")) {
    String v = cmd.substring(8);
    v.trim();
    if (v.length() > 0) {
      wifi_ssid = v;
      saveCredentials();
      Serial.println("SSID updated");
    } else Serial.println("Usage: setssid <ssid>");
    return;
  }
  if (cmd.startsWith("setpass ")) {
    String v = cmd.substring(8);
    v.trim();
    if (v.length() > 0) {
      wifi_password = v;
      saveCredentials();
      Serial.println("Password updated");
    } else Serial.println("Usage: setpass <password>");
    return;
  }
  if (cmd.equalsIgnoreCase("showcreds")) {
    Serial.printf("SSID: %s\n", wifi_ssid.c_str());
    String masked = "";
    for (size_t i = 0; i < wifi_password.length(); ++i) masked += '*';
    Serial.printf("Password: %s\n", masked.c_str());
    return;
  }
  if (cmd.equalsIgnoreCase("showip")) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
    } else {
      Serial.println("Not connected to WiFi");
    }
    return;
  }
  if (cmd.equalsIgnoreCase("connect")) {
    connectWiFi();
    return;
  }
  if (cmd.equalsIgnoreCase("erasecreds")) {
    eraseCredentials();
    // reload defaults from secrets/example will be handled by main
    return;
  }
  Serial.println("Unknown command. Type 'help' for commands.");
}

void serialCmdsLoop() {
  while (Serial.available()) {
    int c = Serial.read();
    if (c == '\r') continue; // ignore CR
    if (c == '\n') {
      handleSerialCommand(incoming);
      incoming = "";
    } else {
      incoming += (char)c;
      // prevent runaway memory usage
      if (incoming.length() > 256) incoming.remove(0, incoming.length() - 256);
    }
  }
}

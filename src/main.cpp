#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>

// ===========================
// Select camera model in board_config.h
// ===========================
#include "board_config.h"

// ===========================
// WiFi credentials are loaded from secrets/secrets.h (not tracked by git)
// Copy secrets/secrets.h.example -> secrets/secrets.h and fill in your values.
// The file must define these variables:
//   const char* WIFI_SSID = "your_ssid";
//   const char* WIFI_PASSWORD = "your_password";
// ===========================
#include "../secrets/secrets.h"

#include <Preferences.h>

// WiFi credentials stored in RAM for runtime modification and persisted in NVS
String wifi_ssid;
String wifi_password;
Preferences prefs;

// Initialize wifi_ssid/password from stored NVS values or fall back to secrets/defaults
void loadCredentials() {
  prefs.begin("wifi", false);
  String s = prefs.getString("ssid", "");
  String p = prefs.getString("pass", "");
  prefs.end();

  // If credentials are stored in NVS, use them. Otherwise use the values
  // provided in secrets/secrets.h (WIFI_SSID and WIFI_PASSWORD).
  if (s.length() > 0) {
    wifi_ssid = s;
  } else {
    // secrets.h must define WIFI_SSID as a const char* (see example file)
    wifi_ssid = String(WIFI_SSID);
  }

  if (p.length() > 0) {
    wifi_password = p;
  } else {
    // secrets.h must define WIFI_PASSWORD as a const char*
    wifi_password = String(WIFI_PASSWORD);
  }
}

void saveCredentials() {
  prefs.begin("wifi", false);
  prefs.putString("ssid", wifi_ssid);
  prefs.putString("pass", wifi_password);
  prefs.end();
  Serial.println("Credentials saved to NVS");
}

void eraseCredentials() {
  prefs.begin("wifi", false);
  prefs.remove("ssid");
  prefs.remove("pass");
  prefs.end();
  Serial.println("Credentials removed from NVS");
}

// Helper to (re)connect using current wifi_ssid/wifi_password
bool connectWiFi(unsigned long timeoutMs = 15000) {
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

// Serial command processing
void printHelp() {
  Serial.println("Serial commands:");
  Serial.println("  setssid <ssid>    - Set SSID and save");
  Serial.println("  setpass <pass>    - Set password and save");
  Serial.println("  showcreds         - Show current SSID and masked password");
  Serial.println("  connect           - Attempt to connect using current credentials");
  Serial.println("  erasecreds        - Remove saved credentials from NVS (resets to defaults)");
  Serial.println("  help              - Show this message");
}

void handleSerialCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  if (cmd.equalsIgnoreCase("help")) {
    printHelp();
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
    // reload defaults from secrets/example
    loadCredentials();
    return;
  }
  Serial.println("Unknown command. Type 'help' for commands.");
}

void startCameraServer();
void setupLedFlash();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;  // for streaming
  //config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    // Best option for face detection/recognition
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // flip it back
    s->set_brightness(s, 1);   // up the brightness just a bit
    s->set_saturation(s, -2);  // lower the saturation
  }
  // drop down frame size for higher initial frame rate
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif
  // Load credentials from NVS or fallback to secrets
  loadCredentials();

  Serial.printf("Using SSID: %s\n", wifi_ssid.c_str());
  bool wifi_ok = connectWiFi();
  if (wifi_ok) {
    WiFi.setSleep(false);
  }

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
}

void loop() {
  static String incoming = "";
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

  // Keep the rest of the original loop behavior if any (camera server is event driven)
  delay(10);
}

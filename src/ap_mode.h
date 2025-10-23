#pragma once

#include <Arduino.h>

// Start an access point with given SSID and optional password.
// If pass == nullptr or empty, AP is opened (no password).
// Returns true on success.
bool apModeStart(const char *ssid, const char *pass = nullptr);

// Stop AP mode
void apModeStop();

// Returns the AP IP as a NUL-terminated C string (owned by module)
const char *apModeIP();

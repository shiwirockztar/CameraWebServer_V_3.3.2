#pragma once

#include <Arduino.h>

// Initialize module (if needed)
void serialCmdsBegin();

// Called periodically from main loop to process serial input
void serialCmdsLoop();

// Expose helper to print help from other modules
void serialCmdsPrintHelp();

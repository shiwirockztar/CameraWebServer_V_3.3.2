#pragma once

#include "esp_http_server.h"

// Register the portal endpoints on an existing httpd server handle
void portal_register(httpd_handle_t server);

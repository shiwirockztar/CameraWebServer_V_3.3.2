#include "portal.h"
#include <Preferences.h>
#include <Arduino.h>

static String urlDecode(const String &input) {
  String ret = "";
  for (size_t i = 0; i < input.length(); ++i) {
    char c = input.charAt(i);
    if (c == '+') ret += ' ';
    else if (c == '%' && i + 2 < input.length()) {
      char hex[3] = { input.charAt(i+1), input.charAt(i+2), 0 };
      char val = (char) strtol(hex, NULL, 16);
      ret += val;
      i += 2;
    } else ret += c;
  }
  return ret;
}

static const char *portal_form =
"<html><head><title>Camera WiFi Portal</title></head><body>"
"<h2>Configure WiFi</h2>"
"<form method=POST action=\"/portal/save\">"
"SSID:<br><input type=text name=ssid size=32><br>"
"Password:<br><input type=password name=pass size=32><br><br>"
"<input type=submit value=Save>"
"</form>"
"<p>After saving, press <a href=\"/portal/reboot\">reboot</a> to apply.</p>"
"</body></html>";

static esp_err_t portal_get_handler(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, portal_form, strlen(portal_form));
}

static esp_err_t portal_save_handler(httpd_req_t *req) {
  int total_len = req->content_len;
  if (total_len <= 0) {
    httpd_resp_set_status(req, "400 Bad Request");
    const char *bad = "Bad Request";
    httpd_resp_send(req, bad, strlen(bad));
    return ESP_FAIL;
  }
  char *buf = (char *)malloc(total_len + 1);
  if (!buf) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }
  int received = 0;
  while (received < total_len) {
    int r = httpd_req_recv(req, buf + received, total_len - received);
    if (r <= 0) {
      free(buf);
      httpd_resp_send_500(req);
      return ESP_FAIL;
    }
    received += r;
  }
  buf[total_len] = '\0';
  String body = String(buf);
  free(buf);

  String ssid = "";
  String pass = "";
  int i = body.indexOf("ssid=");
  if (i >= 0) {
    int j = body.indexOf('&', i);
    String v = (j >= 0) ? body.substring(i+5, j) : body.substring(i+5);
    ssid = urlDecode(v);
  }
  i = body.indexOf("pass=");
  if (i >= 0) {
    int j = body.indexOf('&', i);
    String v = (j >= 0) ? body.substring(i+5, j) : body.substring(i+5);
    pass = urlDecode(v);
  }

  Preferences prefs;
  prefs.begin("wifi", false);
  if (ssid.length() > 0) prefs.putString("ssid", ssid);
  if (pass.length() > 0) prefs.putString("pass", pass);
  prefs.end();

  const char *resp = "<html><body><h3>Saved. Please reboot the device to apply settings.</h3>"
                     "<p><a href=\"/portal/reboot\">Reboot now</a></p></body></html>";
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, resp, strlen(resp));
}

static esp_err_t portal_reboot_handler(httpd_req_t *req) {
  const char *resp = "<html><body><h3>Rebooting...</h3></body></html>";
  httpd_resp_set_type(req, "text/html");
  httpd_resp_send(req, resp, strlen(resp));
  esp_restart();
  return ESP_OK;
}

void portal_register(httpd_handle_t server) {
  httpd_uri_t portal_uri = {
    .uri = "/portal",
    .method = HTTP_GET,
    .handler = portal_get_handler,
    .user_ctx = NULL
  };
  httpd_register_uri_handler(server, &portal_uri);

  httpd_uri_t portal_save_uri = {
    .uri = "/portal/save",
    .method = HTTP_POST,
    .handler = portal_save_handler,
    .user_ctx = NULL
  };
  httpd_register_uri_handler(server, &portal_save_uri);

  httpd_uri_t portal_reboot_uri = {
    .uri = "/portal/reboot",
    .method = HTTP_GET,
    .handler = portal_reboot_handler,
    .user_ctx = NULL
  };
  httpd_register_uri_handler(server, &portal_reboot_uri);
}

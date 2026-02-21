
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include "Arduino.h"
#include <time.h>


const char* ssid = "";
const char* password = "";

// NTP
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 10800;
const int   daylightOffset_sec = 0;


#define FLASH_LED_PIN 4

// Пины AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

httpd_handle_t camera_httpd = NULL;

static esp_err_t stream_handler(httpd_req_t *req){
  esp_err_t res = ESP_OK;
  char part_buf[64];

  res = httpd_resp_set_type(req, "multipart/x-mixed-replace;boundary=123456789000000000000987654321");
  if(res != ESP_OK) return res;
  
  while(true){
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      vTaskDelay(50 / portTICK_PERIOD_MS);
      continue;
    }
    
    if(fb->format != PIXFORMAT_JPEG){
      esp_camera_fb_return(fb);
      vTaskDelay(50 / portTICK_PERIOD_MS);
      continue;
    }
    
    size_t hlen = snprintf(part_buf, 64, "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", fb->len);
    res = httpd_resp_send_chunk(req, part_buf, hlen);
    if(res != ESP_OK){
      esp_camera_fb_return(fb);
      break;
    }
    
    res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
    if(res != ESP_OK){
      esp_camera_fb_return(fb);
      break;
    }
    
    res = httpd_resp_send_chunk(req, "\r\n--123456789000000000000987654321\r\n", 42);
    esp_camera_fb_return(fb);
    
    if(res != ESP_OK) break;
    vTaskDelay(40 / portTICK_PERIOD_MS);
  }
  return res;
}

static esp_err_t index_handler(httpd_req_t *req){
  httpd_resp_set_type(req, "text/html");
  
  const char* html = 
    "<!DOCTYPE html><html><head>"
    "<meta charset='UTF-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>ESP32-CAM HD</title>"
    "<style>"
    "*{margin:0;padding:0;box-sizing:border-box;}"
    "html,body{height:100vh;width:100vw;overflow:hidden;background:#000;}"
    "#stream{width:100vw;height:100vh;object-fit:cover;}"
    ".controls{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);"
    "display:flex;gap:10px;background:rgba(0,0,0,0.8);padding:15px;border-radius:30px;}"
    ".btn{padding:12px 20px;background:#00ff41;color:#000;border:none;border-radius:20px;"
    "font-weight:bold;cursor:pointer;font-size:14px;transition:0.3s;}"
    ".btn:hover{transform:scale(1.05);background:#00cc33;}"
    "</style></head><body>"
    "<img id='stream' src='/stream' autoplay muted playsinline>"
    "<div class='controls'>"
    "<button class='btn' onclick='location.reload()'>🔄</button>"
    "<button class='btn' onclick='document.getElementById(`stream`).requestFullscreen()'>📱</button>"
    "</div>"
    "</body></html>";
  
  return httpd_resp_send(req, html, strlen(html));
}

void startCameraServer(){
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.max_uri_handlers = 2;
  config.stack_size = 8192;
  config.task_priority = 5;
  config.lru_purge_enable = true;
  
  httpd_uri_t index_uri = {
    .uri = "/", .method = HTTP_GET, .handler = index_handler, .user_ctx = NULL
  };
  httpd_uri_t stream_uri = {
    .uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = NULL
  };

  if (httpd_start(&camera_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(camera_httpd, &index_uri);
    httpd_register_uri_handler(camera_httpd, &stream_uri);
  }
}


void flashLed(bool state) {
  digitalWrite(FLASH_LED_PIN, state ? HIGH : LOW);
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("\n🚀 ESP32-CAM FLASH HD v5.9");
  

  pinMode(FLASH_LED_PIN, OUTPUT);
  digitalWrite(FLASH_LED_PIN, LOW);  // Выключить сначала
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 18000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_CIF;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_DRAM;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed: 0x%x\n", err);
    return;
  }
  
  sensor_t * s = esp_camera_sensor_get();
  s->set_framesize(s, FRAMESIZE_CIF);
  s->set_quality(s, 12);
  s->set_brightness(s, 1);
  s->set_contrast(s, 1);
  s->set_saturation(s, 1);
  
  Serial.println("✅ HD Camera 400x296 OK");

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  Serial.print("📶 WiFi");
  int i = 0;
  while (WiFi.status() != WL_CONNECTED && i++ < 20) {
    delay(500);
    Serial.print(".");
  }
  
  char ipStr[16];
  sprintf(ipStr, "%d.%d.%d.%d", WiFi.localIP()[0], WiFi.localIP()[1], WiFi.localIP()[2], WiFi.localIP()[3]);
  
  Serial.println("\n✅ WiFi OK!");
  
  // ✅ ВКЛЮЧИТЬ ФОНАРЬ ПОСЛЕ КАМЕРЫ И WIFI
  Serial.println("💡 Включаем фонарь...");
  flashLed(true);  // ВКЛЮЧИТЬ ФОНАРЬ!
  delay(500);
  
  Serial.println("═══════════════════════════════");
  Serial.printf("🌐 http://%s/\n", ipStr);
  Serial.printf("📱 http://%s/stream\n", ipStr);
  Serial.println("═══════════════════════════════");

  startCameraServer();
  Serial.println("✅ FLASH HD Server OK v5.9 | Фонарь ВКЛ!");
}

void loop() {
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 20000) {
    if(WiFi.status() == WL_CONNECTED){
      char ipStr[16];
      sprintf(ipStr, "%d.%d.%d.%d", WiFi.localIP()[0], WiFi.localIP()[1], WiFi.localIP()[2], WiFi.localIP()[3]);
      Serial.printf("🔥 HD LIVE + FLASH | http://%s/ | RAM: %d\n", ipStr, ESP.getFreeHeap());
    }
    lastPrint = millis();
  }
  delay(2000);
}

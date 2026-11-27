/*
 * StreetWatch Neo ESP32 firmware
 * L298N pinout retained. Setup portal uses Preferences/NVS and a WPA2 AP.
 * Libraries: ArduinoJson 7.x, ESP32 Arduino core.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <time.h>

static const int ENA=25, IN1=26, IN2=27, ENB=33, IN3=14, IN4=13;
static const int TRIG_PIN=5, ECHO_PIN=18;
static const int LINE_PINS[4]={32,34,35,36};
static const int BRUSH_PIN=16, LED_PIN=17, SPRAY_PIN=19, RIG_UP_PIN=21, RIG_DOWN_PIN=22;
static const int BATTERY_PIN=39;
static const int SETUP_BUTTON_PIN=4; // momentary button to GND, hold 4 seconds
static const bool USE_BATTERY_SENSOR=false, USE_ULTRASONIC_INTERLOCK=true;
static const float BATTERY_DIVIDER_RATIO=2.0f, BATTERY_EMPTY_V=6.4f, BATTERY_FULL_V=8.4f;
static const float OBSTACLE_STOP_CM=16.0f, LINE_KP=34.0f;
static const unsigned long COMMAND_INTERVAL_MS=2000, TELEMETRY_INTERVAL_MS=30000;
static const unsigned long COMMAND_STALE_MS=8000, WIFI_RECOVERY_MS=120000;
static const char *SETUP_SSID="STREETWATCH-SETUP";

// ISRG Root X1. Keep certificate verification enabled for Render HTTPS.
static const char ROOT_CA[] PROGMEM = R"PEM(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
)PEM";

Preferences prefs;
WebServer portal(80);
DNSServer dns;
WiFiClientSecure tls;
WiFiClient plain;
String wifiSsid, wifiPassword, deviceId, deviceToken, serverUrl;
String modeNow="manual", commandNow="stop", lineColor="white";
int speedNow=150;
unsigned long nextCommandPoll=0,lastTelemetry=0,lastWifiAttempt=0,lastGoodCommand=0,wifiLostAt=0,serverBackoffMs=COMMAND_INTERVAL_MS;
float distanceCm=-1;
bool obstacleDetected=false,serverStop=true,portalMode=false,timeSynced=false,stationReady=false,requireFreshCommand=true;\nuint32_t lastCommandId=0;
bool brushOn=false,ledOn=false,sprayOn=false,rigUpOn=false,rigDownOn=false;
bool lineActive[4]={false,false,false,false};

void allAccessoriesOff(){brushOn=ledOn=sprayOn=rigUpOn=rigDownOn=false;digitalWrite(BRUSH_PIN,LOW);digitalWrite(LED_PIN,LOW);digitalWrite(SPRAY_PIN,LOW);digitalWrite(RIG_UP_PIN,LOW);digitalWrite(RIG_DOWN_PIN,LOW);}
void stopMotors(){digitalWrite(IN1,LOW);digitalWrite(IN2,LOW);digitalWrite(IN3,LOW);digitalWrite(IN4,LOW);analogWrite(ENA,0);analogWrite(ENB,0);}
void motorOne(int en,int a,int b,int value){value=constrain(value,-255,255);if(value>0){digitalWrite(a,HIGH);digitalWrite(b,LOW);analogWrite(en,value);}else if(value<0){digitalWrite(a,LOW);digitalWrite(b,HIGH);analogWrite(en,-value);}else{digitalWrite(a,LOW);digitalWrite(b,LOW);analogWrite(en,0);}}
void drive(int a,int b){motorOne(ENA,IN1,IN2,a);motorOne(ENB,IN3,IN4,b);}
void applyAccessories(){if(rigUpOn&&rigDownOn)rigUpOn=rigDownOn=false;digitalWrite(BRUSH_PIN,brushOn);digitalWrite(LED_PIN,ledOn);digitalWrite(SPRAY_PIN,sprayOn);digitalWrite(RIG_UP_PIN,rigUpOn);digitalWrite(RIG_DOWN_PIN,rigDownOn);}
void applyManual(){int s=speedNow;if(commandNow=="forward")drive(s,s);else if(commandNow=="reverse")drive(-s,-s);else if(commandNow=="left")drive(s,-s);else if(commandNow=="right")drive(-s,s);else stopMotors();}
float readDistance(){if(!USE_ULTRASONIC_INTERLOCK)return -1;digitalWrite(TRIG_PIN,LOW);delayMicroseconds(3);digitalWrite(TRIG_PIN,HIGH);delayMicroseconds(10);digitalWrite(TRIG_PIN,LOW);unsigned long d=pulseIn(ECHO_PIN,HIGH,22000UL);return d?d*0.0343f/2.0f:-1;}
void readLines(){for(int i=0;i<4;i++)lineActive[i]=digitalRead(LINE_PINS[i])==(lineColor=="black"?LOW:HIGH);}
void runAuto(){readLines();distanceCm=readDistance();obstacleDetected=distanceCm>0&&distanceCm<OBSTACLE_STOP_CM;if(obstacleDetected){stopMotors();return;}int w[4]={-3,-1,1,3},count=0,sum=0;for(int i=0;i<4;i++)if(lineActive[i]){count++;sum+=w[i];}if(!count){stopMotors();return;}int correction=(int)(LINE_KP*((float)sum/count));drive(constrain(speedNow+correction,0,255),constrain(speedNow-correction,0,255));}
String macSuffix(){uint64_t mac=ESP.getEfuseMac();char b[7];snprintf(b,sizeof(b),"%06X",(uint32_t)(mac&0xFFFFFF));return String(b);}
String setupPassword(){return "SWneo-"+macSuffix();}
String htmlPage(const String &message=""){
 String h=R"HTML(<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta charset="utf-8"><title>StreetWatch Neo Setup</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e8eef9;font:16px system-ui;padding:20px}.wrap{max-width:480px;margin:20px auto;background:#151f32;border:1px solid #2a3a55;border-radius:18px;padding:22px;box-shadow:0 15px 45px #0006}h1{margin:0 0 6px;font-size:25px}p{color:#aab8ce;line-height:1.5}.tag{color:#62d6c5;font-size:12px;font-weight:700;letter-spacing:1px}label{display:block;margin:15px 0 6px;font-size:13px;color:#cbd7e8}input{width:100%;padding:13px;border:1px solid #3b4d69;border-radius:9px;background:#0c1627;color:#fff;font-size:16px}button{width:100%;margin-top:20px;padding:14px;border:0;border-radius:10px;background:#39c6b4;color:#06211e;font-weight:800;font-size:16px}.msg{padding:10px;background:#173c3a;border-radius:8px;color:#a9fff0;margin:12px 0}.small{font-size:12px}</style></head><body><main class="wrap"><div class="tag">STREETWATCH NEO · DEVICE SETUP</div><h1>Connect your ESP32</h1><p>Enter the Wi-Fi network and your registered StreetWatch device details. The token is stored in ESP32 Preferences/NVS flash storage (not shown again).</p>)HTML";
 if(message.length())h+="<div class='msg'>"+message+"</div>";
 h+=R"HTML(<form method="POST" action="/save"><label>Wi-Fi name (SSID)</label><input name="ssid" maxlength="32" required autocomplete="off"><label>Wi-Fi password</label><input name="password" type="password" maxlength="64" autocomplete="new-password"><label>StreetWatch HTTPS server URL</label><input name="server" type="url" placeholder="https://your-app.onrender.com" required><label>Device ID</label><input name="device" maxlength="80" required><label>Device token</label><input name="token" type="password" maxlength="128" required autocomplete="off"><button type="submit">SAVE & CONNECT</button></form><p class="small">After saving, the device reboots and joins your Wi-Fi. To reopen setup, hold the physical SETUP button (GPIO4 to GND) for 4 seconds.</p></main></body></html>)HTML";
 return h;
}
void enterPortal(){
 stopMotors();allAccessoriesOff();serverStop=true;portalMode=true;WiFi.disconnect(true);WiFi.mode(WIFI_AP);
 String pass=setupPassword();WiFi.softAP(SETUP_SSID,pass.c_str());
 dns.start(53,"*",WiFi.softAPIP());
 portal.on("/",HTTP_GET,[]{portal.send(200,"text/html",htmlPage());});
 portal.on("/save",HTTP_POST,[]{
   String ssid=portal.arg("ssid"),pw=portal.arg("password"),url=portal.arg("server"),id=portal.arg("device"),token=portal.arg("token");
   url.trim();while(url.endsWith("/"))url.remove(url.length()-1);
   if(!ssid.length()||ssid.length()>32||!id.length()||id.length()>80||!token.length()||token.length()>128||!url.startsWith("https://")){
     portal.send(400,"text/html",htmlPage("Invalid input. Use a Wi-Fi SSID, device ID/token and an HTTPS server URL."));return;
   }
   prefs.begin("streetwatch",false);
   String oldDevice=prefs.getString("device",""),oldToken=prefs.getString("token","");
   if(oldDevice!=id||oldToken!=token)prefs.putULong("cmdseq",0);
   prefs.putString("ssid",ssid);prefs.putString("pass",pw);prefs.putString("server",url);prefs.putString("device",id);prefs.putString("token",token);prefs.end();
   portal.send(200,"text/html","<!doctype html><meta name='viewport' content='width=device-width'><body style='font:18px system-ui;background:#101827;color:white;padding:30px'><h2>Saved successfully</h2><p>Your ESP32 is restarting and will connect to the configured Wi-Fi.</p></body>");
   delay(1200);ESP.restart();
 });
 portal.onNotFound([]{portal.sendHeader("Location","/");portal.send(302,"text/plain","");});
 portal.begin();
 Serial.printf("Setup AP: %s | AP IP: 192.168.4.1 | MAC suffix: %s\n",SETUP_SSID,macSuffix().c_str());
}
bool loadSettings(){prefs.begin("streetwatch",true);wifiSsid=prefs.getString("ssid","");wifiPassword=prefs.getString("pass","");serverUrl=prefs.getString("server","");deviceId=prefs.getString("device","");deviceToken=prefs.getString("token","");lastCommandId=prefs.getULong("cmdseq",0);prefs.end();return wifiSsid.length()&&deviceId.length()&&deviceToken.length()&&serverUrl.startsWith("https://");}
void setupButtonCheck(){if(digitalRead(SETUP_BUTTON_PIN)==LOW){unsigned long t=millis();while(digitalRead(SETUP_BUTTON_PIN)==LOW&&millis()-t<4500)delay(20);if(millis()-t>=4000)enterPortal();}}
bool beginApi(HTTPClient &http,const String &path){tls.setCACert(ROOT_CA);http.setTimeout(3500);return http.begin(tls,serverUrl+path);}
void auth(HTTPClient &h){h.addHeader("X-Device-Token",deviceToken);}
bool pollCommand(){
 if(WiFi.status()!=WL_CONNECTED){serverStop=true;stopMotors();allAccessoriesOff();return false;}
 HTTPClient h;
 if(!beginApi(h,"/api/device/command")){serverStop=true;stopMotors();allAccessoriesOff();return false;}
 auth(h);
 int code=h.GET();
 bool success=false;
 if(code==200){
   StaticJsonDocument<768>d;
   if(deserializeJson(d,h.getString())==DeserializationError::Ok){
     success=true;
     uint32_t incomingId=d["command_id"]|0;
     bool freshCommand=!requireFreshCommand||incomingId>lastCommandId;
     bool forced=(d["stop"]|true)||!freshCommand;
     String m=d["mode"]|"manual",c=d["command"]|"stop",col=d["line_color"]|"white";
     int sp=d["speed"]|0;
     JsonObject a=d["accessories"].as<JsonObject>();
     brushOn=a["brush"]|false;ledOn=a["led"]|false;sprayOn=a["spray"]|false;
     rigUpOn=a["rig_up"]|false;rigDownOn=a["rig_down"]|false;
     if(freshCommand&&incomingId>lastCommandId){
       lastCommandId=incomingId;requireFreshCommand=false;
       prefs.begin("streetwatch",false);prefs.putULong("cmdseq",lastCommandId);prefs.end();
     }
     if(forced){commandNow="stop";serverStop=true;allAccessoriesOff();}
     else{
       modeNow=m;commandNow=c;lineColor=col;speedNow=constrain(sp,0,255);
       serverStop=false;applyAccessories();lastGoodCommand=millis();
     }
   }else{serverStop=true;commandNow="stop";stopMotors();allAccessoriesOff();}
 }else{serverStop=true;commandNow="stop";stopMotors();allAccessoriesOff();}
 h.end();
 return success;
}
int batteryPercent(){if(!USE_BATTERY_SENSOR)return -1;float v=analogRead(BATTERY_PIN)/4095.0f*3.3f*BATTERY_DIVIDER_RATIO;return constrain((int)roundf((v-BATTERY_EMPTY_V)*100/(BATTERY_FULL_V-BATTERY_EMPTY_V)),0,100);}
void telemetry(){
 if(WiFi.status()!=WL_CONNECTED)return;readLines();HTTPClient h;if(!beginApi(h,"/api/device/telemetry"))return;h.addHeader("Content-Type","application/json");auth(h);
 StaticJsonDocument<512>d;d["device_id"]=deviceId;d["firmware"]="3.0.0-ap-setup";d["rssi"]=WiFi.RSSI();d["line_color"]=lineColor;d["obstacle"]=obstacleDetected;JsonArray a=d.createNestedArray("line_sensors");for(int i=0;i<4;i++)a.add(lineActive[i]);if(distanceCm>=0)d["distance_cm"]=distanceCm;int b=batteryPercent();if(b>=0)d["battery"]=b;String body;serializeJson(d,body);h.POST(body);h.end();
}
void setup(){
 Serial.begin(115200);pinMode(SETUP_BUTTON_PIN,INPUT_PULLUP);
 pinMode(ENA,OUTPUT);pinMode(IN1,OUTPUT);pinMode(IN2,OUTPUT);pinMode(ENB,OUTPUT);pinMode(IN3,OUTPUT);pinMode(IN4,OUTPUT);pinMode(TRIG_PIN,OUTPUT);pinMode(ECHO_PIN,INPUT);
 for(int i=0;i<4;i++)pinMode(LINE_PINS[i],INPUT);pinMode(BRUSH_PIN,OUTPUT);pinMode(LED_PIN,OUTPUT);pinMode(SPRAY_PIN,OUTPUT);pinMode(RIG_UP_PIN,OUTPUT);pinMode(RIG_DOWN_PIN,OUTPUT);if(USE_BATTERY_SENSOR)pinMode(BATTERY_PIN,INPUT);
 stopMotors();allAccessoriesOff();WiFi.setSleep(false);setupButtonCheck();
 if(!loadSettings()){enterPortal();return;}
 WiFi.mode(WIFI_STA);WiFi.begin(wifiSsid.c_str(),wifiPassword.c_str());lastWifiAttempt=millis();wifiLostAt=millis();
}
void loop(){
 if(portalMode){dns.processNextRequest();portal.handleClient();delay(2);return;}
 setupButtonCheck();
 unsigned long now=millis();
 if(WiFi.status()!=WL_CONNECTED){
   stationReady=false;requireFreshCommand=true;
   stopMotors();allAccessoriesOff();serverStop=true;
   if(!wifiLostAt)wifiLostAt=now;
   if(now-lastWifiAttempt>10000){lastWifiAttempt=now;WiFi.disconnect();WiFi.begin(wifiSsid.c_str(),wifiPassword.c_str());}
   if(now-wifiLostAt>WIFI_RECOVERY_MS)enterPortal();
   delay(10);return;
 }
 wifiLostAt=0;
 if(!stationReady){stationReady=true;lastTelemetry=now-TELEMETRY_INTERVAL_MS;nextCommandPoll=now;serverBackoffMs=COMMAND_INTERVAL_MS;}
 if(!timeSynced){
   configTime(0,0,"pool.ntp.org","time.nist.gov");
   if(time(nullptr)>1700000000)timeSynced=true;
   else{stopMotors();allAccessoriesOff();delay(100);return;}
 }
 if(now>=nextCommandPoll){
   bool ok=pollCommand();
   if(ok)serverBackoffMs=COMMAND_INTERVAL_MS;
   else serverBackoffMs=min(serverBackoffMs*2UL,30000UL);
   nextCommandPoll=millis()+serverBackoffMs;
 }
 if(serverStop||now-lastGoodCommand>COMMAND_STALE_MS){serverStop=true;stopMotors();allAccessoriesOff();}
 else if(modeNow=="auto")runAuto();else applyManual();
 if(now-lastTelemetry>=TELEMETRY_INTERVAL_MS){lastTelemetry=now;distanceCm=readDistance();obstacleDetected=distanceCm>0&&distanceCm<OBSTACLE_STOP_CM;telemetry();}
 delay(8);
}

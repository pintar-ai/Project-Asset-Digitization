// LoRa 9x_TX
// -*- mode: C++ -*-
// Example sketch showing how to create a simple messaging client (transmitter)
// with the RH_RF95 class. RH_RF95 class does not provide for addressing or
// reliability, so you should only use RH_RF95 if you do not need the higher
// level messaging abilities.
// It is designed to work with the other example LoRa9x_RX
 
#include <SPI.h>
#include <RH_RF95.h>

#include <HP20x_dev.h>
#include "Arduino.h"
#include "Wire.h" 
#include <KalmanFilter.h>

#include <TinyGPS++.h>
TinyGPSPlus gps;
#include <Time.h>

////////////////////////////////////////////////////////////////////////////////////////// GROVE SECTION START HERE ////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

unsigned char ret = 0;

/* Instance */
KalmanFilter t_filter;    //temperature filter
KalmanFilter p_filter;    //pressure filter
KalmanFilter a_filter;    //altitude filter
 
////////////////////////////////////////////////////////////////////////////////////////// LORA SECTION START HERE ////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#define RFM95_CS 10
#define RFM95_RST 7
#define RFM95_INT 2
#define node_id "B"
 
// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 915.0
 
// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

//////////////////////////////////////////////////////////////////////////////////////// REACH M+ SECTION START HERE //////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
String latitude = "";
String longitude = "";
String gmt = "";
int seconds;
//////////////////////////////////////////////////////////////////////////////////////////// SETUP START HERE /////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void setup() {

  /* Reset HP20x_dev */
  HP20x.begin();
  delay(100);
  
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
 
  
  Serial.begin(9600);
  delay(100);
  //while (!Serial&& (millis() < 30000));
 
  Serial.println("Arduino LoRa Client initializing...");
 
  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);
 
  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    while (1);
  }
  Serial.println("LoRa radio init OK!");
 
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);
  
  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
 
  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then 
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);
  Serial1.begin(9600);
  seconds=second(); 
}

/////////////////////////////////////////////////////////////////////////////////////////// MAIN LOOP START HERE //////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void loop() {
  //Serial.println("Sending to rf95_server");
  // Send a message to rf95_server
  while (Serial1.available()){
    if (gps.encode(Serial1.read())){
      if (((second()-seconds)>=1)|| (seconds==59)){
        String radiopacket = fetch_llh();
        radiopacket += fetch_grove();
        if (send_data(radiopacket)){
          Serial.println(radiopacket);
          Serial.println("Sending success "+String(seconds));
        }else{
          Serial.println("Sending failed");
        }
        seconds=second();
      }
    }
  }
}

bool send_data(String radiopacket){
  //Serial.print("Sending "); 
  //Serial.println(radiopacket); delay(10);
  rf95.send((uint8_t*)(radiopacket.c_str()), radiopacket.length()+1);
 
  //Serial.println("Waiting for packet to complete..."); delay(10);
  rf95.waitPacketSent();
  // Now wait for a reply
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
 
  //Serial.println("Waiting for reply..."); 
  //delay(10);
  if (rf95.waitAvailableTimeout(1000))
  { 
    // Should be a reply message for us now   
    if (rf95.recv(buf, &len))
   {
      Serial.print("Got reply: ");
      Serial.println((char*)buf);
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);
      return true;    
    }
    else
    {
      //Serial.println("Receive failed");
      return false;
    }
  }
  else
  {
    //Serial.println("No reply, is there a listener around?");
    return false;
  }
  //delay(1000);
}

String fetch_grove(){
  String data = "sensors:";
  long Temper = HP20x.ReadTemperature();
  float t = Temper/100.0;
  data += String(t_filter.Filter(t));
  data += ",";
  long Pressure = HP20x.ReadPressure();
  t = Pressure/100.0;
  data += String(p_filter.Filter(t));
  data += ",";
  long Altitude = HP20x.ReadAltitude();
  t = Altitude/100.0;
  data += String(a_filter.Filter(t));
  return data;
}

String fetch_llh(){
  String bodystring = "";
  char buff[12];
  
  if (gps.location.isValid() && gps.time.isValid())
  {
    Serial.print(gps.location.rawLat().negative);
    latitude = String(gps.location.rawLat().negative ? "-" : "")+String(gps.location.rawLat().deg)+"."+String(gps.location.rawLat().billionths);
    longitude = String(gps.location.rawLng().negative ? "-" : "")+String(gps.location.rawLng().deg)+"."+String(gps.location.rawLng().billionths);
    gmt = "";
    if (gps.time.hour() < 10) ;
    gmt += gps.time.hour();
    gmt += ":";
    if (gps.time.minute() < 10) gmt += "0";
    gmt += gps.time.minute();
    gmt += ":";
    if (gps.time.second() < 10) gmt += "0";
    gmt += gps.time.second();
  }
  bodystring = "llh:"+gmt+","+latitude+","+longitude+"\n";
  Serial.println(bodystring);
  return bodystring;
}

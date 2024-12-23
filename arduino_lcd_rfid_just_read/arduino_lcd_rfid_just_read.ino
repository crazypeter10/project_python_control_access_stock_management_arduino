#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>

#define RST_PIN 9
#define SS_PIN 10

MFRC522 mfrc522(SS_PIN, RST_PIN);
// Adjust the I2C address (0x27) to match your LCD if needed:
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  lcd.setCursor(0, 1);
  lcd.print("Scan your card");
  delay(500);
}

void loop() {
  // If no new card present, do nothing
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Clear LCD, prepare to show UID
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("UID: ");

  // Build UID string (e.g. "63:19:CE:12"). 
  // Some RFID cards might have more than 4 bytes; 'mfrc522.uid.size' tells you how many.
  String uidString = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    // Convert each byte to hex
    if (mfrc522.uid.uidByte[i] < 0x10) {
      // add a leading zero for formatting, e.g. 0A
      uidString += "0";
    }
    uidString += String(mfrc522.uid.uidByte[i], HEX);
    if (i < mfrc522.uid.size - 1) {
      uidString += ":";
    }
  }
  uidString.toUpperCase(); // Make it uppercase

  lcd.print(uidString);

  // Send UID to Python via Serial
  Serial.print("Scanned UID: ");
  Serial.println(uidString);

  // Wait up to 2 seconds for Python's response
  String response = "";
  unsigned long startTime = millis();
  while (millis() - startTime < 2000) {
    if (Serial.available() > 0) {
      response = Serial.readStringUntil('\n');
      response.trim();
      break;
    }
  }

  // Default to DENIED if no response or unexpected response
  lcd.setCursor(0, 1);
  if (response == "GRANTED") {
    lcd.print("Access Granted");
  } else {
    lcd.print("Access Denied");
  }

  // Let user see the LCD message for 2 seconds
  delay(2000);

  // Reset LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  lcd.setCursor(0, 1);
  lcd.print("Scan your card");

  // Halt PICC
  mfrc522.PICC_HaltA();
}

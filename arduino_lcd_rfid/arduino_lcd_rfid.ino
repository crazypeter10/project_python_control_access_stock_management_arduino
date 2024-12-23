#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>

#define RST_PIN 9
#define SS_PIN 10

// Master card UID
byte masterCard[4] = {99, 25, 206, 18}; // Replace with your master card UID
byte readCard[4];

// Create MFRC522 instance
MFRC522 mfrc522(SS_PIN, RST_PIN);
// Initialize LCD
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600); // Initialize serial communication
  SPI.begin();        // Initialize SPI bus
  mfrc522.PCD_Init(); // Initialize RFID reader

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  lcd.setCursor(0, 1);
  lcd.print("Scan your card");
  Serial.println("System Ready");
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Read the card UID
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("UID: ");
  Serial.print("Scanned UID: ");
  for (byte i = 0; i < 4; i++) {
    readCard[i] = mfrc522.uid.uidByte[i];
    Serial.print(readCard[i], HEX);
    lcd.print(readCard[i], HEX);
    if (i < 3) {
      Serial.print(":");
      lcd.print(":");
    }
  }
  Serial.println(); // Newline for clarity

  // Check access
  if (memcmp(readCard, masterCard, 4) == 0) {
    Serial.println("Access Granted: Master Card");
    lcd.setCursor(0, 1);
    lcd.print("Access Granted");
  } else {
    Serial.println("Access Denied");
    lcd.setCursor(0, 1);
    lcd.print("Access Denied");
  }

  delay(2000); // Allow the message to be read
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  lcd.setCursor(0, 1);
  lcd.print("Scan your card");

  mfrc522.PICC_HaltA();
}

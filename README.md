RFID + Stock Management System
This project demonstrates a simple IoT-based stock management system using RFID (via an Arduino) for user authentication. The backend is a Python application that manages a SQLite database to store users, stock items, and logs (both access logs and stock change logs). The GUI is built with Tkinter.

When an RFID card is scanned on the Arduino, the UID is sent over Serial to the Python app, which checks the UID in a users table. If valid, the Arduino displays “Access Granted” on its LCD; otherwise, “Access Denied.”

Table of Contents
Features
Architecture
Requirements
Getting Started
1. Arduino Setup
2. Python Setup
How to Run
Usage Flow
Database Schema
Screenshots (Optional)
License (Optional)
Credits
Features
RFID-Based Login

Arduino reads an RFID card’s UID.
Sends Scanned UID: <UID> to Python over Serial.
Python verifies the UID in the users table.
Access Control & Logging

Python logs Granted or Denied in the access_logs table.
Arduino displays “Access Granted/Denied” on the LCD.
Local SQLite Database

User Management (only by Admins): add, delete users.
Stock Management: add new items, update item quantities.
Stock Logs: each stock change is timestamped, recording which user made the change.
Tkinter GUI

Login Screen: Waits for RFID scan.
Main Screen: If access is granted, user sees:
Admin Tools: Manage Users, View Stock Logs
Manage Stock: Add items, update quantities
Stock Log Viewer: Admins can view all historical changes.
Architecture
sql
Copy code
         +-------------------+
         |   RFID Cards/Tags |
         +-------------------+
                   |
                   v
    +--------------------------------+  
    |  Arduino + MFRC522 + I2C LCD   |  
    |  (Reads UID, sends to Python)  |  
    +--------------------------------+  
                   |
                   |  (Serial: UID, then GRANTED/DENIED)
                   v
         +-------------------+
         |   Python App     |
         | Tkinter + SQLite |
         +-------------------+
                   |
                   v
         +-------------------+
         |  inventory.db    |
         | (Users, Stock,   |
         |  Logs)           |
         +-------------------+
Requirements
Hardware
Arduino board (e.g., Arduino UNO)
MFRC522 RFID reader & compatible RFID tags
I2C LCD display (e.g., 16x2)
Software
Arduino IDE or PlatformIO for uploading code
Python 3.7+
pyserial (for Python serial comm)
tkinter (often included with Python)
Make sure your Arduino code is set to 9600 baud and your Python code also uses BAUD_RATE = 9600.

Getting Started
1. Arduino Setup
Wire the MFRC522 RFID reader to your Arduino’s SPI pins (RST_PIN, SS_PIN, etc.).
Wire the I2C LCD to SDA/SCL, 5V, and GND.
Upload your Arduino sketch that:
Prints Scanned UID: <UID> to Serial
Waits for Python’s response: GRANTED or DENIED
Displays it on the LCD accordingly
RFID Module
Pin RFID	Pin Arduino Uno
VCC	            3.3V
GND	            GND
SDA	            10
SCK	            13
MOSI	        11
MISO	        12
RST	            9

LCD Module
Pin LCD	Pin Arduino Uno
VCC	        5V
GND	        GND
SDA	        SDA
SCL	        SCL

2. Python Setup
Clone or download this repository to your local machine.
In a terminal, navigate to the project folder (e.g., cd path/to/project).
(Optional) Create a virtual environment:
bash
Copy code
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
Install dependencies:
bash
Copy code
pip install pyserial
# tkinter is usually installed by default with Python, 
# but if not, install via your OS package manager
Edit the code to set SERIAL_PORT to your Arduino’s port (e.g., COM3 or /dev/ttyUSB0).
How to Run
Connect your Arduino to the computer via USB.
Run the Python script:
bash
Copy code
python app.py
You should see a Tkinter window titled "RFID + Stock Management". It shows a Login Screen prompting to "Scan your RFID card."
On the Arduino side, you should see “System Ready” or similar text on the LCD.
Usage Flow
Scan Card

When you place an RFID card near the MFRC522 reader, the Arduino reads its UID and sends Scanned UID: 63:19:CE:12 (example) to Python.
Python Checks DB

If the UID is found in users, Python logs "Granted" in access_logs, sends “GRANTED” back to Arduino, and transitions to the Main Screen in the GUI.
If the UID is not found, Python logs "Denied", sends “DENIED” back, and shows a warning message. Arduino displays “Access Denied.”
Main Screen

Shows a welcome message with the user’s role (Admin or User).
Admin can open Manage Users or View Stock Logs.
All roles (by default) can Manage Stock.
Manage Stock

Add items, update quantities. Each operation is recorded in stock_logs with a timestamp, user name, and the UID of who performed it.
View Stock Logs (Admin Only)

Lists all stock changes in chronological order, including who changed what and how much.
Logout returns to the login screen, Exit closes the application.

Database Schema
users

Column	Type	Description
id	INTEGER	Primary key (auto-increment)
uid	TEXT	RFID UID (unique)
name	TEXT	Human-readable name
role	TEXT	"Admin" or "User"
access_logs

Column	Type	Description
id	INTEGER	Primary key (auto-increment)
uid	TEXT	UID that was scanned
timestamp	DATETIME	Defaults to CURRENT_TIMESTAMP
status	TEXT	"Granted" or "Denied"
stock

Column	Type	Description
id	INTEGER	Primary key (auto-increment)
name	TEXT	Item name
quantity	INTEGER	Current quantity (default 0)
stock_logs

Column	Type	Description
id	INTEGER	Primary key (auto-increment)
name	TEXT	Item name
change	INTEGER	+X or -X for quantity changes
user_name	TEXT	Name of user who made the change
user_uid	TEXT	UID of user who made the change
timestamp	DATETIME	Defaults to CURRENT_TIMESTAMP
Screenshots (Optional)
(Add screenshots here to show the GUI, the Arduino setup, or any relevant images.)



Credits
Arduino RFID: MFRC522 library by miguelbalboa
LCD I2C: Various libraries like LiquidCrystal_I2C.h
Python:
PySerial
Tkinter (included by default on most Python installations)
SQLite: Built into Python
Created by CrazyPeter for demonstration / educational purposes
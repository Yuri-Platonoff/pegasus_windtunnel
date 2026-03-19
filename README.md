# pegasus_windtunnel
Code of the sensors and stuff for my Cornerstone group's project 2.
# Wind Tunnel Rocket Exhibit

This project is a MicroPython-based interactive wind tunnel exhibit designed for a museum-style engineering activity. Users select a rocket configuration, interact with buttons and a display, and test how far the rocket moves in the wind tunnel.

## Features
- HC-SR04 ultrasonic sensor measures rocket travel distance
- RFID-RC522 identifies rocket or nose cone configurations
- Buttons allow user interaction
- Display shows instructions and results
- Program resets for the next user

## File Structure
- `main.py` starts the program
- `config.py` stores pin assignments
- `ultrasonic.py` reads the HC-SR04 sensor
- `rfid_reader.py` reads RFID tags
- `buttons.py` handles user button input
- `display_manager.py` controls the display
- `game_controller.py` manages the overall logic
- `lib/mfrc522.py` RFID driver
- `lib/ssd1306.py` display driver

## Hardware
- Raspberry Pi Pico / Pico W
- HC-SR04 ultrasonic sensor
- RFID-RC522 reader
- RFID tags/cards
- Display screen
- Push buttons

## Notes
The HC-SR04 Echo pin should be stepped down to 3.3V before going into the Pico GPIO.

## Authors
Yuri Platonoff

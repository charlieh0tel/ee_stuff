# Builds and flashes the PDP-11/03 front panel emulator with arduino-cli.
#
#   make deps              installs the AVR core and MsTimer2 (once)
#   make                   compiles the sketch
#   make upload            flashes it; set PORT if the board isn't on the default
#   make monitor           shows the sketch's serial output

SKETCH := pdp11_03_panel_emulator
FQBN := arduino:avr:uno
CORE := arduino:avr
LIBRARIES := MsTimer2
# Must match Serial.begin() in the sketch.
BAUD := 115200
BUILD_DIR := build
HEX := $(BUILD_DIR)/$(SKETCH).ino.hex

ARDUINO_CLI ?= arduino-cli
PORT ?= /dev/ttyACM0

.PHONY: all deps upload monitor clean

all: $(HEX)

$(HEX): $(SKETCH).ino
	$(ARDUINO_CLI) compile --fqbn $(FQBN) --build-path $(BUILD_DIR) \
		--warnings all .

deps:
	$(ARDUINO_CLI) core update-index
	$(ARDUINO_CLI) core install $(CORE)
	$(ARDUINO_CLI) lib install $(LIBRARIES)

upload: $(HEX)
	$(ARDUINO_CLI) upload --fqbn $(FQBN) --port $(PORT) --input-dir $(BUILD_DIR) .

monitor:
	$(ARDUINO_CLI) monitor --port $(PORT) --config baudrate=$(BAUD)

clean:
	rm -rf $(BUILD_DIR)

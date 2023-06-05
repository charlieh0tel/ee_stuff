// PDP 11/03 QBus Front Panel Emulator
//
// Christopher Hoover <ch@murgatroid.com>

#if defined(ARDUINO_AVR_UNO)

// Pins connected to H9720 backplane connector.
//
//  2/ BEVNT_L   4/ (KEY)  6/ CL3_L   8/ CS3_L   10/ BDCOK_H
//  1/ BPOK_H    3/ SRUN   5/ GND     7/ X        9/ BHALT_L
//
#define SRUN_L 2
#define BPOK_H 3
#define BHALT_L 4
#define BEVNT_L 6
#define BDCOK_H 9

// Power on/off.
// Monetary NO Switch, 5V pull up, buton down shorts pin to GROUND.
#define POWER_SW 10
#define POWER_SW_DOWN LOW
#define POWER_SW_UP HIGH

// Run indicator.
// LED with R to GROUND.
#define RUN_LED 11

// Power good indicator.
// LED with R to GROUND.
#define POWER_GOOD_LED 12
#else
#error "No pin definitions for this board."
#endif

bool buttonIs(int8_t pin, int8_t state) {
  auto button = digitalRead(pin);
  if (button != state) return false;
  delay(10 /*ms*/);
  button = digitalRead(pin);
  if (button != state) return false;
  delay(10 /*ms*/);
  button = digitalRead(pin);
  return button == state;
}

bool buttonPressedAndReleased(int8_t pin, int8_t downState) {
  if (!buttonIs(pin, downState)) {
    return false;
  }
  while (buttonIs(pin, downState))
    ;
  return true;
}

void delay_seconds(uint8_t s) {
  while (s--) {
    delay(1000 /*us*/);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(SRUN_L, INPUT);
  pinMode(BPOK_H, OUTPUT);
  pinMode(BHALT_L, OUTPUT);
  pinMode(BDCOK_H, OUTPUT);
  pinMode(BEVNT_L, OUTPUT);
  pinMode(POWER_GOOD_LED, OUTPUT);
  pinMode(RUN_LED, OUTPUT);
  pinMode(POWER_SW, INPUT);
}

void loop() {
  while (true) {
    digitalWrite(BPOK_H, LOW);
    digitalWrite(BDCOK_H, LOW);
    digitalWrite(BHALT_L, HIGH);
    digitalWrite(BEVNT_L, LOW);
    digitalWrite(POWER_GOOD_LED, LOW);
    digitalWrite(RUN_LED, LOW);

    Serial.println("\n\n\nPDP 11/03 QBUS Front Panel Emulator");
    Serial.println("Christopher Hoover <ch@murgatroid.com>");
    Serial.println();
    Serial.println("CPU is off.");

    Serial.print("Waiting for power switch ... ");
    Serial.flush();
    while (!buttonPressedAndReleased(POWER_SW, POWER_SW_DOWN))
      ;
    Serial.println("pressed.");

    delay_seconds(1);

    Serial.print("Power up sequence starting ... ");
    Serial.flush();
    //RemotePowerOn();
    delay(3 /*ms*/);
    digitalWrite(BDCOK_H, HIGH);
    delay(70 /*ms*/);
    digitalWrite(BPOK_H, HIGH);
    digitalWrite(POWER_GOOD_LED, HIGH);
    Serial.println("finished.");

    delay_seconds(1);

    Serial.println("CPU is on.");
    Serial.println("Press H to halt.  Press power switch to power off.");
    bool halted = false;
    int8_t last_srun_l = -1;
    while (1) {
      auto srun_l = digitalRead(SRUN_L);
      digitalWrite(RUN_LED, !srun_l);
      if (last_srun_l != srun_l) {
        last_srun_l = srun_l;
        if (srun_l == HIGH) {
          Serial.println("SRUN_L went high (stopped).");
        } else {
          Serial.println("SRUN_L went low (running).");
        }
      }

      if (buttonPressedAndReleased(POWER_SW, POWER_SW_DOWN)) {
        break;
      }

      if (Serial.available() > 0) {
        auto ch = Serial.read();
        if ((ch == 'h') || ch == 'H') {
          if (halted) {
            Serial.println("Resuming; press H to halt.");
            digitalWrite(BHALT_L, HIGH);
            halted = false;
          } else {
            digitalWrite(BHALT_L, LOW);
            Serial.println("Processor halted; press H to resume.");
            halted = true;
          }
        }
      }
    }

    Serial.print("Power down sequence starting ... ");
    Serial.flush();
    digitalWrite(BPOK_H, LOW);
    delay(4 /*ms*/);
    digitalWrite(BDCOK_H, LOW);
    delay(5 /*ms*/);
    //remotePowerOff();
    Serial.println("done.");

    Serial.println("CPU is off.");

    delay_seconds(2);
  }
}
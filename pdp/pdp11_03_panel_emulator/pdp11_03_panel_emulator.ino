#include <MsTimer2.h>

// PDP 11/03 QBus Front Panel Emulator
//
// Christopher Hoover <ch@murgatroid.com>

#if defined(ARDUINO_AVR_UNO)

// Pins connected to H9720 backplane connector.
//
//  2/ BEVNT_L   4/ (KEY)  6/ CL3_L   8/ CS3_L   10/ BDCOK_H
//  1/ BPOK_H    3/ SRUN   5/ GND     7/ X        9/ BHALT_L
//b
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

// Halt toggle.
// Monetary NO Switch, 5V pull up, buton down shorts pin to GROUND.
#define HALT_SW 8
#define HALT_SW_DOWN LOW
#define HALT_SW_UP HIGH

// Run indicator.
// LED with R to GROUND.
#define RUN_LED 11

// Power good indicator.
// LED with R to GROUND.
#define POWER_GOOD_LED 12

#else
#error "No pin definitions for this board."
#endif

// Line clock.
constexpr bool supply_line_clock = true;
constexpr int line_clock_freq_hz = 50;   // 60 Hz doesn't really work.
constexpr int line_clock_half_period_ms = (int) (1000. * 1.0 / (double) (2 * line_clock_freq_hz));

// Power on first time automagically.
const bool initial_power_on = true;

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

void toggle_bevent() {
  static bool value = true;
  digitalWrite(BEVNT_L, value);
  value = !value;
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n\nPDP 11/03 QBUS Front Panel Emulator");
  Serial.println("Christopher Hoover <ch@murgatroid.com>");
  Serial.println();

  pinMode(SRUN_L, INPUT);
  pinMode(BPOK_H, OUTPUT);
  pinMode(BHALT_L, OUTPUT);
  pinMode(BDCOK_H, OUTPUT);
  pinMode(BEVNT_L, OUTPUT);
  pinMode(POWER_GOOD_LED, OUTPUT);
  pinMode(RUN_LED, OUTPUT);
  pinMode(POWER_SW, INPUT);

  if (supply_line_clock) {
    Serial.print("Starting LTC at "); Serial.print(line_clock_freq_hz); Serial.print(" Hz ");
    Serial.print("(half_period="); Serial.print(line_clock_half_period_ms); Serial.println(" ms).");
    MsTimer2::set(line_clock_half_period_ms, toggle_bevent);
    MsTimer2::start();
  } 
}

void loop() {
  bool first = true;

  while (true) {
    digitalWrite(BPOK_H, LOW);
    digitalWrite(BDCOK_H, LOW);
    digitalWrite(BHALT_L, HIGH);
    digitalWrite(POWER_GOOD_LED, LOW);
    digitalWrite(RUN_LED, LOW);

    Serial.println("CPU is off.");

    if (!first || !initial_power_on) {
      Serial.print("Waiting for power switch ... ");
      Serial.flush();
      while (!buttonPressedAndReleased(POWER_SW, POWER_SW_DOWN))
        ;
      Serial.println("pressed.");
    }
    first = false;

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
    Serial.println("Press power switch to power off.  Press halt switch to toggle halt state.");

    int8_t last_srun_l = -1;
    bool halted = false;
    while (1) {
      auto srun_l = digitalRead(SRUN_L);
      digitalWrite(RUN_LED, !srun_l);
#ifdef DEBUG
      if (last_srun_l != srun_l) {
        last_srun_l = srun_l;
        if (srun_l == HIGH) {
          Serial.println("SRUN_L went high (stopped).");
        } else {
          Serial.println("SRUN_L went low (running).");
        }
      }
#endif

      if (buttonPressedAndReleased(POWER_SW, POWER_SW_DOWN)) {
        break;
      }

      if (buttonPressedAndReleased(HALT_SW, HALT_SW_DOWN)) {
        if (halted) {
          digitalWrite(BHALT_L, HIGH);
          Serial.println("Releasing HALT_L.");
          halted = false;
        } else {
          digitalWrite(BHALT_L, LOW);
          Serial.println("HALT_L asserted");
          halted = true;
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
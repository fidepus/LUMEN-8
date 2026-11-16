
#include "input.h"
#include "protocol.h"

namespace {

constexpr uint8_t ENCODER_A_PIN = 4;
constexpr uint8_t ENCODER_B_PIN = 5;
constexpr uint8_t ENCODER_BUTTON_PIN = 6;

constexpr uint8_t BUTTON_PINS[8] = {
    7, 8, 9, 10, 14, 15, 16, A0
};

constexpr unsigned long DEBOUNCE_MS = 25;
constexpr int8_t ENCODER_STEPS_PER_DETENT = 4;

struct ButtonState {
    bool lastReading;
    bool stableState;
    unsigned long lastChange;
};

ButtonState buttons[9];

uint8_t selectedParameter = 0;
uint8_t encoderPreviousState = 0;
int8_t encoderAccumulator = 0;

const int8_t ENCODER_TRANSITIONS[16] = {
     0, -1,  1,  0,
     1,  0,  0, -1,
    -1,  0,  0,  1,
     0,  1, -1,  0
};


void initializeButtons() {

    for (uint8_t i = 0; i < 8; i++) {
        pinMode(BUTTON_PINS[i], INPUT_PULLUP);

        bool reading = digitalRead(BUTTON_PINS[i]);

        buttons[i] = {
            reading,
            reading,
            0
        };
    }

    pinMode(ENCODER_BUTTON_PIN, INPUT_PULLUP);

    bool reading = digitalRead(ENCODER_BUTTON_PIN);

    buttons[8] = {
        reading,
        reading,
        0
    };
}


void processButtons() {

    unsigned long now = millis();

    for (uint8_t i = 0; i < 9; i++) {

        uint8_t pin = (i < 8)
            ? BUTTON_PINS[i]
            : ENCODER_BUTTON_PIN;

        bool reading = digitalRead(pin);

        if (reading != buttons[i].lastReading) {
            buttons[i].lastReading = reading;
            buttons[i].lastChange = now;
        }

        if (
            now - buttons[i].lastChange >= DEBOUNCE_MS &&
            reading != buttons[i].stableState
        ) {

            buttons[i].stableState = reading;

            if (buttons[i].stableState == LOW) {

                if (i < 8) {

                    if (!protocolIsParameterEnabled(i)) {
                        continue;
                    }

                    selectedParameter = i;
                    protocolSendSelect(i);

                } else {
                    protocolSendPress();
                }
            }
        }
    }
}


void processEncoder() {

    uint8_t currentState = 0;

    if (digitalRead(ENCODER_A_PIN)) {
        currentState |= 0x02;
    }

    if (digitalRead(ENCODER_B_PIN)) {
        currentState |= 0x01;
    }

    uint8_t transitionIndex =
        (encoderPreviousState << 2) | currentState;

    int8_t movement = ENCODER_TRANSITIONS[transitionIndex];

    encoderAccumulator += movement;
    encoderPreviousState = currentState;

    if (encoderAccumulator >= ENCODER_STEPS_PER_DETENT) {
        protocolSendDelta(1);
        encoderAccumulator = 0;
    }

    if (encoderAccumulator <= -ENCODER_STEPS_PER_DETENT) {
        protocolSendDelta(-1);
        encoderAccumulator = 0;
    }
}

} // namespace


void inputBegin() {

    pinMode(ENCODER_A_PIN, INPUT_PULLUP);
    pinMode(ENCODER_B_PIN, INPUT_PULLUP);

    initializeButtons();

    selectedParameter = protocolGetDefaultParameter();
    if (!protocolIsParameterEnabled(selectedParameter)) {
        for (uint8_t i = 0; i < 8; i++) {
            if (protocolIsParameterEnabled(i)) {
                selectedParameter = i;
                break;
            }
        }
    }

    encoderPreviousState = 0;

    if (digitalRead(ENCODER_A_PIN)) {
        encoderPreviousState |= 0x02;
    }

    if (digitalRead(ENCODER_B_PIN)) {
        encoderPreviousState |= 0x01;
    }
}


void inputUpdate() {
    processButtons();
    processEncoder();
}


uint8_t inputGetSelectedParameter() {
    return selectedParameter;
}

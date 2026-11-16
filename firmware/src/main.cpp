/*
 * ============================================================
 * LUMEN-8
 * Lightroom Utility for Manual Editing: 8 Controls
 *
 * Firmware Version: 0.6.0
 * Board: Arduino Pro Micro ATmega32U4, 5V / 16MHz
 * ============================================================
 */

#include <Arduino.h>

#include "input.h"
#include "display.h"
#include "protocol.h"

uint8_t lastDisplayedParameter = 255;

void setup() {
    protocolBegin();
    inputBegin();
    displayBegin();
}

void loop() {
    protocolUpdate();
    inputUpdate();

    uint8_t selectedParameter = inputGetSelectedParameter();

    if (selectedParameter != lastDisplayedParameter) {
        displayUpdate(selectedParameter);
        lastDisplayedParameter = selectedParameter;
    }
}

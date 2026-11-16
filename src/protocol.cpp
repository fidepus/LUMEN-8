#include "protocol.h"
#include "generated_config.h"

namespace {
constexpr uint8_t PARAMETER_COUNT = LumenConfig::PARAMETER_COUNT;
}

void protocolBegin() {
    Serial.begin(115200);
}

void protocolUpdate() {
    // No configuration handshake is required.
    // The controller sends input events as newline-delimited JSON.
}

void protocolSendSelect(uint8_t index) {
    if (index >= PARAMETER_COUNT || !protocolIsParameterEnabled(index)) return;

    Serial.print(F("{\"event\":\"select\",\"parameter\":\""));
    Serial.print(LumenConfig::PARAMETER_KEYS[index]);
    Serial.println(F("\"}"));
}

void protocolSendDelta(int8_t delta) {
    if (delta != -1 && delta != 1) return;

    Serial.print(F("{\"event\":\"delta\",\"delta\":"));
    Serial.print(delta);
    Serial.println(F("}"));
}

void protocolSendPress() {
    Serial.println(F("{\"event\":\"press\",\"control\":\"encoder\"}"));
}

bool protocolIsParameterEnabled(uint8_t index) {
    if (index >= PARAMETER_COUNT) return false;
    return LumenConfig::PARAMETER_ENABLED[index];
}

const char* protocolGetParameterName(uint8_t index) {
    if (index >= PARAMETER_COUNT) return "";
    return LumenConfig::PARAMETER_NAMES[index];
}

const char* protocolGetParameterLabel(uint8_t index) {
    if (index >= PARAMETER_COUNT) return "";
    return LumenConfig::PARAMETER_LABELS[index];
}

uint8_t protocolGetDefaultParameter() {
    return LumenConfig::DEFAULT_PARAMETER_INDEX;
}

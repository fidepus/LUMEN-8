#include <string.h>

#include "protocol.h"
#include "generated_config.h"

#ifndef LUMEN8_VERSION
#define LUMEN8_VERSION "0.0.0"
#endif

namespace {

constexpr uint8_t PARAMETER_COUNT = LumenConfig::PARAMETER_COUNT;
constexpr uint8_t PROTOCOL_VERSION = 1;
constexpr char IDENTIFY_COMMAND[] = "LUMEN8:IDENTIFY?";
constexpr uint8_t COMMAND_BUFFER_SIZE = 24;

char commandBuffer[COMMAND_BUFFER_SIZE];
uint8_t commandLength = 0;
bool commandOverflow = false;


void processCommand() {
    commandBuffer[commandLength] = '\0';

    if (strcmp(commandBuffer, IDENTIFY_COMMAND) == 0) {
        Serial.print(F("LUMEN8:HELLO:"));
        Serial.print(PROTOCOL_VERSION);
        Serial.print(':');
        Serial.println(F(LUMEN8_VERSION));
    }

    commandLength = 0;
    commandOverflow = false;
}

} // namespace


void protocolBegin() {
    Serial.begin(115200);
}


void protocolUpdate() {
    // The only host-to-device command in protocol v1 is the short identify
    // request. Configuration remains compile-time generated; no JSON parser
    // or runtime configuration transfer is used.
    while (Serial.available() > 0) {
        const char incoming = static_cast<char>(Serial.read());

        if (incoming == '\r') {
            continue;
        }

        if (incoming == '\n') {
            if (!commandOverflow) {
                processCommand();
            } else {
                commandLength = 0;
                commandOverflow = false;
            }
            continue;
        }

        if (commandOverflow) {
            continue;
        }

        if (commandLength < COMMAND_BUFFER_SIZE - 1) {
            commandBuffer[commandLength++] = incoming;
        } else {
            commandOverflow = true;
        }
    }
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

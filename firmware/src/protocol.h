#pragma once

#include <Arduino.h>

void protocolBegin();
void protocolUpdate();

void protocolSendSelect(uint8_t index);
void protocolSendDelta(int8_t delta);
void protocolSendPress();

bool protocolIsParameterEnabled(uint8_t index);
const char* protocolGetParameterName(uint8_t index);
const char* protocolGetParameterLabel(uint8_t index);
uint8_t protocolGetDefaultParameter();

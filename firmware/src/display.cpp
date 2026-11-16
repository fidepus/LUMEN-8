
#include "display.h"
#include "protocol.h"
#include <U8g2lib.h>

namespace {

U8G2_SH1106_128X64_NONAME_1_HW_I2C oled(
    U8G2_R0,
    U8X8_PIN_NONE
);


void drawParameterGrid(uint8_t selectedParameter) {

    const uint8_t CELL_WIDTH = 30;
    const uint8_t CELL_HEIGHT = 17;
    const uint8_t COLUMN_SPACING = 32;
    const uint8_t ROW_SPACING = 19;
    const uint8_t GRID_TOP = 13;

    oled.setFont(u8g2_font_7x14_tf);

    for (uint8_t i = 0; i < 8; i++) {

        uint8_t column = i % 4;
        uint8_t row = i / 4;

        uint8_t x = 1 + column * COLUMN_SPACING;
        uint8_t y = GRID_TOP + row * ROW_SPACING;

        if (!protocolIsParameterEnabled(i)) {
            oled.drawFrame(x, y, CELL_WIDTH, CELL_HEIGHT);
            oled.drawHLine(x + 10, y + 8, 10);
            continue;
        }

        if (i == selectedParameter) {
            oled.drawBox(x, y, CELL_WIDTH, CELL_HEIGHT);
            oled.setDrawColor(0);
        } else {
            oled.drawFrame(x, y, CELL_WIDTH, CELL_HEIGHT);
            oled.setDrawColor(1);
        }

        const char* label = protocolGetParameterLabel(i);

        uint8_t textWidth = oled.getStrWidth(label);
        uint8_t textX = x + (CELL_WIDTH - textWidth) / 2;

        oled.drawStr(textX, y + 13, label);
        oled.setDrawColor(1);
    }
}


void drawFooter(uint8_t selectedParameter) {

    oled.drawHLine(0, 51, 128);
    oled.setFont(u8g2_font_5x7_tf);

    oled.drawStr(
        0,
        62,
        protocolGetParameterName(selectedParameter)
    );

    oled.drawStr(96, 62, "READY");
}


} // namespace


void displayBegin() {

    oled.begin();
    oled.setContrast(200);
}


void displayUpdate(uint8_t selectedParameter) {

    if (selectedParameter >= 8) return;

    oled.firstPage();

    do {

        oled.setDrawColor(1);

        oled.setFont(u8g2_font_6x12_tf);
        oled.drawStr(0, 9, "LUMEN-8");
        oled.drawHLine(0, 11, 128);

        drawParameterGrid(selectedParameter);
        drawFooter(selectedParameter);

    } while (oled.nextPage());
}

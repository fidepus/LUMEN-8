
#!/bin/bash

# ============================================================
# LUMEN-8
# Lightroom API Endpoint Test
# ============================================================

API_URL="http://localhost:3000"

echo ""
echo "======================================"
echo "       LUMEN-8 API TEST"
echo "======================================"
echo ""

# Check server availability
if ! curl -s --max-time 3 "$API_URL" > /dev/null; then
    echo "ERROR: Lightroom Controller is not reachable."
    exit 1
fi

# Parameter and test amounts
declare -a PARAMETERS=(
    "Exposure2012:0.05"
    "Contrast2012:1"
    "Highlights2012:1"
    "Shadows2012:1"
    "Whites2012:1"
    "Blacks2012:1"
    "Temperature:50"
    "Saturation:1"
)

SUCCESS=0
FAILED=0

for ENTRY in "${PARAMETERS[@]}"; do

    PARAMETER="${ENTRY%%:*}"
    AMOUNT="${ENTRY##*:}"

    echo -n "Testing $PARAMETER ... "

    RESPONSE=$(curl -s \
        --max-time 5 \
        -w "\n%{http_code}" \
        "$API_URL/$PARAMETER/increment?amount=$AMOUNT")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "OK (HTTP $HTTP_CODE)"
        ((SUCCESS++))
    else
        echo "FAILED (HTTP $HTTP_CODE)"
        echo "  Response: $BODY"
        ((FAILED++))
    fi

    sleep 0.3
done

echo ""
echo "======================================"
echo "RESULTS"
echo "======================================"
echo "Successful: $SUCCESS"
echo "Failed:     $FAILED"
echo "======================================"
echo ""

if [[ "$FAILED" -gt 0 ]]; then
    exit 1
fi

exit 0

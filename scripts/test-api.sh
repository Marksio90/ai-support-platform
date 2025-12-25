#!/bin/bash

# Test API endpoints with curl

API_URL="http://localhost:8000"

echo "🧪 Testing E-commerce Support AI API"
echo "====================================="
echo ""

# 1. Health check
echo "1️⃣  Testing /health endpoint..."
curl -s "${API_URL}/health" | python3 -m json.tool
echo ""
echo ""

# 2. Support query
echo "2️⃣  Testing /support/ask endpoint..."
curl -s -X POST "${API_URL}/support/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Jak mogę zwrócić produkt?",
    "language": "pl"
  }' | python3 -m json.tool
echo ""
echo ""

# 3. Metrics summary
echo "3️⃣  Testing /metrics/summary endpoint..."
curl -s "${API_URL}/metrics/summary" | python3 -m json.tool
echo ""
echo ""

# 4. Multiple queries for stats
echo "4️⃣  Sending multiple queries for statistics..."

queries=(
  "Jakie są koszty dostawy?"
  "Chcę anulować zamówienie"
  "Kiedy otrzymam zwrot pieniędzy?"
  "Gdzie mogę śledzić przesyłkę?"
)

for query in "${queries[@]}"; do
  echo "   Query: $query"
  curl -s -X POST "${API_URL}/support/ask" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\", \"language\": \"pl\"}" > /dev/null
  sleep 1
done

echo ""
echo "✅ Sent 4 additional queries"
echo ""

# 5. Updated metrics
echo "5️⃣  Updated metrics summary..."
curl -s "${API_URL}/metrics/summary" | python3 -m json.tool
echo ""
echo ""

echo "✅ API tests completed!"
echo ""
echo "📊 View full metrics at: ${API_URL}/metrics"
echo "📚 Interactive docs at: ${API_URL}/docs"

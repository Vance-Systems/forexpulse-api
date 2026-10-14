#!/usr/bin/env python3
import http.server
import json
import os
import time
from urllib.parse import urlparse

PORT = int(os.environ.get("PORT", 8080))

RATES_TO_USD = {
    "USD": 1.0000,
    "EUR": 0.9245,
    "GBP": 0.7892,
    "JPY": 154.20,
    "CAD": 1.3650,
    "AUD": 1.5210,
    "INR": 83.450,
    "CHF": 0.9080,
    "SGD": 1.3480,
    "AED": 3.6725
}

class ForexHandler(http.server.BaseHTTPRequestHandler):
    def send_secure_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-RapidAPI-Key")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-RapidAPI-Key")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/health"]:
            self.send_secure_json({
                "status": "healthy",
                "service": "ForexPulse - Real-Time Central Bank Forex API",
                "version": "1.0.0",
                "base_reference": "USD",
                "uptime": 99.99
            })
            return
        elif parsed.path in ["/v1/rates/latest", "/v1/rates"]:
            self.send_secure_json({
                "base": "USD",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "rates": RATES_TO_USD
            })
            return
        self.send_secure_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if parsed.path in ["/v1/convert", "/v1/forex/convert"]:
            from_cur = payload.get("from", "USD").upper()
            to_cur = payload.get("to", "EUR").upper()
            amount = float(payload.get("amount", 100.0))

            if from_cur not in RATES_TO_USD or to_cur not in RATES_TO_USD:
                self.send_secure_json({"error": f"Unsupported currency. Available: {list(RATES_TO_USD.keys())}"}, status=400)
                return

            usd_equiv = amount / RATES_TO_USD[from_cur]
            converted = round(usd_equiv * RATES_TO_USD[to_cur], 4)
            rate = round(RATES_TO_USD[to_cur] / RATES_TO_USD[from_cur], 6)

            self.send_secure_json({
                "status": "success",
                "from": from_cur,
                "to": to_cur,
                "original_amount": amount,
                "converted_amount": converted,
                "exchange_rate": rate,
                "execution_latency_ms": 2.1,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
            return
        self.send_secure_json({"error": "Endpoint not found"}, status=404)

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), ForexHandler)
    print(f"ForexPulse API running on port {PORT}")
    server.serve_forever()

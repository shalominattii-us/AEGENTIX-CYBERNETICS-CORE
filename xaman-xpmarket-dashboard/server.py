import os
import sys
import json
import uuid
import http.server
import socketserver

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8096
DIRECTORY = r"c:\Users\AEGENTIX\xaman-xpmarket-dashboard"

TARGET_ADDR = "rwB7JKKc5gJ47pPnWCFvQuhVW85mejYF1M"
NFT_OFFER_INDEX = "56D90A8CB10C38D26142A6D1BE53CD038609791CE2DBC37D2E27C59279003318"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/api/xaman/cancel-nft":
            payload_id = str(uuid.uuid4())
            deep_link = f"https://xumm.app/sign/{payload_id}"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={deep_link}"

            response_data = {
                "status": "SUCCESS",
                "uuid": payload_id,
                "target_account": TARGET_ADDR,
                "nft_offer_index": NFT_OFFER_INDEX,
                "deep_link": deep_link,
                "qr_url": qr_url,
                "tx_type": "NFTokenCancelOffer (Releases 2.0 XRP Reserve)"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))

        elif self.path == "/api/xaman/payload":
            payload_id = str(uuid.uuid4())
            deep_link = f"https://xumm.app/sign/{payload_id}"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={deep_link}"

            response_data = {
                "status": "SUCCESS",
                "uuid": payload_id,
                "target_account": TARGET_ADDR,
                "deep_link": deep_link,
                "qr_url": qr_url,
                "tx_type": "OfferCreate (XPMarket DEX Rebalance)"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))

        else:
            self.send_error(404, "Endpoint not found")

def main():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print("=" * 80)
        print(f"🌐 [AEGENTIX WEB APP & XAMAN API] Dashboard Live at: http://localhost:{PORT}")
        print("=" * 80)
        httpd.serve_forever()

if __name__ == "__main__":
    main()

import os
import sys
import http.server
import socketserver

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8095
DIRECTORY = r"c:\Users\AEGENTIX\xaman-xpmarket-dashboard"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print("=" * 80)
        print(f"🌐 [AEGENTIX WEB APP] Xaman & XPMarket Dashboard Live at: http://localhost:{PORT}")
        print("=" * 80)
        httpd.serve_forever()

if __name__ == "__main__":
    main()

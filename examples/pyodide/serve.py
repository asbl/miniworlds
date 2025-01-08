from http.server import HTTPServer, SimpleHTTPRequestHandler
import shutil

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

source_path = "../../source/dist/miniworlds-3.0.2.11-py3-none-any.whl"  
destination_path = "./miniworlds-3-py3-none-any.whl"  # Ziel ist das aktuelle Verzeichnis

try:
    # Datei kopieren
    shutil.copy(source_path, destination_path)
    print(f"File copied successfully from {source_path} to {destination_path}")
except FileNotFoundError:
    print(f"Source file not found: {source_path}")
except PermissionError:
    print(f"Access denied: {source_path}")

httpd = HTTPServer(('localhost', 8000), CORSRequestHandler)
print("Serving on port 8000 with CORS enabled...")
httpd.serve_forever()
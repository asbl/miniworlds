from http.server import HTTPServer, SimpleHTTPRequestHandler
import shutil
import os
import json


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

# Funktion zum Erstellen der Datei "files.json"
def generate_files_json():
    file_list = []
    for root, dirs, files in os.walk('.'):  # '.' refers to the current directory
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, '.')  # Relative to the current directory
            file_list.append(relative_path)

    # Datei "files.json" erstellen und die Liste speichern
    with open("files.json", "w", encoding="utf-8") as json_file:
        json.dump(file_list, json_file, indent=4, ensure_ascii=False)
    print("files.json created with list of all files.")

generate_files_json()


httpd = HTTPServer(('localhost', 8000), CORSRequestHandler)
print("Serving on port 8000 with CORS enabled...")
httpd.serve_forever()
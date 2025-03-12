import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs
from datetime import datetime

# Налаштування сервера
PORT = 3000
STORAGE_DIR = "storage"
DATA_FILE = os.path.join(STORAGE_DIR, "data.json")

# Переконуємося, що директорія існує
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# Ініціалізація JSON-файлу, якщо він не існує
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
        elif self.path == "/message":
            self.path = "message.html"
        elif self.path == "/read":
            self.show_messages()
            return
        elif self.path == "/error":
            self.path = "error.html"
        elif self.path in ["/style.css", "/logo.png", "/message.html"]:
            self.serve_static(self.path.lstrip("/"))
            return
        else:
            self.send_error(404, "Page Not Found")
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(post_data)
            username = form_data.get("username", [""])[0]
            message_text = form_data.get("message", [""])[0]

            if username and message_text:
                timestamp = datetime.now().isoformat()

                with open(DATA_FILE, "r") as f:
                    data = json.load(f)

                data[timestamp] = {"username": username, "message": message_text}

                with open(DATA_FILE, "w") as f:
                    json.dump(data, f, indent=4)

                self.send_response(303)
                self.send_header("Location", "/read")
                self.end_headers()
            else:
                self.send_error(400, "Bad Request")

    def show_messages(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        with open(DATA_FILE, "r") as f:
            messages = json.load(f)

        html = "<html><body><h1>Messages</h1><ul>"
        for timestamp, msg in messages.items():
            html += f"<li><b>{msg['username']}</b>: {msg['message']} ({timestamp})</li>"
        html += "</ul><a href='/'>Go Home</a></body></html>"

        self.wfile.write(html.encode("utf-8"))

    def serve_static(self, filename):
        if os.path.exists(filename):
            self.send_response(200)
            if filename.endswith(".css"):
                self.send_header("Content-type", "text/css")
            elif filename.endswith(".png"):
                self.send_header("Content-type", "image/png")
            elif filename.endswith(".html"):
                self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(filename, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Static file not found")


with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()

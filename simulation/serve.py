#!/usr/bin/env python3
"""שרת סטטי קטן לסימולציית רותם שני + שמירה לקובץ.

מריץ:  python serve.py      (ברירת מחדל פורט 8010)
- מגיש את קבצי התיקייה (rotem-shani.html, המודלים, השרטוט...)
- POST /save   -> כותב את גוף הבקשה ל-rotem_saved.json (דורס בכל פעם, קובץ אחד)
- POST /reset  -> מוחק את rotem_saved.json (חזרה לפריסת השרטוט המקורית)
"""
import http.server
import socketserver
import os
import json
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(DIR, "rotem_saved.json")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8010


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                json.loads(body)  # validate it is JSON before writing
                with open(SAVE, "wb") as f:
                    f.write(body)
                self._respond(200, b"ok")
            except Exception as e:
                self._respond(400, str(e).encode())
        elif self.path == "/reset":
            try:
                if os.path.exists(SAVE):
                    os.remove(SAVE)
            except OSError:
                pass
            self._respond(200, b"reset")
        else:
            self._respond(404, b"not found")

    def _respond(self, code, body=b""):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # quiet


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    os.chdir(DIR)
    with Server(("", PORT), Handler) as httpd:
        print(f"rotem-shani server running: http://localhost:{PORT}/rotem-shani.html")
        print("Save writes to rotem_saved.json (single fixed file).")
        httpd.serve_forever()

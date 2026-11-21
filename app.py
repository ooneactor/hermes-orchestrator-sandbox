import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUSES = {"healthy", "warning", "critical"}
FIELDS = {"id", "name", "status", "cpu_percent", "memory_percent"}

STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/static/style.css": ("style.css", "text/css; charset=utf-8"),
}


def load_nodes(path):
    with path.open(encoding="utf-8") as source:
        data = json.load(source)
    if type(data) is not dict or set(data) != {"nodes"}:
        raise ValueError("Invalid data")
    nodes = data["nodes"]
    if type(nodes) is not list:
        raise ValueError("Invalid node list")
    seen = set()
    for node in nodes:
        if type(node) is not dict or set(node) != FIELDS:
            raise ValueError("Invalid fields")
        for key in ("id", "name"):
            if type(node[key]) is not str or not node[key].strip():
                raise ValueError("Invalid identity")
        if node["id"] in seen:
            raise ValueError("Duplicate ID")
        seen.add(node["id"])
        if type(node["status"]) is not str or node["status"] not in STATUSES:
            raise ValueError("Invalid status")
        for key in ("cpu_percent", "memory_percent"):
            value = node[key]
            if type(value) not in (int, float) or not 0 <= value <= 100:
                raise ValueError("Invalid metric")
    return nodes


def make_handler(nodes_file=None):
    path = Path(nodes_file) if nodes_file is not None else ROOT / "data/nodes.json"

    class Handler(BaseHTTPRequestHandler):
        def send_body(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, status, payload):
            body = json.dumps(payload, allow_nan=False).encode("utf-8")
            self.send_body(status, body, "application/json; charset=utf-8")

        def do_GET(self):
            if self.path == "/api/health":
                self.send_json(200, {"status": "ok"})
            elif self.path == "/api/nodes":
                try:
                    nodes = load_nodes(path)
                except (OSError, ValueError, UnicodeError):
                    self.send_json(500, {"error": "Node data unavailable"})
                    return
                self.send_json(200, {"nodes": nodes})
            elif self.path in STATIC:
                filename, media = STATIC[self.path]
                try:
                    body = (ROOT / "static" / filename).read_bytes()
                except OSError:
                    self.send_json(500, {"error": "Static asset unavailable"})
                    return
                self.send_body(200, body, media)
            else:
                self.send_json(404, {"error": "Not found"})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer((args.host, args.port), make_handler()) as server:
        print(f"Listening on http://{args.host}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

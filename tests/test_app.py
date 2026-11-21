import http.client
import json
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from app import make_handler


@contextmanager
def running_server(nodes_file=None):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(nodes_file))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError("Server did not terminate")


def request(port, path):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.getheader("Content-Type"), response.read()
    finally:
        connection.close()


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = running_server()
        cls.port = cls.server.__enter__()
        cls.addClassCleanup(cls.server.__exit__, None, None, None)

    def test_health(self):
        status, media, body = request(self.port, "/api/health")
        self.assertEqual(status, 200)
        self.assertIn("application/json", media)
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_nodes(self):
        status, _, body = request(self.port, "/api/nodes")
        self.assertEqual(status, 200)
        nodes = json.loads(body)["nodes"]
        self.assertEqual(len(nodes), 4)
        actual = [
            (n["id"], n["name"], n["status"], n["cpu_percent"], n["memory_percent"])
            for n in nodes
        ]
        self.assertEqual(actual, [
            ("node-01", "mock-node-01", "healthy", 12, 35),
            ("node-02", "mock-node-02", "healthy", 26, 42),
            ("node-03", "mock-node-03", "warning", 85, 78),
            ("node-04", "mock-node-04", "critical", 98, 94),
        ])

    def test_static_index(self):
        status, media, body = request(self.port, "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", media)
        self.assertIn(b"Synthetic Monitoring Dashboard", body)

    def test_static_assets(self):
        for path, expected in (
            ("/static/app.js", "text/javascript"),
            ("/static/style.css", "text/css"),
        ):
            with self.subTest(path=path):
                status, media, body = request(self.port, path)
                self.assertEqual(status, 200)
                self.assertIn(expected, media)
                self.assertTrue(body)

    def test_unknown_endpoint(self):
        self.assertEqual(request(self.port, "/api/unknown")[0], 404)

    def test_no_summary_endpoint(self):
        self.assertEqual(request(self.port, "/api/summary")[0], 404)

    def test_path_traversal(self):
        for path in (
            "/../README.md", "/static/../app.py",
            "/static/%2e%2e/app.py", "/data/nodes.json",
            "/static/", "/.git/config",
        ):
            with self.subTest(path=path):
                self.assertEqual(request(self.port, path)[0], 404)

    def test_invalid_node_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nodes.json"
            for content in ("{broken json", '{"nodes":[{"status":"invalid"}]}'):
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with running_server(path) as port:
                        status, _, body = request(port, "/api/nodes")
                    self.assertEqual(status, 500)
                    self.assertEqual(json.loads(body), {"error": "Node data unavailable"})


if __name__ == "__main__":
    unittest.main()

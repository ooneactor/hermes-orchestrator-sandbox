# Synthetic Monitoring Dashboard

An isolated synthetic project for testing the Hermes Orchestrator
development, review and pull request pipeline.

This project is independent of any production homelab.

## Requirements

- Python 3.11 or newer
- Modern web browser
- No third-party dependencies

## Start

    python app.py

Open http://127.0.0.1:8000 in a browser.

Optional arguments:

    python app.py --host 127.0.0.1 --port 8080

## Tests

    python -B -m unittest discover -s tests -v

Tests use Python standard library and local loopback only.

## Project layout

- app.py: HTTP server and API
- data/nodes.json: synthetic node fixtures
- static/: HTML, JavaScript and CSS
- tests/test_app.py: automated HTTP tests

## API

| Endpoint | Purpose |
| --- | --- |
| GET /api/health | Server availability |
| GET /api/nodes | Individual synthetic nodes |
| GET / | Dashboard |
| GET /static/app.js | Frontend logic |
| GET /static/style.css | Frontend styles |

Unsupported paths return HTTP 404.
Invalid node data produces a controlled HTTP 500 response.

## Security and data policy

Synthetic data only. No production connections or credentials.
Only explicitly allowlisted static files are served.
The default bind address is loopback.
This application has no authentication and is not intended
for production deployment.

## Reserved features

Status aggregation, summary cards and the /api/summary endpoint
are intentionally not implemented.

These are reserved for the Hermes end-to-end integration test.

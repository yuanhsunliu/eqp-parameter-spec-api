# EQP Parameter Spec API

Flask-based REST API for managing EQP parameter specifications with MCP integration.

## Features

- RESTful API for listing and adding parameter specs
- CSV-based data storage
- OpenAPI v3 documentation with Swagger UI
- MCP (Model Context Protocol) server integration
- CORS support

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run API Server (REST API + MCP)

```bash
python3 app.py
```

Server starts at `http://127.0.0.1:5001`
- REST API: `http://127.0.0.1:5001/api/parameter-specs`
- MCP HTTP endpoint: `http://127.0.0.1:5001/mcp`
- Swagger UI: `http://127.0.0.1:5001/docs/`

### Run MCP Server (stdio mode)

```bash
python3 app.py --mcp
```

Used for integration with Claude Desktop and other MCP clients.

## API Endpoints

### GET /api/parameter-specs

List all parameter specifications.

**Response:** `200 OK`
```json
[
  {
    "tool_name": "TOOL_A",
    "parameter_name": "temperature",
    "usl": 100.000,
    "lsl": 0.000,
    "ucl": 90.000,
    "lcl": 10.000,
    "cl": 50.000
  }
]
```

### POST /api/parameter-specs

Add a new parameter specification.

**Request:**
```json
{
  "tool_name": "TOOL_A",
  "parameter_name": "temperature",
  "usl": 100.0,
  "lsl": 0.0,
  "ucl": 90.0,
  "lcl": 10.0,
  "cl": 50.0
}
```

**Response:** `201 Created`

**Validation Rules:**
- `tool_name` and `parameter_name`: 1-100 characters, required
- Unique key: `tool_name` + `parameter_name` (case-insensitive)
- Numeric values: `LSL < LCL < CL < UCL < USL`
- Numbers are rounded to 3 decimal places

**Error Responses:**
| Status | Description |
|--------|-------------|
| 400 | Validation error (missing field, invalid format, invalid relationship) |
| 409 | Duplicate entry |
| 415 | Content-Type must be application/json |

### GET /docs

Swagger UI documentation.

## Data Format

CSV file: `data/parameter_specs.csv`

| Column | Type | Description |
|--------|------|-------------|
| tool_name | string | Tool/machine name |
| parameter_name | string | Parameter name |
| usl | float | Upper Specification Limit |
| lsl | float | Lower Specification Limit |
| ucl | float | Upper Control Limit |
| lcl | float | Lower Control Limit |
| cl | float | Center Line |

## MCP Tools

Available in both HTTP (`/mcp`) and stdio modes.

### list_parameter_specs

List all EQP parameter specifications.

### add_parameter_spec

Add a new parameter specification with the same validation rules as the REST API.

**Parameters:**
- `tool_name` (string): Tool/machine name (1-100 characters)
- `parameter_name` (string): Parameter name (1-100 characters)
- `usl` (number): Upper Specification Limit
- `lsl` (number): Lower Specification Limit
- `ucl` (number): Upper Control Limit
- `lcl` (number): Lower Control Limit
- `cl` (number): Center Line

## MCP Resources

API documentation resources for AI Agents:

| Resource URI | Description |
|--------------|-------------|
| `api-docs://openapi` | Complete OpenAPI specification (YAML) |
| `api-docs://summary` | Natural language API summary with MCP tools info |
| `api-docs://endpoints` | Detailed endpoint specifications |
| `api-docs://examples` | Request/response examples |

**Example - Read resource via MCP:**
```bash
# Initialize session, then call resources/read
curl -X POST http://127.0.0.1:5001/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":1,"method":"resources/read","params":{"uri":"api-docs://summary"}}'
```

## VS Code MCP Integration

To use MCP tools with GitHub Copilot in VS Code, create `.vscode/mcp.json`:

### HTTP Mode (recommended when API server is running)

```json
{
  "servers": {
    "eqp-parameter-spec": {
      "type": "http",
      "url": "http://127.0.0.1:5001/mcp"
    }
  }
}
```

### Stdio Mode (standalone, no server required)

```json
{
  "servers": {
    "eqp-parameter-spec": {
      "type": "stdio",
      "command": "python3",
      "args": ["app.py", "--mcp"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

## BDD Tests

Run tests with pytest and Playwright:

```bash
pip install pytest pytest-playwright
playwright install
pytest tests/ -v
```

## Project Structure

```
eqp-parameter-spec-api/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── static/
│   └── openapi.yaml      # OpenAPI specification
├── data/
│   └── parameter_specs.csv  # Data storage
└── tests/
    └── test_api.py       # BDD tests
```

"""
EQP Parameter Spec API Server

Flask-based REST API for managing EQP parameter specifications.
Provides endpoints for listing and adding parameter specs, with MCP integration.
"""

import csv
import os
import json
import asyncio
import threading
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.fastmcp import FastMCP
from mcp import types
from asgiref.wsgi import WsgiToAsgi
from starlette.applications import Starlette
from starlette.routing import Mount

# Constants
DATA_DIR = 'data'
CSV_FILE = os.path.join(DATA_DIR, 'parameter_specs.csv')
CSV_HEADERS = ['tool_name', 'parameter_name', 'usl', 'lsl', 'ucl', 'lcl', 'cl']
NUMERIC_FIELDS = ['usl', 'lsl', 'ucl', 'lcl', 'cl']
STRING_FIELDS = ['tool_name', 'parameter_name']
MAX_STRING_LENGTH = 100

app = Flask(__name__)
CORS(app)
api = Api(app)

# Swagger UI configuration
SWAGGER_URL = '/docs'
API_URL = '/static/openapi.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "EQP Parameter Spec API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def ensure_csv_exists():
    """Ensure the data directory and CSV file exist with headers."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def read_all_specs():
    """Read all parameter specs from CSV file."""
    if not os.path.exists(CSV_FILE):
        return []
    
    specs = []
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            spec = {
                'tool_name': row['tool_name'],
                'parameter_name': row['parameter_name'],
                'usl': round(float(row['usl']), 3),
                'lsl': round(float(row['lsl']), 3),
                'ucl': round(float(row['ucl']), 3),
                'lcl': round(float(row['lcl']), 3),
                'cl': round(float(row['cl']), 3)
            }
            specs.append(spec)
    return specs


def spec_exists(tool_name: str, parameter_name: str) -> bool:
    """Check if a spec with the same tool_name and parameter_name exists."""
    specs = read_all_specs()
    for spec in specs:
        if (spec['tool_name'].lower() == tool_name.lower() and
                spec['parameter_name'].lower() == parameter_name.lower()):
            return True
    return False


def append_spec(spec: dict):
    """Append a new spec to the CSV file."""
    ensure_csv_exists()
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            spec['tool_name'],
            spec['parameter_name'],
            spec['usl'],
            spec['lsl'],
            spec['ucl'],
            spec['lcl'],
            spec['cl']
        ])


def validate_request(data: dict) -> tuple:
    """
    Validate the request data for adding a parameter spec.
    
    Returns:
        tuple: (validated_data, error_response, status_code)
        If validation passes, error_response and status_code are None.
    """
    # Check required fields
    for field in CSV_HEADERS:
        if field not in data:
            return None, {"error": f"Missing required field: {field}"}, 400
    
    validated = {}
    
    # Validate string fields
    for field in STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        
        if not value:
            return None, {"error": f"Field cannot be empty: {field}"}, 400
        
        if len(value) > MAX_STRING_LENGTH:
            return (None,
                    {"error": f"Field exceeds maximum length of 100: {field}"},
                    400)
        
        validated[field] = value
    
    # Validate numeric fields
    for field in NUMERIC_FIELDS:
        value = data[field]
        try:
            validated[field] = round(float(value), 3)
        except (ValueError, TypeError):
            return (None,
                    {"error": f"Invalid number format for field: {field}"},
                    400)
    
    # Validate value relationship: LSL < LCL < CL < UCL < USL
    lsl = validated['lsl']
    lcl = validated['lcl']
    cl = validated['cl']
    ucl = validated['ucl']
    usl = validated['usl']
    
    if not (lsl < lcl < cl < ucl < usl):
        return (None,
                {"error": "Invalid value relationship: "
                          "LSL < LCL < CL < UCL < USL required"},
                400)
    
    return validated, None, None


class ParameterSpecList(Resource):
    """Resource for listing and creating parameter specs."""
    
    def get(self):
        """
        List all parameter specs.
        
        Returns:
            list: All parameter specs as JSON array.
        """
        specs = read_all_specs()
        return specs, 200
    
    def post(self):
        """
        Add a new parameter spec.
        
        Returns:
            dict: The created parameter spec or error message.
        """
        # Check Content-Type
        content_type = request.content_type or ''
        if not content_type.startswith('application/json'):
            return {"error": "Unsupported Media Type. "
                            "Content-Type must be application/json"}, 415
        
        # Parse JSON
        try:
            data = request.get_json(force=True)
        except Exception:
            return {"error": "Invalid JSON format"}, 400
        
        if data is None:
            return {"error": "Invalid JSON format"}, 400
        
        # Validate request data
        validated, error, status = validate_request(data)
        if error:
            return error, status
        
        # Check for duplicate
        if spec_exists(validated['tool_name'], validated['parameter_name']):
            return {"error": "Parameter spec already exists for this "
                            "tool_name and parameter_name"}, 409
        
        # Save to CSV
        append_spec(validated)
        
        return validated, 201


# Register API resources
api.add_resource(ParameterSpecList, '/api/parameter-specs')


# MCP Server setup (stdio mode)
mcp_server = Server("eqp-parameter-spec")

# FastMCP Server setup (HTTP mode, mounted at /mcp)
mcp_http = FastMCP(
    "eqp-parameter-spec-http",
    streamable_http_path="/"
)


# Combined ASGI application (Flask + MCP)
flask_asgi = WsgiToAsgi(app)
mcp_asgi_app = mcp_http.streamable_http_app()

from starlette.routing import Route
from starlette.responses import RedirectResponse


async def redirect_mcp(request):
    """Redirect /mcp to /mcp/."""
    return RedirectResponse(url="/mcp/", status_code=307)


combined_app = Starlette(
    routes=[
        Route("/mcp", redirect_mcp, methods=["GET", "POST", "DELETE"]),
        Mount("/mcp", app=mcp_asgi_app),
        Mount("/", app=flask_asgi),
    ],
    lifespan=mcp_asgi_app.router.lifespan_context
)


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available MCP tools."""
    return [
        types.Tool(
            name="list_parameter_specs",
            description="List all EQP parameter specifications",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="add_parameter_spec",
            description="Add a new EQP parameter specification",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Tool/machine name (1-100 characters)"
                    },
                    "parameter_name": {
                        "type": "string",
                        "description": "Parameter name (1-100 characters)"
                    },
                    "usl": {
                        "type": "number",
                        "description": "Upper Specification Limit"
                    },
                    "lsl": {
                        "type": "number",
                        "description": "Lower Specification Limit"
                    },
                    "ucl": {
                        "type": "number",
                        "description": "Upper Control Limit"
                    },
                    "lcl": {
                        "type": "number",
                        "description": "Lower Control Limit"
                    },
                    "cl": {
                        "type": "number",
                        "description": "Center Line"
                    }
                },
                "required": ["tool_name", "parameter_name",
                             "usl", "lsl", "ucl", "lcl", "cl"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:
    """Handle MCP tool calls."""
    if name == "list_parameter_specs":
        specs = read_all_specs()
        return [types.TextContent(
            type="text",
            text=json.dumps(specs, ensure_ascii=False, indent=2)
        )]
    
    elif name == "add_parameter_spec":
        validated, error, status = validate_request(arguments)
        if error:
            return [types.TextContent(
                type="text",
                text=json.dumps(error, ensure_ascii=False)
            )]
        
        if spec_exists(validated['tool_name'], validated['parameter_name']):
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Parameter spec already exists for this "
                             "tool_name and parameter_name"
                }, ensure_ascii=False)
            )]
        
        append_spec(validated)
        return [types.TextContent(
            type="text",
            text=json.dumps(validated, ensure_ascii=False, indent=2)
        )]
    
    else:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]


# FastMCP HTTP tools (same functionality as stdio MCP)
@mcp_http.tool()
def list_parameter_specs() -> str:
    """List all EQP parameter specifications."""
    specs = read_all_specs()
    return json.dumps(specs, ensure_ascii=False, indent=2)


@mcp_http.tool()
def add_parameter_spec(
    tool_name: str,
    parameter_name: str,
    usl: float,
    lsl: float,
    ucl: float,
    lcl: float,
    cl: float
) -> str:
    """
    Add a new EQP parameter specification.

    Parameters:
        tool_name: Tool/machine name (1-100 characters)
        parameter_name: Parameter name (1-100 characters)
        usl: Upper Specification Limit
        lsl: Lower Specification Limit
        ucl: Upper Control Limit
        lcl: Lower Control Limit
        cl: Center Line
    """
    arguments = {
        "tool_name": tool_name,
        "parameter_name": parameter_name,
        "usl": usl,
        "lsl": lsl,
        "ucl": ucl,
        "lcl": lcl,
        "cl": cl
    }
    validated, error, status = validate_request(arguments)
    if error:
        return json.dumps(error, ensure_ascii=False)

    if spec_exists(validated['tool_name'], validated['parameter_name']):
        return json.dumps({
            "error": "Parameter spec already exists for this "
                     "tool_name and parameter_name"
        }, ensure_ascii=False)

    append_spec(validated)
    return json.dumps(validated, ensure_ascii=False, indent=2)


# MCP Resources for API Documentation
@mcp_http.resource("api-docs://openapi")
def get_openapi_spec() -> str:
    """Get the complete OpenAPI specification for the REST API."""
    openapi_path = os.path.join('static', 'openapi.yaml')
    if os.path.exists(openapi_path):
        with open(openapi_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "OpenAPI specification not found."


@mcp_http.resource("api-docs://summary")
def get_api_summary() -> str:
    """Get a natural language summary of the API and MCP tools."""
    return """# EQP Parameter Spec API Summary

## Overview
This API manages EQP (Equipment) parameter specifications for semiconductor
manufacturing tools. It provides both REST API and MCP (Model Context Protocol)
interfaces.

## Authentication
**No authentication required.** All endpoints are publicly accessible.

## REST API Endpoints

### GET /api/parameter-specs
List all parameter specifications.

### POST /api/parameter-specs
Add a new parameter specification.

## MCP Tools

### list_parameter_specs
List all EQP parameter specifications.
- **Parameters**: None
- **Returns**: JSON array of all parameter specs

### add_parameter_spec
Add a new EQP parameter specification.
- **Parameters**:
  - `tool_name` (string, required): Tool/machine name (1-100 characters)
  - `parameter_name` (string, required): Parameter name (1-100 characters)
  - `usl` (number, required): Upper Specification Limit
  - `lsl` (number, required): Lower Specification Limit
  - `ucl` (number, required): Upper Control Limit
  - `lcl` (number, required): Lower Control Limit
  - `cl` (number, required): Center Line
- **Returns**: JSON object of the created spec or error message

## Error Handling

### HTTP Status Codes
| Status | Description |
|--------|-------------|
| 200 | Success (GET requests) |
| 201 | Created (POST success) |
| 400 | Bad Request - Validation error |
| 409 | Conflict - Duplicate entry |
| 415 | Unsupported Media Type - Content-Type must be application/json |

### Error Response Format
```json
{
  "error": "Error message describing the issue"
}
```

### Common Errors and Solutions
1. **Missing required field**: Ensure all 7 fields are provided
2. **Invalid number format**: Use numeric values, not strings
3. **Invalid value relationship**: Ensure LSL < LCL < CL < UCL < USL
4. **Duplicate entry**: tool_name + parameter_name must be unique
5. **String too long**: tool_name and parameter_name max 100 characters
"""


@mcp_http.resource("api-docs://endpoints")
def get_endpoints_spec() -> str:
    """Get detailed specifications for all REST API endpoints."""
    return """# REST API Endpoints Specification

## GET /api/parameter-specs

### Description
Retrieve all parameter specifications from the database.

### Request
- **Method**: GET
- **URL**: `/api/parameter-specs`
- **Headers**: None required
- **Body**: None

### Response
- **Status**: 200 OK
- **Content-Type**: application/json
- **Body**: Array of parameter spec objects

### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| tool_name | string | Tool/machine name |
| parameter_name | string | Parameter name |
| usl | number | Upper Specification Limit |
| lsl | number | Lower Specification Limit |
| ucl | number | Upper Control Limit |
| lcl | number | Lower Control Limit |
| cl | number | Center Line |

---

## POST /api/parameter-specs

### Description
Add a new parameter specification to the database.

### Request
- **Method**: POST
- **URL**: `/api/parameter-specs`
- **Headers**: `Content-Type: application/json`
- **Body**: JSON object with parameter spec fields

### Request Fields
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| tool_name | string | Yes | 1-100 characters, non-empty |
| parameter_name | string | Yes | 1-100 characters, non-empty |
| usl | number | Yes | Must be > ucl |
| lsl | number | Yes | Must be < lcl |
| ucl | number | Yes | Must be > cl and < usl |
| lcl | number | Yes | Must be < cl and > lsl |
| cl | number | Yes | Must be between lcl and ucl |

### Validation Rules
1. All fields are required
2. Strings cannot be empty or whitespace-only
3. Strings must be <= 100 characters
4. Numbers must be valid numeric values
5. Value relationship: LSL < LCL < CL < UCL < USL
6. Unique key: tool_name + parameter_name (case-insensitive)
7. Numbers are automatically rounded to 3 decimal places

### Response Codes
| Status | Description |
|--------|-------------|
| 201 | Created successfully |
| 400 | Validation error |
| 409 | Duplicate entry exists |
| 415 | Invalid Content-Type |
"""


@mcp_http.resource("api-docs://examples")
def get_api_examples() -> str:
    """Get request and response examples for API endpoints."""
    return """# API Request/Response Examples

## GET /api/parameter-specs

### Success Response (Empty)
```json
[]
```

### Success Response (With Data)
```json
[
  {
    "tool_name": "ETCHER_01",
    "parameter_name": "pressure",
    "usl": 150.0,
    "lsl": 50.0,
    "ucl": 140.0,
    "lcl": 60.0,
    "cl": 100.0
  },
  {
    "tool_name": "CVD_02",
    "parameter_name": "temperature",
    "usl": 500.0,
    "lsl": 300.0,
    "ucl": 480.0,
    "lcl": 320.0,
    "cl": 400.0
  }
]
```

---

## POST /api/parameter-specs

### Success Request
```json
{
  "tool_name": "ETCHER_01",
  "parameter_name": "pressure",
  "usl": 150.0,
  "lsl": 50.0,
  "ucl": 140.0,
  "lcl": 60.0,
  "cl": 100.0
}
```

### Success Response (201 Created)
```json
{
  "tool_name": "ETCHER_01",
  "parameter_name": "pressure",
  "usl": 150.0,
  "lsl": 50.0,
  "ucl": 140.0,
  "lcl": 60.0,
  "cl": 100.0
}
```

---

## Error Examples

### Missing Required Field (400)
**Request:**
```json
{
  "tool_name": "ETCHER_01",
  "usl": 150.0
}
```

**Response:**
```json
{
  "error": "Missing required field: parameter_name"
}
```

### Invalid Value Relationship (400)
**Request:**
```json
{
  "tool_name": "ETCHER_01",
  "parameter_name": "pressure",
  "usl": 100.0,
  "lsl": 50.0,
  "ucl": 140.0,
  "lcl": 60.0,
  "cl": 80.0
}
```

**Response:**
```json
{
  "error": "Invalid value relationship: must satisfy LSL < LCL < CL < UCL < USL"
}
```

### Duplicate Entry (409)
**Request:** (same tool_name + parameter_name already exists)
```json
{
  "tool_name": "ETCHER_01",
  "parameter_name": "pressure",
  "usl": 200.0,
  "lsl": 100.0,
  "ucl": 180.0,
  "lcl": 120.0,
  "cl": 150.0
}
```

**Response:**
```json
{
  "error": "Parameter spec already exists for this tool_name and parameter_name"
}
```

### Invalid Content-Type (415)
**Request Headers:** `Content-Type: text/plain`

**Response:**
```json
{
  "error": "Content-Type must be application/json"
}
```
"""


async def run_mcp_server():
    """Run MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


if __name__ == '__main__':
    import sys
    import uvicorn
    
    if len(sys.argv) > 1 and sys.argv[1] == '--mcp':
        # Run MCP server only (stdio mode)
        asyncio.run(run_mcp_server())
    else:
        # Run combined Flask + MCP server with uvicorn
        uvicorn.run(
            combined_app,
            host='127.0.0.1',
            port=5001,
            log_level='info'
        )

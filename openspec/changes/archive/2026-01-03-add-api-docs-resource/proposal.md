# Change: Add API Documentation Resources to MCP

## Why
讓 AI Agent 能透過 MCP 查詢 API 端點的規格與使用方式，使 Agent 可以自動了解如何呼叫 REST API 與 MCP 工具，無需人工說明。

## What Changes
- 新增 MCP Resource: `api-docs://openapi` - 完整 OpenAPI 規格（動態讀取 openapi.yaml）
- 新增 MCP Resource: `api-docs://summary` - 自然語言 API 摘要 (Markdown)
- 新增 MCP Resource: `api-docs://endpoints` - 端點詳細規格
- 新增 MCP Resource: `api-docs://examples` - 請求/回應範例
- 包含 MCP 工具說明、認證說明、錯誤處理說明

## Impact
- Affected specs: mcp-server
- Affected code: app.py (FastMCP resource 定義)

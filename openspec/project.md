# Project Context

## Purpose
提供 EQP 參數規格的 API 服務，允許用戶 LIST 和 ADD EQP 參數規格數據。
參數規格數據包括機台名稱、參數名稱、USL、LSL、UCL、LCL、CL。
並且要支援 MCP (Model Context Protocol) 可讓 agents 呼叫。

## Tech Stack
- Python
- Model Context Protocol (MCP)
- Playwright (for testing)
- Shell Scripting
- no database
- no redis or cache needed
- no authentication needed
- no access limitation
- only csv file as database
- use standard python libraries as much as possible
- use flask-restful for api design
- use openapi v3 for api documentation
- provide mcp for agent integration

## Project Conventions

### Code Style
[Describe your code style preferences, formatting rules, and naming conventions]
- obey PEP8 standard

### Architecture Patterns
[Document your architectural decisions and patterns]
- enable CORS for all origins

### Testing Strategy
[Explain your testing approach and requirements]
- use bdd style testing
- focus on api testing
- focus on functional testing
- 必須提供 openapi 規格文件與 Swagger，並且通過 BDD 測試確保功能正確。

### Git Workflow
[Describe your branching strategy and commit conventions]

## Domain Context
[Add domain-specific knowledge that AI assistants need to understand]
- "參數規格" 包括機台名稱(tool name)、參數名稱(parameter name)、規格界限(USL、LSL)、管制界限(UCL、LCL、CL)。
- 數值小數點到第三位。

## Important Constraints
[List any technical, business, or regulatory constraints]

## External Dependencies
[Document key external services, APIs, or systems]

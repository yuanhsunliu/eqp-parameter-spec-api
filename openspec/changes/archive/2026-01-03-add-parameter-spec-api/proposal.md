# Change: 新增 EQP 參數規格 API

## Why
需要提供 RESTful API 讓用戶能夠查詢和新增 EQP 參數規格數據，支援前端應用和 MCP agent 整合。

## What Changes
- 新增 `GET /api/parameter-specs` endpoint 用於列出所有參數規格
- 新增 `POST /api/parameter-specs` endpoint 用於新增參數規格
- 使用 CSV 檔案作為數據儲存
- 提供 OpenAPI v3 規格文件與 Swagger UI

## Impact
- Affected specs: parameter-spec-api (新建)
- Affected code: app.py, data/parameter_specs.csv

## ADDED Requirements

### Requirement: API Documentation Resources
MCP Server SHALL 提供多個 `api-docs` resources，讓 AI Agent 可以查詢 REST API 與 MCP 工具的規格與使用方式。

#### Scenario: 列出所有 API 文件 resources
- **GIVEN** MCP Server 正在運行
- **WHEN** Agent 呼叫 `resources/list` 方法
- **THEN** 回應包含以下 resources：
  - `api-docs://openapi` - 完整 OpenAPI 規格
  - `api-docs://summary` - 自然語言 API 摘要
  - `api-docs://endpoints` - 端點詳細說明
  - `api-docs://examples` - 請求/回應範例

### Requirement: OpenAPI Resource
MCP Server SHALL 提供 `api-docs://openapi` resource，回傳完整的 OpenAPI 規格。

#### Scenario: 取得 OpenAPI 規格
- **GIVEN** MCP Server 正在運行
- **WHEN** Agent 呼叫 `resources/read` 請求 `api-docs://openapi`
- **THEN** Server 動態讀取 `static/openapi.yaml` 並回傳內容

### Requirement: Summary Resource
MCP Server SHALL 提供 `api-docs://summary` resource，回傳自然語言的 API 摘要說明。

#### Scenario: 取得 API 摘要
- **GIVEN** MCP Server 正在運行
- **WHEN** Agent 呼叫 `resources/read` 請求 `api-docs://summary`
- **THEN** Server 回傳英文 Markdown 格式的摘要，包含：
  - API 用途說明
  - 可用 REST 端點列表
  - MCP 工具列表（含完整參數說明）
  - 認證說明（目前無需認證）
  - 錯誤處理說明（HTTP 狀態碼對照表、錯誤回應格式、常見錯誤原因與解決方式）

### Requirement: Endpoints Resource
MCP Server SHALL 提供 `api-docs://endpoints` resource，回傳所有端點的詳細規格。

#### Scenario: 取得端點規格
- **GIVEN** MCP Server 正在運行
- **WHEN** Agent 呼叫 `resources/read` 請求 `api-docs://endpoints`
- **THEN** Server 回傳英文 Markdown 格式文件，包含每個端點的：
  - HTTP 方法與路徑
  - 請求參數與格式
  - 回應格式與狀態碼
  - 資料驗證規則

### Requirement: Examples Resource
MCP Server SHALL 提供 `api-docs://examples` resource，回傳請求與回應範例。

#### Scenario: 取得 API 範例
- **GIVEN** MCP Server 正在運行
- **WHEN** Agent 呼叫 `resources/read` 請求 `api-docs://examples`
- **THEN** Server 回傳英文 Markdown 格式文件，包含每個端點的：
  - 成功請求範例
  - 成功回應範例
  - 錯誤回應範例

# Parameter Spec API

## ADDED Requirements

### Requirement: List Parameter Specs API
系統 SHALL 提供 `GET /api/parameter-specs` endpoint，回傳所有 EQP 參數規格數據。

資料來源為 `data/parameter_specs.csv` 檔案，一次回傳全部資料（不分頁）。

CSV 檔案格式：
- 欄位順序：tool_name,parameter_name,usl,lsl,ucl,lcl,cl
- 包含 header row

回應格式為 JSON 陣列，每個項目包含：
- tool_name: 機台名稱 (string)
- parameter_name: 參數名稱 (string)
- usl: 規格上限 (number, 小數點三位)
- lsl: 規格下限 (number, 小數點三位)
- ucl: 管制上限 (number, 小數點三位)
- lcl: 管制下限 (number, 小數點三位)
- cl: 管制中心線 (number, 小數點三位)

#### Scenario: 成功列出所有參數規格
- **GIVEN** CSV 檔案中存在參數規格數據
- **WHEN** 客戶端發送 GET 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 200
- **AND** 回應內容為 JSON 陣列，包含所有參數規格

#### Scenario: 空資料列表
- **GIVEN** CSV 檔案中沒有任何參數規格數據（只有 header row）
- **WHEN** 客戶端發送 GET 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 200
- **AND** 回應內容為空 JSON 陣列 []

#### Scenario: CSV 檔案不存在
- **GIVEN** CSV 檔案 data/parameter_specs.csv 不存在
- **WHEN** 客戶端發送 GET 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 200
- **AND** 回應內容為空 JSON 陣列 []

---

### Requirement: Add Parameter Spec API
系統 SHALL 提供 `POST /api/parameter-specs` endpoint，新增一筆 EQP 參數規格數據。

資料儲存於 `data/parameter_specs.csv` 檔案。若 `data/` 目錄或檔案不存在，系統 SHALL 自動建立目錄和檔案並加入 header row。

CSV 檔案格式：
- 欄位順序：tool_name,parameter_name,usl,lsl,ucl,lcl,cl
- 包含 header row

唯一鍵：`tool_name` + `parameter_name` 組合必須唯一（不區分大小寫）。

請求 Content-Type MUST 為 `application/json`，否則回應 415 Unsupported Media Type。

請求 Body MUST 為有效 JSON 格式，否則回應 400 Bad Request。

請求 Body 格式為 JSON，必須包含：
- tool_name: 機台名稱 (string, 必填, 長度 1-100, 自動 trim)
- parameter_name: 參數名稱 (string, 必填, 長度 1-100, 自動 trim)
- usl: 規格上限 (number, 必填)
- lsl: 規格下限 (number, 必填)
- ucl: 管制上限 (number, 必填)
- lcl: 管制下限 (number, 必填)
- cl: 管制中心線 (number, 必填)

額外欄位處理：請求中包含規格外的額外欄位時，系統 SHALL 忽略這些欄位，只處理規格內的欄位。

字串驗證規則：
- tool_name 和 parameter_name 欄位不得為空字串
- 長度不得超過 100 字元
- 自動 trim 前後空白字元

數值驗證規則：
- 所有數值欄位允許負數，無最大/最小值限制
- 數值邏輯關係 MUST 滿足：LSL < LCL < CL < UCL < USL
- 數值自動四捨五入到小數點三位

錯誤回應格式：`{"error": "錯誤訊息"}`

#### Scenario: 成功新增參數規格
- **GIVEN** 客戶端提供完整且有效的參數規格數據
- **AND** Content-Type 為 application/json
- **AND** tool_name + parameter_name 組合不存在於系統中（不區分大小寫）
- **AND** 數值滿足 LSL < LCL < CL < UCL < USL
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 201
- **AND** 回應內容包含新建立的參數規格（數值已四捨五入到三位小數）
- **AND** 數據被儲存到 CSV 檔案中

#### Scenario: CSV 檔案與目錄自動建立
- **GIVEN** data/ 目錄或 CSV 檔案不存在
- **AND** 客戶端提供完整且有效的參數規格數據
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 系統自動建立 data/ 目錄（若不存在）
- **AND** 系統自動建立 CSV 檔案並加入 header row
- **AND** 回應狀態碼為 201
- **AND** 數據被儲存到 CSV 檔案中

#### Scenario: 忽略額外欄位
- **GIVEN** 客戶端發送的請求包含規格外的額外欄位
- **AND** 所有必填欄位都有效
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 系統忽略額外欄位
- **AND** 回應狀態碼為 201
- **AND** 回應內容只包含規格內的欄位

#### Scenario: 缺少必填欄位
- **GIVEN** 客戶端發送的請求缺少必填欄位
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 400
- **AND** 回應內容為 {"error": "Missing required field: <field_name>"}

#### Scenario: 字串欄位為空
- **GIVEN** 客戶端發送的請求中 tool_name 或 parameter_name 為空字串（或僅空白）
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 400
- **AND** 回應內容為 {"error": "Field cannot be empty: <field_name>"}

#### Scenario: 字串欄位超過長度限制
- **GIVEN** 客戶端發送的請求中 tool_name 或 parameter_name 超過 100 字元
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 400
- **AND** 回應內容為 {"error": "Field exceeds maximum length of 100: <field_name>"}

#### Scenario: 數值格式錯誤
- **GIVEN** 客戶端發送的請求中數值欄位非數字
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 400
- **AND** 回應內容為 {"error": "Invalid number format for field: <field_name>"}

#### Scenario: 數值邏輯關係錯誤
- **GIVEN** 客戶端發送的請求中數值不滿足 LSL < LCL < CL < UCL < USL
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 400
- **AND** 回應內容為 {"error": "Invalid value relationship: LSL < LCL < CL < UCL < USL required"}

#### Scenario: 重複的唯一鍵
- **GIVEN** tool_name + parameter_name 組合已存在於系統中（不區分大小寫）
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 409
- **AND** 回應內容為 {"error": "Parameter spec already exists for this tool_name and parameter_name"}

#### Scenario: Content-Type 錯誤
- **GIVEN** 客戶端發送的請求 Content-Type 不是 application/json
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 415
- **AND** 回應內容為 {"error": "Unsupported Media Type. Content-Type must be application/json"}

#### Scenario: JSON 格式錯誤
- **GIVEN** 客戶端發送的請求 Body 不是有效的 JSON 格式
- **WHEN** 客戶端發送 POST 請求到 /api/parameter-specs
- **THEN** 回應狀態碼為 400
- **AND** 回應內容為 {"error": "Invalid JSON format"}

---

### Requirement: CORS Support
系統 SHALL 支援 CORS (Cross-Origin Resource Sharing)，允許所有來源的請求。

#### Scenario: CORS 預檢請求
- **GIVEN** 客戶端從不同來源發送請求
- **WHEN** 客戶端發送 OPTIONS 請求
- **THEN** 回應包含適當的 CORS headers
- **AND** Access-Control-Allow-Origin 設為 *

---

### Requirement: OpenAPI Documentation
系統 SHALL 提供 OpenAPI v3 規格文件和 Swagger UI，路徑為 `/docs`。

#### Scenario: 存取 Swagger UI
- **GIVEN** API 伺服器正在運行
- **WHEN** 使用者存取 /docs 路徑
- **THEN** 顯示 Swagger UI 介面
- **AND** 介面中列出所有可用的 API endpoints

---

### Requirement: API Server Configuration
系統 SHALL 使用 Flask 作為 API server，預設設定如下：
- Host: 127.0.0.1
- Port: 5000
- 啟動指令: `python app.py`
- 依賴套件使用最新穩定版

#### Scenario: 啟動 API Server
- **GIVEN** 系統已安裝所需依賴
- **WHEN** 執行 `python app.py` 指令
- **THEN** Flask server 在 127.0.0.1:5000 啟動
- **AND** 可接收 HTTP 請求

---

### Requirement: MCP Server Integration
系統 SHALL 提供 MCP (Model Context Protocol) server，讓 AI agents 可以呼叫 API 功能。

MCP server 設定：
- 傳輸協定：HTTP
- 與 Flask API server 在同一進程中運行
- 使用同一個啟動指令 `python app.py`

MCP server 提供以下 tools：
- `list_parameter_specs`: 列出所有參數規格
- `add_parameter_spec`: 新增參數規格

#### Scenario: MCP 列出參數規格
- **GIVEN** MCP server 正在運行
- **WHEN** agent 呼叫 list_parameter_specs tool
- **THEN** 回傳所有參數規格數據

#### Scenario: MCP 新增參數規格
- **GIVEN** MCP server 正在運行
- **AND** agent 提供有效的參數規格數據
- **WHEN** agent 呼叫 add_parameter_spec tool
- **THEN** 新增參數規格並回傳結果

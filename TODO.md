# EQP Parameter Spec API - 完成歸檔

## ✅ 已完成功能

### REST API
- [x] GET /api/parameter-specs - 列出所有參數規格
- [x] POST /api/parameter-specs - 新增參數規格
- [x] Swagger UI (/docs/)
- [x] 資料驗證 (必填欄位、數值關係、長度限制)
- [x] CSV 資料儲存

### MCP 整合
- [x] MCP HTTP 端點 (/mcp) - 與 API server 同時運行
- [x] MCP stdio 模式 (--mcp 參數)
- [x] list_parameter_specs 工具
- [x] add_parameter_spec 工具

### MCP Resources (2026-01-03 新增)
- [x] api-docs://openapi - 完整 OpenAPI 規格
- [x] api-docs://summary - 自然語言 API 摘要
- [x] api-docs://endpoints - 端點詳細規格
- [x] api-docs://examples - 請求/回應範例

### 測試
- [x] BDD 測試 (19 個測試案例全部通過)
- [x] HTML 測試報告 (test_report.html)

### 文件
- [x] README.md 更新
- [x] VS Code MCP 設定說明
- [x] OpenAPI 規格 (static/openapi.yaml)

## 啟動方式

```bash
# REST API + MCP HTTP (port 5001)
python3 app.py

# MCP stdio 模式
python3 app.py --mcp
```

## 端點

- REST API: http://127.0.0.1:5001/api/parameter-specs
- MCP HTTP: http://127.0.0.1:5001/mcp
- Swagger UI: http://127.0.0.1:5001/docs/
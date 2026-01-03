"""
BDD-style API tests for EQP Parameter Spec API.

Uses pytest with Playwright for API testing following GIVEN-WHEN-THEN format.
"""

import pytest
import os
import shutil
from playwright.sync_api import APIRequestContext, Playwright

BASE_URL = "http://127.0.0.1:5001"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CSV_FILE = os.path.join(DATA_DIR, "parameter_specs.csv")


@pytest.fixture(scope="session")
def api_context(playwright: Playwright) -> APIRequestContext:
    """Create API request context for all tests."""
    context = playwright.request.new_context(base_url=BASE_URL)
    yield context
    context.dispose()


@pytest.fixture(autouse=True)
def clean_csv():
    """Clean CSV file before each test."""
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    yield
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)


class TestListParameterSpecs:
    """Tests for GET /api/parameter-specs endpoint."""

    def test_list_empty_when_csv_not_exists(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: CSV 檔案不存在
        GIVEN CSV 檔案不存在
        WHEN 客戶端發送 GET 請求到 /api/parameter-specs
        THEN 回應狀態碼為 200
        AND 回應內容為空 JSON 陣列 []
        """
        # GIVEN: CSV file does not exist (handled by fixture)
        assert not os.path.exists(CSV_FILE)

        # WHEN: Send GET request
        response = api_context.get("/api/parameter-specs")

        # THEN: Response is 200 with empty array
        assert response.status == 200
        assert response.json() == []

    def test_list_returns_all_specs(self, api_context: APIRequestContext):
        """
        Scenario: 成功列出所有參數規格
        GIVEN CSV 檔案中存在參數規格數據
        WHEN 客戶端發送 GET 請求到 /api/parameter-specs
        THEN 回應狀態碼為 200
        AND 回應內容為 JSON 陣列，包含所有參數規格
        """
        # GIVEN: Add a spec first
        api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data={
                "tool_name": "TOOL_A",
                "parameter_name": "temp",
                "usl": 100, "lsl": 0, "ucl": 90, "lcl": 10, "cl": 50
            }
        )

        # WHEN: Send GET request
        response = api_context.get("/api/parameter-specs")

        # THEN: Response contains the spec
        assert response.status == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["tool_name"] == "TOOL_A"
        assert data[0]["parameter_name"] == "temp"


class TestAddParameterSpec:
    """Tests for POST /api/parameter-specs endpoint."""

    def test_add_spec_success(self, api_context: APIRequestContext):
        """
        Scenario: 成功新增參數規格
        GIVEN 客戶端提供完整且有效的參數規格數據
        AND Content-Type 為 application/json
        AND tool_name + parameter_name 組合不存在於系統中
        AND 數值滿足 LSL < LCL < CL < UCL < USL
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 201
        AND 回應內容包含新建立的參數規格
        """
        # GIVEN: Valid data
        data = {
            "tool_name": "TOOL_A",
            "parameter_name": "temperature",
            "usl": 100.0,
            "lsl": 0.0,
            "ucl": 90.0,
            "lcl": 10.0,
            "cl": 50.0
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 201 with created spec
        assert response.status == 201
        result = response.json()
        assert result["tool_name"] == "TOOL_A"
        assert result["parameter_name"] == "temperature"
        assert result["usl"] == 100.0

    def test_add_spec_auto_round_decimals(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: 數值自動四捨五入到三位小數
        GIVEN 客戶端提供超過三位小數的數值
        WHEN 客戶端發送 POST 請求
        THEN 回應中的數值被四捨五入到三位小數
        """
        # GIVEN: Data with more than 3 decimal places
        data = {
            "tool_name": "TOOL_B",
            "parameter_name": "pressure",
            "usl": 100.12345,
            "lsl": 0.00001,
            "ucl": 90.5555,
            "lcl": 10.4444,
            "cl": 50.9999
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Values are rounded
        assert response.status == 201
        result = response.json()
        assert result["usl"] == 100.123
        assert result["lsl"] == 0.0
        assert result["cl"] == 51.0

    def test_add_spec_missing_field(self, api_context: APIRequestContext):
        """
        Scenario: 缺少必填欄位
        GIVEN 客戶端發送的請求缺少必填欄位
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 400
        AND 回應內容為 {"error": "Missing required field: <field_name>"}
        """
        # GIVEN: Missing tool_name
        data = {
            "parameter_name": "temp",
            "usl": 100, "lsl": 0, "ucl": 90, "lcl": 10, "cl": 50
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 400 with error message
        assert response.status == 400
        result = response.json()
        assert "Missing required field" in result["error"]

    def test_add_spec_empty_string_field(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: 字串欄位為空
        GIVEN 客戶端發送的請求中 tool_name 為空字串
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 400
        AND 回應內容包含 "Field cannot be empty"
        """
        # GIVEN: Empty tool_name
        data = {
            "tool_name": "   ",
            "parameter_name": "temp",
            "usl": 100, "lsl": 0, "ucl": 90, "lcl": 10, "cl": 50
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 400
        assert response.status == 400
        assert "cannot be empty" in response.json()["error"]

    def test_add_spec_field_exceeds_max_length(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: 字串欄位超過長度限制
        GIVEN 客戶端發送的請求中 tool_name 超過 100 字元
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 400
        AND 回應內容包含 "exceeds maximum length"
        """
        # GIVEN: tool_name exceeds 100 chars
        data = {
            "tool_name": "A" * 101,
            "parameter_name": "temp",
            "usl": 100, "lsl": 0, "ucl": 90, "lcl": 10, "cl": 50
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 400
        assert response.status == 400
        assert "exceeds maximum length" in response.json()["error"]

    def test_add_spec_invalid_number_format(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: 數值格式錯誤
        GIVEN 客戶端發送的請求中數值欄位非數字
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 400
        AND 回應內容包含 "Invalid number format"
        """
        # GIVEN: usl is not a number
        data = {
            "tool_name": "TOOL_A",
            "parameter_name": "temp",
            "usl": "not_a_number",
            "lsl": 0, "ucl": 90, "lcl": 10, "cl": 50
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 400
        assert response.status == 400
        assert "Invalid number format" in response.json()["error"]

    def test_add_spec_invalid_value_relationship(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: 數值邏輯關係錯誤
        GIVEN 客戶端發送的請求中數值不滿足 LSL < LCL < CL < UCL < USL
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 400
        AND 回應內容包含 "Invalid value relationship"
        """
        # GIVEN: USL < UCL (invalid)
        data = {
            "tool_name": "TOOL_A",
            "parameter_name": "temp",
            "usl": 50, "lsl": 0, "ucl": 90, "lcl": 10, "cl": 30
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 400
        assert response.status == 400
        assert "Invalid value relationship" in response.json()["error"]

    def test_add_spec_duplicate_key(self, api_context: APIRequestContext):
        """
        Scenario: 重複的唯一鍵
        GIVEN tool_name + parameter_name 組合已存在於系統中（不區分大小寫）
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 409
        AND 回應內容包含 "already exists"
        """
        # GIVEN: Add first spec
        data = {
            "tool_name": "TOOL_A",
            "parameter_name": "temp",
            "usl": 100, "lsl": 0, "ucl": 90, "lcl": 10, "cl": 50
        }
        api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # WHEN: Try to add duplicate (different case)
        data["tool_name"] = "tool_a"
        data["parameter_name"] = "TEMP"
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 409
        assert response.status == 409
        assert "already exists" in response.json()["error"]

    def test_add_spec_wrong_content_type(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: Content-Type 錯誤
        GIVEN 客戶端發送的請求 Content-Type 不是 application/json
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 415
        AND 回應內容包含 "Unsupported Media Type"
        """
        # WHEN: Send POST with wrong content type
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "text/plain"},
            data="some text"
        )

        # THEN: Response is 415
        assert response.status == 415
        assert "Unsupported Media Type" in response.json()["error"]

    def test_add_spec_invalid_json(self, api_context: APIRequestContext):
        """
        Scenario: JSON 格式錯誤
        GIVEN 客戶端發送的請求 Body 不是有效的 JSON 格式
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 回應狀態碼為 400
        AND 回應內容包含 "Invalid JSON format"
        
        Note: This test uses requests library since Playwright auto-serializes
        """
        import requests
        
        # WHEN: Send POST with invalid JSON
        response = requests.post(
            f"{BASE_URL}/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data="{invalid json}",
            timeout=5
        )

        # THEN: Response is 400
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["error"]

    def test_add_spec_ignores_extra_fields(
        self, api_context: APIRequestContext
    ):
        """
        Scenario: 忽略額外欄位
        GIVEN 客戶端發送的請求包含規格外的額外欄位
        WHEN 客戶端發送 POST 請求到 /api/parameter-specs
        THEN 系統忽略額外欄位
        AND 回應狀態碼為 201
        """
        # GIVEN: Data with extra field
        data = {
            "tool_name": "TOOL_A",
            "parameter_name": "temp",
            "usl": 100, "lsl": 0, "ucl": 90, "lcl": 10, "cl": 50,
            "extra_field": "should be ignored"
        }

        # WHEN: Send POST request
        response = api_context.post(
            "/api/parameter-specs",
            headers={"Content-Type": "application/json"},
            data=data
        )

        # THEN: Response is 201, extra field not in response
        assert response.status == 201
        result = response.json()
        assert "extra_field" not in result


class TestSwaggerUI:
    """Tests for Swagger UI endpoint."""

    def test_swagger_ui_accessible(self, api_context: APIRequestContext):
        """
        Scenario: 存取 Swagger UI
        GIVEN API 伺服器正在運行
        WHEN 使用者存取 /docs 路徑
        THEN 顯示 Swagger UI 介面
        """
        # WHEN: Access /docs
        response = api_context.get("/docs/")

        # THEN: Response is successful (200 or redirect)
        assert response.status in [200, 301, 302]


class TestMCPApiDocsResources:
    """
    Feature: MCP API Documentation Resources
    As an AI Agent
    I want to query API documentation through MCP
    So that I can understand how to use the REST API
    """

    @pytest.fixture
    def mcp_session(self, api_context: APIRequestContext) -> str:
        """Initialize MCP session and return session ID."""
        response = api_context.post(
            "/mcp/",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            data={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
        )
        session_id = response.headers.get("mcp-session-id")
        return session_id

    def test_list_api_docs_resources(
        self, api_context: APIRequestContext, mcp_session: str
    ):
        """
        Scenario: List all API documentation resources
        GIVEN MCP Server is running
        WHEN Agent calls resources/list method
        THEN Response contains all 4 api-docs resources
        """
        # WHEN: Call resources/list
        response = api_context.post(
            "/mcp/",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": mcp_session
            },
            data={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/list",
                "params": {}
            }
        )

        # THEN: Response contains all 4 resources
        assert response.status == 200
        text = response.text()
        assert "api-docs://openapi" in text
        assert "api-docs://summary" in text
        assert "api-docs://endpoints" in text
        assert "api-docs://examples" in text

    def test_read_openapi_resource(
        self, api_context: APIRequestContext, mcp_session: str
    ):
        """
        Scenario: Read OpenAPI specification resource
        GIVEN MCP Server is running
        WHEN Agent calls resources/read for api-docs://openapi
        THEN Server returns the OpenAPI YAML content
        """
        # WHEN: Read openapi resource
        response = api_context.post(
            "/mcp/",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": mcp_session
            },
            data={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": {"uri": "api-docs://openapi"}
            }
        )

        # THEN: Response contains OpenAPI spec
        assert response.status == 200
        text = response.text()
        assert "openapi:" in text or "OpenAPI" in text

    def test_read_summary_resource(
        self, api_context: APIRequestContext, mcp_session: str
    ):
        """
        Scenario: Read API summary resource
        GIVEN MCP Server is running
        WHEN Agent calls resources/read for api-docs://summary
        THEN Server returns Markdown summary with API and MCP tools info
        """
        # WHEN: Read summary resource
        response = api_context.post(
            "/mcp/",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": mcp_session
            },
            data={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "api-docs://summary"}
            }
        )

        # THEN: Response contains summary with required sections
        assert response.status == 200
        text = response.text()
        assert "REST API" in text
        assert "MCP Tools" in text
        assert "Authentication" in text
        assert "Error Handling" in text
        assert "list_parameter_specs" in text
        assert "add_parameter_spec" in text

    def test_read_endpoints_resource(
        self, api_context: APIRequestContext, mcp_session: str
    ):
        """
        Scenario: Read endpoints specification resource
        GIVEN MCP Server is running
        WHEN Agent calls resources/read for api-docs://endpoints
        THEN Server returns detailed endpoint specifications
        """
        # WHEN: Read endpoints resource
        response = api_context.post(
            "/mcp/",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": mcp_session
            },
            data={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "resources/read",
                "params": {"uri": "api-docs://endpoints"}
            }
        )

        # THEN: Response contains endpoint specifications
        assert response.status == 200
        text = response.text()
        assert "GET /api/parameter-specs" in text
        assert "POST /api/parameter-specs" in text
        assert "Validation Rules" in text

    def test_read_examples_resource(
        self, api_context: APIRequestContext, mcp_session: str
    ):
        """
        Scenario: Read API examples resource
        GIVEN MCP Server is running
        WHEN Agent calls resources/read for api-docs://examples
        THEN Server returns request/response examples in Markdown
        """
        # WHEN: Read examples resource
        response = api_context.post(
            "/mcp/",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": mcp_session
            },
            data={
                "jsonrpc": "2.0",
                "id": 6,
                "method": "resources/read",
                "params": {"uri": "api-docs://examples"}
            }
        )

        # THEN: Response contains examples
        assert response.status == 200
        text = response.text()
        assert "Success Request" in text
        assert "Success Response" in text
        assert "Error Examples" in text
        assert "tool_name" in text

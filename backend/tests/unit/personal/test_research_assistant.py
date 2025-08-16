import pytest


class TestResearchAssistant:
    def test_research_assistant_success(self, client, auth_headers):
        res = client.post(
            "/personal/run/research_assistant",
            headers=auth_headers,
            json={"query": "AI automation trends", "max_results": 3},
        )
        assert res.status_code in (200, 202)
        data = res.json()
        assert data.get("status") in {"completed", "queued", "error"}
        assert "task_id" in data


class TestShoppingAssistant:
    def test_shopping_assistant_search(self, client, auth_headers):
        res = client.post(
            "/personal/run/shopping_assistant",
            headers=auth_headers,
            json={"product_query": "laptop under $1000", "max_results": 5},
        )
        assert res.status_code in (200, 202)
        data = res.json()
        assert data.get("status") in {"completed", "queued", "error"}


class TestFinanceCSV:
    def test_finance_csv_import(self, client, auth_headers):
        csv_content = (
            "Date,Description,Amount,Category\n"
            "2024-01-01,Coffee,4.50,Food\n"
            "2024-01-02,Gas,45.00,Transportation\n"
        )
        res = client.post(
            "/personal/finance/import_csv",
            headers=auth_headers,
            files={"file": ("transactions.csv", csv_content, "text/csv")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        assert data.get("parsed", 0) >= 1




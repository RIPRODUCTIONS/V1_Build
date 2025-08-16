import pytest


class TestAutomationFlows:
    def test_research_then_shopping_then_finance(self, client, auth_headers):
        r1 = client.post(
            "/personal/run/research_assistant",
            headers=auth_headers,
            json={"query": "AI automation", "max_results": 3},
        )
        assert r1.status_code in (200, 202)

        r2 = client.post(
            "/personal/run/shopping_assistant",
            headers=auth_headers,
            json={"product_query": "laptop", "max_results": 5},
        )
        assert r2.status_code in (200, 202)

        csv_content = (
            "Date,Description,Amount,Category\n"
            "2024-01-01,Coffee,4.50,Food\n"
            "2024-01-02,Gas,45.00,Transportation\n"
        )
        r3 = client.post(
            "/personal/finance/import_csv",
            headers=auth_headers,
            files={"file": ("transactions.csv", csv_content, "text/csv")},
        )
        assert r3.status_code == 200




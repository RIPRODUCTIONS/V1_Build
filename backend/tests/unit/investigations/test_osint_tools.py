import pytest


class TestOSINTDossier:
    def test_osint_dossier_basic(self, client, auth_headers):
        res = client.post(
            "/investigations/osint/run",
            headers=auth_headers,
            json={"subject": {"name": "Jane Doe"}},
        )
        assert res.status_code in (200, 202)
        data = res.json()
        assert data.get("status") in {"queued", "completed", "error"}


class TestMalwareAnalysis:
    def test_malware_dynamic_skeleton(self, client, auth_headers):
        res = client.post(
            "/investigations/malware/dynamic/run",
            headers=auth_headers,
            json={"sample": "test.exe"},
        )
        assert res.status_code in (200, 202)
        data = res.json()
        assert data.get("status") in {"queued", "completed", "error"}


class TestForensicsTimeline:
    def test_forensics_timeline_skeleton(self, client, auth_headers):
        res = client.post(
            "/investigations/forensics/timeline/run",
            headers=auth_headers,
            json={"source": "image.dd"},
        )
        assert res.status_code in (200, 202)
        data = res.json()
        assert data.get("status") in {"queued", "completed", "error"}




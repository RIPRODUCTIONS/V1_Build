# ruff: noqa: I001
import asyncio
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.automation.skills.ideation import (
    generate_ideas,
    research_validate_ideas,
    market_analysis,
    _generate_base_ideas,
    _calculate_opportunity_score,
)


client = TestClient(app)


class TestIdeaEngineSkills:
    """Test the Idea Engine skills in isolation"""

    @pytest.mark.asyncio
    async def test_generate_base_ideas(self):
        """Test base idea generation"""
        ideas = _generate_base_ideas("test topic", 3)
        assert len(ideas) == 3
        assert all("title" in idea for idea in ideas)
        assert all("description" in idea for idea in ideas)
        assert all("category" in idea for idea in ideas)
        assert all("complexity" in idea for idea in ideas)
        assert all("market_size" in idea for idea in ideas)
        assert all("time_to_market" in idea for idea in ideas)

    @pytest.mark.asyncio
    async def test_calculate_opportunity_score(self):
        """Test opportunity score calculation"""
        idea = {
            "market_sentiment": {"score": 0.8},
            "trend_data": {"trend_score": 75},
            "market_size": "Large",
            "complexity": "Medium",
        }
        score = _calculate_opportunity_score(idea)
        assert 0 <= score <= 1
        assert isinstance(score, float)

    @pytest.mark.asyncio
    async def test_generate_ideas_skill(self):
        """Test the generate_ideas skill"""
        context = {"topic": "test automation", "count": 3, "include_research": False}
        result = await generate_ideas(context)

        assert "ideas" in result
        assert len(result["ideas"]) == 3
        assert result["research_included"] is False
        assert all("title" in idea for idea in result["ideas"])

    @pytest.mark.asyncio
    async def test_research_validate_ideas_skill(self):
        """Test the research_validate_ideas skill"""
        # First generate ideas
        context = {"topic": "test automation", "count": 3, "include_research": True}
        context = await generate_ideas(context)

        # Then validate them
        result = await research_validate_ideas(context)

        assert "validated_ideas" in result
        assert "top_opportunities" in result
        assert "research_timestamp" in result
        assert len(result["validated_ideas"]) == 3
        assert len(result["top_opportunities"]) == 3

        # Check that ideas are sorted by validation score
        scores = [idea.get("validation_score", 0) for idea in result["validated_ideas"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_market_analysis_skill(self):
        """Test the market_analysis skill"""
        # First generate and validate ideas
        context = {"topic": "test automation", "count": 3, "include_research": True}
        context = await generate_ideas(context)
        context = await research_validate_ideas(context)

        # Then perform market analysis
        result = await market_analysis(context)

        assert "market_analysis" in result
        assert "analysis_timestamp" in result
        assert "next_steps" in result
        assert len(result["market_analysis"]) == 3
        assert len(result["next_steps"]) > 0

        # Check market analysis structure
        for analysis in result["market_analysis"]:
            assert "idea_id" in analysis
            assert "title" in analysis
            assert "market_analysis" in analysis
            assert "technical_analysis" in analysis
            assert "business_model" in analysis


class TestIdeaEngineAPI:
    """Test the Idea Engine through the API"""

    def test_submit_idea_generation(self):
        """Test submitting idea generation through API"""
        response = client.post(
            "/automation/submit",
            json={
                "intent": "ideation.generate",
                "payload": {"topic": "test automation", "count": 3, "include_research": True},
                "idempotency_key": "test-idea-1",
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert "run_id" in result

        # Wait for completion
        run_id = result["run_id"]
        status = None
        for _ in range(20):
            status_response = client.get(f"/automation/runs/{run_id}")
            status = status_response.json()
            if status["status"] in ("succeeded", "failed"):
                break
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))

        assert status is not None
        assert status["status"] == "succeeded"
        assert "detail" in status
        assert "result" in status["detail"]
        assert "ideas" in status["detail"]["result"]

    def test_submit_full_pipeline(self):
        """Test submitting the full ideation pipeline through API"""
        response = client.post(
            "/automation/submit",
            json={
                "intent": "ideation.full_pipeline",
                "payload": {"topic": "test automation", "count": 3, "include_research": True},
                "idempotency_key": "test-pipeline-1",
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert "run_id" in result

        # Wait for completion
        run_id = result["run_id"]
        status = None
        for _ in range(30):  # Full pipeline takes longer
            status_response = client.get(f"/automation/runs/{run_id}")
            status = status_response.json()
            if status["status"] in ("succeeded", "failed"):
                break
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))

        assert status is not None
        assert status["status"] == "succeeded"
        assert "detail" in status
        assert "result" in status["detail"]

        # Check that all pipeline stages completed
        result = status["detail"]["result"]
        assert "ideas" in result
        assert "validated_ideas" in result
        assert "market_analysis" in result
        assert "next_steps" in result


class TestIdeaEngineIntegration:
    """Test the Idea Engine integration with the orchestrator"""

    def test_ideation_dag_registration(self):
        """Test that ideation DAGs are properly registered"""
        from app.automation.orchestrator import get_dag

        # Check that ideation DAGs exist
        generate_dag = get_dag("ideation.generate")
        full_pipeline_dag = get_dag("ideation.full_pipeline")

        assert generate_dag is not None
        assert full_pipeline_dag is not None
        assert "ideation.generate" in generate_dag
        assert "ideation.generate" in full_pipeline_dag
        assert "ideation.research_validate" in full_pipeline_dag
        assert "ideation.market_analysis" in full_pipeline_dag

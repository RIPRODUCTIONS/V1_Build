from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.automation.registry import skill
from app.obs.metrics import (
    AI_DEPARTMENT_LATENCY,
    AI_DEPARTMENT_RUNS,
)

logger = logging.getLogger(__name__)

# External API configurations (graceful fallbacks if no keys)
EXTERNAL_APIS = {
    'google_trends': 'https://trends.google.com/trends/api/dailytrends',
    'reddit': 'https://www.reddit.com/r/entrepreneur/hot.json',
    'crunchbase': 'https://api.crunchbase.com/v3.1/',
    'web_search': 'https://serpapi.com/search',
}

# Market size constants for scoring
TAM_10B = 10_000_000_000  # $10 billion
TAM_1B = 1_000_000_000  # $1 billion
TAM_100M = 100_000_000  # $100 million

# Competition thresholds
HIGH_COMPETITION_THRESHOLD = 20
MEDIUM_COMPETITION_THRESHOLD = 10

# Scoring thresholds
PROCEED_SCORE_THRESHOLD = 80
PROTOTYPE_SCORE_THRESHOLD = 60
WATCHLIST_SCORE_THRESHOLD = 40
STRONG_TREND_THRESHOLD = 70
POSITIVE_SENTIMENT_THRESHOLD = 0.3


@skill('research.validate_idea')
async def validate_idea(context: dict[str, Any]) -> dict[str, Any]:
    """Validate business idea using external data sources and AI analysis."""
    start_time = time.time()

    # Extract inputs
    idea = context.get('idea', {})
    correlation_id = context.get('correlation_id', 'unknown')
    run_id = context.get('run_id', 'unknown')

    if not idea:
        raise ValueError('No idea provided for validation')

    try:
        # Phase 1: Trend Analysis
        trend_score = await _analyze_trends(idea)

        # Phase 2: Sentiment Analysis
        sentiment_data = await _analyze_sentiment(idea)

        # Phase 3: Market Size Estimation
        market_size = await _estimate_market_size(idea)

        # Phase 4: Competition Analysis
        competition = await _analyze_competition(idea)

        # Phase 5: Risk Assessment
        risks = await _assess_risks(idea, competition, market_size)

        # Phase 6: Generate Recommendations
        recommended_action, explanations = await _generate_recommendations(
            trend_score, sentiment_data, competition, risks, market_size
        )

        # Create validation artifact
        validation_result = {
            'idea': idea,
            'trend_score': trend_score,
            'sentiment': sentiment_data,
            'market_size': market_size,
            'competition': competition,
            'risk': risks,
            'recommended_action': recommended_action,
            'explanations': explanations,
            'validation_timestamp': datetime.now(UTC).isoformat(),
            'correlation_id': correlation_id,
            'run_id': run_id,
        }

        # Record metrics
        execution_time = time.time() - start_time
        AI_DEPARTMENT_RUNS.labels(department='research', status='success').inc()

        AI_DEPARTMENT_LATENCY.labels(department='research').observe(execution_time)

        return {
            **context,
            'validation_result': validation_result,
            'status': 'completed',
            'artifacts': [
                {'kind': 'research_validation', 'content': validation_result, 'format': 'json'}
            ],
        }

    except Exception as e:
        logger.error(f'Research validation failed: {str(e)}')

        # Record failure metrics
        AI_DEPARTMENT_RUNS.labels(department='research', status='failed').inc()

        return {**context, 'error': str(e), 'status': 'failed'}


async def _analyze_trends(idea: dict[str, Any]) -> int:
    """Analyze trend data for the idea (0-100 score)."""
    try:
        # Mock trend analysis - in production, call Google Trends API
        # For now, simulate based on idea keywords
        keywords = idea.get('title', '').lower()

        # Simple keyword-based scoring
        trend_keywords = ['ai', 'automation', 'saas', 'mobile', 'blockchain', 'fintech']
        score = 50  # Base score

        for keyword in trend_keywords:
            if keyword in keywords:
                score += 10

        return min(100, max(0, score))
    except Exception as e:
        logger.warning(f'Trend analysis failed: {e}')
        return 50  # Default neutral score


async def _analyze_sentiment(idea: dict[str, Any]) -> dict[str, Any]:
    """Analyze sentiment from social media and forums."""
    try:
        # Mock sentiment analysis - in production, call Reddit API, Twitter, etc.
        # For now, simulate based on idea characteristics
        title = idea.get('title', '').lower()

        # Simple sentiment scoring
        positive_words = ['innovative', 'efficient', 'sustainable', 'secure', 'fast']
        negative_words = ['complex', 'expensive', 'slow', 'risky', 'difficult']

        positive_count = sum(1 for word in positive_words if word in title)
        negative_count = sum(1 for word in negative_words if word in title)

        if positive_count == 0 and negative_count == 0:
            sentiment_avg = 0.0
        else:
            sentiment_avg = (positive_count - negative_count) / max(
                positive_count + negative_count, 1
            )

        return {
            'avg': max(-1.0, min(1.0, sentiment_avg)),
            'n': positive_count + negative_count,
            'positive_count': positive_count,
            'negative_count': negative_count,
        }
    except Exception as e:
        logger.warning(f'Sentiment analysis failed: {e}')
        return {'avg': 0.0, 'n': 0, 'positive_count': 0, 'negative_count': 0}


async def _estimate_market_size(idea: dict[str, Any]) -> dict[str, Any]:
    """Estimate market size (TAM, SAM, SOM)."""
    try:
        # Mock market size estimation - in production, call industry reports, Crunchbase, etc.
        industry = idea.get('industry', 'technology').lower()

        # Simple industry-based estimation
        market_sizes = {
            'technology': {'tam': TAM_1B, 'sam': TAM_100M, 'notes': 'Growing tech sector'},
            'healthcare': {'tam': TAM_10B, 'sam': TAM_1B, 'notes': 'Large healthcare market'},
            'finance': {'tam': TAM_10B, 'sam': TAM_1B, 'notes': 'Established financial sector'},
            'retail': {'tam': TAM_1B, 'sam': TAM_100M, 'notes': 'Competitive retail space'},
            'education': {'tam': TAM_100M, 'sam': TAM_100M, 'notes': 'Niche education market'},
        }

        return market_sizes.get(
            industry, {'tam': TAM_100M, 'sam': TAM_100M, 'notes': 'General market estimation'}
        )
    except Exception as e:
        logger.warning(f'Market size estimation failed: {e}')
        return {'tam': None, 'sam': None, 'notes': 'Estimation failed'}


async def _analyze_competition(idea: dict[str, Any]) -> dict[str, Any]:
    """Analyze competitive landscape."""
    try:
        # Mock competition analysis - in production, call Crunchbase, web search, etc.
        title = idea.get('title', '').lower()

        # Simple competition estimation based on idea type
        if 'ai' in title or 'automation' in title:
            competition_count = 15
            top_competitors = [
                {'name': 'OpenAI', 'url': 'https://openai.com'},
                {'name': 'Anthropic', 'url': 'https://anthropic.com'},
                {'name': 'Google AI', 'url': 'https://ai.google'},
            ]
        elif 'saas' in title or 'platform' in title:
            competition_count = 25
            top_competitors = [
                {'name': 'Salesforce', 'url': 'https://salesforce.com'},
                {'name': 'HubSpot', 'url': 'https://hubspot.com'},
                {'name': 'Notion', 'url': 'https://notion.so'},
            ]
        else:
            competition_count = 10
            top_competitors = [{'name': 'General Competitor', 'url': '#'}]

        return {
            'count': competition_count,
            'top': top_competitors,
            'market_saturation': (
                'high'
                if competition_count > HIGH_COMPETITION_THRESHOLD
                else 'medium'
                if competition_count > MEDIUM_COMPETITION_THRESHOLD
                else 'low'
            ),
        }
    except Exception as e:
        logger.warning(f'Competition analysis failed: {e}')
        return {'count': 0, 'top': [], 'market_saturation': 'unknown'}


async def _assess_risks(
    idea: dict[str, Any], competition: dict[str, Any], market_size: dict[str, Any]
) -> list[dict[str, Any]]:
    """Assess various risk factors."""
    risks = []

    try:
        # Market risk
        if competition.get('count', 0) > HIGH_COMPETITION_THRESHOLD:
            risks.append(
                {
                    'type': 'market',
                    'level': 'high',
                    'note': 'Highly competitive market with many established players',
                }
            )
        elif competition.get('count', 0) > MEDIUM_COMPETITION_THRESHOLD:
            risks.append(
                {
                    'type': 'market',
                    'level': 'medium',
                    'note': 'Moderate competition in established market',
                }
            )

        # Technology risk
        if 'ai' in idea.get('title', '').lower():
            risks.append(
                {
                    'type': 'tech',
                    'level': 'medium',
                    'note': 'AI technology rapidly evolving, risk of obsolescence',
                }
            )

        # Regulatory risk
        if (
            'finance' in idea.get('industry', '').lower()
            or 'healthcare' in idea.get('industry', '').lower()
        ):
            risks.append(
                {
                    'type': 'regulatory',
                    'level': 'high',
                    'note': 'Heavily regulated industry with compliance requirements',
                }
            )

        # Operational risk
        if not risks:  # If no specific risks identified
            risks.append(
                {
                    'type': 'ops',
                    'level': 'low',
                    'note': 'Standard operational risks for new business',
                }
            )

    except Exception as e:
        logger.warning(f'Risk assessment failed: {e}')
        risks.append({'type': 'unknown', 'level': 'medium', 'note': 'Risk assessment failed'})

    return risks


async def _generate_recommendations(
    trend_score: int,
    sentiment_data: dict[str, Any],
    competition: dict[str, Any],
    risks: list[dict[str, Any]],
    market_size: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    """Generate action recommendations based on analysis."""
    explanations = []

    # Calculate composite score
    sentiment_score = (sentiment_data.get('avg', 0) + 1) * 50  # Convert -1..1 to 0..100
    competition_score = max(0, 100 - (competition.get('count', 0) * 2))  # Inverse relationship
    market_score = 50  # Default market score

    if market_size.get('tam'):
        if market_size['tam'] >= TAM_10B:
            market_score = 90
        elif market_size['tam'] >= TAM_1B:
            market_score = 70
        elif market_size['tam'] >= TAM_100M:
            market_score = 50
        else:
            market_score = 30

    # Weighted composite score
    composite_score = (
        trend_score * 0.5 + sentiment_score * 0.2 + competition_score * 0.2 + market_score * 0.1
    )

    # Determine recommended action
    if composite_score >= PROCEED_SCORE_THRESHOLD:
        recommended_action = 'proceed'
        explanations.append(
            {
                'title': 'High Opportunity Score',
                'detail': f'Composite score of {composite_score:.1f}/100 indicates strong market opportunity',
            }
        )
    elif composite_score >= PROTOTYPE_SCORE_THRESHOLD:
        recommended_action = 'prototype'
        explanations.append(
            {
                'title': 'Moderate Opportunity Score',
                'detail': f'Composite score of {composite_score:.1f}/100 suggests prototyping to validate assumptions',
            }
        )
    elif composite_score >= WATCHLIST_SCORE_THRESHOLD:
        recommended_action = 'watchlist'
        explanations.append(
            {
                'title': 'Low Opportunity Score',
                'detail': f'Composite score of {composite_score:.1f}/100 suggests monitoring market changes',
            }
        )
    else:
        recommended_action = 'drop'
        explanations.append(
            {
                'title': 'Poor Opportunity Score',
                'detail': f'Composite score of {composite_score:.1f}/100 indicates low market potential',
            }
        )

    # Add specific explanations
    if trend_score >= STRONG_TREND_THRESHOLD:
        explanations.append(
            {
                'title': 'Strong Trend Alignment',
                'detail': f'Trend score of {trend_score}/100 shows good market timing',
            }
        )

    if sentiment_data.get('avg', 0) > POSITIVE_SENTIMENT_THRESHOLD:
        explanations.append(
            {
                'title': 'Positive Market Sentiment',
                'detail': 'Market sentiment analysis shows positive reception',
            }
        )

    if competition.get('count', 0) < MEDIUM_COMPETITION_THRESHOLD:
        explanations.append(
            {
                'title': 'Low Competition',
                'detail': f'Only {competition["count"]} competitors identified, good market positioning opportunity',
            }
        )

    # Add risk-based explanations
    high_risks = [r for r in risks if r.get('level') == 'high']
    if high_risks:
        explanations.append(
            {
                'title': 'High Risk Factors',
                'detail': f'Identified {len(high_risks)} high-risk factors requiring mitigation',
            }
        )

    return recommended_action, explanations

# Research Department

## Overview

The Research Department is responsible for validating business ideas using market research,
sentiment analysis, and competitive intelligence. It takes outputs from the Idea Engine and provides
comprehensive validation with actionable recommendations.

## Architecture

### Core Components

1. **Research Validation Skill** (`research.validate_idea`)

   - Input: Business idea (JSON or run_id reference)
   - Output: Validation report with scoring and recommendations
   - Metrics: Execution time, success/failure rates

2. **External Data Sources**

   - Google Trends API (trend analysis)
   - Reddit API (sentiment analysis)
   - Crunchbase API (competitive landscape)
   - Web search (market intelligence)

3. **Validation Pipeline**
   - Trend Analysis (0-100 score)
   - Sentiment Analysis (-1 to +1 scale)
   - Market Size Estimation (TAM/SAM)
   - Competition Analysis
   - Risk Assessment
   - Action Recommendations

## API Endpoints

### POST /research/validate

Start a new idea validation run.

**Request Body:**

```json
{
  "idea": {
    "title": "AI-powered business automation",
    "description": "Automated business processes using AI",
    "industry": "technology"
  }
}
```

**Or reference existing run:**

```json
{
  "run_id": "uuid-from-idea-engine"
}
```

**Response:**

```json
{
  "run_id": "validation-run-uuid",
  "status": "started",
  "correlation_id": "research_validate_timestamp",
  "message": "Idea validation started successfully"
}
```

**Required Scope:** `research.run`

### GET /research/validations

Get paginated list of validations with filters.

**Query Parameters:**

- `min_trend`: Minimum trend score (0-100)
- `min_sentiment`: Minimum sentiment (-1.0 to 1.0)
- `competition_max`: Maximum competition count
- `action`: Filter by recommended action
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**Response:**

```json
{
  "validations": [
    {
      "run_id": "uuid",
      "status": "completed",
      "created_at": "2025-01-01T00:00:00Z",
      "correlation_id": "research_validate_timestamp",
      "validation_result": {
        "idea": {...},
        "trend_score": 75,
        "sentiment": {"avg": 0.6, "n": 5},
        "market_size": {"tam": 1000000000, "sam": 100000000},
        "competition": {"count": 12, "market_saturation": "medium"},
        "risk": [...],
        "recommended_action": "prototype",
        "explanations": [...]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "pages": 3
  }
}
```

**Required Scope:** `research.read`

## Validation Output Schema

### Trend Score (0-100)

- **90-100**: Exceptional trend alignment
- **70-89**: Strong trend alignment
- **50-69**: Moderate trend alignment
- **30-49**: Weak trend alignment
- **0-29**: Poor trend alignment

### Sentiment Analysis

- **Range**: -1.0 (very negative) to +1.0 (very positive)
- **Sample Size**: Number of sentiment sources analyzed
- **Positive/Negative Counts**: Raw sentiment indicators

### Market Size

- **TAM**: Total Addressable Market (in USD)
- **SAM**: Serviceable Addressable Market (in USD)
- **Notes**: Market characteristics and growth indicators

### Competition Analysis

- **Count**: Number of identified competitors
- **Top Competitors**: List of major players with URLs
- **Market Saturation**: low/medium/high based on competition density

### Risk Assessment

- **Types**: market, tech, regulatory, ops, unknown
- **Levels**: low, medium, high
- **Notes**: Specific risk descriptions and mitigation suggestions

### Recommended Actions

- **proceed**: High opportunity, low risk
- **prototype**: Good opportunity, moderate risk
- **watchlist**: Moderate opportunity, high risk
- **drop**: Low opportunity, high risk

## Scoring Algorithm

### Composite Score Calculation

```
Composite Score = (Trend × 0.5) + (Sentiment × 0.2) + (Competition × 0.2) + (Market × 0.1)
```

Where:

- **Trend**: Raw trend score (0-100)
- **Sentiment**: (sentiment_avg + 1) × 50 (converts -1..1 to 0..100)
- **Competition**: max(0, 100 - competition_count × 2) (inverse relationship)
- **Market**: Based on TAM size (10B+ = 90, 1B+ = 70, 100M+ = 50, <100M = 30)

### Action Thresholds

- **proceed**: Composite score ≥ 80
- **prototype**: Composite score 60-79
- **watchlist**: Composite score 40-59
- **drop**: Composite score < 40

## Integration with Idea Engine

### Full Pipeline Flow

1. **Idea Generation**: Idea Engine creates business ideas
2. **Event Trigger**: `run.completed` event with `ideation.generate` intent
3. **Research Validation**: Automatically triggered for each idea
4. **Artifact Storage**: Validation results stored as `research_validation` artifacts
5. **UI Updates**: Research page shows validation results

### Manual Triggering

- Use "Run Full Pipeline" button in Business page
- Paste idea JSON directly in Research page
- Reference existing Idea Engine run by ID

## Error Handling

### Graceful Degradation

- **Missing API Keys**: Fall back to simulated data
- **API Rate Limits**: Implement exponential backoff
- **Network Failures**: Retry with increasing delays
- **Invalid Inputs**: Return detailed error messages

### Retry Policies

- **Transient Failures**: Retry up to 3 times
- **Backoff Strategy**: Exponential backoff (1s, 2s, 4s)
- **Dead Letter Queue**: Failed validations sent to DLQ for manual review

## Monitoring & Metrics

### Prometheus Metrics

- `ai_department_runs_total{department="research", status}`
- `ai_department_latency_seconds{department="research"}`
- `ai_department_token_usage_total{department="research", model}`

### Key Performance Indicators

- **Validation Success Rate**: Target > 95%
- **Average Processing Time**: Target < 30 seconds
- **External API Success Rate**: Target > 90%
- **User Satisfaction**: Based on action recommendation accuracy

## Configuration

### Environment Variables

```bash
# External API Keys
CRUNCHBASE_API_KEY=your_key
REDDIT_CLIENT_ID=your_client_id
REDDIT_SECRET=your_secret
SERP_API_KEY=your_key

# Rate Limiting
RESEARCH_API_RATE_LIMIT=100  # requests per hour
RESEARCH_RETRY_ATTEMPTS=3
RESEARCH_BACKOFF_BASE=1      # seconds
```

### Feature Flags

- `ENABLE_EXTERNAL_APIS`: Toggle external API usage
- `ENABLE_SENTIMENT_ANALYSIS`: Toggle sentiment analysis
- `ENABLE_COMPETITION_ANALYSIS`: Toggle competition analysis
- `ENABLE_RISK_ASSESSMENT`: Toggle risk assessment

## Usage Examples

### Basic Validation

```bash
curl -X POST http://localhost:8080/research/validate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "idea": {
      "title": "AI-powered business automation",
      "description": "Automated business processes using AI",
      "industry": "technology"
    }
  }'
```

### Filter Validations

```bash
curl "http://localhost:8080/research/validations?min_trend=70&action=proceed" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Troubleshooting

### Common Issues

1. **Validation Failing**

   - Check external API keys and rate limits
   - Verify Redis connectivity
   - Review application logs for errors

2. **Slow Performance**

   - Monitor external API response times
   - Check Redis performance
   - Review validation complexity

3. **Inaccurate Results**
   - Verify external API data quality
   - Check scoring algorithm parameters
   - Review fallback logic for missing data

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG
```

This will show detailed validation steps and external API responses.

## Future Enhancements

### Planned Features

- **Machine Learning Scoring**: Train models on historical validation data
- **Industry-Specific Analysis**: Custom validation logic per industry
- **Real-time Market Data**: Live market trend integration
- **Competitive Intelligence**: Automated competitor monitoring
- **Risk Prediction**: ML-based risk assessment models

### Integration Roadmap

- **Financial Modeling**: Revenue and cost projections
- **Technical Feasibility**: Development complexity assessment
- **Regulatory Compliance**: Industry-specific compliance checks
- **Market Timing**: Optimal launch window recommendations

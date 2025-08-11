# Configuration Guide

## Environment Variables

The AI Business Engine can be configured using environment variables. Create a `.env` file in the `backend/` directory with the following settings:

### Core Configuration

```bash
# Database
DATABASE_URL=sqlite:///./ai_business_engine.db
# For production: postgresql://user:password@localhost/dbname

# Security
JWT_SECRET=your-super-secret-jwt-key-here
SECURE_MODE=true
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379
```

### External API Keys (Optional)

These keys enable enhanced features but are not required for basic operation:

```bash
# Market Research APIs
CRUNCHBASE_API_KEY=your_crunchbase_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_SECRET=your_reddit_secret
SERP_API_KEY=your_serp_api_key
GOOGLE_TRENDS_API_KEY=your_google_trends_key

# LLM Providers
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
LMSTUDIO_BASE_URL=http://localhost:1234/v1
```

### Autonomous Mode

Enable fully autonomous operation of the AI Business Engine:

```bash
# Autonomous Mode
AUTONOMOUS_MODE=true
NOTIFY_EMAIL_TO=your-email@example.com

# Email Configuration (if using SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Feature Degradation

When external API keys are not provided:

- **Google Trends**: Falls back to keyword-based trend scoring
- **Reddit Sentiment**: Falls back to text analysis of idea descriptions
- **Crunchbase**: Falls back to industry-based market size estimation
- **Web Search**: Falls back to simulated competitive analysis
- **Email Notifications**: Disabled (autonomous mode still works)

## Security Considerations

- **JWT_SECRET**: Use a strong, random string for production
- **SECURE_MODE**: When enabled, enforces authentication on all routes
- **API Keys**: Store securely and rotate regularly
- **Database**: Use strong passwords and limit network access

## Production Deployment

For production environments:

1. Use PostgreSQL instead of SQLite
2. Enable Redis persistence
3. Set up proper SSL/TLS certificates
4. Configure firewall rules
5. Set up monitoring and alerting
6. Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)

## Example .env File

```bash
# Production Example
DATABASE_URL=postgresql://user:pass@localhost/ai_business_engine
JWT_SECRET=your-256-bit-random-secret-key
SECURE_MODE=true
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379

# External APIs
CRUNCHBASE_API_KEY=your_key_here
REDDIT_CLIENT_ID=your_client_id
REDDIT_SECRET=your_secret
SERP_API_KEY=your_serp_key

# Autonomous Mode
AUTONOMOUS_MODE=true
NOTIFY_EMAIL_TO=admin@yourcompany.com

# LLM
ANTHROPIC_API_KEY=your_anthropic_key
```

# Legitimate Background Research System

A comprehensive, **legal**, and **ethical** system for conducting background research using publicly available information and legitimate services.

## 🎯 Core Principles

- **Only use publicly available information**
- **Respect privacy laws and terms of service**
- **Have legitimate business purposes**
- **Provide transparency and opt-out options**
- **Follow all applicable regulations (FCRA, GDPR, etc.)**

## 🚀 Features

### Comprehensive Data Sources
- **Public Records**: Court records, property records, business registrations, professional licenses
- **Commercial Services**: Spokeo, WhitePages, BeenVerified, Intelius, PeopleFinders
- **Web Presence**: Professional networks, news mentions, business directories, academic publications
- **Social Media**: Public profiles from LinkedIn, Twitter, Facebook, Instagram, YouTube

### Advanced Data Processing
- **Multi-Source Aggregation**: Collect data from 20+ sources simultaneously
- **Intelligent Cross-Referencing**: Verify data accuracy across multiple sources
- **Confidence Scoring**: Calculate reliability scores for each data point
- **Inconsistency Detection**: Flag conflicting information automatically

### Compliance & Security
- **Audit Logging**: Complete trail of all research activities
- **Data Retention**: Automatic cleanup based on configurable policies
- **Privacy Protection**: Implement data minimization and encryption
- **Legal Compliance**: Built-in FCRA and GDPR compliance features

## 📋 Prerequisites

- Python 3.8 or higher
- Chrome/Chromium browser (for web scraping)
- API keys for commercial services (optional but recommended)
- Internet connection for data collection

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd background_research_system
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Chrome/Chromium
The system uses Selenium for JavaScript-heavy websites. Install Chrome or Chromium:

**macOS:**
```bash
brew install --cask google-chrome
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install chromium-browser
```

**Windows:**
Download from [Chrome's official website](https://www.google.com/chrome/)

### 5. Configure API Keys
Copy the example configuration and add your API keys:

```bash
cp config.json.example config.json
# Edit config.json with your API keys
```

## ⚙️ Configuration

### API Keys Configuration
Edit `config.json` to add your API keys:

```json
{
  "api_keys": {
    "spokeo": "YOUR_SPOKEO_API_KEY",
    "whitepages": "YOUR_WHITEPAGES_API_KEY",
    "been_verified": "YOUR_BEENVERIFIED_API_KEY",
    "intelius": "YOUR_INTELIUS_API_KEY",
    "google_search": "YOUR_GOOGLE_SEARCH_API_KEY",
    "newsapi": "YOUR_NEWSAPI_API_KEY"
  }
}
```

### Rate Limiting
Configure rate limits for each service:

```json
{
  "rate_limits": {
    "spokeo": 60,
    "whitepages": 100,
    "been_verified": 50,
    "web_scraping": 120
  }
}
```

### Compliance Settings
Set compliance parameters:

```json
{
  "compliance": {
    "fcra_mode": false,
    "retention_days": 365,
    "audit_enabled": true,
    "data_encryption": true
  }
}
```

## 🚀 Usage

### Command Line Interface

#### Basic Research
```bash
python main.py \
  --name "John Doe" \
  --location "New York, NY" \
  --purpose employment_background_verification \
  --user-id "hr_001" \
  --output report.json
```

#### List Available Purposes
```bash
python main.py --list-purposes
```

#### Custom Configuration
```bash
python main.py \
  --name "Jane Smith" \
  --location "Los Angeles, CA" \
  --purpose tenant_screening \
  --user-id "property_mgr_001" \
  --config custom_config.json \
  --output tenant_report.json
```

#### Data Cleanup
```bash
python main.py --cleanup
```

### Programmatic Usage

```python
from core_system import LegitimateResearchEngine

# Initialize the engine
engine = LegitimateResearchEngine('config.json')

# Conduct research
profile_id = engine.conduct_comprehensive_search(
    name="John Doe",
    initial_location="New York, NY",
    legitimate_purpose="employment_background_verification",
    user_id="hr_001"
)

# Generate report
report = engine.generate_comprehensive_report(profile_id)

# Cleanup
engine.close()
```

## 📊 Data Sources

### Public Records
- **Federal Courts**: PACER system integration
- **State Courts**: 10 major states supported
- **Property Records**: County assessor databases
- **Business Records**: Secretary of State databases
- **Professional Licenses**: State licensing boards
- **Voter Records**: Where publicly available

### Commercial Services
- **Spokeo**: Comprehensive people search
- **WhitePages**: Contact information and address history
- **BeenVerified**: Background checks and public records
- **Intelius**: Additional data aggregation
- **PeopleFinders**: Address and contact information

### Web Scraping
- **Professional Networks**: LinkedIn, ResearchGate, Academia.edu
- **News Sources**: Google News, Bing News, NewsAPI
- **Business Directories**: YellowPages, Manta, Bizapedia
- **Academic Sources**: Google Scholar, ResearchGate

## 🔒 Compliance & Legal Considerations

### FCRA Compliance
- Obtain proper authorization for background checks
- Use only FCRA-compliant data sources
- Provide required disclosures to subjects
- Maintain proper records and documentation

### Privacy Protection
- Implement data minimization principles
- Provide opt-out mechanisms where required
- Secure storage of collected information
- Regular data purging and retention policies

### Terms of Service Compliance
- Respect website robots.txt files
- Follow API rate limits and usage guidelines
- Avoid circumventing access controls
- Use data only for stated legitimate purposes

## 📈 Report Structure

### Comprehensive Report
```json
{
  "profile_id": "unique_identifier",
  "subject_name": "John Doe",
  "report_date": "2024-01-15T10:30:00Z",
  "data_summary": {
    "total_data_points": 45,
    "data_types_found": ["addresses", "phone_numbers", "employment_history"],
    "overall_confidence": 0.85
  },
  "detailed_findings": {
    "addresses": [...],
    "phone_numbers": [...],
    "employment_history": [...]
  },
  "verification_summary": {
    "overall_score": 0.82,
    "verification_status": "moderately_verified",
    "data_quality_summary": {...},
    "recommendations": [...]
  },
  "compliance_notes": {
    "legitimate_purpose": "employment_background_verification",
    "consent_obtained": false,
    "data_retention_policy": "365 days"
  }
}
```

## 🧪 Testing

### Run Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Test Specific Module
```bash
pytest tests/test_data_verification.py -v
```

## 📝 Logging

The system provides comprehensive logging:

- **File Logging**: All activities logged to `research_system.log`
- **Console Output**: Real-time status updates
- **Audit Trail**: Complete compliance audit log
- **Error Tracking**: Detailed error logging with stack traces

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General information about operations
- **WARNING**: Potential issues that don't stop execution
- **ERROR**: Errors that prevent successful completion

## 🔧 Troubleshooting

### Common Issues

#### Chrome Driver Issues
```bash
# Install webdriver-manager
pip install webdriver-manager

# Update Chrome to latest version
# Ensure Chrome is in PATH
```

#### API Rate Limiting
```bash
# Check rate limit configuration
# Increase delays between requests
# Use multiple API keys if available
```

#### Database Issues
```bash
# Check file permissions
# Verify SQLite installation
# Check disk space
```

### Performance Optimization

#### Parallel Processing
```bash
# Adjust worker count in config
"parallel_workers": 5
```

#### Caching
```bash
# Enable result caching
"enable_caching": true,
"cache_ttl_hours": 24
```

## 📚 API Reference

### Core Classes

#### LegitimateResearchEngine
Main engine for conducting research.

```python
engine = LegitimateResearchEngine(config_path)
profile_id = engine.conduct_comprehensive_search(name, location, purpose, user_id)
report = engine.generate_comprehensive_report(profile_id)
engine.close()
```

#### PublicRecordsSearch
Handles public records searches.

```python
searcher = PublicRecordsSearch(api_keys, rate_limiter)
results = searcher.comprehensive_search(name, location)
```

#### CommercialDataAggregator
Aggregates data from commercial services.

```python
aggregator = CommercialDataAggregator(api_keys, rate_limiter)
results = aggregator.aggregate_all_sources(name, location)
```

#### DataVerification
Verifies and cross-references data.

```python
verifier = DataVerification()
verification_report = verifier.verify_and_merge_data(profile_id, database_manager)
```

## 🚨 Important Notes

### Legal Compliance
- **Always** specify a legitimate purpose for research
- **Never** use this system for stalking or harassment
- **Comply** with all applicable laws and regulations
- **Respect** individual privacy rights

### Data Quality
- Cross-reference information from multiple sources
- Verify critical information independently
- Maintain documentation of verification methods
- Regular data quality reviews

### Security
- Secure API keys and credentials
- Implement proper access controls
- Regular security updates
- Monitor for suspicious activity

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run linting
black .
flake8 .
mypy .
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Include unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Disclaimer

This software is provided for educational and legitimate business purposes only. Users are responsible for ensuring compliance with all applicable laws and regulations. The authors are not liable for any misuse of this software.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide
- Consult legal professionals for compliance questions

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added advanced verification and cross-referencing
- **v1.2.0**: Enhanced compliance features and audit logging
- **v1.3.0**: Improved performance and additional data sources

---

**Remember**: Always prioritize legal compliance and ethical practices over comprehensiveness. It's better to have accurate, legally obtained information than to risk legal issues with questionable data collection methods.

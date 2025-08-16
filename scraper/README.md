# Modular Web Scraper System

A production-ready, modular web scraping solution built with Python, featuring async operations, data validation, database integration, and workflow orchestration.

## 🚀 Features

- **Async Scraping**: High-performance scraping using Playwright and BeautifulSoup
- **Pagination Support**: Automatic handling of multi-page content
- **Concurrency Management**: Configurable concurrent scraping with rate limiting
- **Data Validation**: Pydantic models for type safety and data integrity
- **Database Integration**: PostgreSQL support with SQLAlchemy ORM
- **Workflow Orchestration**: Apache Airflow DAGs for automated scraping
- **API Control**: FastAPI endpoints for triggering and monitoring scraping operations
- **Containerization**: Docker support for easy deployment
- **Configuration Management**: YAML config with environment variable overrides

## 🏗️ Architecture

```
scraper/
├── core_scraper.py          # Core scraping logic
├── data_models.py           # Pydantic data models
├── config_loader.py         # Configuration management
├── load_data.py            # Database operations
├── fastapi_endpoint.py     # API control interface
├── main_scraper.py         # CLI entry point
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── airflow_dags/          # Airflow workflow definitions
│   └── automated_web_scraper.py
└── README.md              # This file
```

## 📦 Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Docker (optional, for containerized deployment)
- Apache Airflow (optional, for workflow orchestration)

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scraper
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Create configuration:
```bash
python main_scraper.py --create-config
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t web_scraper .
```

2. Run the container:
```bash
docker run -it --rm web_scraper --help
```

## ⚙️ Configuration

The system uses a YAML configuration file (`config.yaml`) with environment variable overrides:

```yaml
scraping:
  max_concurrent: 5
  timeout: 30000
  wait_for_network_idle: true
  retry_attempts: 3
  retry_delay: 5

database:
  host: localhost
  port: 5432
  database: scraper_db
  username: scraper_user

airflow:
  url: http://localhost:8080
  dag_id: automated_web_scraper
  api_version: v1

logging:
  level: INFO
  output_dir: ./output
```

### Environment Variables

- `DB_CONN_STRING`: Full database connection string
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database connection details
- `AIRFLOW_URL`: Airflow server URL
- `AIRFLOW_AUTH`: Airflow authentication token
- `MAX_CONCURRENT`: Maximum concurrent scraping operations
- `TIMEOUT`: Request timeout in milliseconds

## 🎯 Usage

### Command Line Interface

#### Basic Scraping
```bash
python main_scraper.py \
  --urls "https://example.com/page1" "https://example.com/page2" \
  --selectors '{"title": "h1", "content": "p", "price": ".price"}' \
  --output results.json
```

#### With Pagination
```bash
python main_scraper.py \
  --urls "https://example.com/products" \
  --selectors '{"title": ".product-title", "price": ".product-price"}' \
  --next-page-selector ".next-page" \
  --max-concurrent 3 \
  --output products.json
```

#### From Configuration Files
```bash
python main_scraper.py \
  --urls-file urls.txt \
  --selectors-file selectors.json \
  --save-to-db \
  --output results.json
```

### Python API

```python
from scraper import run_scraper, ScrapedItem

# Define selectors
selectors = {
    'title': 'h1.product-title',
    'price': '.product-price',
    'description': '.product-description'
}

# Run scraper
results = await run_scraper(
    urls=['https://example.com/products'],
    selectors=selectors,
    next_page_selector='.next-page',
    max_concurrent=5
)

# Process results
for page_data in results:
    for item in page_data:
        print(f"Title: {item['title']}, Price: {item['price']}")
```

### FastAPI Endpoints

#### Start the API Server
```bash
python fastapi_endpoint.py
```

#### Trigger Manual Scraping
```bash
curl -X POST "http://localhost:8000/scrape-manual" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "selectors": {"title": "h1", "content": "p"},
    "max_concurrent": 3
  }'
```

#### Trigger Airflow DAG
```bash
curl -X POST "http://localhost:8000/trigger-airflow" \
  -H "Content-Type: application/json" \
  -d '{"dag_id": "automated_web_scraper"}'
```

## 🔄 Airflow Integration

The system includes an Airflow DAG that orchestrates the complete scraping workflow:

1. **Get URLs**: Fetch URLs to scrape from API or database
2. **Run Scraper**: Execute scraping in Docker container
3. **Validate Data**: Quality checks on scraped data
4. **Prepare Data**: Format data for database insertion
5. **Load to Database**: Insert data into PostgreSQL
6. **Cleanup**: Remove old data
7. **Notification**: Send completion alerts

### Deploying the DAG

1. Copy `airflow_dags/automated_web_scraper.py` to your Airflow DAGs folder
2. Configure the `postgres_default` connection in Airflow
3. Ensure Docker is accessible from Airflow
4. The DAG will run daily at 3:00 AM UTC

## 🗄️ Database Schema

The system creates a `scraped_data` table with the following structure:

```sql
CREATE TABLE scraped_data (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    price FLOAT,
    url TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_url VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    raw_data TEXT
);
```

## 🐳 Docker Deployment

### Building the Image
```bash
docker build -t web_scraper:latest .
```

### Running with Environment Variables
```bash
docker run -d \
  --name web_scraper \
  -e DB_CONN_STRING="postgresql://user:pass@host:port/db" \
  -e MAX_CONCURRENT=5 \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/output:/app/output \
  web_scraper:latest
```

### Docker Compose Example
```yaml
version: '3.8'
services:
  web_scraper:
    build: .
    environment:
      - DB_CONN_STRING=postgresql://user:pass@db:5432/scraper_db
      - MAX_CONCURRENT=5
    volumes:
      - ./output:/app/output
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=scraper_db
      - POSTGRES_USER=scraper_user
      - POSTGRES_PASSWORD=scraper_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=scraper tests/
```

## 📊 Monitoring and Logging

The system provides comprehensive logging and monitoring:

- **Structured Logging**: JSON-formatted logs with configurable levels
- **Performance Metrics**: Execution time, success rates, data volumes
- **Health Checks**: API endpoints for system status
- **Error Tracking**: Detailed error logging with context

## 🔒 Security Considerations

- **Rate Limiting**: Built-in concurrency controls to avoid overwhelming target sites
- **User Agent Rotation**: Configurable user agent strings
- **Request Delays**: Configurable delays between requests
- **Authentication**: Support for protected endpoints
- **Data Validation**: Input sanitization and output validation

## 🚨 Error Handling

The system includes robust error handling:

- **Retry Logic**: Automatic retries for failed requests
- **Graceful Degradation**: Continue processing on partial failures
- **Error Reporting**: Detailed error messages and logging
- **Fallback Mechanisms**: Alternative data sources when possible

## 🔧 Customization

### Adding New Data Models
```python
from pydantic import BaseModel

class CustomItem(BaseModel):
    custom_field: str
    another_field: int
```

### Custom Selectors
```python
# Support for complex CSS selectors
selectors = {
    'title': 'h1.product-title',
    'price': '.price-wrapper .current-price',
    'availability': '[data-stock-status]'
}
```

### Custom Validation
```python
from pydantic import validator

class ProductItem(BaseModel):
    price: float

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be positive')
        return v
```

## 📈 Performance Optimization

- **Async Operations**: Non-blocking I/O for high concurrency
- **Connection Pooling**: Efficient database connection management
- **Memory Management**: Streaming data processing for large datasets
- **Caching**: Optional result caching to avoid re-scraping

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the example configurations

## 🔮 Roadmap

- [ ] Support for JavaScript-heavy sites
- [ ] Machine learning-based content extraction
- [ ] Real-time scraping with WebSockets
- [ ] Advanced proxy rotation
- [ ] Cloud deployment templates
- [ ] Integration with data warehouses
- [ ] Advanced scheduling and monitoring
- [ ] Multi-language support

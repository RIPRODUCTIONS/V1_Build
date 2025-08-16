# airflow_dags/automated_web_scraper.py
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.docker_operator import DockerOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

# Default arguments for the DAG
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email_on_retry': False,
}

# Define the DAG
dag = DAG(
    'automated_web_scraper',
    default_args=default_args,
    description='Automated web scraping workflow with Docker and PostgreSQL',
    schedule_interval='0 3 * * *',  # Daily at 3:00 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['web-scraping', 'automation', 'data-pipeline'],
)

def get_urls_task_func(**kwargs):
    """
    Fetch URLs to scrape from API or database
    This task can be customized based on your URL source
    """
    try:
        # Example: Fetch URLs from an API
        # response = requests.get('https://your-api.com/urls-to-scrape')
        # urls = response.json().get('urls', [])

        # For demonstration, using a static list
        urls = [
            'https://example.com/page1',
            'https://example.com/page2',
            'https://example.com/page3'
        ]

        # Store URLs in XCom for next task
        kwargs['ti'].xcom_push(key='urls', value=urls)
        logging.info(f"Retrieved {len(urls)} URLs to scrape")

        return urls

    except Exception as e:
        logging.error(f"Error fetching URLs: {e}")
        raise

def validate_data_task_func(**kwargs):
    """
    Validate scraped data quality
    """
    try:
        # Get data from previous task
        data = kwargs['ti'].xcom_pull(task_ids='run_scraper_task', key='scraped_data')

        if not data:
            raise ValueError("No data scraped")

        # Basic validation
        validated_data = []
        for item in data:
            if item.get('title') and item.get('url'):
                validated_data.append(item)
            else:
                logging.warning(f"Skipping invalid item: {item}")

        if not validated_data:
            raise ValueError("No valid data after validation")

        # Store validated data in XCom
        kwargs['ti'].xcom_push(key='validated_data', value=validated_data)
        logging.info(f"Validated {len(validated_data)} items out of {len(data)}")

        return validated_data

    except Exception as e:
        logging.error(f"Data validation error: {e}")
        raise

def prepare_data_for_db(**kwargs):
    """
    Prepare validated data for database insertion
    """
    try:
        validated_data = kwargs['ti'].xcom_pull(task_ids='validate_data_task', key='validated_data')

        # Convert to database format
        db_data = []
        for item in validated_data:
            db_item = {
                'title': item.get('title', 'Unknown'),
                'price': item.get('price'),
                'url': item.get('url', ''),
                'source_url': item.get('source_url', ''),
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            db_data.append(db_item)

        # Store prepared data in XCom
        kwargs['ti'].xcom_push(key='db_ready_data', value=db_data)
        logging.info(f"Prepared {len(db_data)} items for database insertion")

        return db_data

    except Exception as e:
        logging.error(f"Error preparing data for database: {e}")
        raise

# Task 1: Get URLs to scrape
get_urls_task = PythonOperator(
    task_id='get_urls_task',
    python_callable=get_urls_task_func,
    provide_context=True,
    dag=dag,
)

# Task 2: Run the scraper in Docker
run_scraper_task = DockerOperator(
    task_id='run_scraper_task',
    image='web_scraper:latest',  # Your Docker image name
    container_name='web_scraper_container',
    command='--urls "{{ ti.xcom_pull(key="urls") }}" --output /app/output',
    docker_url='unix://var/run/docker.sock',
    network_mode='bridge',
    auto_remove=True,
    environment={
        'MAX_CONCURRENT': '5',
        'TIMEOUT': '30000',
        'LOG_LEVEL': 'INFO'
    },
    dag=dag,
)

# Task 3: Validate scraped data
validate_data_task = PythonOperator(
    task_id='validate_data_task',
    python_callable=validate_data_task_func,
    provide_context=True,
    dag=dag,
)

# Task 4: Prepare data for database
prepare_data_task = PythonOperator(
    task_id='prepare_data_task',
    python_callable=prepare_data_for_db,
    provide_context=True,
    dag=dag,
)

# Task 5: Load data to PostgreSQL
load_to_warehouse_task = PostgresOperator(
    task_id='load_to_warehouse_task',
    postgres_conn_id='postgres_default',  # Configure this in Airflow
    sql="""
        INSERT INTO scraped_data (title, price, url, source_url, timestamp, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            price = EXCLUDED.price,
            timestamp = EXCLUDED.timestamp,
            status = EXCLUDED.status
    """,
    parameters="{{ ti.xcom_pull(key='db_ready_data') }}",
    dag=dag,
)

# Task 6: Cleanup old data (optional)
cleanup_old_data_task = PostgresOperator(
    task_id='cleanup_old_data_task',
    postgres_conn_id='postgres_default',
    sql="""
        DELETE FROM scraped_data
        WHERE timestamp < NOW() - INTERVAL '30 days'
        AND status = 'inactive'
    """,
    dag=dag,
)

# Task 7: Send completion notification
def send_notification(**kwargs):
    """Send notification about scraping completion"""
    try:
        validated_count = kwargs['ti'].xcom_pull(task_ids='validate_data_task', key='validated_data')
        total_count = len(validated_count) if validated_count else 0

        # Example: Send to Slack, email, or other notification service
        message = f"Web scraping completed successfully! Processed {total_count} items."
        logging.info(message)

        # You can implement actual notification logic here
        # e.g., Slack webhook, email, etc.

        return message

    except Exception as e:
        logging.error(f"Error sending notification: {e}")
        return f"Error: {e}"

notification_task = PythonOperator(
    task_id='notification_task',
    python_callable=send_notification,
    provide_context=True,
    dag=dag,
)

# Define task dependencies
get_urls_task >> run_scraper_task >> validate_data_task >> prepare_data_task >> load_to_warehouse_task >> cleanup_old_data_task >> notification_task

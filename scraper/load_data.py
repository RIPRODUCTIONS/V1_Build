import logging
from datetime import datetime, timedelta
from typing import Any

from config_loader import get_database_config
from data_models import ScrapedItem
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ScrapedItemTable(Base):
    """SQLAlchemy table model for scraped items"""
    __tablename__ = 'scraped_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    price = Column(Float, nullable=True)
    url = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source_url = Column(String(500), nullable=False)
    status = Column(String(50), default='active')
    raw_data = Column(Text, nullable=True)  # JSON string for additional data

class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or self._get_connection_string()
        self.engine = None
        self.Session = None
        self._setup_connection()

    def _get_connection_string(self) -> str:
        """Get database connection string from config or environment"""
        db_config = get_database_config()

        if db_config['conn_string']:
            return db_config['conn_string']

        # Build connection string from individual components
        password = db_config['password']
        if password:
            return f"postgresql://{db_config['username']}:{password}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        else:
            return f"postgresql://{db_config['username']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

    def _setup_connection(self):
        """Setup database connection and session factory"""
        try:
            self.engine = create_engine(self.connection_string)
            self.Session = sessionmaker(bind=self.engine)

            # Test connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")

            logging.info("Database connection established successfully")
        except Exception as e:
            logging.error(f"Failed to establish database connection: {e}")
            raise

    def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            Base.metadata.create_all(self.engine)
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Failed to create tables: {e}")
            raise

    def insert_data(self, data: list[ScrapedItem], source_url: str = None) -> bool:
        """
        Insert scraped data into the database

        Args:
            data: List of ScrapedItem objects
            source_url: Source URL for the data (optional, will use first item's URL if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        if not data:
            logging.warning("No data to insert")
            return False

        if not source_url:
            source_url = str(data[0].url)

        session = self.Session()
        try:
            for item in data:
                db_item = ScrapedItemTable(
                    title=item.title,
                    price=item.price,
                    url=str(item.url),
                    timestamp=item.timestamp,
                    source_url=source_url,
                    status='active',
                    raw_data=str(item.raw_data) if item.raw_data else None
                )
                session.add(db_item)

            session.commit()
            logging.info(f"Successfully inserted {len(data)} items into database")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Database error during insert: {e}")
            return False
        except Exception as e:
            session.rollback()
            logging.error(f"Unexpected error during insert: {e}")
            return False
        finally:
            session.close()

    def insert_raw_data(self, data: list[dict[str, Any]], source_url: str) -> bool:
        """
        Insert raw scraped data (dictionary format) into the database

        Args:
            data: List of dictionaries containing scraped data
            source_url: Source URL for the data

        Returns:
            bool: True if successful, False otherwise
        """
        if not data:
            logging.warning("No data to insert")
            return False

        session = self.Session()
        try:
            for item in data:
                db_item = ScrapedItemTable(
                    title=item.get('title', 'Unknown'),
                    price=item.get('price'),
                    url=item.get('url', source_url),
                    timestamp=datetime.utcnow(),
                    source_url=source_url,
                    status='active',
                    raw_data=str(item)
                )
                session.add(db_item)

            session.commit()
            logging.info(f"Successfully inserted {len(data)} items into database")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Database error during insert: {e}")
            return False
        except Exception as e:
            session.rollback()
            logging.error(f"Unexpected error during insert: {e}")
            return False
        finally:
            session.close()

    def get_data_by_source(self, source_url: str, limit: int = 100) -> list[ScrapedItemTable]:
        """Retrieve data from a specific source URL"""
        session = self.Session()
        try:
            items = session.query(ScrapedItemTable).filter(
                ScrapedItemTable.source_url == source_url
            ).limit(limit).all()
            return items
        except Exception as e:
            logging.error(f"Error retrieving data: {e}")
            return []
        finally:
            session.close()

    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Remove data older than specified days"""
        session = self.Session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = session.query(ScrapedItemTable).filter(
                ScrapedItemTable.timestamp < cutoff_date
            ).delete()
            session.commit()
            logging.info(f"Cleaned up {deleted_count} old records")
            return deleted_count
        except Exception as e:
            session.rollback()
            logging.error(f"Error during cleanup: {e}")
            return 0
        finally:
            session.close()

def insert_data(data: list[ScrapedItem], source_url: str = None) -> bool:
    """Convenience function for inserting data"""
    db_manager = DatabaseManager()
    return db_manager.insert_data(data, source_url)

def insert_raw_data(data: list[dict[str, Any]], source_url: str) -> bool:
    """Convenience function for inserting raw data"""
    db_manager = DatabaseManager()
    return db_manager.insert_raw_data(data, source_url)

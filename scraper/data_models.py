from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any

class ScrapedItem(BaseModel):
    """Base model for scraped data items"""
    title: str
    price: Optional[float] = None
    url: HttpUrl
    timestamp: datetime = datetime.utcnow()
    raw_data: Optional[Dict[str, Any]] = None

    @field_validator('price', mode='before')
    @classmethod
    def parse_price(cls, v):
        if isinstance(v, str):
            # Remove currency symbols and convert to float
            cleaned = v.replace('$', '').replace('€', '').replace('£', '').replace(',', '')
            try:
                return float(cleaned)
            except ValueError:
                return None
        return v

class ScrapedItemDB(BaseModel):
    """Database model for scraped items"""
    id: Optional[int] = None
    title: str
    price: Optional[float] = None
    url: str
    timestamp: datetime = datetime.utcnow()
    source_url: str
    status: str = "active"

    class Config:
        from_attributes = True

class ScrapingConfig(BaseModel):
    """Configuration for scraping operations"""
    selectors: Dict[str, str]
    next_page_selector: Optional[str] = None
    max_concurrent: int = 5
    timeout: int = 30000
    wait_for_network_idle: bool = True
    user_agent: Optional[str] = None

class ScrapingResult(BaseModel):
    """Result of a scraping operation"""
    success: bool
    data: List[ScrapedItem]
    errors: List[str] = []
    total_items: int = 0
    execution_time: float = 0.0
    timestamp: datetime = datetime.utcnow()

    @field_validator('total_items', mode='before')
    @classmethod
    def set_total_items(cls, v, values):
        if hasattr(values, 'data') and values.data:
            return len(values.data)
        return v

"""
Database Storage Service

SQLite-based persistent storage for scraping results using async operations.
Implements clean architecture with proper separation of concerns.
"""

import asyncio
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..domain.interfaces import IResultStorageService, ILogger
from ..domain.models import (
    ScrapingResult, Product, SellerInfo, DatabaseScrape, 
    DatabaseProduct, DatabaseSeller, ScrapingStatus, SearchCriteria
)


class DatabaseStorageService(IResultStorageService):
    """
    SQLite-based storage service for scraping results.
    
    Features:
    - Async operations using threading
    - Normalized database schema
    - Automatic migration support
    - Efficient querying with indexes
    """
    
    def __init__(self, db_path: str, logger: ILogger):
        """
        Initialize database storage service.
        
        Args:
            db_path: Path to SQLite database file
            logger: Logger instance for tracking operations
        """
        self.db_path = db_path
        self.logger = logger
        self._db_lock = asyncio.Lock()
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize database schema."""
        await self._execute_async(self._create_tables)
        await self.logger.log_info("Database storage service initialized", db_path=self.db_path)
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create database tables with proper schema."""
        cursor = conn.cursor()
        
        # Scrapes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrapes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id TEXT UNIQUE NOT NULL,
                keyword TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                total_products INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                duration REAL,
                error_message TEXT,
                criteria_json TEXT NOT NULL,
                market_analysis_json TEXT,
                created_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP
            )
        """)
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scrape_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                condition TEXT NOT NULL,
                sold_count INTEGER,
                seller_name TEXT,
                marketplace TEXT NOT NULL,
                item_url TEXT NOT NULL,
                image_url TEXT,
                shipping_cost REAL,
                free_shipping BOOLEAN DEFAULT 0,
                location TEXT,
                listing_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (scrape_id) REFERENCES scrapes (id) ON DELETE CASCADE
            )
        """)
        
        # Sellers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_name TEXT NOT NULL,
                feedback_score INTEGER,
                feedback_percentage REAL,
                total_sold_items INTEGER DEFAULT 0,
                marketplace TEXT NOT NULL,
                first_seen TIMESTAMP NOT NULL,
                last_updated TIMESTAMP NOT NULL,
                UNIQUE(seller_name, marketplace)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrapes_keyword ON scrapes (keyword)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrapes_marketplace ON scrapes (marketplace)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrapes_created_at ON scrapes (created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_scrape_id ON products (scrape_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_item_id ON products (item_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_price ON products (price)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sellers_name ON sellers (seller_name)")
        
        conn.commit()
    
    async def _execute_async(self, func, *args) -> Any:
        """Execute database operation asynchronously."""
        async with self._db_lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._execute_sync, func, *args)
    
    def _execute_sync(self, func, *args) -> Any:
        """Execute database operation synchronously."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return func(conn, *args)
    
    async def store_scraping_result(self, result: ScrapingResult) -> str:
        """Store complete scraping result in database."""
        if not result.result_id:
            result.result_id = str(uuid.uuid4())
        
        await self._execute_async(self._store_scraping_result_sync, result)
        
        await self.logger.log_info(
            "Stored scraping result in database",
            result_id=result.result_id,
            products_count=len(result.products),
            keyword=result.criteria.keyword
        )
        
        return result.result_id
    
    def _store_scraping_result_sync(self, conn: sqlite3.Connection, result: ScrapingResult) -> None:
        """Store scraping result synchronously."""
        cursor = conn.cursor()
        
        # Store main scrape record
        cursor.execute("""
            INSERT OR REPLACE INTO scrapes (
                result_id, keyword, marketplace, total_products, status,
                duration, error_message, criteria_json, market_analysis_json,
                created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.result_id,
            result.criteria.keyword,
            result.criteria.marketplace.value,
            len(result.products),
            result.status.value,
            result.scraping_duration,
            result.error_message,
            result.criteria.json(),
            result.market_analysis.json() if result.market_analysis else None,
            result.created_at,
            result.completed_at
        ))
        
        scrape_id = cursor.lastrowid
        
        # Store products
        for product in result.products:
            cursor.execute("""
                INSERT INTO products (
                    scrape_id, item_id, title, price, condition, sold_count,
                    seller_name, marketplace, item_url, image_url, shipping_cost,
                    free_shipping, location, listing_date, end_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scrape_id,
                product.item_id,
                product.title,
                float(product.price),
                product.condition.value,
                product.sold_count,
                product.seller_info.seller_name if product.seller_info else None,
                product.marketplace.value,
                str(product.item_url),
                str(product.image_url) if product.image_url else None,
                float(product.shipping_cost) if product.shipping_cost else None,
                product.free_shipping,
                product.location,
                product.listing_date,
                product.end_date,
                datetime.utcnow()
            ))
            
            # Store or update seller info
            if product.seller_info:
                cursor.execute("""
                    INSERT OR REPLACE INTO sellers (
                        seller_name, feedback_score, feedback_percentage,
                        total_sold_items, marketplace, first_seen, last_updated
                    ) VALUES (?, ?, ?, ?, ?, 
                        COALESCE((SELECT first_seen FROM sellers WHERE seller_name = ? AND marketplace = ?), ?),
                        ?
                    )
                """, (
                    product.seller_info.seller_name,
                    product.seller_info.feedback_score,
                    product.seller_info.feedback_percentage,
                    product.seller_info.total_sold_items or 0,
                    product.marketplace.value,
                    product.seller_info.seller_name,
                    product.marketplace.value,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
        
        conn.commit()
    
    async def get_scraping_result(self, result_id: str) -> Optional[ScrapingResult]:
        """Retrieve scraping result by ID."""
        data = await self._execute_async(self._get_scraping_result_sync, result_id)
        
        if not data:
            return None
        
        return self._build_scraping_result_from_data(data)
    
    def _get_scraping_result_sync(self, conn: sqlite3.Connection, result_id: str) -> Optional[Dict]:
        """Get scraping result synchronously."""
        cursor = conn.cursor()
        
        # Get scrape record
        cursor.execute("SELECT * FROM scrapes WHERE result_id = ?", (result_id,))
        scrape_row = cursor.fetchone()
        
        if not scrape_row:
            return None
        
        # Get products for this scrape
        cursor.execute("SELECT * FROM products WHERE scrape_id = ?", (scrape_row['id'],))
        product_rows = cursor.fetchall()
        
        return {
            'scrape': dict(scrape_row),
            'products': [dict(row) for row in product_rows]
        }
    
    async def get_scraping_history(
        self, 
        keyword: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ScrapingResult]:
        """Get historical scraping results."""
        data_list = await self._execute_async(
            self._get_scraping_history_sync, keyword, limit, offset
        )
        
        results = []
        for data in data_list:
            result = self._build_scraping_result_from_data(data)
            if result:
                results.append(result)
        
        return results
    
    def _get_scraping_history_sync(
        self, 
        conn: sqlite3.Connection, 
        keyword: Optional[str], 
        limit: int, 
        offset: int
    ) -> List[Dict]:
        """Get scraping history synchronously."""
        cursor = conn.cursor()
        
        if keyword:
            cursor.execute("""
                SELECT * FROM scrapes 
                WHERE keyword LIKE ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (f"%{keyword}%", limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM scrapes 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
        
        scrape_rows = cursor.fetchall()
        
        results = []
        for scrape_row in scrape_rows:
            cursor.execute("SELECT * FROM products WHERE scrape_id = ?", (scrape_row['id'],))
            product_rows = cursor.fetchall()
            
            results.append({
                'scrape': dict(scrape_row),
                'products': [dict(row) for row in product_rows]
            })
        
        return results
    
    async def search_products(
        self,
        keyword: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 100
    ) -> List[Product]:
        """Search stored products with filtering."""
        product_data = await self._execute_async(
            self._search_products_sync, keyword, min_price, max_price, limit
        )
        
        products = []
        for data in product_data:
            product = self._build_product_from_data(data)
            if product:
                products.append(product)
        
        return products
    
    def _search_products_sync(
        self,
        conn: sqlite3.Connection,
        keyword: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        limit: int
    ) -> List[Dict]:
        """Search products synchronously."""
        cursor = conn.cursor()
        
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND title LIKE ?"
            params.append(f"%{keyword}%")
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def _build_scraping_result_from_data(self, data: Dict) -> Optional[ScrapingResult]:
        """Build ScrapingResult object from database data."""
        try:
            scrape_data = data['scrape']
            product_data = data['products']
            
            # Rebuild criteria from JSON
            criteria_dict = json.loads(scrape_data['criteria_json'])
            criteria = SearchCriteria.parse_obj(criteria_dict)
            
            # Build products
            products = []
            for p_data in product_data:
                product = self._build_product_from_data(p_data)
                if product:
                    products.append(product)
            
            # Build market analysis if available
            market_analysis = None
            if scrape_data['market_analysis_json']:
                analysis_dict = json.loads(scrape_data['market_analysis_json'])
                from ..domain.models import MarketAnalysis
                market_analysis = MarketAnalysis.parse_obj(analysis_dict)
            
            return ScrapingResult(
                result_id=scrape_data['result_id'],
                criteria=criteria,
                products=products,
                market_analysis=market_analysis,
                status=ScrapingStatus(scrape_data['status']),
                error_message=scrape_data['error_message'],
                scraping_duration=scrape_data['duration'],
                created_at=datetime.fromisoformat(scrape_data['created_at']),
                completed_at=datetime.fromisoformat(scrape_data['completed_at']) if scrape_data['completed_at'] else None
            )
            
        except Exception as e:
            asyncio.create_task(self.logger.log_error(
                "Failed to build scraping result from database data",
                error=str(e),
                data=data
            ))
            return None
    
    def _build_product_from_data(self, data: Dict) -> Optional[Product]:
        """Build Product object from database data."""
        try:
            from ..domain.models import Product, ProductCondition, Marketplace
            
            # Build seller info if available
            seller_info = None
            if data['seller_name']:
                seller_info = SellerInfo(seller_name=data['seller_name'])
            
            return Product(
                item_id=data['item_id'],
                title=data['title'],
                price=data['price'],
                condition=ProductCondition(data['condition']),
                sold_count=data['sold_count'],
                item_url=data['item_url'],
                image_url=data['image_url'] if data['image_url'] else None,
                seller_info=seller_info,
                shipping_cost=data['shipping_cost'] if data['shipping_cost'] else None,
                free_shipping=bool(data['free_shipping']),
                location=data['location'],
                listing_date=datetime.fromisoformat(data['listing_date']) if data['listing_date'] else None,
                end_date=datetime.fromisoformat(data['end_date']) if data['end_date'] else None,
                marketplace=Marketplace(data['marketplace'])
            )
            
        except Exception as e:
            asyncio.create_task(self.logger.log_error(
                "Failed to build product from database data",
                error=str(e),
                data=data
            ))
            return None
    
    async def cleanup(self) -> None:
        """Cleanup database connections."""
        await self.logger.log_info("Database storage service cleanup completed") 
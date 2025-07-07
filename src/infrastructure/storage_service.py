"""
File Storage Service

Handles persistence of scraping results to files.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..domain.interfaces import IDataStorage, ILogger
from ..domain.models import ScrapingResult


class FileStorageService(IDataStorage):
    """
    File-based storage service for scraping results.
    
    Features:
    - JSON file storage
    - Unique result IDs
    - Configurable output directory
    """
    
    def __init__(self, config, logger: ILogger):
        """
        Initialize storage service.
        
        Args:
            config: Storage configuration
            logger: Logging service
        """
        self.config = config
        self.logger = logger
        self.output_dir = Path(config.output_directory)
        self.output_dir.mkdir(exist_ok=True)
    
    async def save_result(self, result: ScrapingResult) -> str:
        """
        Save scraping result to file.
        
        Args:
            result: Scraping result to save
            
        Returns:
            Unique identifier for saved result
        """
        result_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"scraping_result_{timestamp}_{result_id[:8]}.json"
        filepath = self.output_dir / filename
        
        try:
            # Convert result to dict for JSON serialization
            result_data = {
                "id": result_id,
                "criteria": result.criteria.dict(),
                "products": [p.dict() for p in result.products],
                "market_analysis": result.market_analysis.dict() if result.market_analysis else None,
                "status": result.status.value,
                "error_message": result.error_message,
                "scraping_duration": result.scraping_duration,
                "created_at": result.created_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            await self.logger.log_info(
                "Scraping result saved",
                result_id=result_id,
                filename=filename,
                products_count=len(result.products)
            )
            
            return result_id
            
        except Exception as e:
            await self.logger.log_error(
                "Failed to save scraping result",
                error=str(e),
                result_id=result_id
            )
            raise
    
    async def get_result(self, result_id: str) -> Optional[ScrapingResult]:
        """
        Retrieve scraping result by ID.
        
        Args:
            result_id: Unique result identifier
            
        Returns:
            Scraping result or None if not found
        """
        # For now, return None as this would require indexing files
        # In a real implementation, you might use a database or file index
        await self.logger.log_info(
            "Result retrieval not implemented for file storage",
            result_id=result_id
        )
        return None 
"""
Keyword Input Service

Handles validation and processing of user search input.
Following Single Responsibility Principle.
"""

from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta

from ...domain.models import SearchCriteria, ProductCondition
from ...domain.exceptions import ValidationError
from ...domain.interfaces import ILogger


class KeywordInputService:
    """
    Service for processing and validating keyword search input.
    
    Responsibilities:
    - Validate search criteria
    - Sanitize user input
    - Convert form data to domain models
    """
    
    def __init__(self, logger: ILogger):
        """
        Initialize the service.
        
        Args:
            logger: Logging service for recording validation events
        """
        self._logger = logger
        self._max_keyword_length = 200
        self._max_results_limit = 100
        self._max_date_range_days = 365

    async def process_search_input(
        self,
        keyword: str,
        category_id: Optional[str] = None,
        min_price: Optional[str] = None,
        max_price: Optional[str] = None,
        condition: Optional[str] = None,
        sold_listings_only: bool = False,
        date_range_days: Optional[str] = None,
        max_results: Optional[str] = None
    ) -> SearchCriteria:
        """
        Process and validate search input from user.
        
        Args:
            keyword: Search keyword (required)
            category_id: eBay category ID (optional)
            min_price: Minimum price filter as string
            max_price: Maximum price filter as string
            condition: Product condition filter
            sold_listings_only: Whether to search only sold listings
            date_range_days: Date range in days as string
            max_results: Maximum results as string
            
        Returns:
            Validated SearchCriteria object
            
        Raises:
            ValidationError: When input validation fails
        """
        await self._logger.log_info(
            "Processing search input",
            keyword=keyword,
            category_id=category_id
        )
        
        try:
            # Validate and sanitize keyword
            validated_keyword = await self._validate_keyword(keyword)
            
            # Validate and convert numeric fields
            validated_min_price = await self._validate_price(min_price, "min_price")
            validated_max_price = await self._validate_price(max_price, "max_price")
            
            # Validate price range
            await self._validate_price_range(validated_min_price, validated_max_price)
            
            # Validate condition
            validated_condition = await self._validate_condition(condition)
            
            # Validate date range
            validated_date_range = await self._validate_date_range(date_range_days)
            
            # Validate max results
            validated_max_results = await self._validate_max_results(max_results)
            
            # Create SearchCriteria object
            criteria = SearchCriteria(
                keyword=validated_keyword,
                category_id=category_id.strip() if category_id else None,
                min_price=validated_min_price,
                max_price=validated_max_price,
                condition=validated_condition,
                sold_listings_only=sold_listings_only,
                date_range_days=validated_date_range,
                max_results=validated_max_results
            )
            
            await self._logger.log_info(
                "Search input validated successfully",
                criteria=criteria.dict()
            )
            
            return criteria
            
        except ValidationError:
            raise
        except Exception as e:
            await self._logger.log_error(
                "Unexpected error during input validation",
                error=str(e),
                keyword=keyword
            )
            raise ValidationError(
                f"Failed to process search input: {str(e)}",
                field="general"
            )

    async def _validate_keyword(self, keyword: str) -> str:
        """Validate and sanitize search keyword."""
        if not keyword or not keyword.strip():
            raise ValidationError(
                "Search keyword is required",
                field="keyword",
                value=keyword
            )
        
        cleaned_keyword = keyword.strip()
        
        if len(cleaned_keyword) > self._max_keyword_length:
            raise ValidationError(
                f"Keyword too long (max {self._max_keyword_length} characters)",
                field="keyword",
                value=cleaned_keyword
            )
        
        # Basic sanitization - remove potentially harmful characters
        if any(char in cleaned_keyword for char in ['<', '>', '"', "'"]):
            raise ValidationError(
                "Keyword contains invalid characters",
                field="keyword",
                value=cleaned_keyword
            )
        
        return cleaned_keyword

    async def _validate_price(self, price_str: Optional[str], field_name: str) -> Optional[Decimal]:
        """Validate and convert price string to Decimal."""
        if not price_str or not price_str.strip():
            return None
        
        try:
            price = Decimal(price_str.strip())
            if price < 0:
                raise ValidationError(
                    f"{field_name} cannot be negative",
                    field=field_name,
                    value=price_str
                )
            if price > Decimal('999999.99'):
                raise ValidationError(
                    f"{field_name} too large (max $999,999.99)",
                    field=field_name,
                    value=price_str
                )
            return price
        except (InvalidOperation, ValueError):
            raise ValidationError(
                f"{field_name} must be a valid number",
                field=field_name,
                value=price_str
            )

    async def _validate_price_range(
        self,
        min_price: Optional[Decimal],
        max_price: Optional[Decimal]
    ) -> None:
        """Validate price range logic."""
        if min_price is not None and max_price is not None:
            if min_price >= max_price:
                raise ValidationError(
                    "Maximum price must be greater than minimum price",
                    field="price_range"
                )

    async def _validate_condition(self, condition: Optional[str]) -> Optional[ProductCondition]:
        """Validate product condition."""
        if not condition or not condition.strip():
            return None
        
        try:
            return ProductCondition(condition.lower().strip())
        except ValueError:
            valid_conditions = [c.value for c in ProductCondition]
            raise ValidationError(
                f"Invalid condition. Valid options: {', '.join(valid_conditions)}",
                field="condition",
                value=condition
            )

    async def _validate_date_range(self, date_range_str: Optional[str]) -> int:
        """Validate date range in days."""
        if not date_range_str or not date_range_str.strip():
            return 30  # Default to 30 days
        
        try:
            days = int(date_range_str.strip())
            if days < 1:
                raise ValidationError(
                    "Date range must be at least 1 day",
                    field="date_range_days",
                    value=date_range_str
                )
            if days > self._max_date_range_days:
                raise ValidationError(
                    f"Date range too large (max {self._max_date_range_days} days)",
                    field="date_range_days",
                    value=date_range_str
                )
            return days
        except ValueError:
            raise ValidationError(
                "Date range must be a valid number of days",
                field="date_range_days",
                value=date_range_str
            )

    async def _validate_max_results(self, max_results_str: Optional[str]) -> int:
        """Validate maximum results."""
        if not max_results_str or not max_results_str.strip():
            return 20  # Default to 20 results
        
        try:
            max_results = int(max_results_str.strip())
            if max_results < 1:
                raise ValidationError(
                    "Maximum results must be at least 1",
                    field="max_results",
                    value=max_results_str
                )
            if max_results > self._max_results_limit:
                raise ValidationError(
                    f"Maximum results too large (max {self._max_results_limit})",
                    field="max_results",
                    value=max_results_str
                )
            return max_results
        except ValueError:
            raise ValidationError(
                "Maximum results must be a valid number",
                field="max_results",
                value=max_results_str
            )

    async def validate_form_data(self, form_data: Dict[str, Any]) -> SearchCriteria:
        """
        Validate form data from web interface.
        
        Args:
            form_data: Dictionary containing form fields
            
        Returns:
            Validated SearchCriteria object
        """
        return await self.process_search_input(
            keyword=form_data.get('keyword', ''),
            category_id=form_data.get('category_id'),
            min_price=form_data.get('min_price'),
            max_price=form_data.get('max_price'),
            condition=form_data.get('condition'),
            sold_listings_only=bool(form_data.get('sold_listings_only')),
            date_range_days=form_data.get('date_range_days'),
            max_results=form_data.get('max_results')
        ) 
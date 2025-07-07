# 📋 **Individual Coding Standards & Principles Report**
## Claude Sonnet 4 - Python Development Standards & Best Practices

**Document Version:** 2.0  
**Last Updated:** December 2024  
**Author:** Claude Sonnet 4 (AI Assistant)  
**Scope:** Python Development Standards & Architecture Principles  

---

## 🎯 **Executive Summary**

This document establishes the comprehensive coding standards, principles, and best practices I adhere to when developing Python applications. These standards ensure code quality, maintainability, type safety, and production readiness across all projects.

---

## 📚 **Table of Contents**

1. [Core Philosophy](#core-philosophy)
2. [Technology Stack Standards](#technology-stack-standards)
3. [Code Quality Principles](#code-quality-principles)
4. [Architecture & Design Patterns](#architecture--design-patterns)
5. [SOLID Principles](#solid-principles)
6. [Type Safety & Validation](#type-safety--validation)
7. [Error Handling Standards](#error-handling-standards)
8. [Performance & Optimization](#performance--optimization)
9. [Documentation Standards](#documentation-standards)
10. [Testing Principles](#testing-principles)
11. [Security Considerations](#security-considerations)

---

## 🏛️ **Core Philosophy**

### **1. Pythonic Excellence**
- **Zen of Python Compliance**: Follow PEP 20 principles religiously
- **Readability First**: Code is read 10x more than written
- **Explicit Over Implicit**: Clear, unambiguous code intent
- **Simple Over Complex**: Avoid unnecessary complexity

### **2. Professional Standards**
- **Production-Ready Code**: Every line written for enterprise deployment
- **Type-Safe Development**: 100% type coverage with modern annotations
- **Defensive Programming**: Anticipate and handle edge cases
- **Future-Proof Design**: Built for maintainability and scalability

### **3. Modern Python Approach**
- **Python 3.10+ Features**: Leverage latest language capabilities
- **Async-First**: Concurrent programming for I/O operations
- **Dataclass & Pydantic**: Modern data structures with validation
- **Functional Programming**: Pure functions where applicable

---

## 🛠️ **Technology Stack Standards**

### **Core Requirements**
```yaml
Python Version: 3.10+
Dependency Management: Poetry / Rye
Code Formatting: Ruff (replaces black, isort, flake8)
Type Checking: mypy with strict mode
Testing Framework: pytest with coverage
Documentation: Google-style docstrings
```

### **Framework Preferences**
```yaml
Web Framework: FastAPI (async-first, type-safe)
Data Validation: Pydantic (automatic validation)
Database ORM: SQLAlchemy 2.0+ (async support)
Async Runtime: asyncio (native Python)
Containerization: Docker + docker-compose
```

### **Development Tools**
```yaml
Environment: conda / venv
Version Control: git with conventional commits
CI/CD: GitHub Actions / GitLab CI
Monitoring: structlog for logging
Configuration: Hydra / YAML configs
```

---

## 📐 **Code Quality Principles**

### **1. Type Annotations (100% Coverage)**
```python
# ✅ ALWAYS: Complete type annotations
from typing import Dict, List, Optional, Union, Any, Callable
from collections.abc import Awaitable

def process_data(
    items: List[Dict[str, Any]], 
    processor: Callable[[Dict[str, Any]], str],
    batch_size: int = 100
) -> Dict[str, Union[int, List[str]]]:
    """Process data with full type safety."""
    pass

# ✅ Generic types for reusability
from typing import TypeVar
T = TypeVar('T')

async def retry_operation(
    operation: Callable[[], Awaitable[T]], 
    max_attempts: int = 3
) -> T:
    """Generic retry with type preservation."""
    pass
```

### **2. Google-Style Documentation**
```python
def calculate_metrics(
    data: List[Dict[str, Any]], 
    threshold: float = 0.95
) -> Dict[str, float]:
    """Calculate performance metrics from dataset.
    
    This function processes performance data and calculates key metrics
    including accuracy, precision, recall, and F1-score.
    
    Args:
        data: List of performance records with 'actual' and 'predicted' keys.
        threshold: Confidence threshold for binary classification (0.0-1.0).
        
    Returns:
        Dictionary containing calculated metrics:
        - accuracy: Overall prediction accuracy
        - precision: Positive prediction precision  
        - recall: True positive recall rate
        - f1_score: Harmonic mean of precision and recall
        
    Raises:
        ValueError: If threshold is outside valid range [0.0, 1.0].
        KeyError: If required keys missing from data records.
        
    Example:
        >>> data = [{'actual': 1, 'predicted': 0.98}, {'actual': 0, 'predicted': 0.12}]
        >>> metrics = calculate_metrics(data, threshold=0.5)
        >>> metrics['accuracy']
        1.0
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be in [0.0, 1.0], got {threshold}")
    
    # Implementation with proper error handling
    pass
```

### **3. Comprehensive Error Handling**
```python
# ✅ Custom exception hierarchy
class ApplicationError(Exception):
    """Base application exception with context."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(ApplicationError):
    """Data validation failures."""
    pass

class NetworkError(ApplicationError):
    """Network operation failures."""
    pass

# ✅ Specific error handling with context
async def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data with comprehensive error handling."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException as e:
        raise NetworkError(
            "Request timeout occurred", 
            details={"url": url, "timeout": 30.0}
        ) from e
        
    except httpx.HTTPStatusError as e:
        raise NetworkError(
            f"HTTP error {e.response.status_code}",
            details={"url": url, "status": e.response.status_code}
        ) from e
        
    except Exception as e:
        raise ApplicationError(
            "Unexpected error during data fetch",
            details={"url": url, "error_type": type(e).__name__}
        ) from e
```

---

## 🏗️ **Architecture & Design Patterns**

### **1. Modular Design (Single Responsibility)**
```python
# ✅ Each module has ONE clear purpose
# config.py - Configuration management only
# models.py - Data structures only  
# services.py - Business logic only
# utils.py - Utility functions only
# exceptions.py - Error definitions only

# ✅ Clean imports and interfaces
from .config import AppConfig, DatabaseConfig
from .models import User, Product, Order
from .services import UserService, ProductService
from .exceptions import ValidationError, NotFoundError
```

### **2. Dependency Injection Pattern**
```python
# ✅ Injectable dependencies for testing
class UserService:
    """User service with injected dependencies."""
    
    def __init__(
        self,
        repository: UserRepository,
        config: AppConfig,
        logger: logging.Logger
    ) -> None:
        self.repository = repository
        self.config = config
        self.logger = logger
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create user with proper dependency usage."""
        # Validate using injected config
        if len(user_data.get('email', '')) < self.config.min_email_length:
            raise ValidationError("Email too short")
        
        # Log using injected logger
        self.logger.info("Creating user", extra={"email": user_data['email']})
        
        # Save using injected repository
        return await self.repository.create(user_data)
```

### **3. Configuration Management**
```python
# ✅ Type-safe configuration with dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

@dataclass(frozen=True)
class DatabaseConfig:
    """Database configuration settings."""
    host: str = "localhost"
    port: int = 5432
    database: str = "app_db"
    pool_size: int = 10
    max_overflow: int = 20
    
@dataclass(frozen=True)
class APIConfig:
    """API configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    cors_origins: List[str] = field(default_factory=list)
    
@dataclass
class AppConfig:
    """Main application configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    log_level: str = "INFO"
    debug: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.database.port <= 0:
            raise ValueError("Database port must be positive")
```

### **4. SOLID Principles**

#### **1. Single Responsibility Principle (SRP)**
*"A class should have only one reason to change."*

```python
# ❌ BAD: Multiple responsibilities in one class
class UserManager:
    """Violates SRP - handles user logic, email, and database operations."""
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        # User creation logic
        user = User(**user_data)
        
        # Database operation
        self.database.save(user)
        
        # Email sending
        self.send_welcome_email(user.email)
        
        return user
    
    def send_welcome_email(self, email: str) -> None:
        # Email logic here
        pass

# ✅ GOOD: Separated responsibilities
class UserService:
    """Single responsibility: User business logic only."""
    
    def __init__(
        self, 
        repository: UserRepository,
        email_service: EmailService
    ) -> None:
        self.repository = repository
        self.email_service = email_service
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create user with proper separation of concerns."""
        user = User(**user_data)
        saved_user = await self.repository.save(user)
        await self.email_service.send_welcome_email(saved_user.email)
        return saved_user

class UserRepository:
    """Single responsibility: Data persistence only."""
    
    async def save(self, user: User) -> User:
        """Save user to database."""
        # Database logic only
        pass

class EmailService:
    """Single responsibility: Email operations only."""
    
    async def send_welcome_email(self, email: str) -> None:
        """Send welcome email to user."""
        # Email logic only
        pass
```

#### **2. Open/Closed Principle (OCP)**
*"Software entities should be open for extension, but closed for modification."*

```python
# ✅ GOOD: Using abstract base classes for extensibility
from abc import ABC, abstractmethod
from enum import Enum

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    CRYPTO = "crypto"

class PaymentProcessor(ABC):
    """Abstract payment processor - closed for modification."""
    
    @abstractmethod
    async def process_payment(
        self, 
        amount: Decimal, 
        payment_data: Dict[str, Any]
    ) -> PaymentResult:
        """Process payment - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def validate_payment_data(self, payment_data: Dict[str, Any]) -> bool:
        """Validate payment data format."""
        pass

# ✅ Extensions without modifying existing code
class CreditCardProcessor(PaymentProcessor):
    """Credit card payment processor - open for extension."""
    
    async def process_payment(
        self, 
        amount: Decimal, 
        payment_data: Dict[str, Any]
    ) -> PaymentResult:
        """Process credit card payment."""
        if not self.validate_payment_data(payment_data):
            raise ValidationError("Invalid credit card data")
        
        # Credit card processing logic
        return PaymentResult(success=True, transaction_id="cc_123")
    
    def validate_payment_data(self, payment_data: Dict[str, Any]) -> bool:
        """Validate credit card data."""
        required_fields = ["card_number", "expiry", "cvv"]
        return all(field in payment_data for field in required_fields)

class PayPalProcessor(PaymentProcessor):
    """PayPal payment processor - new extension."""
    
    async def process_payment(
        self, 
        amount: Decimal, 
        payment_data: Dict[str, Any]
    ) -> PaymentResult:
        """Process PayPal payment."""
        # PayPal processing logic
        return PaymentResult(success=True, transaction_id="pp_456")
    
    def validate_payment_data(self, payment_data: Dict[str, Any]) -> bool:
        """Validate PayPal data."""
        return "paypal_token" in payment_data

# ✅ Factory pattern for processor selection
class PaymentProcessorFactory:
    """Factory for creating payment processors."""
    
    _processors = {
        PaymentMethod.CREDIT_CARD: CreditCardProcessor,
        PaymentMethod.PAYPAL: PayPalProcessor,
        # Easy to add new processors without modifying existing code
    }
    
    @classmethod
    def create_processor(cls, method: PaymentMethod) -> PaymentProcessor:
        """Create appropriate payment processor."""
        if method not in cls._processors:
            raise ValueError(f"Unsupported payment method: {method}")
        
        return cls._processors[method]()
```

#### **3. Liskov Substitution Principle (LSP)**
*"Objects of a superclass should be replaceable with objects of its subclasses."*

```python
# ✅ GOOD: Proper inheritance hierarchy respecting LSP
class Shape(ABC):
    """Base shape class."""
    
    @abstractmethod
    def area(self) -> float:
        """Calculate area - must return positive value."""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Calculate perimeter - must return positive value."""
        pass

class Rectangle(Shape):
    """Rectangle implementation respecting LSP."""
    
    def __init__(self, width: float, height: float) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        self.width = width
        self.height = height
    
    def area(self) -> float:
        """Calculate rectangle area."""
        return self.width * self.height
    
    def perimeter(self) -> float:
        """Calculate rectangle perimeter."""
        return 2 * (self.width + self.height)

class Square(Rectangle):
    """Square as special case of rectangle - proper LSP implementation."""
    
    def __init__(self, side: float) -> None:
        super().__init__(side, side)
    
    @property
    def side(self) -> float:
        """Get square side length."""
        return self.width
    
    # Inherits area() and perimeter() - works correctly as Rectangle

# ✅ Client code works with any Shape
def calculate_total_area(shapes: List[Shape]) -> float:
    """Calculate total area - works with any Shape subclass."""
    return sum(shape.area() for shape in shapes)

# ✅ LSP respected - substitution works perfectly
shapes = [
    Rectangle(5, 10),
    Square(4),
    # Any new Shape subclass will work here
]
total = calculate_total_area(shapes)  # Works correctly
```

#### **4. Interface Segregation Principle (ISP)**
*"Many client-specific interfaces are better than one general-purpose interface."*

```python
# ✅ GOOD: Segregated interfaces following ISP
class Printer(Protocol):
    """Focused interface for printing only."""
    
    def print_document(self, document: str) -> None:
        """Print a document."""
        ...

class Scanner(Protocol):
    """Focused interface for scanning only."""
    
    def scan_document(self) -> str:
        """Scan and return document content."""
        ...

class FaxMachine(Protocol):
    """Focused interface for faxing only."""
    
    def fax_document(self, document: str, number: str) -> None:
        """Fax document to number."""
        ...

class Copier(Protocol):
    """Focused interface for copying only."""
    
    def copy_document(self) -> str:
        """Copy and return document."""
        ...

# ✅ Implementations only depend on what they need
class SimplePrinter:
    """Simple printer - only implements what it needs."""
    
    def print_document(self, document: str) -> None:
        """Print document implementation."""
        print(f"Printing: {document}")

class MultiFunctionPrinter:
    """Advanced device implementing multiple interfaces."""
    
    def print_document(self, document: str) -> None:
        """Print implementation."""
        print(f"MFP Printing: {document}")
    
    def scan_document(self) -> str:
        """Scan implementation."""
        return "Scanned content"
    
    def copy_document(self) -> str:
        """Copy implementation."""
        scanned = self.scan_document()
        self.print_document(scanned)
        return scanned

# ✅ Clients depend only on interfaces they use
class PrintService:
    """Service only needs printing capability."""
    
    def __init__(self, printer: Printer) -> None:
        self.printer = printer  # Only depends on Printer interface
    
    def print_report(self, data: Dict[str, Any]) -> None:
        """Print report using any printer."""
        report = self.format_report(data)
        self.printer.print_document(report)
```

#### **5. Dependency Inversion Principle (DIP)**
*"Depend on abstractions, not concretions."*

```python
# ✅ GOOD: Depending on abstractions (DIP compliant)
class EmailService(Protocol):
    """Email service abstraction."""
    
    async def send_confirmation(self, email: str, order: Order) -> None:
        """Send order confirmation email."""
        ...

class OrderRepository(Protocol):
    """Order repository abstraction."""
    
    async def save_order(self, order: Order) -> Order:
        """Save order to storage."""
        ...

class OrderService:
    """High-level module depending on abstractions."""
    
    def __init__(
        self,
        email_service: EmailService,      # Abstraction
        repository: OrderRepository       # Abstraction
    ) -> None:
        self.email_service = email_service
        self.repository = repository
    
    async def process_order(self, order: Order) -> Order:
        """Process order using injected dependencies."""
        saved_order = await self.repository.save_order(order)
        await self.email_service.send_confirmation(
            saved_order.customer_email, 
            saved_order
        )
        return saved_order

# ✅ Concrete implementations
class SMTPEmailService:
    """SMTP email implementation."""
    
    async def send_confirmation(self, email: str, order: Order) -> None:
        """Send email via SMTP."""
        # SMTP implementation
        pass

class PostgreSQLOrderRepository:
    """PostgreSQL order repository."""
    
    async def save_order(self, order: Order) -> Order:
        """Save order to PostgreSQL."""
        # PostgreSQL implementation
        pass

class InMemoryOrderRepository:
    """In-memory repository for testing."""
    
    def __init__(self) -> None:
        self.orders: List[Order] = []
    
    async def save_order(self, order: Order) -> Order:
        """Save order to memory."""
        self.orders.append(order)
        return order

# ✅ Dependency injection at application boundary
def create_order_service() -> OrderService:
    """Factory function for dependency injection."""
    email_service = SMTPEmailService()
    repository = PostgreSQLOrderRepository()
    
    return OrderService(
        email_service=email_service,
        repository=repository
    )

# ✅ Easy testing with dependency injection
def create_test_order_service() -> OrderService:
    """Create service with test doubles."""
    email_service = MockEmailService()
    repository = InMemoryOrderRepository()
    
    return OrderService(
        email_service=email_service,
        repository=repository
    )
```

### **SOLID Principles in Practice**
```python
# ✅ SOLID-compliant class example
class UserRegistrationService:
    """
    Example demonstrating all SOLID principles:
    
    S - Single responsibility: Only handles user registration
    O - Open/closed: Extensible via strategy pattern for validation
    L - Liskov substitution: All validators are interchangeable
    I - Interface segregation: Small, focused interfaces
    D - Dependency inversion: Depends on abstractions, not concretions
    """
    
    def __init__(
        self,
        user_repository: UserRepository,           # DIP: Abstraction
        email_service: EmailService,               # DIP: Abstraction
        validators: List[UserValidator]            # DIP: Abstractions
    ) -> None:
        self._repository = user_repository
        self._email_service = email_service
        self._validators = validators
    
    async def register_user(self, user_data: Dict[str, Any]) -> User:
        """
        Register new user following SOLID principles.
        
        SRP: Only responsible for user registration flow
        OCP: New validators can be added without modification
        LSP: All validators work interchangeably
        ISP: Uses focused interfaces
        DIP: Depends on abstractions
        """
        # Validate using strategy pattern (OCP)
        for validator in self._validators:
            await validator.validate(user_data)  # LSP: All validators substitutable
        
        # Create and save user (SRP: delegate to repository)
        user = User(**user_data)
        saved_user = await self._repository.save(user)  # DIP: Use abstraction
        
        # Send welcome email (SRP: delegate to email service)
        await self._email_service.send_welcome_email(saved_user.email)  # DIP
        
        return saved_user
```

---

## 🛡️ **Type Safety & Validation**

### **1. Pydantic Models for Data Validation**
```python
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from typing import Optional
import re

class UserProfile(BaseModel):
    """Type-safe user profile with validation."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    age: int = Field(..., ge=18, le=120)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    tags: List[str] = Field(default_factory=list, max_items=10)
    
    @validator('username')
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only alphanumeric, underscore, hyphen')
        return v.lower()
    
    @validator('tags')
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @root_validator
    def validate_model(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-field validation."""
        username = values.get('username', '')
        email = values.get('email', '')
        
        if username in email:
            raise ValueError('Username cannot be part of email')
        
        return values
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = 'forbid'  # Prevent extra fields
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### **2. Generic Types and Type Variables**
```python
from typing import TypeVar, Generic, Protocol
from abc import ABC, abstractmethod

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Repository(Protocol, Generic[T]):
    """Repository protocol for type safety."""
    
    async def get(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        ...
    
    async def create(self, entity: T) -> T:
        """Create new entity."""
        ...
    
    async def update(self, id: int, entity: T) -> T:
        """Update existing entity."""
        ...

class BaseService(Generic[T]):
    """Generic service class."""
    
    def __init__(self, repository: Repository[T]) -> None:
        self.repository = repository
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID with type safety."""
        return await self.repository.get(id)
```

---

## ⚡ **Performance & Optimization**

### **1. Async/Await Patterns**
```python
import asyncio
from typing import List, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor

# ✅ Async I/O operations
async def fetch_multiple_urls(urls: List[str]) -> List[Dict[str, Any]]:
    """Fetch multiple URLs concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for response in responses:
            if isinstance(response, Exception):
                logger.error(f"Request failed: {response}")
                continue
            results.append(response.json())
        
        return results

# ✅ CPU-bound operations with thread pool
async def process_data_concurrently(
    data: List[Any], 
    processor: Callable[[Any], Any]
) -> List[Any]:
    """Process CPU-bound tasks concurrently."""
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(executor, processor, item) 
            for item in data
        ]
        return await asyncio.gather(*tasks)
```

### **2. Caching and Memoization**
```python
from functools import lru_cache, wraps
from typing import Dict, Any
import asyncio

# ✅ LRU cache for expensive computations
@lru_cache(maxsize=128)
def compute_expensive_result(data: str) -> float:
    """Cache expensive computational results."""
    # Expensive computation here
    return sum(ord(c) for c in data) / len(data)

# ✅ Async cache decorator
def async_cache(maxsize: int = 128):
    """Async LRU cache decorator."""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        cache: Dict[str, T] = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            key = f"{args}{kwargs}"
            if key not in cache:
                cache[key] = await func(*args, **kwargs)
                # Implement LRU eviction logic
                if len(cache) > maxsize:
                    # Remove oldest entry
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
            return cache[key]
        return wrapper
    return decorator
```

---

## 📝 **Documentation Standards**

### **1. Module-Level Documentation**
```python
"""
User management module for the application.

This module provides comprehensive user management functionality including
user creation, authentication, profile management, and role-based access control.

Classes:
    UserService: Main service for user operations
    UserRepository: Data access layer for users
    UserProfile: Pydantic model for user data

Functions:
    create_user: Create a new user account
    authenticate_user: Authenticate user credentials
    get_user_profile: Retrieve user profile information

Example:
    >>> from app.users import UserService, UserRepository
    >>> repo = UserRepository(database_url="sqlite:///users.db")
    >>> service = UserService(repo)
    >>> user = await service.create_user({"username": "john", "email": "john@example.com"})
"""
```

### **2. API Documentation (FastAPI)**
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI(
    title="User Management API",
    description="Comprehensive user management system with authentication",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

class UserCreateRequest(BaseModel):
    """Request model for user creation."""
    username: str = Field(..., description="Unique username (3-50 characters)")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")

@app.post(
    "/users/", 
    response_model=UserProfile,
    status_code=201,
    summary="Create new user",
    description="Create a new user account with validation and password hashing",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Username or email already exists"}
    }
)
async def create_user(
    user_data: UserCreateRequest,
    service: UserService = Depends(get_user_service)
) -> UserProfile:
    """
    Create a new user account.
    
    This endpoint creates a new user with the provided information,
    validates all inputs, and returns the created user profile.
    """
    try:
        return await service.create_user(user_data.dict())
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 🧪 **Testing Principles**

### **1. Comprehensive Test Coverage**
```python
import pytest
from unittest.mock import AsyncMock, Mock
from app.services import UserService
from app.exceptions import ValidationError

class TestUserService:
    """Comprehensive test suite for UserService."""
    
    @pytest.fixture
    async def user_service(self) -> UserService:
        """Create UserService with mocked dependencies."""
        mock_repo = AsyncMock()
        mock_config = Mock()
        mock_config.min_username_length = 3
        mock_logger = Mock()
        
        return UserService(
            repository=mock_repo,
            config=mock_config,
            logger=mock_logger
        )
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service: UserService):
        """Test successful user creation."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "secure123"
        }
        expected_user = UserProfile(**user_data)
        user_service.repository.create.return_value = expected_user
        
        # Act
        result = await user_service.create_user(user_data)
        
        # Assert
        assert result == expected_user
        user_service.repository.create.assert_called_once_with(user_data)
        user_service.logger.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_validation_error(self, user_service: UserService):
        """Test user creation with invalid data."""
        # Arrange
        invalid_data = {"username": "ab", "email": "invalid"}  # Too short username
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(invalid_data)
        
        assert "username too short" in str(exc_info.value).lower()
    
    @pytest.mark.parametrize("username,expected_valid", [
        ("validuser", True),
        ("ab", False),
        ("a" * 51, False),
        ("user-123", True),
        ("user@invalid", False),
    ])
    async def test_username_validation(
        self, 
        user_service: UserService, 
        username: str, 
        expected_valid: bool
    ):
        """Test username validation with various inputs."""
        user_data = {
            "username": username,
            "email": "test@example.com",
            "password": "secure123"
        }
        
        if expected_valid:
            # Should not raise exception
            await user_service.create_user(user_data)
        else:
            # Should raise ValidationError
            with pytest.raises(ValidationError):
                await user_service.create_user(user_data)
```

### **2. Property-Based Testing**
```python
from hypothesis import given, strategies as st
import pytest

@given(
    username=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    email=st.emails(),
    age=st.integers(min_value=18, max_value=120)
)
def test_user_profile_creation_properties(username: str, email: str, age: int):
    """Property-based test for UserProfile validation."""
    user_data = {
        "username": username,
        "email": email,
        "age": age
    }
    
    # Should always create valid user profile
    profile = UserProfile(**user_data)
    assert profile.username == username.lower()  # Should be normalized
    assert profile.email == email
    assert profile.age == age
    assert profile.is_active is True  # Default value
```

---

## 🔒 **Security Considerations**

### **1. Input Validation and Sanitization**
```python
import html
import re
from typing import Any, Dict

def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize user input to prevent injection attacks."""
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # HTML escape
            value = html.escape(value)
            # Remove potentially dangerous characters
            value = re.sub(r'[<>"\']', '', value)
            # Limit length
            value = value[:1000]
        
        sanitized[key] = value
    
    return sanitized

# ✅ SQL injection prevention with parameterized queries
async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email with SQL injection prevention."""
    query = "SELECT * FROM users WHERE email = :email"
    # Use parameterized query - never string formatting!
    result = await database.fetch_one(query, {"email": email})
    return User(**result) if result else None
```

### **2. Authentication and Authorization**
```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityService:
    """Security service for authentication and authorization."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def hash_password(self, password: str) -> str:
        """Hash password securely."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
```

---

## 📊 **Quality Metrics & Standards**

### **Enforcement Checklist**
```yaml
Code Quality:
  - ✅ Type coverage: 100%
  - ✅ Documentation coverage: 100%
  - ✅ Test coverage: >90%
  - ✅ Complexity: <10 per function
  - ✅ Line length: <88 characters
  - ✅ Function length: <50 lines

SOLID Principles:
  - ✅ Single Responsibility: One class, one purpose
  - ✅ Open/Closed: Open for extension, closed for modification
  - ✅ Liskov Substitution: Subclasses replaceable with base classes
  - ✅ Interface Segregation: Small, focused interfaces
  - ✅ Dependency Inversion: Depend on abstractions

Security:
  - ✅ Input validation: All user inputs
  - ✅ SQL injection prevention: Parameterized queries
  - ✅ XSS prevention: HTML escaping
  - ✅ Authentication: JWT with secure algorithms
  - ✅ Authorization: Role-based access control

Performance:
  - ✅ Async I/O: All network operations
  - ✅ Database connections: Connection pooling
  - ✅ Caching: LRU cache for expensive operations
  - ✅ Monitoring: Structured logging with metrics
```

---

## 🎯 **Conclusion**

These coding standards represent my commitment to producing **enterprise-grade, maintainable, and secure Python applications**. Every line of code adheres to these principles, ensuring:

### **Core Foundations**
- **Type Safety**: 100% type coverage prevents runtime errors
- **Documentation**: Complete documentation enables team collaboration
- **SOLID Principles**: Clean object-oriented design for maintainability
- **Performance**: Async-first approach handles scale effectively
- **Security**: Comprehensive input validation and authentication
- **Testing**: High coverage ensures reliability
- **Modern Python**: Leverages latest language features

### **Quality Guarantees**
- ✅ **Maintainable**: Modular design enables easy updates
- ✅ **Extensible**: Open/Closed principle allows growth without breaking changes
- ✅ **Testable**: Dependency injection enables comprehensive testing
- ✅ **Secure**: Input validation and authentication prevent vulnerabilities
- ✅ **Performant**: Async operations and caching optimize speed
- ✅ **Readable**: Clear documentation and type hints improve understanding

**These standards are non-negotiable and form the foundation of all my development work.**

---

**Document Status: ✅ ACTIVE**  
**Last Updated: December 2024**  
**Next Review: Quarterly**  
**Compliance: MANDATORY**
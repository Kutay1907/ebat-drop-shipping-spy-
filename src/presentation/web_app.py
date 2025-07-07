"""
Web Application

Main Flask/Quart web application with clean architecture.
Implements dependency injection and follows SOLID principles.
"""

import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid

from quart import Quart, request, jsonify, render_template, redirect, url_for
from quart_cors import cors

from ..application.services.keyword_input_service import KeywordInputService
from ..application.services.scraping_orchestrator import ScrapingOrchestrator
from ..domain.models import SearchCriteria, ScrapingResult
from ..domain.exceptions import ValidationError, ScrapingError
from ..infrastructure.dependency_injection import DependencyContainer
from config.simple_settings import settings


class EbayScraperWebApp:
    """
    Main web application class implementing clean architecture.
    
    Responsibilities:
    - HTTP request handling
    - Route definition
    - Template rendering
    - API endpoint management
    """
    
    def __init__(self, dependency_container: DependencyContainer):
        """
        Initialize web application with dependency injection.
        
        Args:
            dependency_container: Container with all configured dependencies
        """
        # Get the project root directory (two levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        template_dir = project_root / "templates"
        
        self.app = Quart(__name__, template_folder=str(template_dir))
        self.app.secret_key = settings.web_server.secret_key
        
        # Enable CORS if configured
        if settings.web_server.enable_cors:
            cors(self.app, allow_origin="*")
        
        # Inject dependencies
        self._keyword_service = dependency_container.get_keyword_input_service()
        self._scraping_orchestrator = dependency_container.get_scraping_orchestrator()
        self._database_storage = dependency_container.get_database_storage()
        self._logger = dependency_container.get_logger()
        
        # Register routes
        self._register_routes()
        
        # Register error handlers
        self._register_error_handlers()

    def _register_routes(self) -> None:
        """Register all application routes."""
        
        # Main routes
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/search', 'search', self.search, methods=['GET', 'POST'])
        self.app.add_url_rule('/results/<result_id>', 'results', self.results, methods=['GET'])
        self.app.add_url_rule('/health', 'health', self.health_check, methods=['GET'])
        
        # API routes
        api_prefix = settings.web_server.api_prefix
        self.app.add_url_rule(f'{api_prefix}/scrape', 'api_scrape', self.api_scrape, methods=['POST'])
        self.app.add_url_rule(f'{api_prefix}/status/<result_id>', 'api_status', self.api_status, methods=['GET'])
        self.app.add_url_rule(f'{api_prefix}/health', 'api_health', self.api_health_check, methods=['GET'])

    def _register_error_handlers(self) -> None:
        """Register error handlers for the application."""
        
        @self.app.errorhandler(ValidationError)
        async def handle_validation_error(error: ValidationError):
            """Handle validation errors."""
            await self._logger.log_warning(
                "Validation error occurred",
                error=str(error),
                field=getattr(error, 'field', None)
            )
            
            if request.is_json:
                return jsonify({
                    'error': 'validation_error',
                    'message': str(error),
                    'field': getattr(error, 'field', None)
                }), 400
            else:
                return await render_template(
                    'error.html',
                    error_type='Validation Error',
                    error_message=str(error)
                ), 400
        
        @self.app.errorhandler(ScrapingError)
        async def handle_scraping_error(error: ScrapingError):
            """Handle scraping errors."""
            await self._logger.log_error(
                "Scraping error occurred",
                error=str(error),
                url=getattr(error, 'url', None)
            )
            
            if request.is_json:
                return jsonify({
                    'error': 'scraping_error',
                    'message': str(error)
                }), 500
            else:
                return await render_template(
                    'error.html',
                    error_type='Scraping Error',
                    error_message=str(error)
                ), 500
        
        @self.app.errorhandler(500)
        async def handle_internal_error(error):
            """Handle internal server errors."""
            await self._logger.log_error(
                "Internal server error",
                error=str(error)
            )
            
            if request.is_json:
                return jsonify({
                    'error': 'internal_error',
                    'message': 'An internal error occurred'
                }), 500
            else:
                return await render_template(
                    'error.html',
                    error_type='Internal Error',
                    error_message='An unexpected error occurred'
                ), 500

    async def index(self):
        """Home page."""
        return await render_template('index.html', app_name=settings.app.app_name)

    async def search(self):
        """Search page for inputting keywords and criteria."""
        if request.method == 'GET':
            return await render_template('search.html')
        
        # POST request - process search
        try:
            form_data = await request.form
            
            # Validate input using KeywordInputService
            search_criteria = await self._keyword_service.validate_form_data(dict(form_data))
            
            # Start scraping operation and get REAL result ID from database
            result = await self._scraping_orchestrator.execute_scraping(search_criteria)
            
            # Use the actual result_id from database storage, not Python object ID
            actual_result_id = result.result_id
            if not actual_result_id:
                # This should not happen with the fixed storage, but fail safe
                await self._logger.log_error(
                    "❌ No result ID returned from scraping operation",
                    keyword=search_criteria.keyword,
                    status=result.status.value
                )
                return await render_template(
                    'search.html',
                    error="Scraping completed but result ID is missing. Please try again.",
                    form_data=dict(await request.form)
                ), 500
            
            await self._logger.log_info(
                "🚀 REAL SCRAPING: Redirecting to results",
                result_id=actual_result_id,
                keyword=search_criteria.keyword,
                products_found=len(result.products) if result.products else 0
            )
            
            # Redirect to results page with REAL result ID from database
            return redirect(url_for('results', result_id=actual_result_id))
            
        except ValidationError as e:
            await self._logger.log_warning(
                "Search validation failed",
                error=str(e),
                form_data=dict(await request.form)
            )
            
            return await render_template(
                'search.html',
                error=str(e),
                form_data=dict(await request.form)
            ), 400
        
        except Exception as e:
            await self._logger.log_error(
                "Search processing failed",
                error=str(e),
                form_data=dict(await request.form)
            )
            
            return await render_template(
                'search.html',
                error="An unexpected error occurred. Please try again.",
                form_data=dict(await request.form)
            ), 500

    async def results(self, result_id: str):
        """Display scraping results."""
        try:
            # Get real result from database storage directly
            result = await self._database_storage.get_scraping_result(result_id)
            
            if not result:
                await self._logger.log_warning(
                    "❌ No scraping result found in database",
                    result_id=result_id
                )
                return await render_template(
                    'error.html',
                    error_type='Results Not Found',
                    error_message=f'No scraping result found for ID: {result_id}'
                ), 404
            
            # Convert result to dictionary for template
            result_data = {
                'result_id': result_id,
                'keyword': result.criteria.keyword,
                'status': result.status.value,
                'products_found': len(result.products),
                'duration': result.scraping_duration or 0.0,
                'created_at': result.created_at.isoformat(),
                'products': []
            }
            
            # Convert products to template-friendly format
            for product in result.products:
                product_data = {
                    'title': product.title,
                    'price': f"${product.price}",
                    'condition': product.condition.value,
                    'sold_count': product.sold_count,
                    'url': str(product.item_url),
                    'seller_name': product.seller_info.seller_name if product.seller_info else 'Unknown',
                    'free_shipping': product.free_shipping
                }
                result_data['products'].append(product_data)
            
            await self._logger.log_info(
                "✅ REAL DATA: Displaying scraping results from database",
                result_id=result_id,
                products_count=len(result.products),
                status=result.status.value
            )
            
            return await render_template(
                'results.html',
                result=result_data,
                result_id=result_id
            )
            
        except Exception as e:
            await self._logger.log_error(
                "Failed to load real scraping results",
                result_id=result_id,
                error=str(e)
            )
            
            return await render_template(
                'error.html',
                error_type='Results Error',
                error_message='Failed to load scraping results'
            ), 500

    async def health_check(self):
        """Health check endpoint."""
        try:
            # Simple health status check
            health_status = {
                'overall': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {
                    'scraping_orchestrator': 'available',
                    'database_storage': 'available',
                    'production_mode': not settings.app.use_mock_data
                }
            }
            
            return await render_template('health.html', status=health_status)
                
        except Exception as e:
            await self._logger.log_error("Health check failed", error=str(e))
            
            health_status = {
                'overall': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
            
            return await render_template(
                'error.html',
                error_type='Health Check Error',
                error_message='Health check failed'
            ), 503

    # API Endpoints

    async def api_scrape(self):
        """API endpoint for starting scraping operation."""
        try:
            data = await request.get_json()
            
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Validate input
            search_criteria = await self._keyword_service.validate_form_data(data)
            
            # Start scraping (in a real implementation, this might be async)
            result = await self._scraping_orchestrator.execute_scraping(search_criteria)
            
            return jsonify({
                'status': 'success',
                'result_id': str(id(result)),
                'message': 'Scraping completed successfully',
                'data': {
                    'products_found': len(result.products),
                    'status': result.status.value,
                    'duration': result.scraping_duration
                }
            })
            
        except ValidationError as e:
            return jsonify({
                'error': 'validation_error',
                'message': str(e),
                'field': getattr(e, 'field', None)
            }), 400
            
        except ScrapingError as e:
            return jsonify({
                'error': 'scraping_error',
                'message': str(e)
            }), 500
            
        except Exception as e:
            await self._logger.log_error("API scraping failed", error=str(e))
            
            return jsonify({
                'error': 'internal_error',
                'message': 'An unexpected error occurred'
            }), 500

    async def api_status(self, result_id: str):
        """API endpoint for checking scraping status."""
        try:
            # Use database storage for API status retrieval
            result = await self._database_storage.get_scraping_result(result_id)
            
            if not result:
                return jsonify({'error': 'Result not found'}), 404
            
            return jsonify({
                'result_id': result_id,
                'status': result.status.value,
                'created_at': result.created_at.isoformat(),
                'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                'duration': result.scraping_duration,
                'products_count': len(result.products),
                'error_message': result.error_message
            })
            
        except Exception as e:
            await self._logger.log_error(
                "API status check failed",
                result_id=result_id,
                error=str(e)
            )
            
            return jsonify({
                'error': 'internal_error',
                'message': 'Failed to retrieve status'
            }), 500

    async def api_health_check(self):
        """API health check endpoint."""
        try:
            # Simple health status for API
            health_status = {
                'overall': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {
                    'scraping_orchestrator': 'available',
                    'database_storage': 'available',
                    'production_mode': not settings.app.use_mock_data
                }
            }
            
            return jsonify(health_status), 200
            
        except Exception as e:
            await self._logger.log_error("API health check failed", error=str(e))
            
            return jsonify({
                'overall': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    def run(self):
        """Run the web application."""
        return self.app.run(
            host=settings.web_server.host,
            port=settings.web_server.port,
            debug=settings.web_server.debug
        ) 
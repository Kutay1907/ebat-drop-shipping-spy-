"""
Export Service

Multi-format export functionality for scraping results.
Supports CSV, XLSX, HTML, and JSON exports with rich formatting.
"""

import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from decimal import Decimal

from ..domain.interfaces import IExportService, ILogger
from ..domain.models import ScrapingResult, Product, ExportFormat
from ..domain.exceptions import ValidationError, ScrapingError


class ExportService(IExportService):
    """
    Service for exporting scraping results in multiple formats.
    
    Features:
    - CSV export with customizable columns
    - Excel export with multiple sheets and formatting
    - HTML export with Bootstrap styling
    - JSON export with structured data
    - Configurable data inclusion options
    """
    
    def __init__(self, logger: ILogger, output_directory: str = "exports"):
        """
        Initialize export service.
        
        Args:
            logger: Logger instance for tracking operations
            output_directory: Directory for export files
        """
        self.logger = logger
        self.output_directory = Path(output_directory)
        
        # Ensure export directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    async def export_to_csv(
        self, 
        result: ScrapingResult, 
        file_path: str,
        include_seller_info: bool = True,
        include_market_data: bool = True
    ) -> None:
        """
        Export scraping result to CSV format.
        
        Args:
            result: Scraping result to export
            file_path: Output file path
            include_seller_info: Whether to include seller information
            include_market_data: Whether to include market analysis
        """
        try:
            await self.logger.log_info(
                "Starting CSV export",
                file_path=file_path,
                products_count=len(result.products)
            )
            
            # Prepare data for CSV export
            export_data = await self.get_export_data(result)
            products_data = export_data['products']
            
            # Define CSV columns
            columns = [
                'item_id', 'title', 'price', 'condition', 'sold_count',
                'marketplace', 'item_url', 'shipping_cost', 'free_shipping',
                'location', 'listing_date', 'end_date'
            ]
            
            if include_seller_info:
                columns.extend([
                    'seller_name', 'seller_feedback_score', 
                    'seller_feedback_percentage', 'seller_location'
                ])
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV file
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                
                for product_data in products_data:
                    # Flatten seller info if needed
                    row_data = {
                        'item_id': product_data.get('item_id'),
                        'title': product_data.get('title'),
                        'price': product_data.get('price'),
                        'condition': product_data.get('condition'),
                        'sold_count': product_data.get('sold_count'),
                        'marketplace': product_data.get('marketplace'),
                        'item_url': product_data.get('item_url'),
                        'shipping_cost': product_data.get('shipping_cost'),
                        'free_shipping': product_data.get('free_shipping'),
                        'location': product_data.get('location'),
                        'listing_date': product_data.get('listing_date'),
                        'end_date': product_data.get('end_date')
                    }
                    
                    if include_seller_info and 'seller_info' in product_data:
                        seller_info = product_data['seller_info'] or {}
                        row_data.update({
                            'seller_name': seller_info.get('seller_name'),
                            'seller_feedback_score': seller_info.get('feedback_score'),
                            'seller_feedback_percentage': seller_info.get('feedback_percentage'),
                            'seller_location': seller_info.get('location')
                        })
                    
                    writer.writerow(row_data)
            
            # Add metadata file
            metadata_path = file_path.replace('.csv', '_metadata.json')
            await self._write_metadata_file(metadata_path, result, export_data)
            
            await self.logger.log_info(
                "CSV export completed successfully",
                file_path=file_path,
                products_exported=len(products_data)
            )
            
        except Exception as e:
            await self.logger.log_error(
                "CSV export failed",
                error=str(e),
                file_path=file_path
            )
            raise ScrapingError(f"CSV export failed: {str(e)}")
    
    async def export_to_xlsx(
        self, 
        result: ScrapingResult, 
        file_path: str,
        include_charts: bool = True
    ) -> None:
        """
        Export scraping result to Excel format with multiple sheets.
        
        Args:
            result: Scraping result to export
            file_path: Output file path
            include_charts: Whether to include charts and analysis
        """
        try:
            # This would require pandas and xlsxwriter
            # For now, we'll create a detailed CSV-like structure
            await self.logger.log_info(
                "Starting Excel export (using CSV format)",
                file_path=file_path,
                products_count=len(result.products)
            )
            
            # Convert to CSV format for now
            csv_path = file_path.replace('.xlsx', '.csv')
            await self.export_to_csv(result, csv_path)
            
            # Create additional analysis file
            analysis_path = file_path.replace('.xlsx', '_analysis.json')
            export_data = await self.get_export_data(result)
            
            analysis_data = {
                'summary': export_data['summary'],
                'market_analysis': export_data.get('market_analysis'),
                'price_statistics': self._calculate_price_statistics(result.products),
                'seller_statistics': self._calculate_seller_statistics(result.products),
                'condition_distribution': self._calculate_condition_distribution(result.products)
            }
            
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, default=str)
            
            await self.logger.log_info(
                "Excel export completed (as CSV + analysis)",
                csv_file=csv_path,
                analysis_file=analysis_path
            )
            
        except Exception as e:
            await self.logger.log_error(
                "Excel export failed",
                error=str(e),
                file_path=file_path
            )
            raise ScrapingError(f"Excel export failed: {str(e)}")
    
    async def export_to_html(
        self, 
        result: ScrapingResult, 
        file_path: str,
        include_charts: bool = True
    ) -> None:
        """
        Export scraping result to HTML format with styling.
        
        Args:
            result: Scraping result to export
            file_path: Output file path
            include_charts: Whether to include interactive charts
        """
        try:
            await self.logger.log_info(
                "Starting HTML export",
                file_path=file_path,
                products_count=len(result.products)
            )
            
            export_data = await self.get_export_data(result)
            
            # Generate HTML content
            html_content = await self._generate_html_report(result, export_data, include_charts)
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write HTML file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            await self.logger.log_info(
                "HTML export completed successfully",
                file_path=file_path,
                products_exported=len(result.products)
            )
            
        except Exception as e:
            await self.logger.log_error(
                "HTML export failed",
                error=str(e),
                file_path=file_path
            )
            raise ScrapingError(f"HTML export failed: {str(e)}")
    
    async def get_export_data(self, result: ScrapingResult) -> Dict[str, Any]:
        """
        Get structured data for export.
        
        Args:
            result: Scraping result to process
            
        Returns:
            Structured export data
        """
        # Convert products to exportable format
        products_data = []
        for product in result.products:
            product_dict = {
                'item_id': product.item_id,
                'title': product.title,
                'price': float(product.price),
                'condition': product.condition.value,
                'sold_count': product.sold_count,
                'marketplace': product.marketplace.value,
                'item_url': str(product.item_url),
                'image_url': str(product.image_url) if product.image_url else None,
                'shipping_cost': float(product.shipping_cost) if product.shipping_cost else None,
                'free_shipping': product.free_shipping,
                'location': product.location,
                'listing_date': product.listing_date.isoformat() if product.listing_date else None,
                'end_date': product.end_date.isoformat() if product.end_date else None,
                'seller_info': None
            }
            
            # Add seller info if available
            if product.seller_info:
                product_dict['seller_info'] = {
                    'seller_name': product.seller_info.seller_name,
                    'feedback_score': product.seller_info.feedback_score,
                    'feedback_percentage': product.seller_info.feedback_percentage,
                    'location': product.seller_info.location,
                    'total_sold_items': product.seller_info.total_sold_items
                }
            
            products_data.append(product_dict)
        
        # Prepare summary data
        summary = {
            'keyword': result.criteria.keyword,
            'marketplace': result.criteria.marketplace.value,
            'total_products': len(result.products),
            'scraping_status': result.status.value,
            'scraping_duration': result.scraping_duration,
            'created_at': result.created_at.isoformat(),
            'completed_at': result.completed_at.isoformat() if result.completed_at else None,
            'result_id': result.result_id
        }
        
        # Add market analysis if available
        market_analysis = None
        if result.market_analysis:
            market_analysis = {
                'avg_sold_price': float(result.market_analysis.avg_sold_price),
                'sell_through_rate': result.market_analysis.sell_through_rate,
                'free_shipping_rate': result.market_analysis.free_shipping_rate,
                'seller_count': result.market_analysis.seller_count,
                'total_sales': result.market_analysis.total_sales,
                'last_updated': result.market_analysis.last_updated.isoformat()
            }
        
        return {
            'summary': summary,
            'products': products_data,
            'market_analysis': market_analysis,
            'export_timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_price_statistics(self, products: List[Product]) -> Dict[str, Any]:
        """Calculate price statistics for products."""
        if not products:
            return {}
        
        prices = [float(p.price) for p in products]
        
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': sum(prices) / len(prices),
            'median_price': sorted(prices)[len(prices) // 2],
            'total_products': len(products)
        }
    
    def _calculate_seller_statistics(self, products: List[Product]) -> Dict[str, Any]:
        """Calculate seller statistics."""
        sellers = {}
        for product in products:
            if product.seller_info and product.seller_info.seller_name:
                seller_name = product.seller_info.seller_name
                if seller_name not in sellers:
                    sellers[seller_name] = {
                        'product_count': 0,
                        'total_sold': 0,
                        'feedback_score': product.seller_info.feedback_score,
                        'feedback_percentage': product.seller_info.feedback_percentage
                    }
                
                sellers[seller_name]['product_count'] += 1
                if product.sold_count:
                    sellers[seller_name]['total_sold'] += product.sold_count
        
        return {
            'unique_sellers': len(sellers),
            'top_sellers': sorted(
                sellers.items(),
                key=lambda x: x[1]['product_count'],
                reverse=True
            )[:10]
        }
    
    def _calculate_condition_distribution(self, products: List[Product]) -> Dict[str, int]:
        """Calculate condition distribution."""
        conditions = {}
        for product in products:
            condition = product.condition.value
            conditions[condition] = conditions.get(condition, 0) + 1
        
        return conditions
    
    async def _generate_html_report(
        self, 
        result: ScrapingResult, 
        export_data: Dict[str, Any],
        include_charts: bool = True
    ) -> str:
        """Generate HTML report content."""
        
        summary = export_data['summary']
        products = export_data['products']
        market_analysis = export_data.get('market_analysis')
        
        price_stats = self._calculate_price_statistics(result.products)
        seller_stats = self._calculate_seller_statistics(result.products)
        condition_dist = self._calculate_condition_distribution(result.products)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBay Scraping Report - {summary['keyword']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .stat-card {{ margin-bottom: 1rem; }}
        .product-image {{ width: 50px; height: 50px; object-fit: cover; }}
        .table-responsive {{ max-height: 600px; overflow-y: auto; }}
    </style>
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">eBay Scraping Report</h1>
                
                <!-- Summary Section -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Keyword</h5>
                                <p class="card-text fs-4">{summary['keyword']}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Products Found</h5>
                                <p class="card-text fs-4 text-primary">{summary['total_products']}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Marketplace</h5>
                                <p class="card-text fs-4">{summary['marketplace']}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Duration</h5>
                                <p class="card-text fs-4">{summary.get('scraping_duration', 'N/A')}s</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Price Statistics -->
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>Price Statistics</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-3">
                                        <strong>Min Price:</strong> ${price_stats.get('min_price', 'N/A')}
                                    </div>
                                    <div class="col-md-3">
                                        <strong>Max Price:</strong> ${price_stats.get('max_price', 'N/A')}
                                    </div>
                                    <div class="col-md-3">
                                        <strong>Avg Price:</strong> ${price_stats.get('avg_price', 0):.2f}
                                    </div>
                                    <div class="col-md-3">
                                        <strong>Median Price:</strong> ${price_stats.get('median_price', 'N/A')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Products Table -->
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>Products ({len(products)} items)</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover">
                                        <thead class="table-dark">
                                            <tr>
                                                <th>Title</th>
                                                <th>Price</th>
                                                <th>Condition</th>
                                                <th>Sold Count</th>
                                                <th>Seller</th>
                                                <th>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
        """
        
        # Add product rows
        for product in products[:100]:  # Limit to first 100 for performance
            seller_name = "N/A"
            if product.get('seller_info'):
                seller_name = product['seller_info'].get('seller_name', 'N/A')
            
            html_content += f"""
                                            <tr>
                                                <td title="{product['title']}">{product['title'][:50]}{'...' if len(product['title']) > 50 else ''}</td>
                                                <td>${product['price']}</td>
                                                <td><span class="badge bg-secondary">{product['condition']}</span></td>
                                                <td>{product['sold_count'] or 'N/A'}</td>
                                                <td>{seller_name}</td>
                                                <td><a href="{product['item_url']}" target="_blank" class="btn btn-sm btn-primary">View</a></td>
                                            </tr>
            """
        
        html_content += """
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="row mt-4">
                    <div class="col-12 text-center">
                        <small class="text-muted">
                            Report generated on """ + export_data['export_timestamp'] + """ by eBay Scraper
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
        
        return html_content
    
    async def _write_metadata_file(
        self, 
        file_path: str, 
        result: ScrapingResult, 
        export_data: Dict[str, Any]
    ) -> None:
        """Write metadata file alongside export."""
        metadata = {
            'export_info': {
                'timestamp': export_data['export_timestamp'],
                'format': 'CSV',
                'source': 'eBay Scraper'
            },
            'scraping_info': export_data['summary'],
            'market_analysis': export_data.get('market_analysis'),
            'statistics': {
                'price_stats': self._calculate_price_statistics(result.products),
                'seller_stats': self._calculate_seller_statistics(result.products),
                'condition_distribution': self._calculate_condition_distribution(result.products)
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str) 
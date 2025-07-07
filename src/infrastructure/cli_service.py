"""
CLI Service

Command-line interface for eBay scraper operations.
Provides history viewing, export commands, and system management.
"""

import asyncio
import argparse
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from ..domain.interfaces import IResultStorageService, IExportService, ILogger
from ..domain.models import ScrapingResult, ExportFormat
from ..application.services.scraping_orchestrator import ScrapingOrchestrator


class CLIService:
    """
    Command-line interface service for eBay scraper.
    
    Features:
    - View scraping history
    - Export results in various formats
    - Search historical data
    - System status and health checks
    """
    
    def __init__(
        self,
        storage_service: IResultStorageService,
        export_service: IExportService,
        scraping_orchestrator: ScrapingOrchestrator,
        logger: ILogger
    ):
        """
        Initialize CLI service.
        
        Args:
            storage_service: Storage service for database operations
            export_service: Export service for data export
            scraping_orchestrator: Main scraping orchestrator
            logger: Logger instance
        """
        self.storage_service = storage_service
        self.export_service = export_service
        self.scraping_orchestrator = scraping_orchestrator
        self.logger = logger
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="eBay Scraper CLI",
            prog="python -m ebay_scraper"
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # History command
        history_parser = subparsers.add_parser('history', help='View scraping history')
        history_parser.add_argument(
            '--keyword', '-k',
            type=str,
            help='Filter by keyword'
        )
        history_parser.add_argument(
            '--limit', '-l',
            type=int,
            default=10,
            help='Number of results to show (default: 10)'
        )
        history_parser.add_argument(
            '--format', '-f',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format (default: table)'
        )
        
        # Export command
        export_parser = subparsers.add_parser('export', help='Export scraping results')
        export_parser.add_argument(
            'result_id',
            type=str,
            help='Result ID to export'
        )
        export_parser.add_argument(
            '--format', '-f',
            choices=['csv', 'xlsx', 'html', 'json'],
            default='csv',
            help='Export format (default: csv)'
        )
        export_parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output file path'
        )
        
        # Search command
        search_parser = subparsers.add_parser('search', help='Search historical products')
        search_parser.add_argument(
            '--keyword', '-k',
            type=str,
            help='Product keyword to search'
        )
        search_parser.add_argument(
            '--min-price',
            type=float,
            help='Minimum price filter'
        )
        search_parser.add_argument(
            '--max-price',
            type=float,
            help='Maximum price filter'
        )
        search_parser.add_argument(
            '--limit', '-l',
            type=int,
            default=20,
            help='Number of products to show (default: 20)'
        )
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show system status')
        status_parser.add_argument(
            '--detailed', '-d',
            action='store_true',
            help='Show detailed status information'
        )
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show usage statistics')
        stats_parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        
        return parser
    
    async def run_cli(self, args: Optional[List[str]] = None) -> int:
        """
        Run CLI with provided arguments.
        
        Args:
            args: Command line arguments (defaults to sys.argv)
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        parser = self.create_parser()
        
        if args is None:
            args = sys.argv[1:]
        
        try:
            parsed_args = parser.parse_args(args)
            
            if not parsed_args.command:
                parser.print_help()
                return 0
            
            # Route to appropriate command handler
            if parsed_args.command == 'history':
                return await self._handle_history_command(parsed_args)
            elif parsed_args.command == 'export':
                return await self._handle_export_command(parsed_args)
            elif parsed_args.command == 'search':
                return await self._handle_search_command(parsed_args)
            elif parsed_args.command == 'status':
                return await self._handle_status_command(parsed_args)
            elif parsed_args.command == 'stats':
                return await self._handle_stats_command(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                return 1
                
        except Exception as e:
            print(f"Error: {e}")
            await self.logger.log_error("CLI command failed", error=str(e), args=args)
            return 1
    
    async def _handle_history_command(self, args) -> int:
        """Handle history command."""
        try:
            print(f"📊 Fetching scraping history...")
            
            results = await self.storage_service.get_scraping_history(
                keyword=args.keyword,
                limit=args.limit
            )
            
            if not results:
                print("No scraping history found.")
                return 0
            
            if args.format == 'json':
                import json
                data = [
                    {
                        'result_id': r.result_id,
                        'keyword': r.criteria.keyword,
                        'marketplace': r.criteria.marketplace.value,
                        'products_count': len(r.products),
                        'status': r.status.value,
                        'created_at': r.created_at.isoformat(),
                        'duration': r.scraping_duration
                    }
                    for r in results
                ]
                print(json.dumps(data, indent=2))
            
            elif args.format == 'csv':
                print("result_id,keyword,marketplace,products_count,status,created_at,duration")
                for result in results:
                    print(f"{result.result_id},{result.criteria.keyword},{result.criteria.marketplace.value},"
                          f"{len(result.products)},{result.status.value},{result.created_at.isoformat()},"
                          f"{result.scraping_duration or 'N/A'}")
            
            else:  # table format
                self._print_history_table(results)
            
            return 0
            
        except Exception as e:
            print(f"Failed to fetch history: {e}")
            return 1
    
    async def _handle_export_command(self, args) -> int:
        """Handle export command."""
        try:
            print(f"📤 Exporting result {args.result_id}...")
            
            # Get result from storage
            result = await self.storage_service.get_scraping_result(args.result_id)
            if not result:
                print(f"Result {args.result_id} not found.")
                return 1
            
            # Determine output file path
            if args.output:
                output_path = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                keyword_safe = "".join(c for c in result.criteria.keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = f"export_{keyword_safe}_{timestamp}.{args.format}"
            
            # Export based on format
            if args.format == 'csv':
                await self.export_service.export_to_csv(result, output_path)
            elif args.format == 'xlsx':
                await self.export_service.export_to_xlsx(result, output_path)
            elif args.format == 'html':
                await self.export_service.export_to_html(result, output_path)
            elif args.format == 'json':
                export_data = await self.export_service.get_export_data(result)
                with open(output_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Export completed: {output_path}")
            print(f"   Products: {len(result.products)}")
            print(f"   Keyword: {result.criteria.keyword}")
            print(f"   Marketplace: {result.criteria.marketplace.value}")
            
            return 0
            
        except Exception as e:
            print(f"Export failed: {e}")
            return 1
    
    async def _handle_search_command(self, args) -> int:
        """Handle search command."""
        try:
            print(f"🔍 Searching products...")
            
            products = await self.storage_service.search_products(
                keyword=args.keyword,
                min_price=args.min_price,
                max_price=args.max_price,
                limit=args.limit
            )
            
            if not products:
                print("No products found matching criteria.")
                return 0
            
            print(f"\n📦 Found {len(products)} products:")
            print("-" * 100)
            print(f"{'Title':<40} {'Price':<10} {'Condition':<12} {'Sold':<8} {'Marketplace':<12}")
            print("-" * 100)
            
            for product in products:
                title = product.title[:37] + "..." if len(product.title) > 40 else product.title
                sold_count = str(product.sold_count) if product.sold_count else "N/A"
                print(f"{title:<40} ${product.price:<9} {product.condition.value:<12} "
                      f"{sold_count:<8} {product.marketplace.value:<12}")
            
            return 0
            
        except Exception as e:
            print(f"Search failed: {e}")
            return 1
    
    async def _handle_status_command(self, args) -> int:
        """Handle status command."""
        try:
            print("🔍 Checking system status...")
            
            # Get health check from orchestrator
            health_status = await self.scraping_orchestrator.health_check()
            
            print(f"\n📊 System Status: {health_status.get('overall', 'unknown').upper()}")
            print("-" * 50)
            
            services = health_status.get('services', {})
            for service, status in services.items():
                status_icon = "✅" if status == "healthy" or status == "running" else "❌"
                print(f"{status_icon} {service.replace('_', ' ').title()}: {status}")
            
            if args.detailed:
                print(f"\n📈 Metrics:")
                metrics = health_status.get('metrics', {})
                for metric, value in metrics.items():
                    print(f"   {metric.replace('_', ' ').title()}: {value}")
                
                print(f"\n⏰ Timestamp: {health_status.get('timestamp', 'N/A')}")
                print(f"🔧 Version: {health_status.get('version', 'N/A')}")
            
            return 0
            
        except Exception as e:
            print(f"Status check failed: {e}")
            return 1
    
    async def _handle_stats_command(self, args) -> int:
        """Handle stats command."""
        try:
            print(f"📊 Generating usage statistics for last {args.days} days...")
            
            # Get recent history
            results = await self.storage_service.get_scraping_history(limit=1000)
            
            if not results:
                print("No data available for statistics.")
                return 0
            
            # Calculate statistics
            total_scrapes = len(results)
            total_products = sum(len(r.products) for r in results)
            successful_scrapes = len([r for r in results if r.success])
            
            # Keywords frequency
            keyword_counts = {}
            marketplaces = {}
            
            for result in results:
                keyword = result.criteria.keyword.lower()
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                
                marketplace = result.criteria.marketplace.value
                marketplaces[marketplace] = marketplaces.get(marketplace, 0) + 1
            
            print(f"\n📈 Usage Statistics ({args.days} days)")
            print("=" * 50)
            print(f"Total Scrapes: {total_scrapes}")
            print(f"Total Products: {total_products}")
            print(f"Success Rate: {(successful_scrapes/total_scrapes)*100:.1f}%" if total_scrapes > 0 else "N/A")
            print(f"Avg Products/Scrape: {total_products/total_scrapes:.1f}" if total_scrapes > 0 else "N/A")
            
            print(f"\n🔍 Top Keywords:")
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for keyword, count in top_keywords:
                print(f"   {keyword}: {count} times")
            
            print(f"\n🌍 Marketplaces:")
            for marketplace, count in sorted(marketplaces.items(), key=lambda x: x[1], reverse=True):
                print(f"   {marketplace}: {count} scrapes")
            
            return 0
            
        except Exception as e:
            print(f"Stats generation failed: {e}")
            return 1
    
    def _print_history_table(self, results: List[ScrapingResult]) -> None:
        """Print history in table format."""
        print(f"\n📊 Scraping History ({len(results)} results)")
        print("-" * 120)
        print(f"{'ID':<8} {'Keyword':<25} {'Marketplace':<12} {'Products':<8} {'Status':<10} {'Date':<16} {'Duration':<8}")
        print("-" * 120)
        
        for result in results:
            result_id = result.result_id[:8] if result.result_id else "N/A"
            keyword = result.criteria.keyword[:22] + "..." if len(result.criteria.keyword) > 25 else result.criteria.keyword
            products_count = str(len(result.products))
            status = result.status.value
            date = result.created_at.strftime("%Y-%m-%d %H:%M")
            duration = f"{result.scraping_duration:.1f}s" if result.scraping_duration else "N/A"
            
            print(f"{result_id:<8} {keyword:<25} {result.criteria.marketplace.value:<12} "
                  f"{products_count:<8} {status:<10} {date:<16} {duration:<8}")


# CLI entry point function
async def main_cli():
    """Main CLI entry point."""
    # This would typically be called with a fully initialized dependency container
    print("eBay Scraper CLI")
    print("Note: This is a standalone CLI demo. Full functionality requires dependency injection.")
    
    parser = argparse.ArgumentParser(description="eBay Scraper CLI Demo")
    parser.add_argument('--help-commands', action='store_true', help='Show available commands')
    
    args = parser.parse_args()
    
    if args.help_commands:
        print("\nAvailable commands:")
        print("  history    - View scraping history")
        print("  export     - Export scraping results")
        print("  search     - Search historical products")
        print("  status     - Show system status")
        print("  stats      - Show usage statistics")
        print("\nUse 'python -m ebay_scraper <command> --help' for command-specific help.")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main_cli()) 
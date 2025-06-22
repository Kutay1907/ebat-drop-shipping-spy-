"""
Main module for the dropshipping analysis tool.
Orchestrates eBay scraping, Amazon product matching, and result generation.
"""

import asyncio
import argparse
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from utils import setup_logging, save_results_to_file, format_currency
from ebay_scraper import EbayScraper
from amazon_scraper import AmazonScraper
from matcher import ProductMatcher


class DropshippingAnalyzer:
    """
    Main class for dropshipping analysis.
    """
    
    def __init__(self, 
                 use_mock_amazon: bool = True,
                 use_mock_ebay: bool = True,
                 use_image_matching: bool = False,
                 max_ebay_products: int = 10,
                 min_profit_margin: float = 50.0,
                 output_file: str = "dropshipping_results.json"):
        """
        Initialize the dropshipping analyzer.
        
        Args:
            use_mock_amazon: Whether to use mock Amazon data for testing
            use_mock_ebay: Whether to use mock eBay data for testing
            use_image_matching: Whether to use image similarity matching
            max_ebay_products: Maximum number of eBay products to analyze
            min_profit_margin: Minimum profit margin percentage for matches
            output_file: Output file for results
        """
        self.use_mock_amazon = use_mock_amazon
        self.use_mock_ebay = use_mock_ebay
        self.use_image_matching = use_image_matching
        self.max_ebay_products = max_ebay_products
        self.min_profit_margin = min_profit_margin
        self.output_file = output_file
        
        # Setup logging
        self.logger = setup_logging("INFO")
        
    async def analyze_category(self, ebay_category: str) -> Dict[str, Any]:
        """
        Analyze a specific eBay category for dropshipping opportunities.
        
        Args:
            ebay_category: eBay category ID or search term
        
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        results = {
            "analysis_info": {
                "ebay_category": ebay_category,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "settings": {
                    "max_ebay_products": self.max_ebay_products,
                    "min_profit_margin": self.min_profit_margin,
                    "use_mock_amazon": self.use_mock_amazon,
                    "use_image_matching": self.use_image_matching
                }
            },
            "ebay_products": [],
            "matches": [],
            "summary": {}
        }
        
        try:
            # Step 1: Scrape eBay products
            self.logger.info(f"Starting eBay scraping for category: {ebay_category}")
            
            async with EbayScraper(
                headless=True, 
                use_mock=self.use_mock_ebay
            ) as ebay_scraper:
                self.logger.info("Scraping eBay products...")
                ebay_products = await ebay_scraper.scrape_category(
                    category_id=ebay_category,
                    max_products=self.max_ebay_products
                )
            
            print(f"DEBUG: Main.py - Found {len(ebay_products)} eBay products after scraping")
            
            if not ebay_products:
                self.logger.warning("No eBay products found")
                return results
            
            # Store eBay products in results
            results["ebay_products"] = [
                {
                    "title": product.title,
                    "price": product.price,
                    "sold_count": product.sold_count,
                    "url": product.url,
                    "image_url": product.image_url,
                    "condition": product.condition,
                    "shipping": product.shipping
                }
                for product in ebay_products
            ]
        
            print(f"DEBUG: Main.py - Stored {len(results['ebay_products'])} products in results")
            
            # Step 2: Search for Amazon matches
            self.logger.info("Searching for Amazon matches...")
            
            async with AmazonScraper(
                use_mock_data=self.use_mock_amazon,
                headless=True,
                delay=3.0
            ) as amazon_scraper:
                all_amazon_products = []
                
                # Search Amazon for each eBay product
                for i, ebay_product in enumerate(ebay_products):
                    search_term = self._create_search_term(ebay_product.title)
                    self.logger.info(f"Searching Amazon for: {search_term}")
                    print(f"DEBUG: Main.py - Searching Amazon for: {search_term}")
                    
                    amazon_products = await amazon_scraper.search_products(
                        search_term, 
                        max_results=5
                    )
                    
                    print(f"DEBUG: Main.py - Found {len(amazon_products)} Amazon products for search: {search_term}")
                    
                    all_amazon_products.extend(amazon_products)
                    
                    # Small delay between searches
                    await asyncio.sleep(1)
                
                self.logger.info(f"Found {len(all_amazon_products)} potential Amazon matches")
                print(f"DEBUG: Main.py - Total Amazon products: {len(all_amazon_products)}")
            
            # Step 3: Match products
            self.logger.info("Matching products...")
            print(f"DEBUG: Main.py - Starting product matching...")
            
            async with ProductMatcher(
                min_profit_margin=self.min_profit_margin,
                use_image_matching=self.use_image_matching
            ) as matcher:
                
                matches = await matcher.match_products(ebay_products, all_amazon_products)
                print(f"DEBUG: Main.py - Found {len(matches)} total matches")
                
                profitable_matches = matcher.filter_profitable_matches(matches)
                print(f"DEBUG: Main.py - Found {len(profitable_matches)} profitable matches (min margin: {self.min_profit_margin}%)")
                
                self.logger.info(f"Found {len(profitable_matches)} profitable matches")
                
                # Format matches for output
                results["matches"] = matcher.format_matches_for_output(profitable_matches)
                print(f"DEBUG: Main.py - Formatted {len(results['matches'])} matches for output")
            
            # Step 4: Generate summary
            results["summary"] = self._generate_summary(ebay_products, results["matches"])
            print(f"DEBUG: Main.py - Generated summary: {results['summary']}")
            
            # Calculate execution time
            execution_time = time.time() - start_time
            results["analysis_info"]["execution_time_seconds"] = round(execution_time, 2)
            
            self.logger.info(f"Analysis completed in {execution_time:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {e}")
            print(f"DEBUG: Main.py - Analysis error: {e}")
            import traceback
            traceback.print_exc()
            results["error"] = str(e)
        
        return results
    
    def _create_search_term(self, ebay_title: str) -> str:
        """
        Create an effective search term from eBay title.
        
        Args:
            ebay_title: Original eBay product title
        
        Returns:
            Optimized search term for Amazon
        """
        # Remove common eBay-specific terms
        remove_terms = [
            'free shipping', 'fast shipping', 'brand new', 'new with tags',
            'nwt', 'nib', 'new in box', 'authentic', 'genuine', 'original',
            'lot of', 'wholesale', 'bulk', 'used', 'refurbished'
        ]
        
        title_lower = ebay_title.lower()
        
        for term in remove_terms:
            title_lower = title_lower.replace(term, '')
        
        # Split into words and keep important ones
        words = title_lower.split()
        
        # Remove very short words and numbers that might be model-specific
        filtered_words = []
        for word in words:
            if len(word) > 2 and not word.isdigit():
                filtered_words.append(word)
        
        # Take first 5-6 most important words
        search_term = ' '.join(filtered_words[:6])
        
        return search_term.strip()
    
    def _generate_summary(self, ebay_products, formatted_matches) -> Dict[str, Any]:
        """
        Generate summary statistics.
        
        Args:
            ebay_products: List of eBay products
            formatted_matches: List of formatted match dictionaries (not ProductMatch objects)
        
        Returns:
            Summary dictionary
        """
        if not formatted_matches:
            return {
                "total_ebay_products": len(ebay_products),
                "total_matches": 0,
                "match_rate": 0.0,
                "average_profit_margin": 0.0,
                "total_potential_profit": 0.0,
                "best_match": None
            }
        
        # Calculate statistics from formatted matches
        profit_margins = [match["match_details"]["profit_margin_percent"] for match in formatted_matches]
        potential_profits = [match["match_details"]["potential_profit"] for match in formatted_matches]
        
        # Find best match
        best_match = max(formatted_matches, key=lambda x: x["match_details"]["profit_margin_percent"])
        
        summary = {
            "total_ebay_products": len(ebay_products),
            "total_matches": len(formatted_matches),
            "match_rate": round((len(formatted_matches) / len(ebay_products)) * 100, 1),
            "average_profit_margin": round(sum(profit_margins) / len(profit_margins), 1),
            "total_potential_profit": round(sum(potential_profits), 2),
            "best_match": {
                "ebay_title": best_match["ebay"]["title"],
                "amazon_title": best_match["amazon"]["title"],
                "profit_margin": best_match["match_details"]["profit_margin_percent"],
                "potential_profit": best_match["match_details"]["potential_profit"]
            }
        }
        
        return summary
    
    async def run_analysis(self, ebay_category: str) -> None:
        """
        Run the complete analysis and save results.
        
        Args:
            ebay_category: eBay category ID or search term
        """
        self.logger.info("Starting dropshipping analysis...")
        
        try:
            # Run analysis
            results = await self.analyze_category(ebay_category)
            
            # Save results
            await save_results_to_file(results, self.output_file)
            
            # Print summary
            self._print_summary(results)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """
        Print a formatted summary of results.
        
        Args:
            results: Analysis results dictionary
        """
        print("\n" + "="*60)
        print("DROPSHIPPING ANALYSIS SUMMARY")
        print("="*60)
        
        summary = results.get("summary", {})
        analysis_info = results.get("analysis_info", {})
        
        print(f"Category Analyzed: {analysis_info.get('ebay_category', 'Unknown')}")
        print(f"Analysis Time: {analysis_info.get('timestamp', 'Unknown')}")
        print(f"Execution Time: {analysis_info.get('execution_time_seconds', 0):.1f} seconds")
        print()
        
        print(f"eBay Products Found: {summary.get('total_ebay_products', 0)}")
        print(f"Profitable Matches: {summary.get('total_matches', 0)}")
        print(f"Match Rate: {summary.get('match_rate', 0):.1f}%")
        print()
        
        if summary.get('total_matches', 0) > 0:
            print(f"Average Profit Margin: {summary.get('average_profit_margin', 0):.1f}%")
            print(f"Total Potential Profit: {format_currency(summary.get('total_potential_profit', 0))}")
            print()
            
            best_match = summary.get('best_match')
            if best_match:
                print("BEST OPPORTUNITY:")
                print(f"  eBay: {best_match['ebay_title'][:60]}...")
                print(f"  Amazon: {best_match['amazon_title'][:60]}...")
                print(f"  Profit Margin: {best_match['profit_margin']:.1f}%")
                print(f"  Potential Profit: {format_currency(best_match['potential_profit'])}")
        
        print()
        print(f"Detailed results saved to: {self.output_file}")
        print("="*60)


async def main():
    """
    Main function with command line interface.
    """
    parser = argparse.ArgumentParser(description="Dropshipping Analysis Tool")
    parser.add_argument("category", help="eBay category ID or search term")
    parser.add_argument("--max-products", type=int, default=10, 
                       help="Maximum number of eBay products to analyze")
    parser.add_argument("--min-profit", type=float, default=50.0,
                       help="Minimum profit margin percentage")
    parser.add_argument("--real-amazon", action="store_true",
                       help="Use real Amazon scraping instead of mock data")
    parser.add_argument("--image-matching", action="store_true",
                       help="Enable image similarity matching")
    parser.add_argument("--output", default="dropshipping_results.json",
                       help="Output filename")
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = DropshippingAnalyzer(
        use_mock_amazon=not args.real_amazon,
        use_image_matching=args.image_matching,
        max_ebay_products=args.max_products,
        min_profit_margin=args.min_profit,
        output_file=args.output
    )
    
    # Run analysis
    await analyzer.run_analysis(args.category)


# Example usage for testing
async def example_analysis():
    """
    Example analysis for testing purposes.
    """
    analyzer = DropshippingAnalyzer(
        use_mock_amazon=True,  # Use mock data for testing
        use_image_matching=False,  # Disable image matching for faster testing
        max_ebay_products=5,  # Analyze fewer products for testing
        min_profit_margin=30.0,  # Lower threshold for testing
        output_file="test_results.json"
    )
    
    # Test with electronics category
    await analyzer.run_analysis("electronics")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # No arguments provided, run example
        print("No arguments provided. Running example analysis...")
        asyncio.run(example_analysis())
    else:
        # Run with command line arguments
        asyncio.run(main()) 
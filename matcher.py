"""
Product matching module using fuzzy string matching and image similarity.
"""

import asyncio
import logging
import difflib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import aiohttp
import imagehash
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

from ebay_scraper import EbayProduct
from amazon_scraper import AmazonProduct
from utils import clean_title, calculate_profit_margin


@dataclass
class ProductMatch:
    """Data class for a product match between eBay and Amazon."""
    ebay_product: EbayProduct
    amazon_product: AmazonProduct
    text_similarity: float
    image_similarity: float
    overall_confidence: float
    profit_margin: float
    price_difference: float


class ProductMatcher:
    """
    Product matcher class for finding similar products between eBay and Amazon.
    """
    
    def __init__(self, 
                 min_text_similarity: float = 0.4,
                 min_image_similarity: float = 0.7,
                 min_profit_margin: float = 50.0,
                 use_image_matching: bool = True):
        """
        Initialize product matcher.
        
        Args:
            min_text_similarity: Minimum text similarity score (0-1)
            min_image_similarity: Minimum image similarity score (0-1)
            min_profit_margin: Minimum profit margin percentage
            use_image_matching: Whether to use image similarity matching
        """
        self.min_text_similarity = min_text_similarity
        self.min_image_similarity = min_image_similarity
        self.min_profit_margin = min_profit_margin
        self.use_image_matching = use_image_matching
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self) -> None:
        """Start aiohttp session for image downloads."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self.logger.info("HTTP session started for image matching")
    
    async def close_session(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.logger.info("HTTP session closed")
    
    def calculate_text_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate text similarity between two product titles.
        
        Args:
            title1: First product title
            title2: Second product title
        
        Returns:
            Similarity score between 0 and 1
        """
        # Clean and normalize titles
        clean1 = clean_title(title1).lower()
        clean2 = clean_title(title2).lower()
        
        if not clean1 or not clean2:
            return 0.0
        
        # Use difflib SequenceMatcher for basic similarity
        matcher = difflib.SequenceMatcher(None, clean1, clean2)
        basic_similarity = matcher.ratio()
        
        # Calculate word-level similarity
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        if not words1 or not words2:
            return basic_similarity
        
        # Jaccard similarity for words
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        word_similarity = intersection / union if union > 0 else 0.0
        
        # Combine both similarities (weighted average)
        combined_similarity = (basic_similarity * 0.4) + (word_similarity * 0.6)
        
        return combined_similarity
    
    async def download_image(self, url: str) -> Optional[Image.Image]:
        """
        Download and convert image to PIL Image.
        
        Args:
            url: Image URL
        
        Returns:
            PIL Image object or None if failed
        """
        if not url or not self.session:
            return None
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data))
                    return image.convert('RGB')
        except Exception as e:
            self.logger.warning(f"Failed to download image from {url}: {e}")
        
        return None
    
    def calculate_image_hash_similarity(self, image1: Image.Image, image2: Image.Image) -> float:
        """
        Calculate image similarity using perceptual hashing.
        
        Args:
            image1: First PIL Image
            image2: Second PIL Image
        
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Calculate perceptual hashes
            hash1 = imagehash.phash(image1)
            hash2 = imagehash.phash(image2)
            
            # Calculate similarity (lower hash difference = higher similarity)
            hash_diff = hash1 - hash2
            max_diff = len(hash1.hash) * len(hash1.hash[0])  # Maximum possible difference
            similarity = 1.0 - (hash_diff / max_diff)
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            self.logger.warning(f"Error calculating image hash similarity: {e}")
            return 0.0
    
    def calculate_image_feature_similarity(self, image1: Image.Image, image2: Image.Image) -> float:
        """
        Calculate image similarity using OpenCV feature matching.
        
        Args:
            image1: First PIL Image
            image2: Second PIL Image
        
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Convert PIL images to OpenCV format
            img1 = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2BGR)
            img2 = cv2.cvtColor(np.array(image2), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Initialize SIFT detector
            sift = cv2.SIFT_create()
            
            # Find keypoints and descriptors
            kp1, des1 = sift.detectAndCompute(gray1, None)
            kp2, des2 = sift.detectAndCompute(gray2, None)
            
            if des1 is None or des2 is None:
                return 0.0
            
            # FLANN matcher
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            
            matches = flann.knnMatch(des1, des2, k=2)
            
            # Apply Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            
            # Calculate similarity based on good matches
            if len(kp1) == 0 or len(kp2) == 0:
                return 0.0
            
            similarity = len(good_matches) / min(len(kp1), len(kp2))
            return min(1.0, similarity)
            
        except Exception as e:
            self.logger.warning(f"Error calculating image feature similarity: {e}")
            return 0.0
    
    async def calculate_image_similarity(self, ebay_image_url: str, amazon_image_url: str) -> float:
        """
        Calculate overall image similarity between two product images.
        
        Args:
            ebay_image_url: eBay product image URL
            amazon_image_url: Amazon product image URL
        
        Returns:
            Similarity score between 0 and 1
        """
        if not self.use_image_matching or not ebay_image_url or not amazon_image_url:
            return 0.5  # Neutral score when image matching is disabled
        
        try:
            # Download both images
            ebay_image = await self.download_image(ebay_image_url)
            amazon_image = await self.download_image(amazon_image_url)
            
            if not ebay_image or not amazon_image:
                return 0.0
            
            # Calculate hash similarity
            hash_similarity = self.calculate_image_hash_similarity(ebay_image, amazon_image)
            
            # Calculate feature similarity (more computationally expensive)
            feature_similarity = self.calculate_image_feature_similarity(ebay_image, amazon_image)
            
            # Combine similarities (weighted average)
            overall_similarity = (hash_similarity * 0.7) + (feature_similarity * 0.3)
            
            return overall_similarity
            
        except Exception as e:
            self.logger.warning(f"Error calculating image similarity: {e}")
            return 0.0
    
    async def match_products(self, 
                           ebay_products: List[EbayProduct], 
                           amazon_products: List[AmazonProduct]) -> List[ProductMatch]:
        """
        Match eBay products with Amazon products.
        
        Args:
            ebay_products: List of eBay products
            amazon_products: List of Amazon products
        
        Returns:
            List of ProductMatch objects
        """
        matches = []
        
        for ebay_product in ebay_products:
            self.logger.info(f"Finding matches for: {ebay_product.title[:50]}...")
            
            best_match = None
            best_confidence = 0.0
            
            for amazon_product in amazon_products:
                # Calculate text similarity
                text_sim = self.calculate_text_similarity(
                    ebay_product.title, 
                    amazon_product.title
                )
                
                # Skip if text similarity is too low
                if text_sim < self.min_text_similarity:
                    continue
                
                # Calculate image similarity
                image_sim = 0.5  # Default neutral score
                if self.use_image_matching and ebay_product.image_url and amazon_product.image_url:
                    image_sim = await self.calculate_image_similarity(
                        ebay_product.image_url,
                        amazon_product.image_url
                    )
                
                # Calculate overall confidence
                if self.use_image_matching:
                    confidence = (text_sim * 0.6) + (image_sim * 0.4)
                else:
                    confidence = text_sim
                
                # Calculate profit metrics
                profit_margin = calculate_profit_margin(ebay_product.price, amazon_product.price)
                price_diff = ebay_product.price - amazon_product.price
                
                # Check if this is a better match
                if confidence > best_confidence and profit_margin >= self.min_profit_margin:
                    best_match = ProductMatch(
                        ebay_product=ebay_product,
                        amazon_product=amazon_product,
                        text_similarity=text_sim,
                        image_similarity=image_sim,
                        overall_confidence=confidence,
                        profit_margin=profit_margin,
                        price_difference=price_diff
                    )
                    best_confidence = confidence
            
            if best_match:
                matches.append(best_match)
                self.logger.info(f"Found match with {best_match.overall_confidence:.2f} confidence")
        
        # Sort matches by confidence (highest first)
        matches.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        return matches
    
    def filter_profitable_matches(self, matches: List[ProductMatch]) -> List[ProductMatch]:
        """
        Filter matches to only include profitable ones.
        
        Args:
            matches: List of ProductMatch objects
        
        Returns:
            Filtered list of profitable matches
        """
        profitable_matches = []
        
        for match in matches:
            # Check if profit margin meets minimum requirement
            if match.profit_margin >= self.min_profit_margin:
                # Additional checks can be added here
                # e.g., minimum price difference, maximum price threshold, etc.
                profitable_matches.append(match)
        
        return profitable_matches
    
    def format_matches_for_output(self, matches: List[ProductMatch]) -> List[Dict[str, Any]]:
        """
        Format matches for JSON output.
        
        Args:
            matches: List of ProductMatch objects
        
        Returns:
            List of dictionaries ready for JSON serialization
        """
        formatted_matches = []
        
        for match in matches:
            formatted_match = {
                "ebay": {
                    "title": match.ebay_product.title,
                    "price": match.ebay_product.price,
                    "sold_count": match.ebay_product.sold_count,
                    "url": match.ebay_product.url,
                    "image_url": match.ebay_product.image_url,
                    "condition": match.ebay_product.condition,
                    "shipping": match.ebay_product.shipping
                },
                "amazon": {
                    "title": match.amazon_product.title,
                    "price": match.amazon_product.price,
                    "url": match.amazon_product.url,
                    "image_url": match.amazon_product.image_url,
                    "rating": match.amazon_product.rating,
                    "reviews_count": match.amazon_product.reviews_count,
                    "prime": match.amazon_product.prime
                },
                "match_details": {
                    "text_similarity": round(match.text_similarity, 3),
                    "image_similarity": round(match.image_similarity, 3),
                    "overall_confidence": round(match.overall_confidence, 3),
                    "profit_margin_percent": round(match.profit_margin, 2),
                    "price_difference": round(match.price_difference, 2),
                    "potential_profit": round(match.price_difference, 2)
                }
            }
            formatted_matches.append(formatted_match)
        
        return formatted_matches


# Example usage function
async def main():
    """Example usage of the product matcher."""
    from utils import setup_logging
    from ebay_scraper import EbayScraper
    from amazon_scraper import AmazonScraper
    
    logger = setup_logging("INFO")
    
    # Mock some test data
    from dataclasses import dataclass
    
    ebay_test = EbayProduct(
        title="Wireless Bluetooth Headphones Noise Cancelling",
        price=59.99,
        sold_count=150,
        url="https://ebay.com/test",
        image_url="https://example.com/ebay_image.jpg"
    )
    
    amazon_test = AmazonProduct(
        title="Bluetooth Headphones with Noise Cancelling",
        price=25.99,
        url="https://amazon.com/test",
        rating=4.5,
        reviews_count=1200,
        prime=True
    )
    
    async with ProductMatcher(use_image_matching=False) as matcher:
        matches = await matcher.match_products([ebay_test], [amazon_test])
        
        if matches:
            match = matches[0]
            print(f"Match found!")
            print(f"Text similarity: {match.text_similarity:.3f}")
            print(f"Confidence: {match.overall_confidence:.3f}")
            print(f"Profit margin: {match.profit_margin:.1f}%")
            print(f"Price difference: ${match.price_difference:.2f}")


if __name__ == "__main__":
    asyncio.run(main()) 
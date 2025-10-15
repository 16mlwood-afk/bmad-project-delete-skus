"""
Data processing and filtering logic for SKU Cleanup Tool
Handles SKU data analysis, age calculation, and deletion eligibility
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes and filters SKU data for cleanup decisions"""

    def __init__(self, amazon_api=None):
        self.amazon_api = amazon_api  # For FBA API calls during processing

    def process_sku_data(self, raw_skus: List[Dict]) -> List[Dict]:
        """Process raw SKU data with simultaneous age and FBA inventory checking"""
        processed_skus = []

        logger.info(f"Starting to process {len(raw_skus)} raw SKUs")

        valid_skus = 0
        old_enough_skus = 0
        fba_skus = 0

        for i, sku_data in enumerate(raw_skus):
            try:
                # Skip invalid or empty SKUs
                if not sku_data.get('sku'):
                    if i < 3:  # Only log first few for brevity
                        logger.warning(f"Skipping SKU with missing SKU field at index {i}")
                    continue

                sku = sku_data.get('sku')
                valid_skus += 1

                # Log fulfillment channel for first few SKUs
                if valid_skus <= 3:
                    fulfillment = sku_data.get('fulfillment_channel', 'MISSING')
                    created_date = sku_data.get('created_date', 'MISSING')
                    logger.info(f"Valid SKU {valid_skus}: {sku}, fulfillment='{fulfillment}', created='{created_date}'")

                # Debug logging for first few SKUs to understand data structure
                if len(processed_skus) < 5:
                    logger.debug(f"Processing SKU: {sku}")
                    logger.debug(f"SKU data keys: {list(sku_data.keys())}")
                    logger.debug(f"Created date: {sku_data.get('created_date', 'None')}")
                    logger.debug(f"Fulfillment channel: {sku_data.get('fulfillment_channel', 'None')}")

                # Check age first
                age_days = self._calculate_sku_age(sku_data.get('created_date', ''))

                # Debug age calculation for first few SKUs
                if len(processed_skus) < 10:
                    logger.info(f"SKU {sku}: Age calculation - created_date='{sku_data.get('created_date', '')}', age_days={age_days}")

                is_old_enough = age_days >= 30 if age_days else False

                # If not old enough, skip FBA check for efficiency
                if not is_old_enough:
                    processed_sku = sku_data.copy()
                    processed_sku['age_days'] = age_days
                    processed_sku['is_old_enough'] = False
                    processed_sku['fba_inventory_check'] = 'skipped'
                    processed_sku['is_eligible_for_deletion'] = False
                    processed_skus.append(processed_sku)
                    continue

                # For old SKUs, check FBA inventory using FBA Inventory API (more reliable for inventory data)
                # Note: Rate limiting and resilience patterns are handled by the API layer
                if self.amazon_api and sku_data.get('fulfillment_channel') in ['AMAZON', 'AMAZON_EU']:
                    try:
                        # Use FBA Inventory API - provides actual quantity data
                        # Resilience patterns (retry, circuit breaker) are handled by amazon_api.py
                        fba_check = self.amazon_api.check_fba_inventory(sku)

                        # Check if there's any FBA inventory (fulfillable or inbound)
                        fulfillable_qty = fba_check.get('fulfillableQuantity', 0)
                        inbound_qty = fba_check.get('inboundQuantity', 0)
                        has_inventory = fulfillable_qty > 0 or inbound_qty > 0

                        processed_sku = sku_data.copy()
                        processed_sku['age_days'] = age_days
                        processed_sku['is_old_enough'] = True
                        processed_sku['fba_inventory_check'] = {
                            'fulfillable_quantity': fulfillable_qty,
                            'inbound_quantity': inbound_qty,
                            'reserved_quantity': fba_check.get('reservedQuantity', 0),
                            'has_inventory': has_inventory
                        }
                        processed_sku['is_eligible_for_deletion'] = not has_inventory

                        status = "SAFE" if not has_inventory else f"HAS INVENTORY (F: {fulfillable_qty}, I: {inbound_qty})"
                        logger.info(f"SKU {sku}: Age={age_days}d, FBA Check - Fulfillable: {fulfillable_qty}, Inbound: {inbound_qty}, Status: {status}")

                    except Exception as e:
                        # Enhanced error categorization for better resilience analysis
                        error_type = self._categorize_api_error(e)
                        logger.warning(f"SKU {sku}: FBA API check failed (age={age_days}d, error_type={error_type}): {e}")

                        # Log additional context for different error types
                        if error_type == 'circuit_breaker':
                            logger.warning(f"SKU {sku}: Circuit breaker is preventing FBA inventory checks")
                        elif error_type == 'rate_limit':
                            logger.warning(f"SKU {sku}: Rate limit exceeded for FBA inventory check")
                        elif error_type == 'network':
                            logger.warning(f"SKU {sku}: Network error during FBA inventory check")

                        # Be conservative - if API fails, don't delete
                        processed_sku = sku_data.copy()
                        processed_sku['age_days'] = age_days
                        processed_sku['is_old_enough'] = True
                        processed_sku['fba_inventory_check'] = {
                            'error': str(e),
                            'error_type': error_type,
                            'safe_decision': True  # Conservative approach
                        }
                        processed_sku['is_eligible_for_deletion'] = False
                else:
                    # Non-FBA or no API available - check fulfillment channel only
                    is_fba_configured = sku_data.get('fulfillment_channel') in ['AMAZON', 'AMAZON_EU']

                    processed_sku = sku_data.copy()
                    processed_sku['age_days'] = age_days
                    processed_sku['is_old_enough'] = True
                    processed_sku['listing_inventory_check'] = 'not_applicable' if not is_fba_configured else 'no_api'
                    processed_sku['is_eligible_for_deletion'] = not is_fba_configured  # Safe if not FBA

                processed_skus.append(processed_sku)

            except Exception as e:
                logger.error(f"Error processing SKU {sku_data.get('sku', 'unknown')}: {e}")
                continue

        return processed_skus

    def identify_deletable_skus(self, processed_skus: List[Dict]) -> List[Dict]:
        """Identify SKUs that are eligible for deletion"""
        deletable_skus = []

        for sku_data in processed_skus:
            if sku_data.get('is_eligible_for_deletion', False):
                deletable_skus.append(sku_data)

        return deletable_skus

    def _calculate_sku_age(self, created_date: str) -> Optional[int]:
        """Calculate SKU age in days from Amazon's datetime format"""
        if not created_date:
            logger.debug("No creation date provided")
            return None

        try:
            # Handle different date formats
            # Format 1: DD/MM/YYYY (old format)
            # Format 2: DD/MM/YYYY HH:MM:SS TIMEZONE (new format from API)

            date_part = created_date.split()[0]  # Get just the date part
            day, month, year = date_part.split('/')
            sku_date = datetime(int(year), int(month), int(day))

            # Calculate age in days
            age = datetime.now() - sku_date
            return age.days

        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid date format '{created_date}': {e}")
            return None

    def _check_fba_eligibility(self, sku_data: Dict) -> bool:
        """Check if SKU has active FBA offers - DETERMINED BY FBA API LATER"""
        fulfillment_channel = sku_data.get('fulfillment_channel', '')

        # For eligibility determination, we rely on the FBA API check in main.py
        # The merchant listings data doesn't reliably tell us about FBA inventory levels
        # All SKUs will go through FBA API verification before deletion

        if fulfillment_channel in ['AMAZON', 'AMAZON_EU']:
            logger.debug(f"SKU {sku_data.get('sku')} is FBA-configured - will verify inventory via API")
            # Don't pre-judge - let FBA API determine if it has active offers
            return False  # Allow FBA SKUs to be considered, API will verify

        # Non-FBA SKUs are safe to consider (no FBA inventory to worry about)
        logger.debug(f"SKU {sku_data.get('sku')} is not FBA-configured")
        return False

    def filter_by_age(self, skus: List[Dict], threshold_days: int = 30) -> List[Dict]:
        """Filter SKUs by age threshold"""
        old_skus = []

        for sku in skus:
            age_days = self._calculate_sku_age(sku.get('created_date', ''))

            if age_days and age_days >= threshold_days:
                old_skus.append(sku)

        logger.info(f"Found {len(old_skus)} SKUs older than {threshold_days} days")
        return old_skus

    def filter_by_fba_status(self, skus: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Separate SKUs with and without active FBA offers"""
        fba_skus = []
        merchant_skus = []

        for sku in skus:
            if self._check_fba_eligibility(sku):
                fba_skus.append(sku)
            else:
                merchant_skus.append(sku)

        logger.info(f"Active FBA SKUs: {len(fba_skus)}, Merchant SKUs: {len(merchant_skus)}")
        return fba_skus, merchant_skus

    def validate_sku_data(self, sku_data: Dict) -> bool:
        """Validate that SKU data is complete and reasonable"""
        required_fields = ['sku', 'asin']
        warnings = []

        # Check required fields
        for field in required_fields:
            if not sku_data.get(field):
                warnings.append(f"Missing {field}")

        # Check data quality
        if sku_data.get('quantity', 0) < 0:
            warnings.append("Negative quantity")

        if warnings:
            logger.warning(f"SKU {sku_data.get('sku', 'unknown')} validation issues: {warnings}")

        return len(warnings) == 0

    def get_cleanup_statistics(self, skus: List[Dict]) -> Dict:
        """Generate statistics about the SKU dataset"""
        total_skus = len(skus)

        if total_skus == 0:
            return {
                'total_skus': 0,
                'old_skus': 0,
                'fba_skus': 0,
                'deletable_skus': 0,
                'average_age': 0,
                'oldest_sku': None,
                'newest_sku': None
            }

        # Age statistics
        ages = [sku.get('age_days', 0) for sku in skus if sku.get('age_days')]
        old_skus = [sku for sku in skus if sku.get('age_days', 0) >= 30]

        # FBA statistics
        fba_skus = [sku for sku in skus if sku.get('fulfillment_channel') in ['AMAZON', 'AMAZON_EU']]

        # Deletable statistics
        deletable_skus = [sku for sku in skus if sku.get('is_eligible_for_deletion', False)]

        stats = {
            'total_skus': total_skus,
            'old_skus': len(old_skus),
            'fba_skus': len(fba_skus),
            'deletable_skus': len(deletable_skus),
            'average_age': sum(ages) / len(ages) if ages else 0,
            'oldest_sku': max(ages) if ages else 0,
            'newest_sku': min(ages) if ages else 0
        }

        logger.info(f"Dataset stats: {stats}")
        return stats

    def _categorize_api_error(self, error: Exception) -> str:
        """Categorize API errors for better resilience analysis"""
        error_str = str(error).lower()

        if 'circuit breaker' in error_str:
            return 'circuit_breaker'
        elif 'rate limit' in error_str or '429' in error_str:
            return 'rate_limit'
        elif any(term in error_str for term in ['connection', 'timeout', 'network', 'ssl']):
            return 'network'
        elif any(term in error_str for term in ['500', '502', '503', 'server']):
            return 'server_error'
        elif any(term in error_str for term in ['401', '403', 'auth']):
            return 'auth_error'
        elif '404' in error_str:
            return 'not_found'
        else:
            return 'unknown'

#!/usr/bin/env python3
"""
Simple SKU Cleanup Tool - Main Entry Point
Automated cleanup of old Amazon FBA SKUs that aren't selling
"""
import logging
import sys
import time
import os
from datetime import datetime
from typing import Dict, List, Any

try:
    # Try relative imports (when run as part of package)
    from .core.config import config
    from .core.amazon_api import AmazonAPI
    from .core.data_processor import DataProcessor
    from .lib.report_generator import ReportGenerator
except ImportError:
    # Fall back to absolute imports (when run as script)
    from core.config import config
    from core.amazon_api import AmazonAPI
    from core.data_processor import DataProcessor
    from lib.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sku_cleanup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SKUCleanupTool:
    """Main application class for SKU cleanup automation"""

    def __init__(self):
        self.amazon_api = AmazonAPI(config.credentials)
        self.data_processor = DataProcessor(amazon_api=self.amazon_api)  # Pass API for FBA checks
        self.report_generator = ReportGenerator()
        self.processed_skus_file = 'logs/processed_skus.txt'

    def run_cleanup(self) -> Dict[str, Any]:
        """
        Execute the complete SKU cleanup process

        Returns:
            Dict containing cleanup results and statistics
        """
        logger.info("Starting SKU cleanup process...")

        # Show test mode status
        if config.settings.test_mode:
            logger.info("🧪 TEST MODE ENABLED")
            logger.info(f"   Sample size: {config.settings.test_sample_size}")
            if config.settings.test_seed_skus:
                logger.info(f"   Test seed SKUs: {config.settings.test_seed_skus}")

            # Safety check: In test mode, warn about dry run setting
            if not config.settings.dry_run:
                logger.warning("🔒 SAFETY WARNING: TEST_MODE enabled but DRY_RUN=false detected!")
                logger.warning("🔒 This will perform ACTUAL DELETIONS on sample SKUs")
                logger.warning("🔒 Are you sure you want to delete SKUs in test mode?")
                logger.warning("🔒 Consider using TEST_MODE=true with DRY_RUN=true for safe testing")
                # Don't force dry_run - let user make explicit choice
        else:
            logger.info("🔄 PRODUCTION MODE - Processing all SKUs")

        try:
            # Step 1: Get all SKUs (or sample in test mode)
            logger.info("Step 1: Retrieving merchant listings...")
            raw_skus = self.amazon_api.get_merchant_listings()
            logger.info(f"Retrieved {len(raw_skus)} SKUs from Amazon")

            # Apply test mode filtering if enabled
            if config.settings.test_mode:
                raw_skus = self._apply_test_mode_filter(raw_skus)
                logger.info(f"Test mode: Using {len(raw_skus)} SKUs for testing")

            # Step 2: Process and filter SKUs (with batching for performance)
            logger.info("Step 2: Processing SKU data...")
            if config.settings.test_mode:
                # In test mode, process all sampled SKUs at once
                processed_skus = self.data_processor.process_sku_data(raw_skus)
            else:
                # In production mode, process in batches for better performance and memory management
                processed_skus = self._process_skus_in_batches(raw_skus)

            logger.info(f"Processed {len(processed_skus)} valid SKUs")

            # Step 3: Identify SKUs for deletion (FBA verification already done during processing)
            logger.info("Step 3: Identifying SKUs for deletion...")

            # Load previously processed SKUs with timestamps
            processed_skus_with_timestamps = self._load_processed_skus_with_timestamps()
            logger.info(f"Found {len(processed_skus_with_timestamps)} previously processed SKUs")

            # Get current SKUs from Amazon listings
            current_sku_ids = {sku.get('sku') for sku in raw_skus if sku.get('sku')}

            # Clean up processed SKUs file - remove SKUs no longer in Amazon listings or expired cooldowns
            import time
            current_time = int(time.time())
            skus_to_remove = []
            active_processed_skus = set()

            for sku, timestamp in processed_skus_with_timestamps.items():
                if sku not in current_sku_ids:
                    # SKU no longer in Amazon listings - can be removed
                    skus_to_remove.append(sku)
                elif timestamp <= current_time:
                    # Cooldown expired - can retry deletion
                    active_processed_skus.add(sku)
                # If timestamp > current_time, keep in cooldown (don't add to active_processed_skus)

            if skus_to_remove:
                logger.info(f"Cleaning up {len(skus_to_remove)} obsolete processed SKUs (no longer in Amazon listings)")
                for sku in skus_to_remove:
                    del processed_skus_with_timestamps[sku]
                self._save_processed_skus_with_timestamps(processed_skus_with_timestamps)
                logger.info(f"Processed SKUs file updated - now contains {len(processed_skus_with_timestamps)} entries")

            logger.info(f"Active processed SKUs (cooldown expired): {len(active_processed_skus)}")

            # Get SKUs that are in cooldown (have future timestamps)
            import time
            current_time = int(time.time())
            cooldown_skus = {sku for sku, timestamp in processed_skus_with_timestamps.items() if timestamp > current_time}

            # Get new SKUs that haven't been processed before and passed FBA verification
            new_skus_to_delete = [sku for sku in processed_skus if sku.get('is_eligible_for_deletion', False) and sku.get('sku') not in cooldown_skus]
            logger.info(f"Found {len(new_skus_to_delete)} NEW SKUs eligible for deletion (FBA-verified)")

            # Check previously processed SKUs that are still in current listings and re-verify FBA status
            previously_processed_still_eligible = []
            for sku in processed_skus:
                sku_id = sku.get('sku')
                if sku_id in active_processed_skus and sku_id in processed_skus_with_timestamps:
                    # This SKU was processed before but is still in current listings and cooldown expired
                    # We need to re-verify FBA inventory status before considering for deletion
                    logger.info(f"Re-verifying FBA status for previously processed SKU: {sku_id}")

                    # Re-process this SKU to get current FBA status
                    reprocessed_skus = self.data_processor.process_sku_data([sku])
                    if reprocessed_skus and len(reprocessed_skus) > 0:
                        rechecked_sku = reprocessed_skus[0]
                        if rechecked_sku.get('is_eligible_for_deletion', False):
                            logger.info(f"SKU {sku_id} passed re-verification and is still eligible for deletion")
                            previously_processed_still_eligible.append(rechecked_sku)
                        else:
                            logger.info(f"SKU {sku_id} failed re-verification - no longer eligible for deletion")
                    else:
                        logger.warning(f"Could not re-process SKU {sku_id} for FBA verification")

            logger.info(f"Found {len(previously_processed_still_eligible)} previously processed SKUs that passed FBA re-verification")

            # Combine both lists for deletion
            all_skus_to_delete = new_skus_to_delete + previously_processed_still_eligible

            # Step 4: Execute deletions (if not dry run)
            logger.info("Step 4: Executing deletions...")
            logger.info(f"Processing {len(all_skus_to_delete)} pre-verified SKUs ({len(new_skus_to_delete)} new + {len(previously_processed_still_eligible)} previously processed)...")
            deletion_results = self._execute_deletions(all_skus_to_delete)

            # Step 5: Generate report
            logger.info("Step 5: Generating cleanup report...")
            report_data = {
                'total_processed': len(processed_skus),
                'eligible_for_deletion': len(all_skus_to_delete),
                'new_eligible': len(new_skus_to_delete),
                'previously_processed_eligible': len(previously_processed_still_eligible),
                'deleted': deletion_results['deleted'],
                'skipped': deletion_results['skipped'],
                'errors': deletion_results['errors'],
                'execution_time': deletion_results['execution_time']
            }

            self.report_generator.generate_report(report_data)

            logger.info("SKU cleanup process completed successfully")
            return report_data

        except Exception as e:
            logger.error(f"Critical error during cleanup: {str(e)}")
            raise

    def _execute_deletions(self, skus_to_delete: List[Dict]) -> Dict[str, Any]:
        """Execute SKU deletions with safety checks"""
        results = {
            'deleted': [],
            'skipped': [],
            'errors': [],
            'execution_time': 0
        }

        if not skus_to_delete:
            logger.info("No SKUs to delete")
            return results

        start_time = datetime.now()

        for sku_data in skus_to_delete:
            sku = sku_data['sku']

            try:
                # Final safety check
                if self._should_skip_sku(sku):
                    logger.info(f"Skipping SKU {sku} (in skip list)")
                    results['skipped'].append({'sku': sku, 'reason': 'in_skip_list'})
                    continue

                # FBA verification already done during processing phase
                # If SKU made it here, it passed both age and FBA inventory checks

                # Execute deletion (unless dry run)
                if not config.settings.dry_run:
                    self.amazon_api.delete_sku(sku)
                    logger.info(f"Successfully deleted SKU: {sku}")
                    results['deleted'].append(sku)
                else:
                    logger.info(f"DRY RUN: Would delete SKU: {sku}")
                    results['deleted'].append(sku)  # Still count in dry run

            except Exception as e:
                logger.error(f"Error processing SKU {sku}: {str(e)}")
                results['errors'].append({'sku': sku, 'error': str(e)})

        results['execution_time'] = (datetime.now() - start_time).total_seconds()

        # Verify deletions actually worked before marking as processed
        # This prevents infinite loops when deletions are accepted but SKUs still appear
        verified_deleted = []
        successfully_deleted = results['deleted']

        if successfully_deleted:
            logger.info(f"Verifying {len(successfully_deleted)} deletions actually removed SKUs from Amazon...")

            # Get fresh inventory to verify deletions worked
            try:
                fresh_inventory = self.amazon_api.get_merchant_listings()
                fresh_sku_ids = {sku.get('sku') for sku in fresh_inventory if sku.get('sku')}

                for sku in successfully_deleted:
                    if sku not in fresh_sku_ids:
                        verified_deleted.append(sku)
                        logger.info(f"✅ Verified deletion: {sku} no longer in Amazon listings")
                    else:
                        logger.warning(f"⚠️ Deletion not verified: {sku} still appears in Amazon listings")

            except Exception as e:
                logger.error(f"Could not verify deletions: {e}")
                # Fallback: assume deletions worked if Amazon accepted them
                verified_deleted = successfully_deleted

            if verified_deleted:
                # Add verified deletions with timestamp to prevent immediate re-attempts
                import time
                current_time = int(time.time())

                # Load existing processed SKUs with timestamps
                existing_skus = self._load_processed_skus_with_timestamps()

                # Add verified deleted SKUs with current timestamp (1 hour cooldown for testing)
                cooldown_seconds = 1 * 60 * 60  # 1 hour
                for sku in verified_deleted:
                    existing_skus[sku] = current_time + cooldown_seconds

                # Save back to file
                self._save_processed_skus_with_timestamps(existing_skus)
                logger.info(f"Saved {len(verified_deleted)} verified deletions with cooldown timestamps")

        return results

    def _should_skip_sku(self, sku: str) -> bool:
        """Check if SKU should be skipped based on configuration or cooldown"""
        # Check user-defined skip list
        if sku in config.settings.skip_skus:
            return True

        # Check if SKU is in cooldown period
        processed_skus_with_timestamps = self._load_processed_skus_with_timestamps()
        import time
        current_time = int(time.time())

        if sku in processed_skus_with_timestamps:
            cooldown_timestamp = processed_skus_with_timestamps[sku]
            if cooldown_timestamp > current_time:
                logger.debug(f"SKU {sku} is in cooldown until {cooldown_timestamp}")
                return True

        return False

    def _load_processed_skus(self) -> set:
        """Load set of SKUs that have already been processed for deletion (legacy method)"""
        try:
            if not os.path.exists(self.processed_skus_file):
                return set()

            with open(self.processed_skus_file, 'r') as f:
                return {line.strip() for line in f if line.strip()}
        except Exception as e:
            logger.warning(f"Could not load processed SKUs file: {e}")
            return set()

    def _load_processed_skus_with_timestamps(self) -> dict:
        """Load dict of SKUs with their deletion timestamps"""
        try:
            if not os.path.exists(self.processed_skus_file):
                return {}

            sku_timestamps = {}
            with open(self.processed_skus_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # Check if line contains timestamp (new format: sku,timestamp)
                        if ',' in line:
                            sku, timestamp_str = line.split(',', 1)
                            try:
                                sku_timestamps[sku] = int(timestamp_str)
                            except ValueError:
                                # Fallback to old format (just SKU)
                                sku_timestamps[sku] = 0
                        else:
                            # Old format (just SKU)
                            sku_timestamps[line] = 0

            return sku_timestamps
        except Exception as e:
            logger.warning(f"Could not load processed SKUs file: {e}")
            return {}

    def _save_processed_skus(self, sku_list: List[str]):
        """Save list of SKUs that were just processed for deletion (legacy method)"""
        try:
            # Load existing processed SKUs
            existing_skus = self._load_processed_skus()

            # Add new SKUs
            existing_skus.update(sku_list)

            # Save back to file
            os.makedirs(os.path.dirname(self.processed_skus_file), exist_ok=True)
            with open(self.processed_skus_file, 'w') as f:
                for sku in sorted(existing_skus):
                    f.write(f"{sku}\n")

            logger.info(f"Saved {len(sku_list)} newly processed SKUs (total: {len(existing_skus)})")
        except Exception as e:
            logger.error(f"Could not save processed SKUs: {e}")

    def _save_processed_skus_with_timestamps(self, sku_timestamps: dict):
        """Save dict of SKUs with their deletion timestamps"""
        try:
            os.makedirs(os.path.dirname(self.processed_skus_file), exist_ok=True)
            with open(self.processed_skus_file, 'w') as f:
                for sku, timestamp in sorted(sku_timestamps.items()):
                    f.write(f"{sku},{timestamp}\n")

            logger.info(f"Saved {len(sku_timestamps)} processed SKUs with timestamps")
        except Exception as e:
            logger.error(f"Could not save processed SKUs: {e}")

    def _apply_test_mode_filter(self, raw_skus: List[Dict]) -> List[Dict]:
        """Apply test mode filtering to reduce dataset size for testing"""
        if not config.settings.test_mode:
            return raw_skus

        import random

        # Method 1: Use specific seed SKUs if provided
        if config.settings.test_seed_skus:
            logger.info(f"Using {len(config.settings.test_seed_skus)} seed SKUs for testing")
            seed_skus = set(config.settings.test_seed_skus)
            filtered_skus = [sku for sku in raw_skus if sku.get('sku') in seed_skus]

            if len(filtered_skus) == 0:
                logger.warning("No seed SKUs found in dataset, falling back to random sampling")
            else:
                logger.info(f"Found {len(filtered_skus)} seed SKUs in dataset")
                return filtered_skus

        # Method 2: Random sampling
        sample_size = min(config.settings.test_sample_size, len(raw_skus))

        if sample_size == len(raw_skus):
            logger.info("Sample size equals total SKUs, using entire dataset")
            return raw_skus

        # Use deterministic sampling for reproducible tests
        random.seed(42)  # Fixed seed for reproducible results
        sampled_skus = random.sample(raw_skus, sample_size)

        logger.info(f"Randomly sampled {len(sampled_skus)} SKUs for testing")
        logger.debug(f"Sample SKUs: {[sku.get('sku') for sku in sampled_skus[:5]]}{'...' if len(sampled_skus) > 5 else ''}")

        return sampled_skus

    def _process_skus_in_batches(self, raw_skus: List[Dict]) -> List[Dict]:
        """Process SKUs in batches for better performance and memory management"""
        total_skus = len(raw_skus)
        batch_size = config.settings.batch_size

        if total_skus <= batch_size:
            logger.info(f"Processing {total_skus} SKUs in single batch")
            return self.data_processor.process_sku_data(raw_skus)

        logger.info(f"Processing {total_skus} SKUs in batches of {batch_size}")

        all_processed_skus = []
        total_batches = (total_skus + batch_size - 1) // batch_size  # Ceiling division

        for i in range(0, total_skus, batch_size):
            batch_num = i // batch_size + 1
            batch_end = min(i + batch_size, total_skus)
            batch_skus = raw_skus[i:batch_end]

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_skus)} SKUs) - {len(all_processed_skus)}/{total_skus} completed")

            try:
                batch_processed = self.data_processor.process_sku_data(batch_skus)
                all_processed_skus.extend(batch_processed)

                # Reduced delay between batches for faster processing
                if batch_num < total_batches:
                    logger.debug(f"Brief pause before next batch...")
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                logger.warning(f"Continuing with next batch despite error in batch {batch_num}")
                # Continue processing other batches even if one fails
                continue

        logger.info(f"Completed processing {len(all_processed_skus)} SKUs across {total_batches} batches")
        return all_processed_skus

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("AMAZON SKU CLEANUP TOOL - Starting Execution")
    logger.info("=" * 60)

    # Show configuration (without sensitive data)
    logger.info("Configuration:")
    logger.info(f"  Dry Run Mode: {config.settings.dry_run}")
    logger.info(f"  Test Mode: {config.settings.test_mode}")
    if config.settings.test_mode:
        logger.info(f"    Sample Size: {config.settings.test_sample_size}")
        logger.info(f"    Seed SKUs: {len(config.settings.test_seed_skus)}")
    logger.info(f"  Age Threshold: {config.settings.age_threshold_days} days")
    logger.info(f"  Batch Size: {config.settings.batch_size}")
    logger.info(f"  Marketplace: {config.credentials.marketplace_id}")
    logger.info(f"  Skip SKUs: {len(config.settings.skip_skus)}")

    # Resilience configuration
    logger.info("Resilience Settings:")
    logger.info(f"  Max Retries: {config.settings.resilience.max_retries}")
    logger.info(f"  Base Delay: {config.settings.resilience.base_delay}s")
    logger.info(f"  Circuit Breaker Threshold: {config.settings.resilience.circuit_breaker_failure_threshold}")
    logger.info(f"  Connection Pool: {config.settings.resilience.max_connections} connections")

    try:
        # Initialize and run cleanup tool
        cleanup_tool = SKUCleanupTool()
        results = cleanup_tool.run_cleanup()

        # Show results summary
        logger.info("=" * 60)
        logger.info("CLEANUP RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total SKUs Processed: {results['total_processed']}")
        logger.info(f"Eligible for Deletion: {results['eligible_for_deletion']}")
        logger.info(f"  - New SKUs: {results['new_eligible']}")
        logger.info(f"  - Previously Processed: {results['previously_processed_eligible']}")
        logger.info(f"Successfully Deleted: {len(results['deleted'])}")
        logger.info(f"Skipped: {len(results['skipped'])}")
        logger.info(f"Errors: {len(results['errors'])}")
        logger.info(f"Execution Time: {results['execution_time']:.2f} seconds")

        if config.settings.dry_run:
            logger.info("DRY RUN MODE - No actual deletions performed")

        logger.info("=" * 60)
        return 0 if len(results['errors']) == 0 else 1

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

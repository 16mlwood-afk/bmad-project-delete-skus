#!/usr/bin/env python3
"""
Download the actual report and run full analysis
"""
import time
from amazon_api import AmazonAPI
from data_processor import DataProcessor
from report_generator import ReportGenerator
from config import config

def download_and_analyze():
    print("🚀 Starting full SKU cleanup analysis...")

    # Initialize components
    api = AmazonAPI(config.credentials)
    processor = DataProcessor(amazon_api=api)  # Pass API for FBA inventory checks
    report_gen = ReportGenerator()

    try:
        # Step 1: Create report
        print("📋 Step 1: Creating merchant listings report...")
        report_response = api._make_api_request('POST', '/reports/2021-06-30/reports', json={
            "reportType": "GET_MERCHANT_LISTINGS_ALL_DATA",
            "marketplaceIds": [config.credentials.marketplace_id]
        })
        report_id = report_response['reportId']
        print(f"✅ Report created: {report_id}")

        # Step 2: Wait for report completion
        print("⏳ Step 2: Waiting for report processing...")
        for i in range(24):  # Wait up to 2 minutes
            status_response = api._make_api_request('GET', f'/reports/2021-06-30/reports/{report_id}')
            status = status_response.get('processingStatus')

            if status == 'DONE':
                print(f"✅ Report completed after {i*5} seconds")
                break
            elif status in ['FATAL', 'CANCELLED']:
                print(f"❌ Report failed: {status}")
                return

            time.sleep(5)

        # Step 3: Download report
        print("📥 Step 3: Downloading report...")
        document_id = status_response['reportDocumentId']
        document_response = api._make_api_request('GET', f'/reports/2021-06-30/documents/{document_id}')
        download_url = document_response['url']

        import requests
        response = requests.get(download_url)
        report_content = response.text

        print(f"✅ Downloaded {len(report_content.split(chr(10)))} lines of data")

        # Step 4: Parse and analyze
        print("🔍 Step 4: Analyzing SKU data...")
        import csv
        import io

        reader = csv.DictReader(io.StringIO(report_content), delimiter='\t')
        skus = []

        for row in reader:
            sku_data = {
                'sku': row.get('seller-sku', '').strip(),
                'asin': row.get('asin1', '').strip(),
                'created_date': row.get('open-date', '').strip(),
                'fulfillment_channel': row.get('fulfillment-channel', '').strip(),
                'quantity': int(row.get('quantity', 0) or 0),
                'item_name': row.get('item-name', '').strip(),
                'listing_id': row.get('listing-id', '').strip(),
                'status': row.get('status', '').strip()
            }
            if sku_data['sku']:
                skus.append(sku_data)

        print(f"📊 Found {len(skus)} valid SKUs")

        # Process SKUs with simultaneous age and FBA inventory checking
        processed_skus = processor.process_sku_data(skus)

        # Analyze results - now with simultaneous age and FBA inventory checking
        deletable_skus = [sku for sku in processed_skus if sku.get('is_eligible_for_deletion', False)]

        # Categorize SKUs by their processing results
        old_skus = [sku for sku in processed_skus if sku.get('is_old_enough', False)]
        fba_verified_safe = [sku for sku in processed_skus if isinstance(sku.get('fba_inventory_check'), dict) and not sku['fba_inventory_check'].get('has_inventory', True)]
        fba_with_inventory = [sku for sku in processed_skus if isinstance(sku.get('fba_inventory_check'), dict) and sku['fba_inventory_check'].get('has_inventory', False)]

        print("\n📈 Analysis Results (Simultaneous Age + FBA Check):")
        print(f"Total SKUs processed: {len(processed_skus)}")
        print(f"SKUs ≥30 days old: {len(old_skus)}")
        print(f"FBA-verified safe for deletion: {len(fba_verified_safe)}")
        print(f"FBA SKUs with inventory (protected): {len(fba_with_inventory)}")
        print(f"Final eligible for deletion: {len(deletable_skus)}")

        if deletable_skus:
            print("\n🗑️  Sample SKUs verified safe for deletion (age + zero FBA inventory):")
            for sku in deletable_skus[:10]:
                fba_check = sku.get('fba_inventory_check', {})
                if isinstance(fba_check, dict):
                    print(f"  - {sku['sku']} ({sku.get('age_days', 0)} days old, FBA: {fba_check.get('fulfillable_quantity', 0)} fulfillable, {fba_check.get('inbound_quantity', 0)} inbound)")
                else:
                    print(f"  - {sku['sku']} ({sku.get('age_days', 0)} days old, Status: {fba_check})")
        else:
            print("\n🗑️  No SKUs are currently safe for deletion.")

        # Generate report
        print("\n📋 Step 5: Generating cleanup report...")
        report_data = {
            'total_processed': len(processed_skus),
            'eligible_for_deletion': len(deletable_skus),
            'deleted': [],  # Dry run - no actual deletions
            'skipped': [],
            'errors': [],
            'execution_time': 0
        }

        report_gen.generate_report(report_data)
        print("✅ Report saved to reports/ directory")

        print("\n🎉 Analysis complete!")
        return True

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False

if __name__ == "__main__":
    download_and_analyze()

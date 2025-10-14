#!/usr/bin/env python3
"""
Parse the downloaded merchant listings report
"""
import csv
import io
from datetime import datetime
from data_processor import DataProcessor

def parse_report_data():
    # Get the report data (this would normally be downloaded)
    # For now, let's use the sample data from our test

    report_content = """item-name	item-description	listing-id	seller-sku	price	quantity	open-date	image-url	item-is-marketplace	product-id-type	zshop-shipping-fee	item-note	item-condition	zshop-category1	zshop-browse-path	zshop-storefront-feature	asin1	asin2	asin3	will-ship-internationally	expedited-shipping	zshop-boldface	product-id	bid-for-featured-placement	add-delete	pending-quantity	fulfillment-channel	merchant-shipping-group	status	Minimum order quantity	Sell remainder
Nespresso Krups XN110BRD Essenza mini coffee capsule machine | 0.6 L | 19 bar | energy saving mode | grey | energy class A		0929FIRW02F	DE-168-20250918-UK-EUSD	120.49		29/09/2025 16:19:39 BST		y	1			11				B06XHNK8NP						B06XHNK8NP				AMAZON_EU	SELLERSMART - GB, DA5 1LR	Active
Krups Nespresso Essenza Mini XN1108 Coffee Machine | 0.6 Litre | 19 Bar | Energy Saving Mode | Black		0925F7CR7RB	DE-172-20250918-UK-EUSD	120		25/09/2025 17:49:35 BST		y	1			11				B06XJ4G828						B06XJ4G828				AMAZON_EU	SELLERSMART - GB, DA5 1LR	Active"""

    # Parse TSV data
    reader = csv.DictReader(io.StringIO(report_content), delimiter='\t')

    skus = []
    for i, row in enumerate(reader):
        # Debug first few rows to understand column structure
        if i < 3:
            print(f"DEBUG Row {i} keys: {list(row.keys())}")
            print(f"DEBUG Row {i} seller-sku: '{row.get('seller-sku', 'MISSING')}'")
            print(f"DEBUG Row {i} fulfillment-channel: '{row.get('fulfillment-channel', 'MISSING')}'")
            print(f"DEBUG Row {i} open-date: '{row.get('open-date', 'MISSING')}'")

        if i >= 5:  # Only debug first few rows
            break
        sku_data = {
            'sku': row.get('seller-sku', '').strip(),
            'asin': row.get('asin1', '').strip(),
            'open-date': row.get('open-date', '').strip(),  # Keep original column name
            'created_date': row.get('open-date', '').strip(),  # Also provide as created_date for compatibility
            'fulfillment-channel': row.get('fulfillment-channel', '').strip(),  # Keep original column name
            'fulfillment_channel': row.get('fulfillment-channel', '').strip(),  # Also provide as fulfillment_channel for compatibility
            'quantity': int(row.get('quantity', 0) or 0),
            'item_name': row.get('item-name', '').strip(),
            'listing_id': row.get('listing-id', '').strip(),
            'status': row.get('status', '').strip()
        }
        if sku_data['sku']:  # Only include SKUs that have actual SKU values
            skus.append(sku_data)

    print(f"📊 Parsed {len(skus)} SKUs from report")

    # Process with DataProcessor
    processor = DataProcessor()
    processed_skus = processor.process_sku_data(skus)

    print("\n🔍 Analysis Results:")
    print(f"Total SKUs: {len(processed_skus)}")

    # Count by fulfillment channel
    fba_skus = [sku for sku in processed_skus if sku.get('has_fba_offers', False)]
    merchant_skus = [sku for sku in processed_skus if not sku.get('has_fba_offers', False)]

    print(f"FBA SKUs (AMAZON_EU): {len(fba_skus)}")
    print(f"Merchant SKUs: {len(merchant_skus)}")

    # Count by age
    old_skus = [sku for sku in processed_skus if sku.get('is_old_enough', False)]
    print(f"SKUs ≥30 days old: {len(old_skus)}")

    # Find deletable SKUs
    deletable_skus = processor.identify_deletable_skus(processed_skus)
    print(f"Eligible for deletion: {len(deletable_skus)}")

    if deletable_skus:
        print("\n💡 Sample deletable SKUs:")
        for sku in deletable_skus[:5]:
            print(f"  - {sku['sku']} ({sku.get('age_days', 0)} days old, {sku['fulfillment_channel']})")

    return processed_skus

if __name__ == "__main__":
    parse_report_data()

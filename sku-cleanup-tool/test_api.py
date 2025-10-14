#!/usr/bin/env python3
"""
Simple API test to debug the 403 error
"""
import requests
from config import config

def test_api_access():
    # Get access token
    token_url = "https://api.amazon.com/auth/o2/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': config.credentials.lwa_refresh_token,
        'client_id': config.credentials.lwa_client_id,
        'client_secret': config.credentials.lwa_client_secret
    }

    print("Getting access token...")
    response = requests.post(token_url, headers=headers, data=data)
    print(f"Token response status: {response.status_code}")

    if response.status_code != 200:
        print(f"Token error: {response.text}")
        return

    token_data = response.json()
    access_token = token_data['access_token']
    print(f"Got access token: {access_token[:20]}...")

    # Try to create report
    report_url = "https://sellingpartnerapi-na.amazon.com/reports/2021-06-30/reports"
    report_headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    print(f"Headers: {report_headers}")

    # Try different marketplace IDs to test
    marketplace_ids = [
        "A1F83G8C2ARO7P",  # US
        "A1AM78C64UM0Y8",  # Canada
        "A1PA6795UKMFR9",  # UK
        "A1RKKUPIHCS9HS",  # Spain
        "A13V1IB3VIYZZH",  # France
        "A1JEUMLCLC2WX2",  # Germany
        "A1805IZSGTT6HS",  # Italy
        "APJ6JRA9NG5V4",   # Mexico
        "A2Q3Y263D00KWC",  # Brazil
        "A2EUQ1WTGCTBG2",  # Australia
        "A39IBJ37TRP1C6",   # Turkey
        "A1VC38T7YXB528",  # Japan
        "AAHKV2XAUZCBG"    # India
    ]

    print(f"Testing different marketplaces for seller: {config.credentials.seller_id}")

    for marketplace_id in marketplace_ids[:3]:  # Test first 3 to avoid rate limits
        payload = {
            "reportType": "GET_MERCHANT_LISTINGS_ALL_DATA",
            "marketplaceIds": [marketplace_id]
        }

        print(f"\nTrying marketplace: {marketplace_id}")
        report_response = requests.post(report_url, headers=report_headers, json=payload)
        print(f"Status: {report_response.status_code}")

        if report_response.status_code == 202:  # Success
            print("SUCCESS! Found working marketplace")
            response_data = report_response.json()
            print(f"Report ID: {response_data.get('reportId')}")
            break
        else:
            print(f"Response: {report_response.text}")

if __name__ == "__main__":
    test_api_access()

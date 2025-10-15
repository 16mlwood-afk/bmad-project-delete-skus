#!/usr/bin/env python3
"""
Check report status and download when ready
"""
import time
from core.amazon_api import AmazonAPI
from core.config import config

def check_and_download_report():
    api = AmazonAPI(config.credentials)
    report_id = '855121020375'

    print('Checking report status...')
    for i in range(12):  # Check for up to 1 minute
        try:
            status = api._make_api_request('GET', f'/reports/2021-06-30/reports/{report_id}')
            current_status = status.get('processingStatus')
            print(f'Attempt {i+1}: Status = {current_status}')

            if current_status == 'DONE':
                print(f'\n🎉 Report completed! Document ID: {status.get("reportDocumentId")}')

                # Download the report
                report_document_id = status.get('reportDocumentId')
                document = api._make_api_request('GET', f'/reports/2021-06-30/documents/{report_document_id}')
                download_url = document.get('url')
                print(f'Download URL: {download_url[:80]}...')

                # Download the actual report
                import requests
                response = requests.get(download_url)
                content = response.text

                # Show first few lines
                lines = content.split('\n')[:10]
                print(f'\n📄 Report preview (first 10 lines):')
                for line in lines:
                    if line.strip():
                        print(f'  {line}')

                print(f'\n📊 Total lines in report: {len(content.split(chr(10)))}')
                return True

            elif current_status in ['FATAL', 'CANCELLED']:
                print(f'❌ Report failed with status: {current_status}')
                return False

        except Exception as e:
            print(f'Error checking status: {e}')

        time.sleep(5)

    print('⏰ Report still processing after 1 minute')
    return False

if __name__ == "__main__":
    check_and_download_report()

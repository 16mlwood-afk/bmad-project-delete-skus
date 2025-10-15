# Technical Specification - Simple SKU Cleanup Tool

## Project Overview
**Project:** Simple SKU Cleanup Tool - Amazon FBA Automation
**Type:** CLI Tool (Python script)
**Level:** 1 (Coherent feature)
**Timeline:** 1 week

## Technical Requirements

### Core Architecture
- **Language:** Python 3.8+
- **Runtime:** Single script execution (daily automation)
- **External Dependencies:** Amazon SP-API, boto3, pandas
- **Output:** Console logging + markdown report file

### Amazon API Integration

#### 1. Authentication & Setup
```
Required Credentials:
- AWS Access Key ID
- AWS Secret Access Key
- Amazon Seller ID
- Marketplace ID (A1F83G8C2ARO7P for UK)
- SP-API Application credentials
```

#### 2. Reports API Integration
```python
# Get merchant listings report
response = reports_api.create_report(
    reportType='GET_MERCHANT_LISTINGS_ALL_DATA',
    marketplaceIds=[marketplace_id]
)
report_id = response.payload['reportId']

# Download and parse report
report_data = reports_api.get_report(report_id)
sku_data = parse_merchant_listings_report(report_data)
```

#### 3. Listings API Integration
```python
# Delete SKU
response = listings_api.delete_listings_item(
    sellerId=seller_id,
    sku=sku_to_delete,
    marketplaceIds=[marketplace_id]
)
```

### Data Processing Pipeline

#### Step 1: SKU Discovery
- Request merchant listings report via Reports API
- Poll for report completion (async operation)
- Download and parse TSV data
- Extract: sku, asin, creation_date, fulfillment_channel, quantity

#### Step 2: Age Filtering
```python
def is_old_enough(sku_data, threshold_days=30):
    """Check if SKU is old enough for deletion"""
    if not sku_data.get('creation_date'):
        return False  # Skip if no creation date

    sku_age = datetime.now() - parse_amazon_date(sku_data['creation_date'])
    return sku_age.days >= threshold_days
```

#### Step 3: FBA Status Verification
```python
def has_active_fba_offers(sku_data):
    """Check if SKU has active FBA inventory"""
    fulfillment = sku_data.get('fulfillment_channel', '')
    quantity = sku_data.get('quantity', 0)

    return (fulfillment in ['AMAZON', 'AMAZON_EU'] and quantity > 0)
```

#### Step 4: Safety Verification
- Double-check age requirement
- Verify no FBA inventory
- Confirm not in skip list
- Log verification details

#### Step 5: Batch Deletion
- Process SKUs in configurable batches (default: 100)
- Handle API rate limits
- Continue processing if individual deletions fail
- Comprehensive error logging

#### Step 6: Report Generation
```python
def generate_cleanup_report(results):
    """Generate markdown report of cleanup actions"""
    report = f"""# SKU Cleanup Report
Date: {datetime.now().isoformat()}

## Summary
- Total SKUs Checked: {results['total_processed']}
- Deleted: {results['deleted_count']}
- Skipped: {results['skipped_count']}
- Errors: {results['error_count']}

## Deleted SKUs ({results['deleted_count']})
{format_deleted_skus(results['deleted'])}

## Skipped SKUs ({results['skipped_count']})
{format_skipped_skus(results['skipped'])}
"""
    return report
```

## Configuration Management

### Settings Structure
```python
class CleanupConfig:
    def __init__(self):
        self.age_threshold_days = 30
        self.dry_run = True  # Safety first!
        self.marketplace_id = "A1F83G8C2ARO7P"
        self.batch_size = 100
        self.skip_skus = ["KEEP-THIS-1"]
        self.report_file = "sku-cleanup-report.md"
        self.log_level = "INFO"
```

### Environment Variables
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AMAZON_SELLER_ID="your_seller_id"
export SP_API_REFRESH_TOKEN="your_refresh_token"
```

## Error Handling & Logging

### Logging Strategy
- **Levels:** DEBUG, INFO, WARNING, ERROR
- **Output:** Console + rotating log file
- **Format:** Timestamp, level, message, SKU context

### Error Scenarios
1. **API Authentication Failures** - Retry with exponential backoff
2. **Rate Limiting** - Implement delays between requests
3. **Network Issues** - Retry failed requests up to 3 times
4. **Invalid Data** - Skip malformed SKUs with detailed logging

### Safety Mechanisms
- **Dry Run Mode** - Test without actual deletions
- **Pre-flight Checks** - Verify credentials and permissions
- **Rollback Capability** - Log all actions for potential reversal
- **Progress Persistence** - Resume from interruption point

## File Structure
```
sku-cleanup-tool/
├── main.py              # Main script entry point
├── config.py           # Configuration management
├── amazon_api.py       # SP-API integration
├── data_processor.py   # SKU filtering and processing
├── report_generator.py # Report creation
├── utils.py           # Helper functions
├── requirements.txt   # Python dependencies
├── .env               # Environment variables (gitignored)
└── logs/             # Log files and reports
    ├── sku_cleanup.log
    └── reports/
        └── sku-cleanup-report-2025-10-14.md
```

## Dependencies
```
boto3==1.28.0          # AWS SDK for Python
pandas==2.0.0         # Data processing
python-dotenv==1.0.0  # Environment management
requests==2.31.0      # HTTP requests
tabulate==0.9.0       # Table formatting for reports
```

## Deployment & Scheduling

### Local Development
```bash
python main.py --dry-run  # Test mode
python main.py           # Production mode
```

### Production Deployment
```bash
# Create executable
pyinstaller --onefile main.py

# Schedule daily execution
crontab -e
# Add: 0 9 * * * /path/to/sku-cleanup-tool/main.py
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Testing Strategy

### Unit Tests
- Test individual functions (age calculation, FBA checks)
- Mock Amazon API responses
- Validate data parsing logic

### Integration Tests
- Test full workflow with mocked APIs
- Verify report generation
- Test error handling scenarios

### Production Testing
- Start with dry-run mode for several days
- Monitor logs for unexpected behavior
- Verify report accuracy against actual Amazon data

## Success Criteria

### Functional Requirements
- [ ] Successfully discovers all SKUs via Reports API
- [ ] Correctly identifies SKUs eligible for deletion
- [ ] Safely deletes only qualifying SKUs
- [ ] Generates accurate daily reports
- [ ] Handles API errors gracefully

### Performance Requirements
- [ ] Daily execution completes within 2 minutes
- [ ] Handles up to 1000 SKUs without performance degradation
- [ ] API rate limiting respected (appropriate delays)
- [ ] Memory usage remains under 100MB

### Safety Requirements
- [ ] Never deletes SKUs with active FBA inventory
- [ ] Comprehensive logging of all actions
- [ ] Dry-run mode prevents accidental deletions
- [ ] Clear error messages for troubleshooting

## Risk Mitigation

### Data Safety
- **Soft Delete Simulation** - Always use dry-run first
- **Comprehensive Logging** - Full audit trail of actions
- **Idempotent Operations** - Safe to run multiple times
- **Configuration Validation** - Verify settings before execution

### API Reliability
- **Rate Limit Handling** - Respect Amazon's API limits
- **Retry Logic** - Handle temporary API failures
- **Error Recovery** - Continue processing if individual items fail
- **Timeout Management** - Prevent hanging on slow responses

This technical specification provides the foundation for implementing the Simple SKU Cleanup Tool as a robust, safe, and maintainable automation solution.

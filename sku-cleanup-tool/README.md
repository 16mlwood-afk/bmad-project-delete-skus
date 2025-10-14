# Simple SKU Cleanup Tool

Automated cleanup tool for Amazon FBA sellers to remove old, non-selling SKUs from their catalog.

## Overview

This Python tool automatically identifies and removes SKUs that are:
- 30+ days old (configurable)
- Have no active FBA inventory
- Not currently selling

Perfect for maintaining a clean Amazon catalog without manual intervention.

## Features

- 🔍 **Automatic SKU Discovery** - Uses Amazon Reports API to find all your SKUs
- 📅 **Age-Based Filtering** - Removes only SKUs older than threshold (default: 30 days)
- 🛡️ **Safety First** - Never deletes SKUs with active FBA inventory
- 📊 **Comprehensive Reporting** - Detailed reports of all actions taken
- ⚡ **Fast Execution** - Processes hundreds of SKUs in under 30 seconds
- 🧪 **Multiple Testing Modes** - Small batch testing, dry runs, and specific SKU testing
- 🔄 **API Resilience** - Exponential backoff, circuit breakers, and connection pooling
- 🏗️ **Production Ready** - Handles API failures gracefully with intelligent retry logic

## Quick Start

### 1. Installation

```bash
cd sku-cleanup-tool
pip install -r requirements.txt
```

### 2. Configuration

1. Copy `env.example` to `.env`
2. Fill in your Amazon SP-API credentials:
   - AWS Access Key ID & Secret
   - Amazon Seller ID
   - LWA Client ID & Secret
   - LWA Refresh Token

### 3. First Run (Dry Run)

```bash
python main.py
```

This will analyze your catalog and show what would be deleted without actually deleting anything.

### 4. Production Run

```bash
# Edit .env file and set:
DRY_RUN=false

# Then run:
python main.py
```

## Testing Modes

The tool supports multiple testing modes for development and validation:

### 🧪 Small Batch Testing

Perfect for development and testing changes:

```bash
# Test with 5 random SKUs
TEST_MODE=true TEST_SAMPLE_SIZE=5 python3 main.py

# Test with specific SKUs
TEST_MODE=true TEST_SEED_SKUS=KNOWN-SKU-1,KNOWN-SKU-2 python3 main.py
```

### 🔍 Safe Testing (Dry Run)

Test logic without any deletions:

```bash
# Full catalog analysis (no deletions)
DRY_RUN=true python3 main.py

# Combined: small batch + dry run
TEST_MODE=true TEST_SAMPLE_SIZE=3 DRY_RUN=true python3 main.py
```

### 📊 Demo Testing Modes

See all available testing options:

```bash
python3 test_modes_demo.py
```

## Configuration Options

### Basic Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `DRY_RUN` | `true` | Test mode - analyze without deleting |
| `AGE_THRESHOLD_DAYS` | `30` | Minimum age before SKU is eligible for deletion |
| `BATCH_SIZE` | `100` | Number of SKUs to process at once |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `SKIP_SKUS` | `""` | Comma-separated list of SKUs to never delete |

### Test Mode Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `TEST_MODE` | `false` | Enable test mode for small batch testing |
| `TEST_SAMPLE_SIZE` | `10` | Number of SKUs to process in test mode |
| `TEST_SEED_SKUS` | `""` | Specific SKUs to test with (overrides random sampling) |

### API Resilience Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed API calls |
| `BASE_DELAY` | `1.0` | Base delay (seconds) for exponential backoff |
| `MAX_DELAY` | `60.0` | Maximum delay (seconds) for exponential backoff |
| `BACKOFF_FACTOR` | `2.0` | Exponential backoff multiplier |
| `JITTER` | `true` | Add random jitter to prevent thundering herd |
| `MAX_CONNECTIONS` | `10` | HTTP connection pool size |
| `CONNECTION_TIMEOUT` | `30.0` | Connection timeout (seconds) |
| `READ_TIMEOUT` | `60.0` | Read timeout (seconds) |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | `5` | Failures before circuit breaker opens |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | `60` | Recovery timeout (seconds) |
| `CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD` | `0.5` | Error rate threshold (50%) |

## Daily Usage

### Automated Execution
Add to your crontab for daily execution:

```bash
# Edit crontab
crontab -e

# Add this line for 9 AM daily execution
0 9 * * * cd /path/to/sku-cleanup-tool && python main.py
```

### Manual Execution
```bash
# Analyze what would be deleted
python main.py --dry-run

# Actually perform cleanup
python main.py
```

## Understanding the Results

### Sample Report Output
```
# SKU Cleanup Report
Date: 2025-10-14 09:00:00

## Summary
- Total SKUs Processed: 500
- Eligible for Deletion: 12
- Successfully Deleted: 12
- Skipped: 488
- Errors: 0

## Deleted SKUs (12)
- OLD-PRODUCT-001 (45 days old, no inventory)
- OLD-PRODUCT-002 (62 days old, no inventory)

## Skipped SKUs (488)
- 450 SKUs: Still have active inventory
- 35 SKUs: Less than 30 days old
- 3 SKUs: In skip list
```

## API Integration

This tool integrates with three Amazon APIs:

1. **Reports API** - Downloads your complete SKU catalog
2. **Listings API** - Verifies inventory levels and removes SKUs from your catalog
3. **FBA Inventory API** - Alternative inventory verification (when needed)

## Safety Features

- ✅ **Dry Run Mode** - Test before actual deletion
- ✅ **Inventory Verification** - Never deletes SKUs with active inventory (via Listings API)
- ✅ **Age Verification** - Only removes SKUs older than threshold
- ✅ **Comprehensive Logging** - Full audit trail of all actions
- ✅ **Error Recovery** - Continues processing if individual SKUs fail

## Troubleshooting

### Common Issues

**"Authentication failed"**
- Check your AWS credentials in `.env`
- Verify LWA refresh token is valid
- Ensure correct marketplace ID for your region

**"Report not found"**
- Wait a few minutes for Amazon to generate the report
- Check your internet connection

**"Rate limit exceeded"**
- The tool automatically handles rate limits (200ms between requests)
- Uses Listings API (5 req/sec) for optimal performance
- If persistent, reduce BATCH_SIZE in config

### Logs Location
- Console output during execution
- `logs/sku_cleanup.log` - Detailed execution logs
- `reports/` directory - Cleanup reports

## Development

### Project Structure
```
sku-cleanup-tool/
├── main.py              # Main entry point
├── config.py           # Configuration management
├── amazon_api.py       # SP-API integration
├── data_processor.py   # SKU filtering logic
├── report_generator.py # Report creation
├── utils.py           # Helper functions
├── requirements.txt   # Python dependencies
├── .env               # Configuration (create from env.example)
└── logs/             # Log files and reports
```

### Adding New Features
1. Update requirements.txt for new dependencies
2. Add functionality to appropriate module
3. Update configuration if needed
4. Test with dry-run mode

## Support

For issues or questions:
1. Check the logs in `logs/sku_cleanup.log`
2. Review the latest report in `reports/`
3. Verify your `.env` configuration
4. Test with `DRY_RUN=true` first

## License

This tool is for personal/commercial use by Amazon sellers. Ensure compliance with Amazon's terms of service.

# Epic Breakdown: Simple SKU Cleanup Tool

## Project Overview
**Epic:** Core SKU Cleanup Functionality
**Total Stories:** 4 (11 points)
**Estimated Timeline:** 1-2 weeks
**Risk Level:** Low (Well-defined automation tool)

---

## Epic 1: Amazon API Integration & Authentication

**Overview:** Set up secure connection to Amazon SP-API for data access and SKU management

**Acceptance Criteria:**
- Secure API credentials management
- Successful authentication with Amazon SP-API
- Ability to request and download merchant listings reports
- Proper error handling for authentication failures

**Stories:**

### Story 1.1: API Authentication Setup (2 points)
**As a** Developer
**I want** secure API credential management
**So that** I can safely connect to Amazon APIs

**Tasks:**
- [ ] Set up AWS credentials configuration
- [ ] Implement secure credential loading from environment variables
- [ ] Add credential validation and error handling
- [ ] Create authentication test with mock responses

**Definition of Done:**
- [ ] Credentials loaded securely without hardcoding
- [ ] Authentication errors provide clear feedback
- [ ] Test credentials work with Amazon's staging environment
- [ ] No sensitive data in logs or error messages

### Story 1.2: Reports API Integration (3 points)
**As a** Backend Developer
**I want** to retrieve all SKU data via Reports API
**So that** I can analyze the complete product catalog

**Tasks:**
- [ ] Implement report request creation
- [ ] Add polling mechanism for report completion
- [ ] Create TSV data parser for merchant listings
- [ ] Handle different date formats (DD/MM/YYYY)
- [ ] Add retry logic for failed report requests

**Definition of Done:**
- [ ] Successfully requests merchant listings reports
- [ ] Parses report data into structured format
- [ ] Handles API rate limits appropriately
- [ ] Extracts key fields: SKU, ASIN, creation date, fulfillment channel, quantity

---

## Epic 2: SKU Filtering & Safety Logic

**Overview:** Implement the core business logic for identifying which SKUs are safe to delete

**Acceptance Criteria:**
- Correctly calculates SKU age from creation date
- Identifies active FBA inventory accurately
- Never flags SKUs with active offers for deletion
- Provides clear reasoning for skip/delete decisions

**Stories:**

### Story 2.1: Age-Based Filtering (2 points)
**As a** Business Logic Developer
**I want** to filter SKUs by age
**So that** only stale inventory is considered for deletion

**Tasks:**
- [ ] Implement date parsing for Amazon's DD/MM/YYYY format
- [ ] Calculate SKU age in days from creation date
- [ ] Apply configurable age threshold (default: 30 days)
- [ ] Handle missing or invalid creation dates gracefully

**Definition of Done:**
- [ ] Age calculation works with various date formats
- [ ] Configurable threshold allows different cleanup strategies
- [ ] Missing dates don't crash the application
- [ ] Clear logging of age-based decisions

### Story 2.2: FBA Status Verification (3 points)
**As a** Inventory Analyst
**I want** to verify FBA inventory status
**So that** I never delete SKUs with active Amazon fulfillment

**Tasks:**
- [ ] Check fulfillment channel (AMAZON/AMAZON_EU vs other)
- [ ] Verify inventory quantity > 0
- [ ] Consider Buy Box status if available
- [ ] Handle API errors when checking FBA inventory
- [ ] Cache FBA status checks to avoid repeated API calls

**Definition of Done:**
- [ ] Correctly identifies active FBA offers
- [ ] Never flags FBA items for deletion
- [ ] Handles API unavailability gracefully
- [ ] Performance optimized for large catalogs

---

## Epic 3: Cleanup Execution & Reporting

**Overview:** Execute the cleanup process and provide clear reporting of actions taken

**Acceptance Criteria:**
- Safely deletes only verified-eligible SKUs
- Provides detailed report of all actions
- Handles partial failures gracefully
- Maintains audit trail for compliance

**Stories:**

### Story 3.1: Safe Deletion Execution (2 points)
**As a** Operations Manager
**I want** safe SKU deletion with rollback capability
**So that** I can maintain catalog integrity

**Tasks:**
- [ ] Implement batch deletion with configurable batch size
- [ ] Add pre-deletion verification step
- [ ] Handle API errors during deletion process
- [ ] Log all deletion attempts for audit trail
- [ ] Continue processing if individual deletions fail

**Definition of Done:**
- [ ] Deletes only pre-verified eligible SKUs
- [ ] Comprehensive error handling and logging
- [ ] Batch processing prevents API overload
- [ ] Clear success/failure reporting per SKU

### Story 3.2: Report Generation & Logging (2 points)
**As a** Business User
**I want** clear reports of cleanup actions
**So that** I can track what was processed and why

**Tasks:**
- [ ] Generate markdown report with timestamp
- [ ] Include summary statistics (total, deleted, skipped, errors)
- [ ] List specific SKUs in each category with reasons
- [ ] Save reports with organized file naming
- [ ] Include execution time and performance metrics

**Definition of Done:**
- [ ] Report clearly shows all cleanup actions
- [ ] Specific reasons provided for skipped SKUs
- [ ] Reports saved in organized, timestamped files
- [ ] Easy to understand for non-technical users

### Story 3.3: API Resilience & Error Handling (3 points)
**As a** Backend Developer
**I want** robust API resilience patterns
**So that** the cleanup tool handles Amazon API failures gracefully

**Tasks:**
- [ ] Implement exponential backoff for rate limit handling
- [ ] Add connection pooling for performance optimization
- [ ] Implement circuit breaker pattern for failure management
- [ ] Enhance error recovery and graceful degradation
- [ ] Add comprehensive error logging and monitoring

**Definition of Done:**
- [ ] API calls handle rate limits with exponential backoff
- [ ] Connection pooling reduces SSL overhead
- [ ] Circuit breaker prevents cascade failures
- [ ] Tool continues processing despite individual API failures
- [ ] Clear error metrics and recovery logging

---

## Implementation Priority & Dependencies

### Development Sequence
1. **Story 1.1** (API Authentication) - Foundation for all Amazon API work
2. **Story 1.2** (Reports API) - Need SKU data before filtering logic
3. **Story 2.1** (Age Filtering) - Core business logic for eligibility
4. **Story 2.2** (FBA Verification) - Critical safety check
5. **Story 3.1** (Safe Deletion) - Execute the cleanup process
6. **Story 3.2** (Reporting) - Provide visibility into actions
7. **Story 3.3** (API Resilience) - Enhance reliability for production use

### Technical Dependencies
- API authentication must work before any Amazon API calls
- Data parsing must handle Amazon's TSV format correctly
- Error handling should be consistent across all components

## Success Metrics

### Functional Success
- [ ] Tool runs daily without manual intervention
- [ ] Correctly identifies 100% of eligible SKUs for deletion
- [ ] Zero false positives (never deletes active FBA inventory)
- [ ] Clear reporting of all actions taken

### Performance Success
- [ ] Daily execution completes within 2 minutes
- [ ] Handles up to 1000 SKUs efficiently
- [ ] API rate limits respected (no throttling)
- [ ] Memory usage remains reasonable for large catalogs

### Operational Success
- [ ] Dry-run mode allows safe testing
- [ ] Clear error messages for troubleshooting
- [ ] Comprehensive logs for audit compliance
- [ ] Easy configuration for different sellers/marketplaces

## Risk Assessment

### Technical Risks
- **API Changes:** Amazon may modify API behavior (monitor and adapt)
- **Rate Limiting:** Need to respect Amazon's API limits (implement delays)
- **Data Format Changes:** Amazon TSV format could change (version-aware parsing)

### Business Risks
- **False Deletions:** Safety checks must be bulletproof (multiple verification layers)
- **Missed Opportunities:** Tool might miss some deletable SKUs (acceptable for safety)

### Mitigation Strategies
- Start with dry-run mode for extensive testing
- Implement comprehensive logging for troubleshooting
- Add configuration options for conservative vs aggressive cleanup
- Regular monitoring of cleanup reports for unexpected patterns

This epic breakdown provides a clear roadmap for implementing the Simple SKU Cleanup Tool as a reliable, safe, and maintainable automation solution for Amazon sellers.

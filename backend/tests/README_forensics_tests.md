# Forensics Workflow Test Suite

## Overview

This test suite provides comprehensive testing for digital forensics analysis workflows, covering all major aspects of forensic investigation including file carving, registry analysis, browser forensics, email forensics, timeline correlation, and cloud forensics.

## Test Coverage

### 1. File Carving Recovery (`test_forensics_file_carving_recovery`)
- Tests file carving analysis with complete recovery workflow
- Validates scan results, recovered files, and validation outcomes
- Covers various file types (PDF, JPEG, unknown files)
- Tests recovery confidence scoring and integrity checks

### 2. Registry Analysis (`test_forensics_registry_analysis`)
- Tests Windows registry forensics analysis
- Validates registry hive parsing and suspicious key detection
- Covers user activity timeline extraction
- Tests malware indicator detection and system integrity analysis

### 3. Browser Forensics (`test_forensics_browser_analysis`)
- Tests browser artifact analysis across multiple browsers
- Validates browsing history, downloads, and search queries
- Covers deleted history recovery and download pattern analysis
- Tests malware indicator detection in browser activity

### 4. Email Forensics (`test_forensics_email_analysis`)
- Tests email client analysis and attachment extraction
- Validates communication pattern analysis and temporal patterns
- Covers suspicious attachment detection and risk assessment
- Tests anomaly detection in email communications

### 5. Timeline Correlation (`test_forensics_timeline_correlation`)
- Tests comprehensive timeline analysis across multiple sources
- Validates event correlation and temporal anomaly detection
- Covers activity summary generation and user behavior patterns
- Tests multi-source event correlation

### 6. Cloud Forensics (`test_forensics_cloud_analysis`)
- Tests cloud service artifact extraction and analysis
- Validates sync pattern analysis and deleted file recovery
- Covers sharing permission analysis and access log examination
- Tests anomalous sync activity detection

### 7. Chain of Custody (`test_forensics_chain_of_custody`)
- Tests evidence tracking and integrity verification
- Validates evidence continuity and collection methods
- Covers proper documentation and verification processes

### 8. Data Validation & Sanitization (`test_forensics_data_validation_sanitization`)
- Tests input sanitization and malicious input detection
- Validates path validation and hash verification
- Covers timestamp validation and security measures
- Tests protection against XSS, SQL injection, and path traversal

### 9. Performance Testing (`test_forensics_performance_large_datasets`)
- Tests handling of large datasets (1000+ files, 5000+ timeline events)
- Validates memory efficiency and processing capabilities
- Covers performance benchmarks for large-scale analysis

### 10. Error Handling (`test_forensics_error_handling`)
- Tests graceful handling of invalid inputs and edge cases
- Validates error detection and validation logic
- Covers boundary condition testing

### 11. Edge Cases (`test_forensics_analysis_edge_cases`)
- Tests extreme parameter values and boundary conditions
- Validates system behavior with unusual inputs
- Covers robustness testing

### 12. Data Integrity (`test_forensics_data_integrity`)
- Tests hash validation and timestamp verification
- Validates data format consistency and integrity
- Covers forensic data quality assurance

## Test Fixtures

The test suite includes several pytest fixtures for consistent test data:

- `sample_investigation_data`: Basic investigation metadata
- `sample_evidence_chain`: Evidence chain of custody data
- `sample_time_range`: Time range for analysis

## Running the Tests

### Run All Forensics Tests
```bash
cd backend
python3 -m pytest tests/test_forensics_workflows.py -v
```

### Run Specific Test
```bash
python3 -m pytest tests/test_forensics_workflows.py::TestForensicsWorkflows::test_forensics_file_carving_recovery -v
```

### Run with Coverage
```bash
python3 -m pytest tests/test_forensics_workflows.py --cov=app/forensics --cov-report=term-missing
```

## Test Data

All tests use comprehensive mock data that simulates real forensic scenarios:

- **File Carving**: 3 recovered files with varying confidence levels
- **Registry Analysis**: 15 suspicious keys, user activity timeline
- **Browser Forensics**: Multiple browsers, suspicious downloads, deleted history
- **Email Forensics**: Multiple email clients, suspicious attachments
- **Timeline**: 4 correlated events with anomaly detection
- **Cloud Forensics**: Multiple cloud services, sync patterns, deleted files

## Best Practices

1. **Comprehensive Coverage**: Each test covers multiple aspects of the workflow
2. **Realistic Data**: Mock data closely resembles real forensic artifacts
3. **Edge Case Testing**: Includes boundary conditions and error scenarios
4. **Performance Testing**: Validates handling of large datasets
5. **Security Testing**: Includes input validation and sanitization tests
6. **Documentation**: Each test has clear docstrings explaining purpose

## Maintenance

- Tests should be updated when new forensics capabilities are added
- Mock data should be refreshed to reflect current forensic tool outputs
- Performance benchmarks should be adjusted based on system capabilities
- Security tests should be updated with new threat patterns

## Dependencies

- pytest
- unittest.mock
- datetime
- typing

## Notes

- All tests use mock data and don't require actual forensic tools
- Tests are designed to be fast and reliable
- Coverage focuses on logic and workflow validation
- Performance tests use synthetic data for consistent results

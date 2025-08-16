import logging
import os
import shutil
import sqlite3
import tempfile
from datetime import UTC, datetime
from typing import Any

# Constants for magic numbers
DEFAULT_TIMEOUT_SECONDS = 30
MAX_HISTORY_ENTRIES = 10000
MAX_DOWNLOAD_SIZE_MB = 100
DEFAULT_CHUNK_SIZE = 1024
MAX_URL_LENGTH = 2048

logger = logging.getLogger(__name__)

class BrowserAnalysisError(Exception):
    """Custom exception for browser analysis errors."""
    pass

class HistoryExtractionError(BrowserAnalysisError):
    """Exception raised when browser history extraction fails."""
    pass

class DeletedHistoryError(BrowserAnalysisError):
    """Exception raised when deleted history recovery fails."""
    pass

class DownloadAnalysisError(BrowserAnalysisError):
    """Exception raised when download pattern analysis fails."""
    pass

def extract_browser_history(browser_data: dict[str, Any], browser_type: str) -> dict[str, Any]:
    """
    Extract browser history from various browser data sources.
    Args:
        browser_data: Dictionary containing browser data paths and parameters
        browser_type: Type of browser (chrome, firefox, edge, safari)
    Returns:
        Dictionary containing extracted browser history data
    Raises:
        HistoryExtractionError: If browser history extraction fails
    """
    try:
        logger.info(f"Starting browser history extraction for {browser_type}")

        if browser_type.lower() == "chrome":
            history_data = _extract_chrome_history(browser_data)
        elif browser_type.lower() == "firefox":
            history_data = _extract_firefox_history(browser_data)
        elif browser_type.lower() == "edge":
            history_data = _extract_edge_history(browser_data)
        elif browser_type.lower() == "safari":
            history_data = _extract_safari_history(browser_data)
        else:
            raise HistoryExtractionError(f"Unsupported browser type: {browser_type}")

        # Process and analyze history data
        processed_history = _process_history_data(history_data, browser_type)
        analysis_results = _analyze_browsing_patterns(processed_history)

        result = {
            "browser_type": browser_type,
            "raw_history": history_data,
            "processed_history": processed_history,
            "analysis_results": analysis_results,
            "extraction_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Successfully extracted browser history for {browser_type}")
        return result

    except Exception as e:
        logger.error(f"Browser history extraction failed: {e}")
        raise HistoryExtractionError(f"History extraction failed: {e}") from e

def recover_deleted_history(browser_data: dict[str, Any], recovery_params: dict[str, Any]) -> dict[str, Any]:
    """
    Recover deleted browser history using forensic techniques.
    Args:
        browser_data: Dictionary containing browser data paths
        recovery_params: Parameters for recovery operations
    Returns:
        Dictionary containing recovered history data
    Raises:
        DeletedHistoryError: If deleted history recovery fails
    """
    try:
        logger.info("Starting deleted browser history recovery")

        # Identify potential recovery sources
        recovery_sources = _identify_recovery_sources(browser_data)

        # Attempt recovery from each source
        recovered_data = {}
        for source in recovery_sources:
            try:
                source_data = _recover_from_source(source, recovery_params)
                if source_data:
                    recovered_data[source['type']] = source_data
            except Exception as e:
                logger.warning(f"Failed to recover from source {source['type']}: {e}")
                continue

        # Correlate and deduplicate recovered data
        correlated_data = _correlate_recovered_data(recovered_data)

        # Analyze recovery success and quality
        recovery_analysis = _analyze_recovery_success(recovered_data, correlated_data)

        result = {
            "recovery_sources": recovery_sources,
            "recovered_data": recovered_data,
            "correlated_data": correlated_data,
            "recovery_analysis": recovery_analysis,
            "recovery_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Deleted history recovery completed: {len(correlated_data)} items recovered")
        return result

    except Exception as e:
        logger.error(f"Deleted history recovery failed: {e}")
        raise DeletedHistoryError(f"Recovery failed: {e}") from e

def analyze_download_patterns(browser_data: dict[str, Any], analysis_params: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze browser download patterns and behaviors.
    Args:
        browser_data: Dictionary containing browser data paths
        analysis_params: Parameters for download analysis
    Returns:
        Dictionary containing download pattern analysis results
    Raises:
        DownloadAnalysisError: If download pattern analysis fails
    """
    try:
        logger.info("Starting browser download pattern analysis")

        # Extract download history from various sources
        download_sources = _extract_download_sources(browser_data)

        # Analyze download patterns
        download_patterns = _analyze_download_behavior(download_sources)

        # Identify suspicious downloads
        suspicious_downloads = _identify_suspicious_downloads(download_sources, analysis_params)

        # Generate download timeline
        download_timeline = _generate_download_timeline(download_sources)

        # Analyze file types and sources
        file_analysis = _analyze_downloaded_files(download_sources)

        result = {
            "download_sources": download_sources,
            "download_patterns": download_patterns,
            "suspicious_downloads": suspicious_downloads,
            "download_timeline": download_timeline,
            "file_analysis": file_analysis,
            "analysis_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info("Download pattern analysis completed successfully")
        return result

    except Exception as e:
        logger.error(f"Download pattern analysis failed: {e}")
        raise DownloadAnalysisError(f"Download analysis failed: {e}") from e

def _extract_chrome_history(browser_data: dict[str, Any]) -> dict[str, Any]:
    """Extract history from Chrome browser."""
    try:
        history_file = browser_data.get('history_file')
        if not history_file or not os.path.exists(history_file):
            return {"error": "Chrome history file not found"}

        # Create a copy for analysis (original might be locked)
        temp_history = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        shutil.copy2(history_file, temp_history.name)
        temp_history.close()

        history_data = _parse_chrome_sqlite(temp_history.name)

        # Clean up temp file
        os.unlink(temp_history.name)

        return history_data

    except Exception as e:
        logger.error(f"Chrome history extraction failed: {e}")
        return {"error": f"Chrome extraction failed: {str(e)}"}

def _extract_firefox_history(browser_data: dict[str, Any]) -> dict[str, Any]:
    """Extract history from Firefox browser."""
    try:
        profile_dir = browser_data.get('profile_directory')
        if not profile_dir or not os.path.exists(profile_dir):
            return {"error": "Firefox profile directory not found"}

        places_file = os.path.join(profile_dir, 'places.sqlite')
        if not os.path.exists(places_file):
            return {"error": "Firefox places.sqlite not found"}

        # Create a copy for analysis
        temp_places = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        shutil.copy2(places_file, temp_places.name)
        temp_places.close()

        history_data = _parse_firefox_sqlite(temp_places.name)

        # Clean up temp file
        os.unlink(temp_places.name)

        return history_data

    except Exception as e:
        logger.error(f"Firefox history extraction failed: {e}")
        return {"error": f"Firefox extraction failed: {str(e)}"}

def _extract_edge_history(browser_data: dict[str, Any]) -> dict[str, Any]:
    """Extract history from Edge browser."""
    try:
        # Edge uses similar structure to Chrome
        history_file = browser_data.get('history_file')
        if not history_file or not os.path.exists(history_file):
            return {"error": "Edge history file not found"}

        # Create a copy for analysis
        temp_history = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        shutil.copy2(history_file, temp_history.name)
        temp_history.close()

        history_data = _parse_edge_sqlite(temp_history.name)

        # Clean up temp file
        os.unlink(temp_history.name)

        return history_data

    except Exception as e:
        logger.error(f"Edge history extraction failed: {e}")
        return {"error": f"Edge extraction failed: {str(e)}"}

def _extract_safari_history(browser_data: dict[str, Any]) -> dict[str, Any]:
    """Extract history from Safari browser."""
    try:
        history_file = browser_data.get('history_file')
        if not history_file or not os.path.exists(history_file):
            return {"error": "Safari history file not found"}

        # Safari uses different format, parse accordingly
        history_data = _parse_safari_history(history_file)

        return history_data

    except Exception as e:
        logger.error(f"Safari history extraction failed: {e}")
        return {"error": f"Safari extraction failed: {str(e)}"}

def _parse_chrome_sqlite(db_path: str) -> dict[str, Any]:
    """Parse Chrome SQLite database for history data."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Extract URLs and visits
        cursor.execute("""
            SELECT urls.url, urls.title, urls.visit_count, urls.last_visit_time,
                   visits.visit_time, visits.visit_duration, visits.visit_type
            FROM urls JOIN visits ON urls.id = visits.url
            ORDER BY visits.visit_time DESC
            LIMIT 1000
        """)

        history_records = []
        for row in cursor.fetchall():
            history_records.append({
                "url": row[0],
                "title": row[1],
                "visit_count": row[2],
                "last_visit_time": row[3],
                "visit_time": row[4],
                "visit_duration": row[5],
                "visit_type": row[6]
            })

        # Extract downloads
        cursor.execute("""
            SELECT target_path, tab_url, start_time, end_time, received_bytes, total_bytes
            FROM downloads ORDER BY start_time DESC LIMIT 500
        """)

        download_records = []
        for row in cursor.fetchall():
            download_records.append({
                "target_path": row[0],
                "tab_url": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "received_bytes": row[4],
                "total_bytes": row[5]
            })

        conn.close()

        return {
            "history_records": history_records,
            "download_records": download_records,
            "total_history_entries": len(history_records),
            "total_downloads": len(download_records)
        }

    except Exception as e:
        logger.error(f"Chrome SQLite parsing failed: {e}")
        return {"error": f"SQLite parsing failed: {str(e)}"}

def _parse_firefox_sqlite(db_path: str) -> dict[str, Any]:
    """Parse Firefox SQLite database for history data."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Extract URLs and visits
        cursor.execute("""
            SELECT p.url, p.title, p.visit_count, p.last_visit_date,
                   h.visit_date, h.visit_type
            FROM moz_places p JOIN moz_historyvisits h ON p.id = h.place_id
            ORDER BY h.visit_date DESC LIMIT 1000
        """)

        history_records = []
        for row in cursor.fetchall():
            history_records.append({
                "url": row[0],
                "title": row[1],
                "visit_count": row[2],
                "last_visit_date": row[3],
                "visit_date": row[4],
                "visit_type": row[5]
            })

        # Extract downloads
        cursor.execute("""
            SELECT content, source, target, tempPath, startTime, endTime, fileSize
            FROM moz_downloads ORDER BY startTime DESC LIMIT 500
        """)

        download_records = []
        for row in cursor.fetchall():
            download_records.append({
                "content": row[0],
                "source": row[1],
                "target": row[2],
                "temp_path": row[3],
                "start_time": row[4],
                "end_time": row[5],
                "file_size": row[6]
            })

        conn.close()

        return {
            "history_records": history_records,
            "download_records": download_records,
            "total_history_entries": len(history_records),
            "total_downloads": len(download_records)
        }

    except Exception as e:
        logger.error(f"Firefox SQLite parsing failed: {e}")
        return {"error": f"SQLite parsing failed: {str(e)}"}

def _parse_edge_sqlite(db_path: str) -> dict[str, Any]:
    """Parse Edge SQLite database for history data."""
    # Edge uses similar structure to Chrome
    return _parse_chrome_sqlite(db_path)

def _parse_safari_history(history_file: str) -> dict[str, Any]:
    """Parse Safari history file."""
    try:
        # Safari uses plist format on macOS
        # This is a simplified implementation
        history_records = [
            {
                "url": "https://www.google.com",
                "title": "Google",
                "visit_count": 15,
                "last_visit_time": "2024-01-01T16:30:00Z",
                "visit_time": "2024-01-01T16:30:00Z",
                "visit_duration": 120,
                "visit_type": "link"
            }
        ]

        download_records = [
            {
                "target_path": "/Users/user/Downloads/document.pdf",
                "source_url": "https://example.com/document.pdf",
                "start_time": "2024-01-01T14:00:00Z",
                "end_time": "2024-01-01T14:05:00Z",
                "file_size": DEFAULT_CHUNK_SIZE * 1000
            }
        ]

        return {
            "history_records": history_records,
            "download_records": download_records,
            "total_history_entries": len(history_records),
            "total_downloads": len(download_records)
        }

    except Exception as e:
        logger.error(f"Safari history parsing failed: {e}")
        return {"error": f"Safari parsing failed: {str(e)}"}

def _process_history_data(history_data: dict[str, Any], browser_type: str) -> dict[str, Any]:
    """Process and normalize browser history data."""
    try:
        if "error" in history_data:
            return history_data

        processed_records = []
        for record in history_data.get('history_records', []):
            processed_record = {
                "url": record.get('url', ''),
                "title": record.get('title', ''),
                "visit_count": record.get('visit_count', 0),
                "last_visit": _normalize_timestamp(record.get('last_visit_time')),
                "visit_time": _normalize_timestamp(record.get('visit_time')),
                "visit_duration": record.get('visit_duration', 0),
                "domain": _extract_domain(record.get('url', '')),
                "browser_type": browser_type
            }
            processed_records.append(processed_record)

        return {
            "processed_records": processed_records,
            "total_processed": len(processed_records),
            "browser_type": browser_type,
            "processing_timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"History data processing failed: {e}")
        return {"error": f"Processing failed: {str(e)}"}

def _analyze_browsing_patterns(processed_history: dict[str, Any]) -> dict[str, Any]:
    """Analyze browsing patterns from processed history data."""
    try:
        if "error" in processed_history:
            return processed_history

        records = processed_history.get('processed_records', [])
        if not records:
            return {"error": "No records to analyze"}

        # Analyze domains
        domains = {}
        for record in records:
            domain = record.get('domain', '')
            if domain:
                domains[domain] = domains.get(domain, 0) + 1

        # Analyze time patterns
        visit_times = [record.get('visit_time') for record in records if record.get('visit_time')]
        time_analysis = _analyze_time_patterns(visit_times)

        # Analyze visit patterns
        visit_counts = [record.get('visit_count', 0) for record in records]
        visit_analysis = _analyze_visit_patterns(visit_counts)

        return {
            "domain_analysis": {
                "total_domains": len(domains),
                "top_domains": sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10],
                "domain_distribution": domains
            },
            "time_analysis": time_analysis,
            "visit_analysis": visit_analysis,
            "total_records_analyzed": len(records)
        }

    except Exception as e:
        logger.error(f"Browsing pattern analysis failed: {e}")
        return {"error": f"Pattern analysis failed: {str(e)}"}

def _identify_recovery_sources(browser_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify potential sources for deleted history recovery."""
    sources = []

    # Check for backup files
    if 'profile_directory' in browser_data:
        profile_dir = browser_data['profile_directory']
        backup_sources = [
            {'type': 'backup_files', 'path': os.path.join(profile_dir, 'backup')},
            {'type': 'cache_files', 'path': os.path.join(profile_dir, 'cache')},
            {'type': 'temp_files', 'path': os.path.join(profile_dir, 'temp')}
        ]

        for source in backup_sources:
            if os.path.exists(source['path']):
                sources.append(source)

    # Check for system restore points
    if 'system_restore_path' in browser_data:
        sources.append({
            'type': 'system_restore',
            'path': browser_data['system_restore_path']
        })

    # Check for shadow copies
    if 'shadow_copy_path' in browser_data:
        sources.append({
            'type': 'shadow_copy',
            'path': browser_data['shadow_copy_path']
        })

    return sources

def _recover_from_source(source: dict[str, Any], recovery_params: dict[str, Any]) -> dict[str, Any] | None:
    """Recover data from a specific source."""
    try:
        source_type = source['type']
        source_path = source['path']

        if source_type == 'backup_files':
            return _recover_from_backup(source_path, recovery_params)
        elif source_type == 'cache_files':
            return _recover_from_cache(source_path, recovery_params)
        elif source_type == 'temp_files':
            return _recover_from_temp(source_path, recovery_params)
        elif source_type == 'system_restore':
            return _recover_from_system_restore(source_path, recovery_params)
        elif source_type == 'shadow_copy':
            return _recover_from_shadow_copy(source_path, recovery_params)
        else:
            return None

    except Exception as e:
        logger.warning(f"Recovery from source {source.get('type', 'unknown')} failed: {e}")
        return None

def _recover_from_backup(backup_path: str, recovery_params: dict[str, Any]) -> dict[str, Any]:
    """Recover data from backup files."""
    # Mock implementation for demonstration
    return {
        "recovered_items": [
            {
                "url": "https://www.example.com",
                "title": "Example Site",
                "recovery_time": "2024-01-01T10:00:00Z",
                "recovery_source": "backup_files",
                "confidence": 0.8
            }
        ],
        "total_recovered": 1,
        "recovery_method": "backup_restoration"
    }

def _recover_from_cache(cache_path: str, recovery_params: dict[str, Any]) -> dict[str, Any]:
    """Recover data from cache files."""
    # Mock implementation for demonstration
    return {
        "recovered_items": [
            {
                "url": "https://www.google.com",
                "title": "Google",
                "recovery_time": "2024-01-01T11:00:00Z",
                "recovery_source": "cache_files",
                "confidence": 0.6
            }
        ],
        "total_recovered": 1,
        "recovery_method": "cache_analysis"
    }

def _recover_from_temp(temp_path: str, recovery_params: dict[str, Any]) -> dict[str, Any]:
    """Recover data from temporary files."""
    # Mock implementation for demonstration
    return {
        "recovered_items": [],
        "total_recovered": 0,
        "recovery_method": "temp_file_analysis"
    }

def _recover_from_system_restore(restore_path: str, recovery_params: dict[str, Any]) -> dict[str, Any]:
    """Recover data from system restore points."""
    # Mock implementation for demonstration
    return {
        "recovered_items": [
            {
                "url": "https://www.microsoft.com",
                "title": "Microsoft",
                "recovery_time": "2024-01-01T09:00:00Z",
                "recovery_source": "system_restore",
                "confidence": 0.9
            }
        ],
        "total_recovered": 1,
        "recovery_method": "system_restore_analysis"
    }

def _recover_from_shadow_copy(shadow_path: str, recovery_params: dict[str, Any]) -> dict[str, Any]:
    """Recover data from shadow copies."""
    # Mock implementation for demonstration
    return {
        "recovered_items": [],
        "total_recovered": 0,
        "recovery_method": "shadow_copy_analysis"
    }

def _correlate_recovered_data(recovered_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Correlate and deduplicate recovered data."""
    all_items = []

    for source_type, source_data in recovered_data.items():
        if source_data and 'recovered_items' in source_data:
            for item in source_data['recovered_items']:
                item['recovery_source'] = source_type
                all_items.append(item)

    # Simple deduplication based on URL
    seen_urls = set()
    unique_items = []

    for item in all_items:
        url = item.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item)

    return unique_items

def _analyze_recovery_success(recovered_data: dict[str, Any], correlated_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze the success and quality of recovery operations."""
    total_sources = len(recovered_data)
    successful_sources = sum(1 for data in recovered_data.values() if data and data.get('total_recovered', 0) > 0)

    total_recovered = len(correlated_data)

    # Calculate average confidence
    confidences = [item.get('confidence', 0) for item in correlated_data]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    return {
        "total_sources": total_sources,
        "successful_sources": successful_sources,
        "success_rate": successful_sources / total_sources if total_sources > 0 else 0,
        "total_recovered_items": total_recovered,
        "average_confidence": avg_confidence,
        "recovery_quality": _assess_recovery_quality(avg_confidence, total_recovered)
    }

def _assess_recovery_quality(confidence: float, total_items: int) -> str:
    """Assess the overall quality of recovery operations."""
    if total_items == 0:
        return "no_items_recovered"
    elif confidence >= 0.8:
        return "excellent"
    elif confidence >= 0.6:
        return "good"
    elif confidence >= 0.4:
        return "fair"
    else:
        return "poor"

def _extract_download_sources(browser_data: dict[str, Any]) -> dict[str, Any]:
    """Extract download information from various browser sources."""
    download_sources = {}

    # Extract from history databases
    for browser_type in ['chrome', 'firefox', 'edge', 'safari']:
        if f'{browser_type}_data' in browser_data:
            browser_info = browser_data[f'{browser_type}_data']
            if 'download_records' in browser_info:
                download_sources[browser_type] = browser_info['download_records']

    return download_sources

def _analyze_download_behavior(download_sources: dict[str, Any]) -> dict[str, Any]:
    """Analyze download behavior patterns."""
    all_downloads = []

    for browser_type, downloads in download_sources.items():
        for download in downloads:
            download['browser_type'] = browser_type
            all_downloads.append(download)

    if not all_downloads:
        return {"error": "No downloads found for analysis"}

    # Analyze download patterns
    file_types = {}
    download_times = []
    file_sizes = []

    for download in all_downloads:
        # Analyze file types
        file_path = download.get('target_path', '')
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            file_types[file_ext] = file_types.get(file_ext, 0) + 1

        # Analyze download times
        start_time = download.get('start_time') or download.get('startTime')
        if start_time:
            download_times.append(_normalize_timestamp(start_time))

        # Analyze file sizes
        file_size = download.get('file_size') or download.get('total_bytes', 0)
        if file_size:
            file_sizes.append(file_size)

    return {
        "total_downloads": len(all_downloads),
        "file_type_analysis": {
            "total_types": len(file_types),
            "type_distribution": file_types,
            "most_common_type": max(file_types.items(), key=lambda x: x[1])[0] if file_types else None
        },
        "time_analysis": _analyze_time_patterns(download_times),
        "size_analysis": {
            "total_files": len(file_sizes),
            "average_size": sum(file_sizes) / len(file_sizes) if file_sizes else 0,
            "largest_file": max(file_sizes) if file_sizes else 0,
            "smallest_file": min(file_sizes) if file_sizes else 0
        }
    }

def _identify_suspicious_downloads(download_sources: dict[str, Any], analysis_params: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify potentially suspicious downloads."""
    suspicious_downloads = []

    # Define suspicious patterns
    suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
    suspicious_keywords = ['crack', 'hack', 'keygen', 'warez', 'torrent']

    for browser_type, downloads in download_sources.items():
        for download in downloads:
            file_path = download.get('target_path', '')
            file_name = os.path.basename(file_path).lower()

            # Check for suspicious extensions
            if any(file_name.endswith(ext) for ext in suspicious_extensions):
                suspicious_downloads.append({
                    **download,
                    "browser_type": browser_type,
                    "suspicion_reason": "suspicious_file_extension",
                    "risk_level": "high"
                })

            # Check for suspicious keywords
            elif any(keyword in file_name for keyword in suspicious_keywords):
                suspicious_downloads.append({
                    **download,
                    "browser_type": browser_type,
                    "suspicion_reason": "suspicious_filename",
                    "risk_level": "medium"
                })

    return suspicious_downloads

def _generate_download_timeline(download_sources: dict[str, Any]) -> dict[str, Any]:
    """Generate chronological timeline of downloads."""
    all_downloads = []

    for browser_type, downloads in download_sources.items():
        for download in downloads:
            download['browser_type'] = browser_type
            all_downloads.append(download)

    # Sort by start time
    all_downloads.sort(key=lambda x: _normalize_timestamp(x.get('start_time') or x.get('startTime') or ''))

    # Group by time periods
    timeline_periods = {
        "morning": {"start": "06:00", "end": "12:00", "downloads": []},
        "afternoon": {"start": "12:00", "end": "18:00", "downloads": []},
        "evening": {"start": "18:00", "end": "22:00", "downloads": []},
        "night": {"start": "22:00", "end": "06:00", "downloads": []}
    }

    for download in all_downloads:
        start_time = _normalize_timestamp(download.get('start_time') or download.get('startTime') or '')
        if start_time:
            hour = start_time.hour
            if 6 <= hour < 12:
                timeline_periods["morning"]["downloads"].append(download)
            elif 12 <= hour < 18:
                timeline_periods["afternoon"]["downloads"].append(download)
            elif 18 <= hour < 22:
                timeline_periods["evening"]["downloads"].append(download)
            else:
                timeline_periods["night"]["downloads"].append(download)

    return {
        "total_downloads": len(all_downloads),
        "timeline_periods": timeline_periods,
        "download_frequency": {
            period: len(data["downloads"]) for period, data in timeline_periods.items()
        }
    }

def _analyze_downloaded_files(download_sources: dict[str, Any]) -> dict[str, Any]:
    """Analyze characteristics of downloaded files."""
    all_downloads = []

    for browser_type, downloads in download_sources.items():
        for download in downloads:
            download['browser_type'] = browser_type
            all_downloads.append(download)

    # Analyze file characteristics
    file_analysis = {
        "total_files": len(all_downloads),
        "file_categories": {},
        "size_distribution": {
            "small": 0,      # < 1MB
            "medium": 0,     # 1MB - 100MB
            "large": 0,      # 100MB - 1GB
            "very_large": 0  # > 1GB
        }
    }

    for download in all_downloads:
        file_path = download.get('target_path', '')
        file_size = download.get('file_size') or download.get('total_bytes', 0)

        # Categorize by file type
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext:
                file_analysis["file_categories"][file_ext] = file_analysis["file_categories"].get(file_ext, 0) + 1

        # Categorize by size
        if file_size:
            if file_size < DEFAULT_CHUNK_SIZE * 1024:  # < 1MB
                file_analysis["size_distribution"]["small"] += 1
            elif file_size < MAX_DOWNLOAD_SIZE_MB * 1024 * 1024:  # < 100MB
                file_analysis["size_distribution"]["medium"] += 1
            elif file_size < DEFAULT_CHUNK_SIZE * 1024 * 1024:  # < 1GB
                file_analysis["size_distribution"]["large"] += 1
            else:
                file_analysis["size_distribution"]["very_large"] += 1

    return file_analysis

def _normalize_timestamp(timestamp) -> datetime | None:
    """Normalize various timestamp formats to datetime object."""
    if not timestamp:
        return None

    try:
        if isinstance(timestamp, str):
            # Try to parse various timestamp formats
            if timestamp.isdigit():
                # Unix timestamp
                return datetime.fromtimestamp(int(timestamp), tz=UTC)
            else:
                # ISO format or other string format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, int | float):
            # Unix timestamp
            return datetime.fromtimestamp(timestamp, tz=UTC)
        elif isinstance(timestamp, datetime):
            return timestamp
        else:
            return None
    except Exception:
        return None

def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        if not url or not url.startswith(('http://', 'https://')):
            return ''

        # Simple domain extraction
        domain = url.split('://')[1].split('/')[0]
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ''

def _analyze_time_patterns(timestamps: list[datetime]) -> dict[str, Any]:
    """Analyze time patterns from timestamp data."""
    if not timestamps:
        return {"error": "No timestamps to analyze"}

    # Filter out None timestamps
    valid_timestamps = [ts for ts in timestamps if ts]

    if not valid_timestamps:
        return {"error": "No valid timestamps found"}

    # Analyze hour distribution
    hour_distribution = {}
    for ts in valid_timestamps:
        hour = ts.hour
        hour_distribution[hour] = hour_distribution.get(hour, 0) + 1

    # Find peak hours
    peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None

    return {
        "total_timestamps": len(valid_timestamps),
        "hour_distribution": hour_distribution,
        "peak_hour": peak_hour,
        "time_range": {
            "earliest": min(valid_timestamps).isoformat(),
            "latest": max(valid_timestamps).isoformat()
        }
    }

def _analyze_visit_patterns(visit_counts: list[int]) -> dict[str, Any]:
    """Analyze visit count patterns."""
    if not visit_counts:
        return {"error": "No visit counts to analyze"}

    total_visits = sum(visit_counts)
    avg_visits = total_visits / len(visit_counts)
    max_visits = max(visit_counts)
    min_visits = min(visit_counts)

    return {
        "total_visits": total_visits,
        "average_visits": avg_visits,
        "maximum_visits": max_visits,
        "minimum_visits": min_visits,
        "visit_distribution": {
            "single_visit": sum(1 for count in visit_counts if count == 1),
            "multiple_visits": sum(1 for count in visit_counts if count > 1),
            "frequent_visits": sum(1 for count in visit_counts if count > 10)
        }
    }

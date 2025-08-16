import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

class TimelineCorrelationError(Exception):
    """Custom exception for timeline correlation errors."""
    pass

class SourceMergeError(TimelineCorrelationError):
    """Exception raised when merging multiple sources fails."""
    pass

class AnomalyDetectionError(TimelineCorrelationError):
    """Exception raised when anomaly detection fails."""
    pass

class SummaryGenerationError(TimelineCorrelationError):
    """Exception raised when summary generation fails."""
    pass

def merge_multiple_sources(timeline_sources: list[dict[str, Any]], merge_params: dict[str, Any]) -> dict[str, Any]:
    """
    Merge multiple timeline sources into a unified timeline.
    Args:
        timeline_sources: List of timeline data from different sources
        merge_params: Parameters for merging operations
    Returns:
        Dictionary containing merged timeline data
    Raises:
        SourceMergeError: If source merging fails
    """
    try:
        logger.info(f"Starting timeline merge for {len(timeline_sources)} sources")

        # Validate and normalize sources
        normalized_sources = _normalize_timeline_sources(timeline_sources)

        # Merge events from all sources
        merged_events = _merge_timeline_events(normalized_sources)

        # Sort events chronologically
        sorted_events = _sort_events_chronologically(merged_events)

        # Remove duplicates
        deduplicated_events = _remove_duplicate_events(sorted_events)

        # Generate correlation matrix
        correlation_matrix = _generate_correlation_matrix(deduplicated_events)

        result = {
            "source_count": len(timeline_sources),
            "merged_events": deduplicated_events,
            "total_events": len(deduplicated_events),
            "correlation_matrix": correlation_matrix,
            "merge_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Successfully merged {len(deduplicated_events)} timeline events")
        return result

    except Exception as e:
        logger.error(f"Timeline source merging failed: {e}")
        raise SourceMergeError(f"Source merging failed: {e}") from e

def detect_temporal_anomalies(timeline_data: dict[str, Any], detection_params: dict[str, Any]) -> dict[str, Any]:
    """
    Detect temporal anomalies in timeline data.
    Args:
        timeline_data: Merged timeline data
        detection_params: Parameters for anomaly detection
    Returns:
        Dictionary containing detected anomalies
    Raises:
        AnomalyDetectionError: If anomaly detection fails
    """
    try:
        logger.info("Starting temporal anomaly detection")

        events = timeline_data.get('merged_events', [])
        if not events:
            return {"error": "No timeline events to analyze"}

        # Detect various types of anomalies
        time_gap_anomalies = _detect_time_gap_anomalies(events, detection_params)
        frequency_anomalies = _detect_frequency_anomalies(events, detection_params)
        pattern_anomalies = _detect_pattern_anomalies(events, detection_params)
        sequence_anomalies = _detect_sequence_anomalies(events, detection_params)

        # Correlate anomalies
        correlated_anomalies = _correlate_anomalies(
            time_gap_anomalies, frequency_anomalies, pattern_anomalies, sequence_anomalies
        )

        result = {
            "time_gap_anomalies": time_gap_anomalies,
            "frequency_anomalies": frequency_anomalies,
            "pattern_anomalies": pattern_anomalies,
            "sequence_anomalies": sequence_anomalies,
            "correlated_anomalies": correlated_anomalies,
            "total_anomalies": len(correlated_anomalies),
            "detection_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Temporal anomaly detection completed: {len(correlated_anomalies)} anomalies found")
        return result

    except Exception as e:
        logger.error(f"Temporal anomaly detection failed: {e}")
        raise AnomalyDetectionError(f"Anomaly detection failed: {e}") from e

def generate_activity_summary(timeline_data: dict[str, Any], summary_params: dict[str, Any]) -> dict[str, Any]:
    """
    Generate comprehensive activity summary from timeline data.
    Args:
        timeline_data: Merged timeline data
        summary_params: Parameters for summary generation
    Returns:
        Dictionary containing activity summary
    Raises:
        SummaryGenerationError: If summary generation fails
    """
    try:
        logger.info("Starting activity summary generation")

        events = timeline_data.get('merged_events', [])
        if not events:
            return {"error": "No timeline events to summarize"}

        # Generate various summary components
        time_summary = _generate_time_summary(events)
        activity_summary = _generate_activity_breakdown(events)
        source_summary = _generate_source_summary(events)
        pattern_summary = _generate_pattern_summary(events)

        # Create comprehensive summary
        comprehensive_summary = _create_comprehensive_summary(
            time_summary, activity_summary, source_summary, pattern_summary
        )

        result = {
            "time_summary": time_summary,
            "activity_summary": activity_summary,
            "source_summary": source_summary,
            "pattern_summary": pattern_summary,
            "comprehensive_summary": comprehensive_summary,
            "summary_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info("Activity summary generation completed successfully")
        return result

    except Exception as e:
        logger.error(f"Activity summary generation failed: {e}")
        raise SummaryGenerationError(f"Summary generation failed: {e}") from e

def _normalize_timeline_sources(timeline_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize timeline sources to common format."""
    normalized_sources = []

    for source in timeline_sources:
        try:
            normalized_source = {
                "source_id": source.get('source_id', f"source_{len(normalized_sources)}"),
                "source_type": source.get('source_type', 'unknown'),
                "events": _normalize_events(source.get('events', [])),
                "metadata": source.get('metadata', {})
            }
            normalized_sources.append(normalized_source)
        except Exception as e:
            logger.warning(f"Failed to normalize source: {e}")
            continue

    return normalized_sources

def _normalize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize events to common format."""
    normalized_events = []

    for event in events:
        try:
            normalized_event = {
                "event_id": event.get('event_id', f"event_{len(normalized_events)}"),
                "timestamp": _normalize_timestamp(event.get('timestamp')),
                "event_type": event.get('event_type', 'unknown'),
                "description": event.get('description', ''),
                "source": event.get('source', 'unknown'),
                "confidence": event.get('confidence', 1.0),
                "metadata": event.get('metadata', {})
            }
            normalized_events.append(normalized_event)
        except Exception as e:
            logger.warning(f"Failed to normalize event: {e}")
            continue

    return normalized_events

def _merge_timeline_events(normalized_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge events from all sources."""
    all_events = []

    for source in normalized_sources:
        for event in source.get('events', []):
            event['source_id'] = source['source_id']
            event['source_type'] = source['source_type']
            all_events.append(event)

    return all_events

def _sort_events_chronologically(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort events chronologically by timestamp."""
    return sorted(events, key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=UTC)))

def _remove_duplicate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate events based on timestamp and description."""
    seen_events = set()
    unique_events = []

    for event in events:
        timestamp = event.get('timestamp')
        description = event.get('description', '')

        if timestamp:
            event_key = (timestamp.isoformat(), description)
            if event_key not in seen_events:
                seen_events.add(event_key)
                unique_events.append(event)

    return unique_events

def _generate_correlation_matrix(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate correlation matrix between different event sources."""
    source_correlations = {}

    for i, event1 in enumerate(events):
        source1 = event1.get('source_id', 'unknown')
        if source1 not in source_correlations:
            source_correlations[source1] = {}

        for _j, event2 in enumerate(events[i+1:], i+1):
            source2 = event2.get('source_id', 'unknown')
            if source2 not in source_correlations[source1]:
                source_correlations[source1][source2] = 0

            # Simple correlation based on temporal proximity
            time_diff = abs((event1.get('timestamp') - event2.get('timestamp')).total_seconds())
            if time_diff < 300:  # 5 minutes
                source_correlations[source1][source2] += 1

    return source_correlations

def _detect_time_gap_anomalies(events: list[dict[str, Any]], detection_params: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect anomalies based on time gaps between events."""
    anomalies = []
    max_gap_threshold = detection_params.get('max_gap_threshold', 3600)  # 1 hour

    for i in range(len(events) - 1):
        current_event = events[i]
        next_event = events[i + 1]

        current_time = current_event.get('timestamp')
        next_time = next_event.get('timestamp')

        if current_time and next_time:
            time_gap = (next_time - current_time).total_seconds()

            if time_gap > max_gap_threshold:
                anomalies.append({
                    "type": "time_gap_anomaly",
                    "gap_duration": time_gap,
                    "gap_duration_hours": time_gap / 3600,
                    "before_event": current_event.get('event_id'),
                    "after_event": next_event.get('event_id'),
                    "gap_start": current_time.isoformat(),
                    "gap_end": next_time.isoformat(),
                    "severity": "medium" if time_gap < 7200 else "high"
                })

    return anomalies

def _detect_frequency_anomalies(events: list[dict[str, Any]], detection_params: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect anomalies based on event frequency patterns."""
    anomalies = []
    high_frequency_threshold = detection_params.get('high_frequency_threshold', 10)  # events per hour
    low_frequency_threshold = detection_params.get('low_frequency_threshold', 1)    # events per hour

    # Group events by hour
    hourly_counts = {}
    for event in events:
        timestamp = event.get('timestamp')
        if timestamp:
            hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1

    # Detect frequency anomalies
    for hour, count in hourly_counts.items():
        if count > high_frequency_threshold:
            anomalies.append({
                "type": "high_frequency_anomaly",
                "hour": hour.isoformat(),
                "event_count": count,
                "threshold": high_frequency_threshold,
                "severity": "medium"
            })
        elif count < low_frequency_threshold:
            anomalies.append({
                "type": "low_frequency_anomaly",
                "hour": hour.isoformat(),
                "event_count": count,
                "threshold": low_frequency_threshold,
                "severity": "low"
            })

    return anomalies

def _detect_pattern_anomalies(events: list[dict[str, Any]], detection_params: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect anomalies based on event patterns."""
    anomalies = []

    # Detect unusual event sequences
    event_types = [event.get('event_type') for event in events]

    # Look for repeated patterns
    pattern_length = 3
    for i in range(len(event_types) - pattern_length + 1):
        pattern = event_types[i:i+pattern_length]

        # Check if this pattern appears multiple times
        pattern_count = 0
        for j in range(len(event_types) - pattern_length + 1):
            if event_types[j:j+pattern_length] == pattern:
                pattern_count += 1

        if pattern_count > 2:  # Pattern appears more than twice
            anomalies.append({
                "type": "repeated_pattern_anomaly",
                "pattern": pattern,
                "pattern_count": pattern_count,
                "first_occurrence": events[i].get('timestamp').isoformat(),
                "severity": "low"
            })

    return anomalies

def _detect_sequence_anomalies(events: list[dict[str, Any]], detection_params: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect anomalies based on event sequence violations."""
    anomalies = []

    # Define expected event sequences
    expected_sequences = [
        ["login", "file_access", "logout"],
        ["file_access", "network_activity", "file_access"],
        ["process_start", "file_access", "process_end"]
    ]

    event_types = [event.get('event_type') for event in events]

    for expected_seq in expected_sequences:
        for i in range(len(event_types) - len(expected_seq) + 1):
            current_seq = event_types[i:i+len(expected_seq)]

            if current_seq == expected_seq:
                # Check if sequence timing is reasonable
                start_time = events[i].get('timestamp')
                end_time = events[i + len(expected_seq) - 1].get('timestamp')

                if start_time and end_time:
                    sequence_duration = (end_time - start_time).total_seconds()

                    # Define reasonable duration thresholds
                    if sequence_duration > 3600:  # More than 1 hour
                        anomalies.append({
                            "type": "sequence_timing_anomaly",
                            "expected_sequence": expected_seq,
                            "actual_duration": sequence_duration,
                            "start_time": start_time.isoformat(),
                            "end_time": end_time.isoformat(),
                            "severity": "medium"
                        })

    return anomalies

def _correlate_anomalies(time_gap_anomalies: list[dict[str, Any]],
                         frequency_anomalies: list[dict[str, Any]],
                         pattern_anomalies: list[dict[str, Any]],
                         sequence_anomalies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Correlate different types of anomalies."""
    correlated_anomalies = []

    # Combine all anomalies
    all_anomalies = (time_gap_anomalies + frequency_anomalies +
                     pattern_anomalies + sequence_anomalies)

    # Group anomalies by time proximity
    time_groups = {}
    for anomaly in all_anomalies:
        # Extract time from anomaly
        anomaly_time = None
        if 'gap_start' in anomaly:
            anomaly_time = datetime.fromisoformat(anomaly['gap_start'])
        elif 'hour' in anomaly:
            anomaly_time = datetime.fromisoformat(anomaly['hour'])
        elif 'first_occurrence' in anomaly:
            anomaly_time = datetime.fromisoformat(anomaly['first_occurrence'])
        elif 'start_time' in anomaly:
            anomaly_time = datetime.fromisoformat(anomaly['start_time'])

        if anomaly_time:
            # Group by hour
            hour_key = anomaly_time.replace(minute=0, second=0, microsecond=0)
            if hour_key not in time_groups:
                time_groups[hour_key] = []
            time_groups[hour_key].append(anomaly)

    # Create correlated anomalies
    for hour, anomalies in time_groups.items():
        if len(anomalies) > 1:
            # Multiple anomalies in the same time period
            correlated_anomalies.append({
                "type": "correlated_anomalies",
                "time_period": hour.isoformat(),
                "anomaly_count": len(anomalies),
                "anomaly_types": list(set(an.get('type') for an in anomalies)),
                "severity": "high" if any(an.get('severity') == 'high' for an in anomalies) else "medium",
                "anomalies": anomalies
            })
        else:
            # Single anomaly
            correlated_anomalies.extend(anomalies)

    return correlated_anomalies

def _generate_time_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate time-based summary of events."""
    if not events:
        return {"error": "No events to summarize"}

    timestamps = [event.get('timestamp') for event in events if event.get('timestamp')]

    if not timestamps:
        return {"error": "No valid timestamps found"}

    earliest = min(timestamps)
    latest = max(timestamps)
    total_duration = (latest - earliest).total_seconds()

    # Group by time periods
    hourly_distribution = {}
    daily_distribution = {}

    for timestamp in timestamps:
        hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
        day_key = timestamp.date()

        hourly_distribution[hour_key] = hourly_distribution.get(hour_key, 0) + 1
        daily_distribution[day_key] = daily_distribution.get(day_key, 0) + 1

    return {
        "time_range": {
            "start": earliest.isoformat(),
            "end": latest.isoformat(),
            "duration_seconds": total_duration,
            "duration_hours": total_duration / 3600,
            "duration_days": total_duration / 86400
        },
        "hourly_distribution": {
            "total_hours": len(hourly_distribution),
            "peak_hour": max(hourly_distribution.items(), key=lambda x: x[1])[0].isoformat() if hourly_distribution else None,
            "distribution": {k.isoformat(): v for k, v in hourly_distribution.items()}
        },
        "daily_distribution": {
            "total_days": len(daily_distribution),
            "peak_day": max(daily_distribution.items(), key=lambda x: x[1])[0].isoformat() if daily_distribution else None,
            "distribution": {k.isoformat(): v for k, v in daily_distribution.items()}
        }
    }

def _generate_activity_breakdown(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate breakdown of activities by type."""
    if not events:
        return {"error": "No events to analyze"}

    # Count events by type
    event_type_counts = {}
    source_counts = {}

    for event in events:
        event_type = event.get('event_type', 'unknown')
        source = event.get('source', 'unknown')

        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1

    return {
        "event_type_breakdown": {
            "total_types": len(event_type_counts),
            "type_distribution": event_type_counts,
            "most_common_type": max(event_type_counts.items(), key=lambda x: x[1])[0] if event_type_counts else None
        },
        "source_breakdown": {
            "total_sources": len(source_counts),
            "source_distribution": source_counts,
            "most_active_source": max(source_counts.items(), key=lambda x: x[1])[0] if source_counts else None
        }
    }

def _generate_source_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate summary of event sources."""
    if not events:
        return {"error": "No events to analyze"}

    source_events = {}

    for event in events:
        source = event.get('source', 'unknown')
        if source not in source_events:
            source_events[source] = []
        source_events[source].append(event)

    source_summary = {}
    for source, source_event_list in source_events.items():
        timestamps = [e.get('timestamp') for e in source_event_list if e.get('timestamp')]

        source_summary[source] = {
            "event_count": len(source_event_list),
            "event_types": list(set(e.get('event_type') for e in source_event_list)),
            "time_range": {
                "start": min(timestamps).isoformat() if timestamps else None,
                "end": max(timestamps).isoformat() if timestamps else None
            } if timestamps else None
        }

    return {
        "total_sources": len(source_summary),
        "source_details": source_summary
    }

def _generate_pattern_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate summary of event patterns."""
    if not events:
        return {"error": "No events to analyze"}

    # Analyze event sequences
    event_types = [event.get('event_type') for event in events]

    # Find common patterns
    pattern_length = 2
    patterns = {}

    for i in range(len(event_types) - pattern_length + 1):
        pattern = tuple(event_types[i:i+pattern_length])
        patterns[pattern] = patterns.get(pattern, 0) + 1

    # Find most common patterns
    common_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "pattern_analysis": {
            "total_patterns": len(patterns),
            "pattern_length": pattern_length,
            "most_common_patterns": [
                {
                    "pattern": list(pattern),
                    "frequency": count
                } for pattern, count in common_patterns
            ]
        }
    }

def _create_comprehensive_summary(time_summary: dict[str, Any],
                                activity_summary: dict[str, Any],
                                source_summary: dict[str, Any],
                                pattern_summary: dict[str, Any]) -> dict[str, Any]:
    """Create comprehensive summary from all components."""
    return {
        "overview": {
            "total_events": activity_summary.get('event_type_breakdown', {}).get('total_types', 0),
            "time_range": time_summary.get('time_range', {}),
            "activity_types": activity_summary.get('event_type_breakdown', {}).get('total_types', 0),
            "data_sources": source_summary.get('total_sources', 0)
        },
        "key_findings": {
            "peak_activity_hour": time_summary.get('hourly_distribution', {}).get('peak_hour'),
            "most_common_activity": activity_summary.get('event_type_breakdown', {}).get('most_common_type'),
            "most_active_source": activity_summary.get('source_breakdown', {}).get('most_active_source'),
            "common_patterns": pattern_summary.get('pattern_analysis', {}).get('most_common_patterns', [])[:3]
        }
    }

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

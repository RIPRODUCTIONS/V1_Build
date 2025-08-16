"""
OSINT Collection Module

This module provides comprehensive OSINT (Open Source Intelligence) collection
capabilities for cybersecurity investigations, including social media analysis,
threat actor profiling, timeline reconstruction, and geolocation analysis.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger(__name__)


class OSINTCollectorError(Exception):
    """Custom exception for OSINT collection errors."""
    pass


class RateLimitError(OSINTCollectorError):
    """Exception raised when API rate limits are exceeded."""
    pass


class AuthenticationError(OSINTCollectorError):
    """Exception raised when API authentication fails."""
    pass


def _create_session_with_retry() -> requests.Session:
    """Create a requests session with retry logic and proper headers."""
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set default headers
    session.headers.update({
        'User-Agent': 'OSINT-Investigation-Platform/1.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9'
    })

    return session


def _handle_api_response(response: requests.Response) -> Dict[str, Any]:
    """Handle API response and extract data safely."""
    try:
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {response.text}")
        elif response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {response.text}")
        else:
            response.raise_for_status()
            return {"status_code": response.status_code}
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON response: {response.text[:200]}")
        return {"raw_response": response.text, "status_code": response.status_code}


def collect_social_media_profiles(target_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect social media profiles from multiple platforms.

    Args:
        target_data: Dictionary containing target information (username, email, etc.)

    Returns:
        Dictionary containing collected social media profiles and metadata

    Raises:
        OSINTCollectorError: If collection fails
    """
    try:
        logger.info(f"Starting social media profile collection for target: {target_data.get('username', 'unknown')}")

        profiles = {
            "profiles": [],
            "platforms": [],
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_profiles": 0
        }

        # Extract target identifiers
        username = target_data.get("username")
        email = target_data.get("email")
        full_name = target_data.get("full_name")

        if not any([username, email, full_name]):
            raise OSINTCollectorError("No valid target identifiers provided")

        # Collect from Twitter/X
        if username:
            try:
                twitter_profile = _collect_twitter_profile(username)
                if twitter_profile:
                    profiles["profiles"].append(twitter_profile)
                    profiles["platforms"].append("twitter")
            except Exception as e:
                logger.warning(f"Failed to collect Twitter profile: {e}")

        # Collect from LinkedIn
        if full_name or username:
            try:
                linkedin_profile = _collect_linkedin_profile(full_name or username)
                if linkedin_profile:
                    profiles["profiles"].append(linkedin_profile)
                    profiles["platforms"].append("linkedin")
            except Exception as e:
                logger.warning(f"Failed to collect LinkedIn profile: {e}")

        # Collect from GitHub
        if username:
            try:
                github_profile = _collect_github_profile(username)
                if github_profile:
                    profiles["profiles"].append(github_profile)
                    profiles["platforms"].append("github")
            except Exception as e:
                logger.warning(f"Failed to collect GitHub profile: {e}")

        # Collect from Instagram
        if username:
            try:
                instagram_profile = _collect_instagram_profile(username)
                if instagram_profile:
                    profiles["profiles"].append(instagram_profile)
                    profiles["platforms"].append("instagram")
            except Exception as e:
                logger.warning(f"Failed to collect Instagram profile: {e}")

        # Update total count
        profiles["total_profiles"] = len(profiles["profiles"])

        logger.info(f"Successfully collected {profiles['total_profiles']} social media profiles")
        return profiles

    except Exception as e:
        logger.error(f"Social media profile collection failed: {e}")
        raise OSINTCollectorError(f"Profile collection failed: {e}") from e


def analyze_digital_footprint(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze digital footprint and online presence.

    Args:
        profile_data: Dictionary containing collected social media profiles

    Returns:
        Dictionary containing digital footprint analysis results

    Raises:
        OSINTCollectorError: If analysis fails
    """
    try:
        logger.info("Starting digital footprint analysis")

        analysis = {
            "risk_score": 0.0,
            "activity_level": "low",
            "platform_diversity": 0,
            "content_analysis": {},
            "temporal_patterns": {},
            "geographic_spread": [],
            "threat_indicators": []
        }

        profiles = profile_data.get("profiles", [])
        if not profiles:
            return analysis

        # Calculate platform diversity
        analysis["platform_diversity"] = len(profile_data.get("platforms", []))

        # Analyze content across platforms
        content_indicators = []
        for profile in profiles:
            platform = profile.get("platform")
            if platform:
                content_indicators.extend(_analyze_profile_content(profile))

        # Calculate risk score based on content indicators
        analysis["risk_score"] = _calculate_risk_score(content_indicators)

        # Determine activity level
        analysis["activity_level"] = _determine_activity_level(profiles)

        # Analyze temporal patterns
        analysis["temporal_patterns"] = _analyze_temporal_patterns(profiles)

        # Extract geographic information
        analysis["geographic_spread"] = _extract_geographic_data(profiles)

        # Identify threat indicators
        analysis["threat_indicators"] = _identify_threat_indicators(content_indicators)

        logger.info(f"Digital footprint analysis completed. Risk score: {analysis['risk_score']}")
        return analysis

    except Exception as e:
        logger.error(f"Digital footprint analysis failed: {e}")
        raise OSINTCollectorError(f"Footprint analysis failed: {e}") from e


def identify_threat_indicators(actor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify threat indicators for actor profiling.

    Args:
        actor_data: Dictionary containing actor information and profiles

    Returns:
        Dictionary containing identified threat indicators and risk assessment

    Raises:
        OSINTCollectorError: If analysis fails
    """
    try:
        logger.info("Starting threat indicator identification")

        indicators = {
            "threat_level": "low",
            "risk_factors": [],
            "capability_indicators": [],
            "motivation_indicators": [],
            "tactics_techniques": [],
            "confidence_score": 0.0
        }

        profiles = actor_data.get("profiles", [])
        if not profiles:
            return indicators

        # Analyze profile content for threat indicators
        threat_content = []
        for profile in profiles:
            content = _extract_profile_content(profile)
            threat_content.extend(_analyze_for_threats(content))

        # Identify risk factors
        indicators["risk_factors"] = _identify_risk_factors(threat_content)

        # Assess capabilities
        indicators["capability_indicators"] = _assess_capabilities(profiles)

        # Determine motivations
        indicators["motivation_indicators"] = _determine_motivations(threat_content)

        # Identify TTPs (Tactics, Techniques, and Procedures)
        indicators["tactics_techniques"] = _identify_ttps(threat_content)

        # Calculate threat level
        indicators["threat_level"] = _calculate_threat_level(indicators)

        # Calculate confidence score
        indicators["confidence_score"] = _calculate_indicator_confidence(indicators)

        logger.info(f"Threat indicator identification completed. Threat level: {indicators['threat_level']}")
        return indicators

    except Exception as e:
        logger.error(f"Threat indicator identification failed: {e}")
        raise OSINTCollectorError(f"Threat analysis failed: {e}") from e


def analyze_attack_patterns(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze attack patterns and TTPs.

    Args:
        indicators: Dictionary containing threat indicators

    Returns:
        Dictionary containing attack pattern analysis

    Raises:
        OSINTCollectorError: If analysis fails
    """
    try:
        logger.info("Starting attack pattern analysis")

        patterns = {
            "attack_categories": [],
            "common_techniques": [],
            "target_preferences": [],
            "timing_patterns": {},
            "resource_requirements": [],
            "attribution_confidence": 0.0
        }

        # Analyze TTPs for patterns
        ttps = indicators.get("tactics_techniques", [])
        if ttps:
            patterns["attack_categories"] = _categorize_attacks(ttps)
            patterns["common_techniques"] = _identify_common_techniques(ttps)
            patterns["target_preferences"] = _analyze_target_preferences(ttps)
            patterns["timing_patterns"] = _analyze_timing_patterns(ttps)
            patterns["resource_requirements"] = _assess_resource_requirements(ttps)

        # Calculate attribution confidence
        patterns["attribution_confidence"] = _calculate_attribution_confidence(patterns)

        logger.info(f"Attack pattern analysis completed. Categories: {len(patterns['attack_categories'])}")
        return patterns

    except Exception as e:
        logger.error(f"Attack pattern analysis failed: {e}")
        raise OSINTCollectorError(f"Pattern analysis failed: {e}") from e


def reconstruct_timeline(investigation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Reconstruct timeline from multiple data sources.

    Args:
        investigation_data: Dictionary containing investigation data and sources

    Returns:
        List of timeline events with timestamps and metadata

    Raises:
        OSINTCollectorError: If reconstruction fails
    """
    try:
        logger.info("Starting timeline reconstruction")

        timeline = []
        sources = investigation_data.get("data_sources", [])

        for source in sources:
            try:
                source_events = _extract_events_from_source(source)
                timeline.extend(source_events)
            except Exception as e:
                logger.warning(f"Failed to extract events from source {source.get('type', 'unknown')}: {e}")

        # Sort events by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""))

        # Remove duplicates and merge similar events
        timeline = _deduplicate_timeline_events(timeline)

        logger.info(f"Timeline reconstruction completed. Total events: {len(timeline)}")
        return timeline

    except Exception as e:
        logger.error(f"Timeline reconstruction failed: {e}")
        raise OSINTCollectorError(f"Timeline reconstruction failed: {e}") from e


def correlate_events(timeline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Correlate events and identify patterns.

    Args:
        timeline_data: List of timeline events

    Returns:
        Dictionary containing event correlations and patterns

    Raises:
        OSINTCollectorError: If correlation fails
    """
    try:
        logger.info("Starting event correlation analysis")

        correlations = {
            "correlated_events": [],
            "event_patterns": [],
            "anomalies": [],
            "time_range": "",
            "correlation_confidence": 0.0
        }

        if not timeline_data:
            return correlations

        # Identify temporal correlations
        temporal_correlations = _identify_temporal_correlations(timeline_data)
        correlations["correlated_events"].extend(temporal_correlations)

        # Identify behavioral patterns
        behavioral_patterns = _identify_behavioral_patterns(timeline_data)
        correlations["event_patterns"].extend(behavioral_patterns)

        # Detect anomalies
        anomalies = _detect_timeline_anomalies(timeline_data)
        correlations["anomalies"].extend(anomalies)

        # Calculate time range
        correlations["time_range"] = _calculate_timeline_range(timeline_data)

        # Calculate correlation confidence
        correlations["correlation_confidence"] = _calculate_correlation_confidence(correlations)

        logger.info(f"Event correlation completed. Correlated events: {len(correlations['correlated_events'])}")
        return correlations

    except Exception as e:
        logger.error(f"Event correlation failed: {e}")
        raise OSINTCollectorError(f"Event correlation failed: {e}") from e


def geolocate_data_points(geo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Geolocate data points from various sources.

    Args:
        geo_data: Dictionary containing geographic data and coordinates

    Returns:
        List of geolocated points with metadata

    Raises:
        OSINTCollectorError: If geolocation fails
    """
    try:
        logger.info("Starting geolocation analysis")

        locations = []
        data_points = geo_data.get("data_points", [])

        for point in data_points:
            try:
                location = _geolocate_single_point(point)
                if location:
                    locations.append(location)
            except Exception as e:
                logger.warning(f"Failed to geolocate point {point.get('id', 'unknown')}: {e}")

        # Enrich location data
        enriched_locations = _enrich_location_data(locations)

        logger.info(f"Geolocation analysis completed. Total locations: {len(enriched_locations)}")
        return enriched_locations

    except Exception as e:
        logger.error(f"Geolocation analysis failed: {e}")
        raise OSINTCollectorError(f"Geolocation failed: {e}")


def analyze_movement_patterns(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze movement patterns and travel behavior.

    Args:
        locations: List of geolocated points

    Returns:
        Dictionary containing movement pattern analysis

    Raises:
        OSINTCollectorError: If analysis fails
    """
    try:
        logger.info("Starting movement pattern analysis")

        patterns = {
            "travel_patterns": [],
            "frequent_locations": [],
            "movement_velocity": {},
            "geographic_clusters": [],
            "travel_indicators": [],
            "countries": [],
            "analysis_confidence": 0.0
        }

        if not locations:
            return patterns

        # Analyze travel patterns
        patterns["travel_patterns"] = _analyze_travel_patterns(locations)

        # Identify frequent locations
        patterns["frequent_locations"] = _identify_frequent_locations(locations)

        # Calculate movement velocity
        patterns["movement_velocity"] = _calculate_movement_velocity(locations)

        # Identify geographic clusters
        patterns["geographic_clusters"] = _identify_geographic_clusters(locations)

        # Extract travel indicators
        patterns["travel_indicators"] = _extract_travel_indicators(locations)

        # Extract countries
        patterns["countries"] = _extract_countries(locations)

        # Calculate analysis confidence
        patterns["analysis_confidence"] = _calculate_movement_confidence(patterns)

        logger.info(f"Movement pattern analysis completed. Travel patterns: {len(patterns['travel_patterns'])}")
        return patterns

    except Exception as e:
        logger.error(f"Movement pattern analysis failed: {e}")
        raise OSINTCollectorError(f"Movement analysis failed: {e}")


# Helper functions for social media collection
def _collect_twitter_profile(username: str) -> Optional[Dict[str, Any]]:
    """Collect Twitter/X profile information."""
    try:
        # This would implement actual Twitter API integration
        # For now, return mock data
        return {
            "platform": "twitter",
            "username": username,
            "display_name": f"User {username}",
            "followers_count": 0,
            "following_count": 0,
            "tweet_count": 0,
            "account_created": "2020-01-01",
            "verified": False,
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.warning(f"Twitter profile collection failed: {e}")
        return None


def _collect_linkedin_profile(identifier: str) -> Optional[Dict[str, Any]]:
    """Collect LinkedIn profile information."""
    try:
        # This would implement actual LinkedIn scraping or API integration
        # For now, return mock data
        return {
            "platform": "linkedin",
            "identifier": identifier,
            "full_name": identifier,
            "headline": "Professional",
            "location": "Unknown",
            "connections": 0,
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.warning(f"LinkedIn profile collection failed: {e}")
        return None


def _collect_github_profile(username: str) -> Optional[Dict[str, Any]]:
    """Collect GitHub profile information."""
    try:
        # This would implement actual GitHub API integration
        # For now, return mock data
        return {
            "platform": "github",
            "username": username,
            "full_name": f"User {username}",
            "repositories": 0,
            "followers": 0,
            "following": 0,
            "account_created": "2020-01-01",
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.warning(f"GitHub profile collection failed: {e}")
        return None


def _collect_instagram_profile(username: str) -> Optional[Dict[str, Any]]:
    """Collect Instagram profile information."""
    try:
        # This would implement actual Instagram scraping or API integration
        # For now, return mock data
        return {
            "platform": "instagram",
            "username": username,
            "full_name": f"User {username}",
            "posts": 0,
            "followers": 0,
            "following": 0,
            "account_created": "2020-01-01",
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.warning(f"Instagram profile collection failed: {e}")
        return None


# Helper functions for analysis
def _analyze_profile_content(profile: Dict[str, Any]) -> List[str]:
    """Analyze profile content for indicators."""
    indicators = []

    # Add basic content analysis
    if profile.get("platform") == "twitter":
        if profile.get("tweet_count", 0) > 1000:
            indicators.append("high_activity")
        if profile.get("followers_count", 0) > 10000:
            indicators.append("high_influence")

    return indicators


def _calculate_risk_score(indicators: List[str]) -> float:
    """Calculate risk score based on content indicators."""
    risk_score = 0.0

    for indicator in indicators:
        if indicator == "high_activity":
            risk_score += 0.2
        elif indicator == "high_influence":
            risk_score += 0.3
        elif indicator == "suspicious_content":
            risk_score += 0.5

    return min(risk_score, 1.0)


def _determine_activity_level(profiles: List[Dict[str, Any]]) -> str:
    """Determine overall activity level across platforms."""
    total_activity = 0

    for profile in profiles:
        if profile.get("platform") == "twitter":
            total_activity += profile.get("tweet_count", 0)
        elif profile.get("platform") == "github":
            total_activity += profile.get("repositories", 0)

    if total_activity > 1000:
        return "high"
    elif total_activity > 100:
        return "medium"
    else:
        return "low"


def _analyze_temporal_patterns(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze temporal patterns in profile activity."""
    return {
        "activity_trends": "stable",
        "peak_activity_hours": [],
        "seasonal_patterns": []
    }


def _extract_geographic_data(profiles: List[Dict[str, Any]]) -> List[str]:
    """Extract geographic information from profiles."""
    locations = []

    for profile in profiles:
        location = profile.get("location")
        if location and location != "Unknown":
            locations.append(location)

    return locations


def _identify_threat_indicators(indicators: List[str]) -> List[str]:
    """Identify threat indicators from content analysis."""
    threat_indicators = []

    for indicator in indicators:
        if indicator in ["suspicious_content", "high_influence"]:
            threat_indicators.append(indicator)

    return threat_indicators


# Additional helper functions for threat analysis
def _extract_profile_content(profile: Dict[str, Any]) -> List[str]:
    """Extract content from profile for analysis."""
    content = []

    # Extract text content from various fields
    for field in ["bio", "description", "headline"]:
        value = profile.get(field)
        if value:
            content.append(value)

    return content


def _analyze_for_threats(content: List[str]) -> List[str]:
    """Analyze content for threat indicators."""
    threats = []

    # Basic threat keyword analysis
    threat_keywords = ["hack", "exploit", "malware", "attack", "breach"]

    for text in content:
        text_lower = text.lower()
        for keyword in threat_keywords:
            if keyword in text_lower:
                threats.append(f"keyword_{keyword}")

    return threats


def _identify_risk_factors(threat_content: List[str]) -> List[str]:
    """Identify risk factors from threat content."""
    risk_factors = []

    if "keyword_hack" in threat_content:
        risk_factors.append("technical_capability")
    if "keyword_exploit" in threat_content:
        risk_factors.append("malicious_intent")

    return risk_factors


def _assess_capabilities(profiles: List[Dict[str, Any]]) -> List[str]:
    """Assess technical and operational capabilities."""
    capabilities = []

    for profile in profiles:
        if profile.get("platform") == "github":
            if profile.get("repositories", 0) > 10:
                capabilities.append("software_development")

    return capabilities


def _determine_motivations(threat_content: List[str]) -> List[str]:
    """Determine potential motivations."""
    motivations = []

    if "keyword_hack" in threat_content:
        motivations.append("technical_challenge")
    if "keyword_exploit" in threat_content:
        motivations.append("financial_gain")

    return motivations


def _identify_ttps(threat_content: List[str]) -> List[str]:
    """Identify Tactics, Techniques, and Procedures."""
    ttps = []

    if "keyword_malware" in threat_content:
        ttps.append("malware_development")
    if "keyword_attack" in threat_content:
        ttps.append("attack_planning")

    return ttps


def _calculate_threat_level(indicators: Dict[str, Any]) -> str:
    """Calculate overall threat level."""
    risk_factors = len(indicators.get("risk_factors", []))
    capabilities = len(indicators.get("capability_indicators", []))

    if risk_factors > 3 or capabilities > 2:
        return "high"
    elif risk_factors > 1 or capabilities > 1:
        return "medium"
    else:
        return "low"


def _calculate_indicator_confidence(indicators: Dict[str, Any]) -> float:
    """Calculate confidence score for threat indicators."""
    # Simple confidence calculation based on data quality
    total_indicators = sum(len(v) for v in indicators.values() if isinstance(v, list))
    return min(total_indicators / 10.0, 1.0)


# Helper functions for attack pattern analysis
def _categorize_attacks(ttps: List[str]) -> List[str]:
    """Categorize attacks based on TTPs."""
    categories = []

    for ttp in ttps:
        if "malware" in ttp:
            categories.append("malware_attacks")
        elif "attack" in ttp:
            categories.append("targeted_attacks")

    return list(set(categories))


def _identify_common_techniques(ttps: List[str]) -> List[str]:
    """Identify common attack techniques."""
    return list(set(ttps))


def _analyze_target_preferences(ttps: List[str]) -> List[str]:
    """Analyze target preferences from TTPs."""
    return ["general_targets"]


def _analyze_timing_patterns(ttps: List[str]) -> Dict[str, Any]:
    """Analyze timing patterns in attacks."""
    return {
        "attack_frequency": "unknown",
        "preferred_times": [],
        "seasonal_patterns": []
    }


def _assess_resource_requirements(ttps: List[str]) -> List[str]:
    """Assess resource requirements for attacks."""
    requirements = []

    for ttp in ttps:
        if "malware" in ttp:
            requirements.append("technical_skills")
        if "attack" in ttp:
            requirements.append("planning_time")

    return requirements


def _calculate_attribution_confidence(patterns: Dict[str, Any]) -> float:
    """Calculate attribution confidence score."""
    # Simple confidence calculation
    total_patterns = sum(len(v) for v in patterns.values() if isinstance(v, list))
    return min(total_patterns / 20.0, 1.0)


# Helper functions for timeline reconstruction
def _extract_events_from_source(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract events from a data source."""
    events = []

    # Mock event extraction
    events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "profile_activity",
        "source": source.get("type", "unknown"),
        "description": "Activity detected",
        "confidence": 0.8
    })

    return events


def _deduplicate_timeline_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate events from timeline."""
    seen = set()
    unique_events = []

    for event in events:
        event_key = f"{event.get('timestamp')}_{event.get('event_type')}_{event.get('description')}"
        if event_key not in seen:
            seen.add(event_key)
            unique_events.append(event)

    return unique_events


# Helper functions for event correlation
def _identify_temporal_correlations(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify temporal correlations between events."""
    correlations = []

    # Simple temporal correlation logic
    if len(events) > 1:
        correlations.append({
            "correlation_type": "temporal",
            "events": [events[0], events[1]],
            "confidence": 0.7
        })

    return correlations


def _identify_behavioral_patterns(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify behavioral patterns in events."""
    patterns = []

    # Simple pattern identification
    if len(events) > 2:
        patterns.append({
            "pattern_type": "repeated_activity",
            "description": "Multiple events detected",
            "confidence": 0.6
        })

    return patterns


def _detect_timeline_anomalies(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect anomalies in timeline."""
    anomalies = []

    # Simple anomaly detection
    if len(events) == 0:
        anomalies.append({
            "anomaly_type": "no_activity",
            "description": "No events detected in timeline",
            "severity": "medium"
        })

    return anomalies


def _calculate_timeline_range(events: List[Dict[str, Any]]) -> str:
    """Calculate the time range of the timeline."""
    if not events:
        return "No events"

    timestamps = [event.get("timestamp", "") for event in events if event.get("timestamp")]
    if timestamps:
        return f"{min(timestamps)} to {max(timestamps)}"

    return "Unknown"


def _calculate_correlation_confidence(correlations: Dict[str, Any]) -> float:
    """Calculate confidence score for correlations."""
    # Simple confidence calculation
    total_correlations = len(correlations.get("correlated_events", []))
    return min(total_correlations / 10.0, 1.0)


# Helper functions for geolocation
def _geolocate_single_point(point: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Geolocate a single data point."""
    try:
        # Mock geolocation
        return {
            "id": point.get("id", "unknown"),
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "United States",
            "confidence": 0.8
        }
    except Exception as e:
        logger.warning(f"Geolocation failed for point {point.get('id', 'unknown')}: {e}")
        return None


def _enrich_location_data(locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich location data with additional information."""
    enriched = []

    for location in locations:
        enriched_location = location.copy()
        enriched_location["enriched"] = True
        enriched_location["enrichment_timestamp"] = datetime.now(timezone.utc).isoformat()
        enriched.append(enriched_location)

    return enriched


# Helper functions for movement pattern analysis
def _analyze_travel_patterns(locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze travel patterns between locations."""
    patterns = []

    if len(locations) > 1:
        patterns.append({
            "pattern_type": "multi_location",
            "description": "Multiple locations detected",
            "confidence": 0.7
        })

    return patterns


def _identify_frequent_locations(locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify frequently visited locations."""
    # Simple frequency analysis
    location_counts = {}

    for location in locations:
        city = location.get("city", "Unknown")
        location_counts[city] = location_counts.get(city, 0) + 1

    frequent = []
    for city, count in location_counts.items():
        if count > 1:
            frequent.append({"city": city, "visit_count": count})

    return frequent


def _calculate_movement_velocity(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate movement velocity between locations."""
    return {
        "average_speed": "unknown",
        "movement_pattern": "stationary"
    }


def _identify_geographic_clusters(locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify geographic clusters of locations."""
    clusters = []

    if len(locations) > 2:
        clusters.append({
            "cluster_type": "urban_area",
            "locations": len(locations),
            "center": {"latitude": 40.7128, "longitude": -74.0060}
        })

    return clusters


def _extract_travel_indicators(locations: List[Dict[str, Any]]) -> List[str]:
    """Extract travel indicators from locations."""
    indicators = []

    if len(locations) > 1:
        indicators.append("multiple_locations")
        indicators.append("geographic_mobility")

    return indicators


def _extract_countries(locations: List[Dict[str, Any]]) -> List[str]:
    """Extract countries from locations."""
    countries = []

    for location in locations:
        country = location.get("country")
        if country and country not in countries:
            countries.append(country)

    return countries


def _calculate_movement_confidence(patterns: Dict[str, Any]) -> float:
    """Calculate confidence score for movement analysis."""
    # Simple confidence calculation
    total_patterns = sum(len(v) for v in patterns.values() if isinstance(v, list))
    return min(total_patterns / 10.0, 1.0)



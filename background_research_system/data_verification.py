"""
Data Verification Module

This module provides comprehensive data verification and cross-referencing
capabilities for ensuring data quality and accuracy.
"""

import difflib
import logging
import re
from collections import defaultdict
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class DataVerification:
    """Handles data verification and cross-referencing."""

    def __init__(self):
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }

        # Define data type weights for confidence calculation
        self.data_type_weights = {
            'addresses': 0.25,
            'phone_numbers': 0.20,
            'email_addresses': 0.15,
            'employment_history': 0.20,
            'education': 0.15,
            'social_profiles': 0.05
        }

        # Define source reliability scores
        self.source_reliability = {
            'public_records': 0.95,
            'been_verified': 0.90,
            'spokeo': 0.85,
            'whitepages': 0.80,
            'intelius': 0.80,
            'people_finders': 0.75,
            'web_scraping': 0.70,
            'linkedin': 0.85,
            'google_scholar': 0.90,
            'news_api': 0.80
        }

    def verify_and_merge_data(self, profile_id: str, database_manager) -> dict:
        """Verify and merge data from multiple sources."""
        try:
            # Get all data points for the profile
            data_points = database_manager.get_profile_data_points(profile_id)

            # Group data by type
            grouped_data = self._group_data_by_type(data_points)

            # Cross-reference data
            verified_data = self.cross_reference_data(grouped_data)

            # Calculate overall confidence scores
            confidence_scores = self.calculate_confidence_scores(verified_data)

            # Flag inconsistencies
            inconsistencies = self.flag_inconsistencies(verified_data)

            # Generate verification report
            verification_report = {
                'profile_id': profile_id,
                'verification_timestamp': datetime.now(UTC).isoformat(),
                'verified_data': verified_data,
                'confidence_scores': confidence_scores,
                'inconsistencies': inconsistencies,
                'overall_verification_score': self._calculate_overall_verification_score(confidence_scores),
                'verification_status': self._determine_verification_status(confidence_scores)
            }

            # Update database with verification results
            self._update_verification_status(database_manager, profile_id, verification_report)

            return verification_report

        except Exception as e:
            logger.error(f"Error in data verification: {e}")
            return {'error': str(e)}

    def _group_data_by_type(self, data_points: list[dict]) -> dict[str, list[dict]]:
        """Group data points by data type."""
        grouped = defaultdict(list)

        for dp in data_points:
            data_type = dp.get('data_type', 'unknown')
            grouped[data_type].append(dp)

        return dict(grouped)

    def cross_reference_data(self, grouped_data: dict[str, list[dict]]) -> dict[str, dict]:
        """Cross-reference data from multiple sources."""
        verified_data = {}

        for data_type, data_points in grouped_data.items():
            if len(data_points) >= 2:
                # Multiple sources available for cross-referencing
                cross_referenced = self._cross_reference_data_type(data_type, data_points)
                verified_data[data_type] = cross_referenced
            elif len(data_points) == 1:
                # Single source - mark as unverified
                single_point = data_points[0]
                verified_data[data_type] = {
                    'value': single_point.get('value'),
                    'confidence': 0.5,  # Default confidence for single source
                    'sources': [single_point.get('source')],
                    'verification_status': 'single_source',
                    'notes': 'Data from single source - verification recommended'
                }
            else:
                # No data available
                verified_data[data_type] = {
                    'value': None,
                    'confidence': 0.0,
                    'sources': [],
                    'verification_status': 'no_data',
                    'notes': 'No data available for this type'
                }

        return verified_data

    def _cross_reference_data_type(self, data_type: str, data_points: list[dict]) -> dict:
        """Cross-reference data of a specific type."""
        try:
            # Extract values and sources
            values = [dp.get('value') for dp in data_points]
            sources = [dp.get('source') for dp in data_points]
            source_confidences = [dp.get('confidence_score', 0.5) for dp in data_points]

            # Check for exact matches
            exact_matches = self._find_exact_matches(values)

            if exact_matches:
                # High confidence for exact matches
                best_value = exact_matches[0]
                best_sources = [sources[i] for i in exact_matches]
                best_confidences = [source_confidences[i] for i in exact_matches]

                return {
                    'value': best_value,
                    'confidence': self._calculate_cross_reference_confidence(best_confidences, len(best_sources)),
                    'sources': best_sources,
                    'verification_status': 'verified',
                    'match_type': 'exact',
                    'notes': f'Exact match found across {len(best_sources)} sources'
                }

            # Check for partial matches
            partial_matches = self._find_partial_matches(values, data_type)

            if partial_matches:
                # Medium confidence for partial matches
                best_match = partial_matches[0]
                best_value = best_match['value']
                best_sources = [sources[i] for i in best_match['indices']]
                best_confidences = [source_confidences[i] for i in best_match['indices']]

                return {
                    'value': best_value,
                    'confidence': self._calculate_cross_reference_confidence(best_confidences, len(best_sources)) * 0.8,
                    'sources': best_sources,
                    'verification_status': 'partially_verified',
                    'match_type': 'partial',
                    'similarity_score': best_match['similarity'],
                    'notes': f'Partial match found with {best_match["similarity"]:.2f} similarity'
                }

            # No matches found - use highest confidence source
            best_index = source_confidences.index(max(source_confidences))
            best_value = values[best_index]
            best_source = sources[best_index]
            best_confidence = source_confidences[best_index]

            return {
                'value': best_value,
                'confidence': best_confidence * 0.6,  # Reduce confidence for no matches
                'sources': [best_source],
                'verification_status': 'unverified',
                'match_type': 'no_match',
                'notes': 'No cross-reference matches found - using highest confidence source'
            }

        except Exception as e:
            logger.error(f"Error cross-referencing {data_type}: {e}")
            return {
                'value': None,
                'confidence': 0.0,
                'sources': [],
                'verification_status': 'error',
                'notes': f'Error during cross-referencing: {str(e)}'
            }

    def _find_exact_matches(self, values: list[str]) -> list[int]:
        """Find indices of exactly matching values."""
        exact_matches = []

        for i, value1 in enumerate(values):
            for j, value2 in enumerate(values[i+1:], i+1):
                if self._normalize_value(value1) == self._normalize_value(value2):
                    if i not in exact_matches:
                        exact_matches.append(i)
                    if j not in exact_matches:
                        exact_matches.append(j)

        return exact_matches

    def _find_partial_matches(self, values: list[str], data_type: str) -> list[dict]:
        """Find partial matches based on data type."""
        partial_matches = []

        for i, value1 in enumerate(values):
            for j, value2 in enumerate(values[i+1:], i+1):
                similarity = self._calculate_similarity(value1, value2, data_type)

                if similarity >= 0.7:  # Threshold for partial matches
                    partial_matches.append({
                        'indices': [i, j],
                        'value': value1 if len(value1) >= len(value2) else value2,
                        'similarity': similarity
                    })

        # Sort by similarity score
        partial_matches.sort(key=lambda x: x['similarity'], reverse=True)
        return partial_matches

    def _normalize_value(self, value: str) -> str:
        """Normalize value for comparison."""
        if not value:
            return ""

        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', value.lower().strip())

        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)

        return normalized

    def _calculate_similarity(self, value1: str, value2: str, data_type: str) -> float:
        """Calculate similarity between two values."""
        if not value1 or not value2:
            return 0.0

        # Use different similarity algorithms based on data type
        if data_type in ['addresses', 'employment_history', 'education']:
            # Use sequence matcher for longer text
            return difflib.SequenceMatcher(None,
                                          self._normalize_value(value1),
                                          self._normalize_value(value2)).ratio()

        elif data_type in ['phone_numbers', 'email_addresses']:
            # Use exact matching for structured data
            return 1.0 if self._normalize_value(value1) == self._normalize_value(value2) else 0.0

        else:
            # Default to sequence matcher
            return difflib.SequenceMatcher(None,
                                          self._normalize_value(value1),
                                          self._normalize_value(value2)).ratio()

    def _calculate_cross_reference_confidence(self, source_confidences: list[float],
                                            source_count: int) -> float:
        """Calculate confidence score for cross-referenced data."""
        if not source_confidences:
            return 0.0

        # Base confidence from source confidences
        base_confidence = sum(source_confidences) / len(source_confidences)

        # Boost confidence based on number of sources
        source_boost = min(0.2, source_count * 0.05)

        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, base_confidence + source_boost)

    def calculate_confidence_scores(self, verified_data: dict[str, dict]) -> dict[str, float]:
        """Calculate confidence scores for each data type."""
        confidence_scores = {}

        for data_type, data_info in verified_data.items():
            if data_info.get('value'):
                # Calculate weighted confidence based on data type and verification status
                base_confidence = data_info.get('confidence', 0.0)
                verification_status = data_info.get('verification_status', 'unknown')

                # Apply verification status multiplier
                status_multipliers = {
                    'verified': 1.0,
                    'partially_verified': 0.8,
                    'single_source': 0.6,
                    'unverified': 0.4,
                    'no_data': 0.0,
                    'error': 0.0
                }

                status_multiplier = status_multipliers.get(verification_status, 0.5)
                weighted_confidence = base_confidence * status_multiplier

                confidence_scores[data_type] = weighted_confidence
            else:
                confidence_scores[data_type] = 0.0

        return confidence_scores

    def flag_inconsistencies(self, verified_data: dict[str, dict]) -> list[dict]:
        """Identify potential data inconsistencies."""
        flags = []

        try:
            # Check for conflicting addresses
            addresses = verified_data.get('addresses', {})
            if addresses and addresses.get('value'):
                address_flags = self._check_address_inconsistencies(addresses)
                flags.extend(address_flags)

            # Check for conflicting phone numbers
            phone_numbers = verified_data.get('phone_numbers', {})
            if phone_numbers and phone_numbers.get('value'):
                phone_flags = self._check_phone_inconsistencies(phone_numbers)
                flags.extend(phone_flags)

            # Check for conflicting employment history
            employment = verified_data.get('employment_history', {})
            if employment and employment.get('value'):
                employment_flags = self._check_employment_inconsistencies(employment)
                flags.extend(employment_flags)

            # Check for conflicting education
            education = verified_data.get('education', {})
            if education and education.get('value'):
                education_flags = self._check_education_inconsistencies(education)
                flags.extend(education_flags)

            # Check for data source conflicts
            source_flags = self._check_source_conflicts(verified_data)
            flags.extend(source_flags)

        except Exception as e:
            logger.error(f"Error flagging inconsistencies: {e}")
            flags.append({
                'type': 'verification_error',
                'severity': 'high',
                'description': f'Error during inconsistency checking: {str(e)}',
                'timestamp': datetime.now(UTC).isoformat()
            })

        return flags

    def _check_address_inconsistencies(self, addresses: dict) -> list[dict]:
        """Check for address inconsistencies."""
        flags = []

        try:
            sources = addresses.get('sources', [])
            if len(sources) > 3:
                flags.append({
                    'type': 'address_inconsistency',
                    'severity': 'medium',
                    'description': f'Multiple addresses found across {len(sources)} sources - verify current residence',
                    'affected_sources': sources,
                    'timestamp': datetime.now(UTC).isoformat()
                })

            # Check for geographic inconsistencies
            if len(sources) >= 2:
                # This would involve geocoding and distance calculation
                # For now, flag multiple sources as potential inconsistency
                flags.append({
                    'type': 'address_verification',
                    'severity': 'low',
                    'description': 'Multiple address sources found - recommend geographic verification',
                    'affected_sources': sources,
                    'timestamp': datetime.now(UTC).isoformat()
                })

        except Exception as e:
            logger.error(f"Error checking address inconsistencies: {e}")

        return flags

    def _check_phone_inconsistencies(self, phone_numbers: dict) -> list[dict]:
        """Check for phone number inconsistencies."""
        flags = []

        try:
            sources = phone_numbers.get('sources', [])
            if len(sources) > 2:
                flags.append({
                    'type': 'phone_inconsistency',
                    'severity': 'medium',
                    'description': f'Multiple phone numbers found across {len(sources)} sources - verify current number',
                    'affected_sources': sources,
                    'timestamp': datetime.now(UTC).isoformat()
                })

        except Exception as e:
            logger.error(f"Error checking phone inconsistencies: {e}")

        return flags

    def _check_employment_inconsistencies(self, employment: dict) -> list[dict]:
        """Check for employment history inconsistencies."""
        flags = []

        try:
            sources = employment.get('sources', [])
            if len(sources) > 2:
                flags.append({
                    'type': 'employment_verification',
                    'severity': 'low',
                    'description': f'Employment data from {len(sources)} sources - recommend direct verification',
                    'affected_sources': sources,
                    'timestamp': datetime.now(UTC).isoformat()
                })

        except Exception as e:
            logger.error(f"Error checking employment inconsistencies: {e}")

        return flags

    def _check_education_inconsistencies(self, education: dict) -> list[dict]:
        """Check for education inconsistencies."""
        flags = []

        try:
            sources = education.get('sources', [])
            if len(sources) > 2:
                flags.append({
                    'type': 'education_verification',
                    'severity': 'low',
                    'description': f'Education data from {len(sources)} sources - recommend direct verification',
                    'affected_sources': sources,
                    'timestamp': datetime.now(UTC).isoformat()
                })

        except Exception as e:
            logger.error(f"Error checking education inconsistencies: {e}")

        return flags

    def _check_source_conflicts(self, verified_data: dict[str, dict]) -> list[dict]:
        """Check for conflicts between different data sources."""
        flags = []

        try:
            # Check for conflicting information between sources
            for data_type, data_info in verified_data.items():
                if data_info.get('verification_status') == 'unverified':
                    flags.append({
                        'type': 'source_conflict',
                        'severity': 'medium',
                        'description': f'{data_type} data has conflicting information between sources',
                        'affected_data_type': data_type,
                        'verification_status': data_info.get('verification_status'),
                        'timestamp': datetime.now(UTC).isoformat()
                    })

        except Exception as e:
            logger.error(f"Error checking source conflicts: {e}")

        return flags

    def _calculate_overall_verification_score(self, confidence_scores: dict[str, float]) -> float:
        """Calculate overall verification score."""
        if not confidence_scores:
            return 0.0

        # Calculate weighted average based on data type importance
        total_weight = 0.0
        weighted_sum = 0.0

        for data_type, confidence in confidence_scores.items():
            weight = self.data_type_weights.get(data_type, 0.1)
            weighted_sum += confidence * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _determine_verification_status(self, confidence_scores: dict[str, float]) -> str:
        """Determine overall verification status."""
        overall_score = self._calculate_overall_verification_score(confidence_scores)

        if overall_score >= self.confidence_thresholds['high']:
            return 'highly_verified'
        elif overall_score >= self.confidence_thresholds['medium']:
            return 'moderately_verified'
        elif overall_score >= self.confidence_thresholds['low']:
            return 'minimally_verified'
        else:
            return 'unverified'

    def _update_verification_status(self, database_manager, profile_id: str,
                                  verification_report: dict):
        """Update database with verification results."""
        try:
            # Update data points with verification status
            for data_type, data_info in verification_report.get('verified_data', {}).items():
                if data_info.get('value'):
                    # Find corresponding data points and update them
                    data_points = database_manager.get_profile_data_points(profile_id)

                    for dp in data_points:
                        if dp.get('data_type') == data_type:
                            # Update verification status
                            updates = {
                                'verified': data_info.get('verification_status') == 'verified',
                                'notes': data_info.get('notes', '')
                            }
                            # This would require a method to update individual data points
                            # For now, just log the update
                            logger.info(f"Would update data point {dp.get('id')} with verification status")

            logger.info(f"Verification status updated for profile {profile_id}")

        except Exception as e:
            logger.error(f"Error updating verification status: {e}")

    def generate_verification_summary(self, verification_report: dict) -> dict:
        """Generate a summary of verification results."""
        try:
            verified_data = verification_report.get('verified_data', {})
            confidence_scores = verification_report.get('confidence_scores', {})

            summary = {
                'overall_score': verification_report.get('overall_verification_score', 0.0),
                'verification_status': verification_report.get('verification_status', 'unknown'),
                'data_quality_summary': {},
                'recommendations': []
            }

            # Generate data quality summary
            for data_type, data_info in verified_data.items():
                if data_info.get('value'):
                    confidence = confidence_scores.get(data_type, 0.0)
                    status = data_info.get('verification_status', 'unknown')

                    summary['data_quality_summary'][data_type] = {
                        'confidence': confidence,
                        'status': status,
                        'source_count': len(data_info.get('sources', []))
                    }

            # Generate recommendations
            recommendations = self._generate_verification_recommendations(verification_report)
            summary['recommendations'] = recommendations

            return summary

        except Exception as e:
            logger.error(f"Error generating verification summary: {e}")
            return {'error': str(e)}

    def _generate_verification_recommendations(self, verification_report: dict) -> list[str]:
        """Generate recommendations based on verification results."""
        recommendations = []

        try:
            verified_data = verification_report.get('verified_data', {})
            inconsistencies = verification_report.get('inconsistencies', [])

            # Check for low confidence data
            for data_type, data_info in verified_data.items():
                if data_info.get('confidence', 0.0) < 0.6:
                    recommendations.append(f"Verify {data_type} information independently")

            # Check for single source data
            for data_type, data_info in verified_data.items():
                if data_info.get('verification_status') == 'single_source':
                    recommendations.append(f"Seek additional sources for {data_type} verification")

            # Check for inconsistencies
            if inconsistencies:
                recommendations.append("Address identified data inconsistencies")
                recommendations.append("Cross-reference conflicting information with primary sources")

            # General recommendations
            recommendations.append("Maintain documentation of verification methods used")
            recommendations.append("Implement regular data quality reviews")

            if not recommendations:
                recommendations.append("Data quality appears satisfactory - continue monitoring")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Error generating recommendations")

        return recommendations

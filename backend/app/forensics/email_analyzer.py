import logging
import os
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json
import re
import email
import base64
import quopri
from email import policy
from email.parser import BytesParser

logger = logging.getLogger(__name__)

class EmailAnalysisError(Exception):
    """Custom exception for email analysis errors."""
    pass

class DatabaseParsingError(EmailAnalysisError):
    """Exception raised when email database parsing fails."""
    pass

class AttachmentExtractionError(EmailAnalysisError):
    """Exception raised when attachment extraction fails."""
    pass

class CommunicationAnalysisError(EmailAnalysisError):
    """Exception raised when communication pattern analysis fails."""
    pass

def parse_email_databases(email_data: Dict[str, Any], email_client: str) -> Dict[str, Any]:
    """
    Parse email databases from various email clients.
    Args:
        email_data: Dictionary containing email data paths and parameters
        email_client: Type of email client (outlook, thunderbird, apple_mail, etc.)
    Returns:
        Dictionary containing parsed email data and metadata
    Raises:
        DatabaseParsingError: If email database parsing fails
    """
    try:
        logger.info(f"Starting email database parsing for {email_client}")

        if email_client.lower() == "outlook":
            parsed_data = _parse_outlook_database(email_data)
        elif email_client.lower() == "thunderbird":
            parsed_data = _parse_thunderbird_database(email_data)
        elif email_client.lower() == "apple_mail":
            parsed_data = _parse_apple_mail_database(email_data)
        elif email_client.lower() == "gmail":
            parsed_data = _parse_gmail_database(email_data)
        else:
            raise DatabaseParsingError(f"Unsupported email client: {email_client}")

        # Process and normalize email data
        processed_emails = _process_email_data(parsed_data, email_client)
        email_statistics = _generate_email_statistics(processed_emails)

        result = {
            "email_client": email_client,
            "raw_data": parsed_data,
            "processed_emails": processed_emails,
            "email_statistics": email_statistics,
            "parsing_timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Successfully parsed email database for {email_client}")
        return result

    except Exception as e:
        logger.error(f"Email database parsing failed: {e}")
        raise DatabaseParsingError(f"Database parsing failed: {e}")

def extract_attachments(email_data: Dict[str, Any], extraction_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract attachments from email data.
    Args:
        email_data: Parsed email data
        extraction_params: Parameters for attachment extraction
    Returns:
        Dictionary containing extracted attachment information
    Raises:
        AttachmentExtractionError: If attachment extraction fails
    """
    try:
        logger.info("Starting email attachment extraction")

        # Extract attachments from processed emails
        all_attachments = []
        for email_item in email_data.get('processed_emails', []):
            if 'attachments' in email_item:
                for attachment in email_item['attachments']:
                    attachment['source_email'] = email_item.get('message_id', 'unknown')
                    attachment['sender'] = email_item.get('from', 'unknown')
                    attachment['recipient'] = email_item.get('to', 'unknown')
                    attachment['subject'] = email_item.get('subject', 'unknown')
                    all_attachments.append(attachment)

        # Analyze attachment characteristics
        attachment_analysis = _analyze_attachment_characteristics(all_attachments)

        # Extract suspicious attachments
        suspicious_attachments = _identify_suspicious_attachments(all_attachments, extraction_params)

        # Generate attachment timeline
        attachment_timeline = _generate_attachment_timeline(all_attachments)

        result = {
            "total_attachments": len(all_attachments),
            "all_attachments": all_attachments,
            "attachment_analysis": attachment_analysis,
            "suspicious_attachments": suspicious_attachments,
            "attachment_timeline": attachment_timeline,
            "extraction_timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Successfully extracted {len(all_attachments)} attachments")
        return result

    except Exception as e:
        logger.error(f"Attachment extraction failed: {e}")
        raise AttachmentExtractionError(f"Attachment extraction failed: {e}")

def analyze_communication_patterns(email_data: Dict[str, Any], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze communication patterns from email data.
    Args:
        email_data: Parsed email data
        analysis_params: Parameters for communication analysis
    Returns:
        Dictionary containing communication pattern analysis results
    Raises:
        CommunicationAnalysisError: If communication analysis fails
    """
    try:
        logger.info("Starting email communication pattern analysis")

        processed_emails = email_data.get('processed_emails', [])
        if not processed_emails:
            return {"error": "No email data available for analysis"}

        # Analyze sender patterns
        sender_analysis = _analyze_sender_patterns(processed_emails)

        # Analyze recipient patterns
        recipient_analysis = _analyze_recipient_patterns(processed_emails)

        # Analyze temporal patterns
        temporal_analysis = _analyze_temporal_patterns(processed_emails)

        # Analyze content patterns
        content_analysis = _analyze_content_patterns(processed_emails)

        # Analyze communication networks
        network_analysis = _analyze_communication_networks(processed_emails)

        # Identify anomalies
        anomalies = _identify_communication_anomalies(processed_emails, analysis_params)

        result = {
            "sender_analysis": sender_analysis,
            "recipient_analysis": recipient_analysis,
            "temporal_analysis": temporal_analysis,
            "content_analysis": content_analysis,
            "network_analysis": network_analysis,
            "anomalies": anomalies,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info("Communication pattern analysis completed successfully")
        return result

    except Exception as e:
        logger.error(f"Communication pattern analysis failed: {e}")
        raise CommunicationAnalysisError(f"Communication analysis failed: {e}")

def _parse_outlook_database(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Outlook email database."""
    try:
        pst_file = email_data.get('pst_file')
        ost_file = email_data.get('ost_file')

        if not pst_file and not ost_file:
            return {"error": "No Outlook data file found"}

        # Mock implementation for demonstration
        # In a real implementation, you would use libraries like libpst or pypff
        emails = [
            {
                "message_id": "msg_001",
                "from": "sender@example.com",
                "to": "recipient@example.com",
                "subject": "Test Email 1",
                "date": "2024-01-01T10:00:00Z",
                "body": "This is a test email body.",
                "attachments": [
                    {
                        "filename": "document.pdf",
                        "size": 1024000,
                        "content_type": "application/pdf",
                        "hash": "sha256_hash_here"
                    }
                ],
                "headers": {
                    "message-id": "<msg_001@example.com>",
                    "x-mailer": "Outlook 2019"
                }
            },
            {
                "message_id": "msg_002",
                "from": "sender@example.com",
                "to": "recipient@example.com",
                "subject": "Test Email 2",
                "date": "2024-01-01T14:30:00Z",
                "body": "Another test email.",
                "attachments": [],
                "headers": {
                    "message-id": "<msg_002@example.com>",
                    "x-mailer": "Outlook 2019"
                }
            }
        ]

        return {
            "emails": emails,
            "total_emails": len(emails),
            "file_type": "outlook",
            "parse_status": "completed"
        }

    except Exception as e:
        logger.error(f"Outlook database parsing failed: {e}")
        return {"error": f"Outlook parsing failed: {str(e)}"}

def _parse_thunderbird_database(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Thunderbird email database."""
    try:
        profile_dir = email_data.get('profile_directory')
        if not profile_dir or not os.path.exists(profile_dir):
            return {"error": "Thunderbird profile directory not found"}

        # Look for mail storage files
        mail_dir = os.path.join(profile_dir, 'Mail')
        if not os.path.exists(mail_dir):
            return {"error": "Thunderbird mail directory not found"}

        # Mock implementation for demonstration
        emails = [
            {
                "message_id": "msg_003",
                "from": "sender@thunderbird.com",
                "to": "recipient@thunderbird.com",
                "subject": "Thunderbird Test",
                "date": "2024-01-01T16:00:00Z",
                "body": "Thunderbird test email.",
                "attachments": [
                    {
                        "filename": "image.jpg",
                        "size": 512000,
                        "content_type": "image/jpeg",
                        "hash": "sha256_hash_here"
                    }
                ],
                "headers": {
                    "message-id": "<msg_003@thunderbird.com>",
                    "x-mailer": "Thunderbird 91.0"
                }
            }
        ]

        return {
            "emails": emails,
            "total_emails": len(emails),
            "file_type": "thunderbird",
            "parse_status": "completed"
        }

    except Exception as e:
        logger.error(f"Thunderbird database parsing failed: {e}")
        return {"error": f"Thunderbird parsing failed: {str(e)}"}

def _parse_apple_mail_database(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Apple Mail database."""
    try:
        mail_dir = email_data.get('mail_directory')
        if not mail_dir or not os.path.exists(mail_dir):
            return {"error": "Apple Mail directory not found"}

        # Mock implementation for demonstration
        emails = [
            {
                "message_id": "msg_004",
                "from": "sender@apple.com",
                "to": "recipient@apple.com",
                "subject": "Apple Mail Test",
                "date": "2024-01-01T18:00:00Z",
                "body": "Apple Mail test email.",
                "attachments": [],
                "headers": {
                    "message-id": "<msg_004@apple.com>",
                    "x-mailer": "Apple Mail"
                }
            }
        ]

        return {
            "emails": emails,
            "total_emails": len(emails),
            "file_type": "apple_mail",
            "parse_status": "completed"
        }

    except Exception as e:
        logger.error(f"Apple Mail database parsing failed: {e}")
        return {"error": f"Apple Mail parsing failed: {str(e)}"}

def _parse_gmail_database(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Gmail database (local cache)."""
    try:
        gmail_cache = email_data.get('gmail_cache')
        if not gmail_cache or not os.path.exists(gmail_cache):
            return {"error": "Gmail cache directory not found"}

        # Mock implementation for demonstration
        emails = [
            {
                "message_id": "msg_005",
                "from": "sender@gmail.com",
                "to": "recipient@gmail.com",
                "subject": "Gmail Test",
                "date": "2024-01-01T20:00:00Z",
                "body": "Gmail test email.",
                "attachments": [
                    {
                        "filename": "spreadsheet.xlsx",
                        "size": 2048000,
                        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "hash": "sha256_hash_here"
                    }
                ],
                "headers": {
                    "message-id": "<msg_005@gmail.com>",
                    "x-mailer": "Gmail"
                }
            }
        ]

        return {
            "emails": emails,
            "total_emails": len(emails),
            "file_type": "gmail",
            "parse_status": "completed"
        }

    except Exception as e:
        logger.error(f"Gmail database parsing failed: {e}")
        return {"error": f"Gmail parsing failed: {str(e)}"}

def _process_email_data(parsed_data: Dict[str, Any], email_client: str) -> List[Dict[str, Any]]:
    """Process and normalize email data."""
    try:
        if "error" in parsed_data:
            return []

        processed_emails = []
        for email_item in parsed_data.get('emails', []):
            processed_email = {
                "message_id": email_item.get('message_id', ''),
                "from": email_item.get('from', ''),
                "to": email_item.get('to', ''),
                "subject": email_item.get('subject', ''),
                "date": _normalize_timestamp(email_item.get('date')),
                "body": email_item.get('body', ''),
                "attachments": email_item.get('attachments', []),
                "headers": email_item.get('headers', {}),
                "email_client": email_client,
                "body_length": len(email_item.get('body', '')),
                "has_attachments": len(email_item.get('attachments', [])) > 0,
                "attachment_count": len(email_item.get('attachments', [])),
                "total_attachment_size": sum(att.get('size', 0) for att in email_item.get('attachments', []))
            }
            processed_emails.append(processed_email)

        return processed_emails

    except Exception as e:
        logger.error(f"Email data processing failed: {e}")
        return []

def _generate_email_statistics(processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics from processed email data."""
    try:
        if not processed_emails:
            return {"error": "No emails to analyze"}

        total_emails = len(processed_emails)
        emails_with_attachments = sum(1 for email in processed_emails if email.get('has_attachments', False))
        total_attachments = sum(email.get('attachment_count', 0) for email in processed_emails)
        total_attachment_size = sum(email.get('total_attachment_size', 0) for email in processed_emails)

        # Analyze email sizes
        body_lengths = [email.get('body_length', 0) for email in processed_emails]
        avg_body_length = sum(body_lengths) / len(body_lengths) if body_lengths else 0

        # Analyze time distribution
        dates = [email.get('date') for email in processed_emails if email.get('date')]
        time_analysis = _analyze_email_time_patterns(dates)

        return {
            "total_emails": total_emails,
            "emails_with_attachments": emails_with_attachments,
            "attachment_statistics": {
                "total_attachments": total_attachments,
                "total_size": total_attachment_size,
                "average_per_email": total_attachments / total_emails if total_emails > 0 else 0
            },
            "body_statistics": {
                "average_length": avg_body_length,
                "shortest": min(body_lengths) if body_lengths else 0,
                "longest": max(body_lengths) if body_lengths else 0
            },
            "time_analysis": time_analysis
        }

    except Exception as e:
        logger.error(f"Email statistics generation failed: {e}")
        return {"error": f"Statistics generation failed: {str(e)}"}

def _analyze_attachment_characteristics(all_attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze characteristics of all attachments."""
    try:
        if not all_attachments:
            return {"error": "No attachments to analyze"}

        # Analyze file types
        file_types = {}
        file_sizes = []
        content_types = {}

        for attachment in all_attachments:
            filename = attachment.get('filename', '')
            size = attachment.get('size', 0)
            content_type = attachment.get('content_type', 'unknown')

            # File type analysis
            if filename:
                file_ext = os.path.splitext(filename)[1].lower()
                file_types[file_ext] = file_types.get(file_ext, 0) + 1

            # Size analysis
            if size:
                file_sizes.append(size)

            # Content type analysis
            content_types[content_type] = content_types.get(content_type, 0) + 1

        return {
            "total_attachments": len(all_attachments),
            "file_type_analysis": {
                "total_types": len(file_types),
                "type_distribution": file_types,
                "most_common_type": max(file_types.items(), key=lambda x: x[1])[0] if file_types else None
            },
            "size_analysis": {
                "total_size": sum(file_sizes),
                "average_size": sum(file_sizes) / len(file_sizes) if file_sizes else 0,
                "largest_file": max(file_sizes) if file_sizes else 0,
                "smallest_file": min(file_sizes) if file_sizes else 0
            },
            "content_type_analysis": {
                "total_types": len(content_types),
                "type_distribution": content_types
            }
        }

    except Exception as e:
        logger.error(f"Attachment characteristics analysis failed: {e}")
        return {"error": f"Characteristics analysis failed: {str(e)}"}

def _identify_suspicious_attachments(all_attachments: List[Dict[str, Any]], extraction_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify potentially suspicious attachments."""
    suspicious_attachments = []

    # Define suspicious patterns
    suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.vbs', '.js']
    suspicious_keywords = ['crack', 'hack', 'keygen', 'warez', 'torrent', 'password']
    suspicious_content_types = ['application/x-executable', 'application/x-msdownload']

    for attachment in all_attachments:
        filename = attachment.get('filename', '').lower()
        content_type = attachment.get('content_type', '').lower()

        # Check for suspicious extensions
        if any(filename.endswith(ext) for ext in suspicious_extensions):
            attachment['suspicion_reason'] = 'suspicious_file_extension'
            attachment['risk_level'] = 'high'
            suspicious_attachments.append(attachment)

        # Check for suspicious keywords
        elif any(keyword in filename for keyword in suspicious_keywords):
            attachment['suspicion_reason'] = 'suspicious_filename'
            attachment['risk_level'] = 'medium'
            suspicious_attachments.append(attachment)

        # Check for suspicious content types
        elif any(susp_type in content_type for susp_type in suspicious_content_types):
            attachment['suspicion_reason'] = 'suspicious_content_type'
            attachment['risk_level'] = 'high'
            suspicious_attachments.append(attachment)

    return suspicious_attachments

def _generate_attachment_timeline(all_attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate chronological timeline of attachments."""
    try:
        if not all_attachments:
            return {"error": "No attachments to analyze"}

        # Sort by email date
        all_attachments.sort(key=lambda x: _normalize_timestamp(x.get('email_date', '')))

        # Group by time periods
        timeline_periods = {
            "morning": {"start": "06:00", "end": "12:00", "attachments": []},
            "afternoon": {"start": "12:00", "end": "18:00", "attachments": []},
            "evening": {"start": "18:00", "end": "22:00", "attachments": []},
            "night": {"start": "22:00", "end": "06:00", "attachments": []}
        }

        for attachment in all_attachments:
            email_date = _normalize_timestamp(attachment.get('email_date', ''))
            if email_date:
                hour = email_date.hour
                if 6 <= hour < 12:
                    timeline_periods["morning"]["attachments"].append(attachment)
                elif 12 <= hour < 18:
                    timeline_periods["afternoon"]["attachments"].append(attachment)
                elif 18 <= hour < 22:
                    timeline_periods["evening"]["attachments"].append(attachment)
                else:
                    timeline_periods["night"]["attachments"].append(attachment)

        return {
            "total_attachments": len(all_attachments),
            "timeline_periods": timeline_periods,
            "attachment_frequency": {
                period: len(data["attachments"]) for period, data in timeline_periods.items()
            }
        }

    except Exception as e:
        logger.error(f"Attachment timeline generation failed: {e}")
        return {"error": f"Timeline generation failed: {str(e)}"}

def _analyze_sender_patterns(processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in email senders."""
    try:
        if not processed_emails:
            return {"error": "No emails to analyze"}

        # Count sender frequencies
        sender_counts = {}
        for email_item in processed_emails:
            sender = email_item.get('from', '')
            if sender:
                sender_counts[sender] = sender_counts.get(sender, 0) + 1

        # Analyze sender behavior
        sender_analysis = {}
        for sender, count in sender_counts.items():
            sender_emails = [e for e in processed_emails if e.get('from') == sender]

            sender_analysis[sender] = {
                "email_count": count,
                "has_attachments": any(e.get('has_attachments') for e in sender_emails),
                "total_attachment_size": sum(e.get('total_attachment_size', 0) for e in sender_emails),
                "average_body_length": sum(e.get('body_length', 0) for e in sender_emails) / len(sender_emails)
            }

        return {
            "total_unique_senders": len(sender_counts),
            "sender_frequencies": sender_counts,
            "top_senders": sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "sender_behavior": sender_analysis
        }

    except Exception as e:
        logger.error(f"Sender pattern analysis failed: {e}")
        return {"error": f"Sender analysis failed: {str(e)}"}

def _analyze_recipient_patterns(processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in email recipients."""
    try:
        if not processed_emails:
            return {"error": "No emails to analyze"}

        # Count recipient frequencies
        recipient_counts = {}
        for email_item in processed_emails:
            recipient = email_item.get('to', '')
            if recipient:
                recipient_counts[recipient] = recipient_counts.get(recipient, 0) + 1

        # Analyze recipient behavior
        recipient_analysis = {}
        for recipient, count in recipient_counts.items():
            recipient_emails = [e for e in processed_emails if e.get('to') == recipient]

            recipient_analysis[recipient] = {
                "email_count": count,
                "has_attachments": any(e.get('has_attachments') for e in recipient_emails),
                "total_attachment_size": sum(e.get('total_attachment_size', 0) for e in recipient_emails),
                "average_body_length": sum(e.get('body_length', 0) for e in recipient_emails) / len(recipient_emails)
            }

        return {
            "total_unique_recipients": len(recipient_counts),
            "recipient_frequencies": recipient_counts,
            "top_recipients": sorted(recipient_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "recipient_behavior": recipient_analysis
        }

    except Exception as e:
        logger.error(f"Recipient pattern analysis failed: {e}")
        return {"error": f"Recipient analysis failed: {str(e)}"}

def _analyze_temporal_patterns(processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze temporal patterns in email communications."""
    try:
        if not processed_emails:
            return {"error": "No emails to analyze"}

        # Extract dates and analyze patterns
        dates = [email_item.get('date') for email_item in processed_emails if email_item.get('date')]

        if not dates:
            return {"error": "No valid dates found"}

        # Analyze time patterns
        time_analysis = _analyze_email_time_patterns(dates)

        # Analyze day-of-week patterns
        day_counts = {}
        for date in dates:
            day = date.strftime('%A')
            day_counts[day] = day_counts.get(day, 0) + 1

        return {
            "time_analysis": time_analysis,
            "day_of_week_analysis": {
                "day_distribution": day_counts,
                "most_active_day": max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
            },
            "total_time_periods": len(dates)
        }

    except Exception as e:
        logger.error(f"Temporal pattern analysis failed: {e}")
        return {"error": f"Temporal analysis failed: {str(e)}"}

def _analyze_content_patterns(processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze content patterns in emails."""
    try:
        if not processed_emails:
            return {"error": "No emails to analyze"}

        # Analyze subject patterns
        subject_keywords = {}
        for email_item in processed_emails:
            subject = email_item.get('subject', '').lower()
            words = re.findall(r'\b\w+\b', subject)
            for word in words:
                if len(word) > 3:  # Only count words longer than 3 characters
                    subject_keywords[word] = subject_keywords.get(word, 0) + 1

        # Analyze body patterns
        body_lengths = [email_item.get('body_length', 0) for email_item in processed_emails]
        body_categories = {
            "short": sum(1 for length in body_lengths if length < 100),
            "medium": sum(1 for length in body_lengths if 100 <= length < 500),
            "long": sum(1 for length in body_lengths if length >= 500)
        }

        return {
            "subject_analysis": {
                "total_keywords": len(subject_keywords),
                "top_keywords": sorted(subject_keywords.items(), key=lambda x: x[1], reverse=True)[:10],
                "keyword_distribution": subject_keywords
            },
            "body_analysis": {
                "length_categories": body_categories,
                "average_length": sum(body_lengths) / len(body_lengths) if body_lengths else 0,
                "length_distribution": body_lengths
            }
        }

    except Exception as e:
        logger.error(f"Content pattern analysis failed: {e}")
        return {"error": f"Content analysis failed: {str(e)}"}

def _analyze_communication_networks(processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze communication networks and relationships."""
    try:
        if not processed_emails:
            return {"error": "No emails to analyze"}

        # Build communication graph
        communication_graph = {}
        for email_item in processed_emails:
            sender = email_item.get('from', '')
            recipient = email_item.get('to', '')

            if sender and recipient:
                if sender not in communication_graph:
                    communication_graph[sender] = {}
                if recipient not in communication_graph[sender]:
                    communication_graph[sender][recipient] = 0
                communication_graph[sender][recipient] += 1

        # Analyze network characteristics
        total_nodes = len(set(list(communication_graph.keys()) +
                           [recipient for connections in communication_graph.values()
                            for recipient in connections.keys()]))

        total_connections = sum(sum(connections.values()) for connections in communication_graph.values())

        # Find most active communicators
        sender_activity = {sender: sum(connections.values()) for sender, connections in communication_graph.items()}
        top_communicators = sorted(sender_activity.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "network_statistics": {
                "total_nodes": total_nodes,
                "total_connections": total_connections,
                "average_connections_per_node": total_connections / total_nodes if total_nodes > 0 else 0
            },
            "communication_graph": communication_graph,
            "top_communicators": top_communicators,
            "network_density": total_connections / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0
        }

    except Exception as e:
        logger.error(f"Communication network analysis failed: {e}")
        return {"error": f"Network analysis failed: {str(e)}"}

def _identify_communication_anomalies(processed_emails: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify anomalies in communication patterns."""
    anomalies = []

    # Define anomaly thresholds
    high_volume_threshold = analysis_params.get('high_volume_threshold', 50)
    unusual_time_threshold = analysis_params.get('unusual_time_threshold', 3)  # AM hours

    # Check for high-volume senders
    sender_counts = {}
    for email_item in processed_emails:
        sender = email_item.get('from', '')
        if sender:
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

    for sender, count in sender_counts.items():
        if count > high_volume_threshold:
            anomalies.append({
                "type": "high_volume_sender",
                "sender": sender,
                "email_count": count,
                "threshold": high_volume_threshold,
                "severity": "medium"
            })

    # Check for unusual timing
    for email_item in processed_emails:
        date = email_item.get('date')
        if date and date.hour < unusual_time_threshold:
            anomalies.append({
                "type": "unusual_timing",
                "email_id": email_item.get('message_id', ''),
                "time": date.isoformat(),
                "hour": date.hour,
                "threshold": unusual_time_threshold,
                "severity": "low"
            })

    return anomalies

def _analyze_email_time_patterns(dates: List[datetime]) -> Dict[str, Any]:
    """Analyze time patterns from email dates."""
    try:
        if not dates:
            return {"error": "No dates to analyze"}

        # Filter out None dates
        valid_dates = [date for date in dates if date]

        if not valid_dates:
            return {"error": "No valid dates found"}

        # Analyze hour distribution
        hour_distribution = {}
        for date in valid_dates:
            hour = date.hour
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1

        # Find peak hours
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None

        return {
            "total_dates": len(valid_dates),
            "hour_distribution": hour_distribution,
            "peak_hour": peak_hour,
            "time_range": {
                "earliest": min(valid_dates).isoformat(),
                "latest": max(valid_dates).isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Email time pattern analysis failed: {e}")
        return {"error": f"Time pattern analysis failed: {str(e)}"}

def _normalize_timestamp(timestamp) -> Optional[datetime]:
    """Normalize various timestamp formats to datetime object."""
    if not timestamp:
        return None

    try:
        if isinstance(timestamp, str):
            # Try to parse various timestamp formats
            if timestamp.isdigit():
                # Unix timestamp
                return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            else:
                # ISO format or other string format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(timestamp, datetime):
            return timestamp
        else:
            return None
    except Exception:
        return None

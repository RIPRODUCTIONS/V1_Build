"""
Memory Manager - Context and Memory Management

This module provides comprehensive memory management for the AI framework:
- Conversation history and context management
- Entity tracking and relationship mapping
- Vector storage for semantic search
- Memory persistence and optimization
- Context window management
- Memory cleanup and garbage collection
"""

import asyncio
import gzip
import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Constants to replace magic numbers
MIN_WORD_LENGTH = 2
MIN_ENTITY_CONFIDENCE = 0.5
DEFAULT_MEMORY_TTL = 86400  # 24 hours in seconds
MAX_MEMORY_ITEMS = 10000
COMPRESSION_THRESHOLD = 1024  # 1KB


class MemoryType(str, Enum):
    """Types of memory stored in the system."""
    CONVERSATION = "conversation"
    ENTITY = "entity"
    FACT = "fact"
    RELATIONSHIP = "relationship"
    CONTEXT = "context"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    EMOTIONAL = "emotional"


class MemoryPriority(str, Enum):
    """Priority levels for memory retention."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryItem:
    """Individual memory item."""
    memory_id: str
    memory_type: MemoryType
    content: str
    metadata: dict[str, Any]
    priority: MemoryPriority
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    confidence: float = 1.0
    source: str | None = None
    tags: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    compressed: bool = False


@dataclass
class ConversationMemory:
    """Memory for conversation context."""
    conversation_id: str
    participants: list[str]
    messages: list[dict[str, Any]]
    context_summary: str
    entities_mentioned: list[str]
    topics_discussed: list[str]
    sentiment: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityMemory:
    """Memory for tracking entities."""
    entity_id: str
    entity_type: str
    name: str
    attributes: dict[str, Any]
    relationships: list[dict[str, Any]]
    first_seen: datetime
    last_seen: datetime
    confidence: float
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """Context window for managing conversation context."""
    window_id: str
    conversation_id: str
    messages: list[dict[str, Any]]
    max_tokens: int
    current_tokens: int
    created_at: datetime
    last_updated: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """Main memory manager for the AI framework."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get("database", {}).get("path", "memory_manager.db"))
        self.max_memory_items = config.get("max_memory_items", 10000)
        self.max_conversation_history = config.get("max_conversation_history", 1000)
        self.context_window_size = config.get("context_window_size", 4096)
        self.memory_compression_threshold = config.get("memory_compression_threshold", 1000)
        self.cleanup_interval = config.get("cleanup_interval", 3600)  # 1 hour

        # Memory storage
        self.memories: dict[str, MemoryItem] = {}
        self.conversations: dict[str, ConversationMemory] = {}
        self.entities: dict[str, EntityMemory] = {}
        self.context_windows: dict[str, ContextWindow] = {}

        # Indexes for fast lookup
        self.memory_index: dict[str, set[str]] = {}
        self.entity_index: dict[str, set[str]] = {}
        self.conversation_index: dict[str, set[str]] = {}

        # Initialize database
        self._init_database()

        # Load existing memories
        self._load_memories()

        # Start background tasks
        self.cleanup_task = None
        self._start_background_tasks()

        logger.info("Memory Manager initialized")

    def _init_database(self):
        """Initialize the memory database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Memories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    tags TEXT NOT NULL,
                    expires_at TEXT,
                    compressed BOOLEAN DEFAULT FALSE
                )
            ''')

            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    participants TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    context_summary TEXT NOT NULL,
                    entities_mentioned TEXT NOT NULL,
                    topics_discussed TEXT NOT NULL,
                    sentiment REAL,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            ''')

            # Entities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    attributes TEXT NOT NULL,
                    relationships TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            ''')

            # Context windows table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS context_windows (
                    window_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    max_tokens INTEGER NOT NULL,
                    current_tokens INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
            ''')

            # Memory indexes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_indexes (
                    index_key TEXT NOT NULL,
                    memory_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (index_key, memory_id),
                    FOREIGN KEY (memory_id) REFERENCES memories (memory_id)
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Memory database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize memory database: {e}")

    def _start_background_tasks(self):
        """Start background memory management tasks."""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def store_memory(self, memory_data: dict[str, Any]) -> str:
        """Store a new memory item using a dictionary to reduce parameter count."""
        try:
            # Extract parameters from dictionary with defaults
            memory_type = memory_data.get("memory_type")
            content = memory_data.get("content")
            metadata = memory_data.get("metadata", {})
            priority = memory_data.get("priority", MemoryPriority.MEDIUM)
            source = memory_data.get("source")
            tags = memory_data.get("tags", [])
            expires_at = memory_data.get("expires_at")

            # Generate memory ID
            memory_id = hashlib.md5(f"{memory_type}_{content}_{time.time()}".encode()).hexdigest()

            # Create memory item
            memory_item = MemoryItem(
                memory_id=memory_id,
                memory_type=memory_type,
                content=content,
                metadata=metadata,
                priority=priority,
                created_at=datetime.now(UTC),
                last_accessed=datetime.now(UTC),
                source=source,
                tags=tags,
                expires_at=expires_at
            )

            # Check if compression is needed
            if len(content) > self.memory_compression_threshold:
                memory_item.content = self._compress_content(content)
                memory_item.compressed = True

            # Store in memory
            self.memories[memory_id] = memory_item

            # Update indexes
            self._update_memory_indexes(memory_item)

            # Save to database
            await self._save_memory_to_db(memory_item)

            # Check memory limits
            await self._enforce_memory_limits()

            logger.info(f"Memory stored: {memory_id} ({memory_type.value})")
            return memory_id

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    async def retrieve_memory(self, memory_id: str) -> MemoryItem | None:
        """Retrieve a memory item by ID."""
        try:
            if memory_id not in self.memories:
                return None

            memory_item = self.memories[memory_id]

            # Update access statistics
            memory_item.last_accessed = datetime.now(UTC)
            memory_item.access_count += 1

            # Decompress if needed
            if memory_item.compressed:
                memory_item.content = self._decompress_content(memory_item.content)

            # Update database
            await self._update_memory_access(memory_item)

            return memory_item

        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return None

    async def search_memories(self, query: str, memory_type: MemoryType | None = None,
                             tags: list[str] = None, limit: int = 100) -> list[MemoryItem]:
        """Search memories by query, type, and tags."""
        try:
            results = []

            for memory_item in self.memories.values():
                # Check if memory matches search criteria
                if not self._memory_matches_search(memory_item, query, memory_type, tags):
                    continue

                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(memory_item, query)

                results.append((memory_item, relevance_score))

            # Sort by relevance and return top results
            results.sort(key=lambda x: x[1], reverse=True)

            # Decompress content for returned memories
            for memory_item, _ in results[:limit]:
                if memory_item.compressed:
                    memory_item.content = self._decompress_content(memory_item.content)

            return [memory_item for memory_item, _ in results[:limit]]

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    def _memory_matches_search(self, memory_item: MemoryItem, query: str,
                              memory_type: MemoryType | None, tags: list[str]) -> bool:
        """Check if a memory item matches search criteria."""
        # Check memory type
        if memory_type and memory_item.memory_type != memory_type:
            return False

        # Check tags
        if tags and not any(tag in memory_item.tags for tag in tags):
            return False

        # Check if query appears in content or metadata
        query_lower = query.lower()
        if query_lower in memory_item.content.lower():
            return True

        # Check metadata
        metadata_str = json.dumps(memory_item.metadata).lower()
        if query_lower in metadata_str:
            return True

        # Check tags
        return query_lower in [tag.lower() for tag in memory_item.tags]

    def _calculate_relevance_score(self, memory_item: MemoryItem, query: str) -> float:
        """Calculate relevance score for a memory item."""
        score = 0.0

        # Content relevance
        query_lower = query.lower()
        content_lower = memory_item.content.lower()

        # Exact phrase match
        if query_lower in content_lower:
            score += 10.0

        # Word matches
        query_words = query_lower.split()
        content_words = content_lower.split()

        word_matches = sum(1 for word in query_words if word in content_words)
        if word_matches > 0:
            score += (word_matches / len(query_words)) * 5.0

        # Recency bonus
        days_old = (datetime.now(UTC) - memory_item.created_at).days
        RECENT_DAYS_THRESHOLD = 1
        WEEK_DAYS_THRESHOLD = 7
        if days_old < RECENT_DAYS_THRESHOLD:
            score += 2.0
        elif days_old < WEEK_DAYS_THRESHOLD:
            score += 1.0

        # Access frequency bonus
        ACCESS_FREQUENCY_MULTIPLIER = 0.1
        MAX_ACCESS_BONUS = 2.0
        score += min(memory_item.access_count * ACCESS_FREQUENCY_MULTIPLIER, MAX_ACCESS_BONUS)

        # Priority bonus
        priority_bonus = {
            MemoryPriority.CRITICAL: 3.0,
            MemoryPriority.HIGH: 2.0,
            MemoryPriority.MEDIUM: 1.0,
            MemoryPriority.LOW: 0.0
        }
        score += priority_bonus.get(memory_item.priority, 0.0)

        return score

    async def store_conversation(self, conversation_data: dict[str, Any]) -> str:
        """Store a conversation in memory using a dictionary to reduce parameter count."""
        try:
            # Extract parameters from dictionary with defaults
            conversation_id = conversation_data.get("conversation_id")
            participants = conversation_data.get("participants", [])
            messages = conversation_data.get("messages", [])
            context_summary = conversation_data.get("context_summary", "")
            entities_mentioned = conversation_data.get("entities_mentioned", [])
            topics_discussed = conversation_data.get("topics_discussed", [])
            sentiment = conversation_data.get("sentiment")

            # Create conversation memory
            conversation = ConversationMemory(
                conversation_id=conversation_id,
                participants=participants,
                messages=messages,
                context_summary=context_summary,
                entities_mentioned=entities_mentioned,
                topics_discussed=topics_discussed,
                sentiment=sentiment
            )

            # Store in memory
            self.conversations[conversation_id] = conversation

            # Update indexes
            self._update_conversation_indexes(conversation)

            # Save to database
            await self._save_conversation_to_db(conversation)

            # Extract and store entities
            await self._extract_entities_from_conversation(conversation)

            # Check conversation limits
            await self._enforce_conversation_limits()

            logger.info(f"Conversation stored: {conversation_id}")
            return conversation_id

        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            raise

    async def get_conversation_context(self, conversation_id: str, max_tokens: int = None) -> ContextWindow | None:
        """Get conversation context window."""
        try:
            if conversation_id not in self.conversations:
                return None

            conversation = self.conversations[conversation_id]
            max_tokens = max_tokens or self.context_window_size

            # Check if context window exists
            window_key = f"{conversation_id}_{max_tokens}"
            if window_key in self.context_windows:
                window = self.context_windows[window_key]
                window.last_updated = datetime.now(UTC)
                return window

            # Create new context window
            context_window = await self._create_context_window(conversation, max_tokens)

            if context_window:
                self.context_windows[window_key] = context_window
                await self._save_context_window_to_db(context_window)

            return context_window

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return None

    async def _create_context_window(self, conversation: ConversationMemory, max_tokens: int) -> ContextWindow | None:
        """Create a context window for a conversation."""
        try:
            # Calculate token count for messages
            messages = conversation.messages
            current_tokens = 0
            selected_messages = []

            # Start from most recent messages and work backwards
            for message in reversed(messages):
                message_tokens = len(message.get("content", "").split())  # Approximate token count

                if current_tokens + message_tokens <= max_tokens:
                    selected_messages.insert(0, message)
                    current_tokens += message_tokens
                else:
                    break

            # Create context window
            window_id = f"{conversation.conversation_id}_{max_tokens}"
            context_window = ContextWindow(
                window_id=window_id,
                conversation_id=conversation.conversation_id,
                messages=selected_messages,
                max_tokens=max_tokens,
                current_tokens=current_tokens,
                created_at=datetime.now(UTC),
                last_updated=datetime.now(UTC)
            )

            return context_window

        except Exception as e:
            logger.error(f"Failed to create context window: {e}")
            return None

    async def store_entity(self, entity_data: dict[str, Any]) -> str:
        """Store an entity in memory using a dictionary to reduce parameter count."""
        try:
            # Extract parameters from dictionary with defaults
            entity_type = entity_data.get("entity_type")
            name = entity_data.get("name")
            attributes = entity_data.get("attributes", {})
            relationships = entity_data.get("relationships", [])
            source = entity_data.get("source")
            confidence = entity_data.get("confidence", 1.0)

            # Generate entity ID
            entity_id = hashlib.md5(f"{entity_type}_{name}_{source}".encode()).hexdigest()

            # Check if entity already exists
            if entity_id in self.entities:
                # Update existing entity
                entity = self.entities[entity_id]
                entity.last_seen = datetime.now(UTC)
                entity.attributes.update(attributes)
                entity.relationships.extend(relationships)
                entity.confidence = max(entity.confidence, confidence)

                # Remove duplicates from relationships
                seen_relationships = set()
                unique_relationships = []
                for rel in entity.relationships:
                    rel_key = f"{rel.get('type')}_{rel.get('target')}"
                    if rel_key not in seen_relationships:
                        seen_relationships.add(rel_key)
                        unique_relationships.append(rel)
                entity.relationships = unique_relationships

            else:
                # Create new entity
                entity = EntityMemory(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    name=name,
                    attributes=attributes,
                    relationships=relationships,
                    first_seen=datetime.now(UTC),
                    last_seen=datetime.now(UTC),
                    confidence=confidence,
                    source=source
                )

                self.entities[entity_id] = entity

            # Update indexes
            self._update_entity_indexes(entity)

            # Save to database
            await self._save_entity_to_db(entity)

            logger.info(f"Entity stored: {entity_id} ({entity_type}: {name})")
            return entity_id

        except Exception as e:
            logger.error(f"Failed to store entity: {e}")
            raise

    async def get_entity(self, entity_id: str) -> EntityMemory | None:
        """Get an entity by ID."""
        return self.entities.get(entity_id)

    async def search_entities(self, query: str, entity_type: str | None = None,
                             limit: int = 100) -> list[EntityMemory]:
        """Search entities by query and type."""
        try:
            results = []

            for entity in self.entities.values():
                # Check if entity matches search criteria
                if entity_type and entity.entity_type != entity_type:
                    continue

                # Check if query appears in entity name or attributes
                query_lower = query.lower()
                if query_lower in entity.name.lower():
                    results.append((entity, 10.0))  # High score for name match
                elif any(query_lower in str(value).lower() for value in entity.attributes.values()):
                    results.append((entity, 5.0))  # Medium score for attribute match
                else:
                    continue

            # Sort by score and return top results
            results.sort(key=lambda x: x[1], reverse=True)
            return [entity for entity, _ in results[:limit]]

        except Exception as e:
            logger.error(f"Entity search failed: {e}")
            return []

    async def _extract_entities_from_conversation(self, conversation: ConversationMemory):
        """Extract entities from conversation messages."""
        try:
            # Simple entity extraction (can be enhanced with NLP)
            entities = set()

            for message in conversation.messages:
                content = message.get("content", "")

                # Extract potential entities (simple approach)
                words = content.split()
                for word in words:
                    # Check if word looks like an entity (capitalized, not common words)
                    if (word[0].isupper() and len(word) > MIN_WORD_LENGTH and
                        word.lower() not in ["the", "and", "or", "but", "in", "on", "at", "to", "for"]):
                        entities.add(word)

            # Store extracted entities
            for entity_name in entities:
                await self.store_entity(
                    entity_type="person",  # Default type
                    name=entity_name,
                    attributes={"source": "conversation_extraction"},
                    relationships=[],
                    source=conversation.conversation_id,
                    confidence=0.5
                )

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")

    def _update_memory_indexes(self, memory_item: MemoryItem):
        """Update memory indexes for fast lookup."""
        # Index by type
        if memory_item.memory_type.value not in self.memory_index:
            self.memory_index[memory_item.memory_type.value] = set()
        self.memory_index[memory_item.memory_type.value].add(memory_item.memory_id)

        # Index by tags
        for tag in memory_item.tags:
            if tag not in self.memory_index:
                self.memory_index[tag] = set()
            self.memory_index[tag].add(memory_item.memory_id)

        # Index by source
        if memory_item.source:
            source_key = f"source_{memory_item.source}"
            if source_key not in self.memory_index:
                self.memory_index[source_key] = set()
            self.memory_index[source_key].add(memory_item.memory_id)

    def _update_conversation_indexes(self, conversation: ConversationMemory):
        """Update conversation indexes."""
        # Index by participants
        for participant in conversation.participants:
            if participant not in self.conversation_index:
                self.conversation_index[participant] = set()
            self.conversation_index[participant].add(conversation.conversation_id)

        # Index by topics
        for topic in conversation.topics_discussed:
            topic_key = f"topic_{topic}"
            if topic_key not in self.conversation_index:
                self.conversation_index[topic_key] = set()
            self.conversation_index[topic_key].add(conversation.conversation_id)

    def _update_entity_indexes(self, entity: EntityMemory):
        """Update entity indexes."""
        # Index by type
        if entity.entity_type not in self.entity_index:
            self.entity_index[entity.entity_type] = set()
        self.entity_index[entity.entity_type].add(entity.entity_id)

        # Index by name
        name_key = f"name_{entity.name.lower()}"
        if name_key not in self.entity_index:
            self.entity_index[name_key] = set()
        self.entity_index[name_key].add(entity.entity_id)

    def _compress_content(self, content: str) -> str:
        """Compress content to save memory."""
        try:
            compressed = gzip.compress(content.encode('utf-8'))
            return compressed.hex()
        except Exception as e:
            logger.warning(f"Content compression failed: {e}")
            return content

    def _decompress_content(self, compressed_content: str) -> str:
        """Decompress content."""
        try:
            if compressed_content.startswith('1f8b'):  # Gzip magic number
                compressed_bytes = bytes.fromhex(compressed_content)
                decompressed = gzip.decompress(compressed_bytes)
                return decompressed.decode('utf-8')
            else:
                return compressed_content
        except Exception as e:
            logger.warning(f"Content decompression failed: {e}")
            return compressed_content

    async def _enforce_memory_limits(self):
        """Enforce memory limits by removing old/low-priority items."""
        try:
            if len(self.memories) <= self.max_memory_items:
                return

            # Sort memories by priority and age
            memory_list = list(self.memories.values())
            memory_list.sort(key=lambda m: (
                self._priority_score(m.priority),
                m.last_accessed
            ))

            # Remove excess memories
            excess_count = len(self.memories) - self.max_memory_items
            memories_to_remove = memory_list[:excess_count]

            for memory in memories_to_remove:
                await self._remove_memory(memory.memory_id)

            logger.info(f"Removed {excess_count} memories to enforce limits")

        except Exception as e:
            logger.error(f"Memory limit enforcement failed: {e}")

    async def _enforce_conversation_limits(self):
        """Enforce conversation history limits."""
        try:
            if len(self.conversations) <= self.max_conversation_history:
                return

            # Sort conversations by last updated
            conversation_list = list(self.conversations.values())
            conversation_list.sort(key=lambda c: c.last_updated)

            # Remove oldest conversations
            excess_count = len(self.conversations) - self.max_conversation_history
            conversations_to_remove = conversation_list[:excess_count]

            for conversation in conversations_to_remove:
                await self._remove_conversation(conversation.conversation_id)

            logger.info(f"Removed {excess_count} conversations to enforce limits")

        except Exception as e:
            logger.error(f"Conversation limit enforcement failed: {e}")

    def _priority_score(self, priority: MemoryPriority) -> int:
        """Convert priority to numeric score for sorting."""
        priority_scores = {
            MemoryPriority.CRITICAL: 0,
            MemoryPriority.HIGH: 1,
            MemoryPriority.MEDIUM: 2,
            MemoryPriority.LOW: 3
        }
        return priority_scores.get(priority, 2)

    async def _remove_memory(self, memory_id: str):
        """Remove a memory item."""
        try:
            if memory_id in self.memories:
                memory = self.memories[memory_id]

                # Remove from indexes
                self._remove_memory_from_indexes(memory)

                # Remove from memory
                del self.memories[memory_id]

                # Remove from database
                await self._remove_memory_from_db(memory_id)

        except Exception as e:
            logger.error(f"Failed to remove memory: {e}")

    async def _remove_conversation(self, conversation_id: str):
        """Remove a conversation."""
        try:
            if conversation_id in self.conversations:
                conversation = self.conversations[conversation_id]

                # Remove from indexes
                self._remove_conversation_from_indexes(conversation)

                # Remove from memory
                del self.conversations[conversation_id]

                # Remove from database
                await self._remove_conversation_from_db(conversation_id)

        except Exception as e:
            logger.error(f"Failed to remove conversation: {e}")

    def _remove_memory_from_indexes(self, memory: MemoryItem):
        """Remove memory from all indexes."""
        # Remove from type index
        if memory.memory_type.value in self.memory_index:
            self.memory_index[memory.memory_type.value].discard(memory.memory_id)

        # Remove from tag indexes
        for tag in memory.tags:
            if tag in self.memory_index:
                self.memory_index[tag].discard(memory.memory_id)

        # Remove from source index
        if memory.source:
            source_key = f"source_{memory.source}"
            if source_key in self.memory_index:
                self.memory_index[source_key].discard(memory.memory_id)

    def _remove_conversation_from_indexes(self, conversation: ConversationMemory):
        """Remove conversation from all indexes."""
        # Remove from participant indexes
        for participant in conversation.participants:
            if participant in self.conversation_index:
                self.conversation_index[participant].discard(conversation.conversation_id)

        # Remove from topic indexes
        for topic in conversation.topics_discussed:
            topic_key = f"topic_{topic}"
            if topic_key in self.conversation_index:
                self.conversation_index[topic_key].discard(conversation.conversation_id)

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(600)  # Retry in 10 minutes

    async def _perform_cleanup(self):
        """Perform memory cleanup tasks."""
        try:
            # Remove expired memories
            current_time = datetime.now(UTC)
            expired_memories = []

            for memory in self.memories.values():
                if memory.expires_at and current_time > memory.expires_at:
                    expired_memories.append(memory.memory_id)

            for memory_id in expired_memories:
                await self._remove_memory(memory_id)

            if expired_memories:
                logger.info(f"Cleaned up {len(expired_memories)} expired memories")

            # Compress old memories
            await self._compress_old_memories()

            # Update database
            await self._save_memory_state()

        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")

    async def _compress_old_memories(self):
        """Compress old memories to save space."""
        try:
            current_time = datetime.now(UTC)
            compression_threshold = current_time - timedelta(days=7)

            compressed_count = 0
            for memory in self.memories.values():
                if (memory.created_at < compression_threshold and
                    not memory.compressed and
                    len(memory.content) > self.memory_compression_threshold):

                    memory.content = self._compress_content(memory.content)
                    memory.compressed = True
                    compressed_count += 1

            if compressed_count > 0:
                logger.info(f"Compressed {compressed_count} old memories")

        except Exception as e:
            logger.error(f"Memory compression failed: {e}")

    def _load_memories(self):
        """Load existing memories from database."""
        try:
            # Load memories
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM memories')
            memory_rows = cursor.fetchall()

            for row in memory_rows:
                memory_item = MemoryItem(
                    memory_id=row[0],
                    memory_type=MemoryType(row[1]),
                    content=row[2],
                    metadata=json.loads(row[3]),
                    priority=MemoryPriority(row[4]),
                    created_at=datetime.fromisoformat(row[5]),
                    last_accessed=datetime.fromisoformat(row[6]),
                    access_count=row[7],
                    confidence=row[8],
                    source=row[9],
                    tags=json.loads(row[10]),
                    expires_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    compressed=bool(row[12])
                )

                self.memories[memory_item.memory_id] = memory_item
                self._update_memory_indexes(memory_item)

            # Load conversations
            cursor.execute('SELECT * FROM conversations')
            conversation_rows = cursor.fetchall()

            for row in conversation_rows:
                conversation = ConversationMemory(
                    conversation_id=row[0],
                    participants=json.loads(row[1]),
                    messages=json.loads(row[2]),
                    context_summary=row[3],
                    entities_mentioned=json.loads(row[4]),
                    topics_discussed=json.loads(row[5]),
                    sentiment=row[6],
                    created_at=datetime.fromisoformat(row[7]),
                    last_updated=datetime.fromisoformat(row[8]),
                    metadata=json.loads(row[9])
                )

                self.conversations[conversation.conversation_id] = conversation
                self._update_conversation_indexes(conversation)

            # Load entities
            cursor.execute('SELECT * FROM entities')
            entity_rows = cursor.fetchall()

            for row in entity_rows:
                entity = EntityMemory(
                    entity_id=row[0],
                    entity_type=row[1],
                    name=row[2],
                    attributes=json.loads(row[3]),
                    relationships=json.loads(row[4]),
                    first_seen=datetime.fromisoformat(row[5]),
                    last_seen=datetime.fromisoformat(row[6]),
                    confidence=row[7],
                    source=row[8],
                    metadata=json.loads(row[9])
                )

                self.entities[entity.entity_id] = entity
                self._update_entity_indexes(entity)

            conn.close()

            logger.info(f"Loaded {len(self.memories)} memories, {len(self.conversations)} conversations, {len(self.entities)} entities")

        except Exception as e:
            logger.error(f"Failed to load memories: {e}")

    async def _save_memory_to_db(self, memory: MemoryItem):
        """Save memory to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO memories
                (memory_id, memory_type, content, metadata, priority, created_at,
                 last_accessed, access_count, confidence, source, tags, expires_at, compressed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.memory_id,
                memory.memory_type.value,
                memory.content,
                json.dumps(memory.metadata),
                memory.priority.value,
                memory.created_at.isoformat(),
                memory.last_accessed.isoformat(),
                memory.access_count,
                memory.confidence,
                memory.source,
                json.dumps(memory.tags),
                memory.expires_at.isoformat() if memory.expires_at else None,
                memory.compressed
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save memory to database: {e}")

    async def _save_conversation_to_db(self, conversation: ConversationMemory):
        """Save conversation to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO conversations
                (conversation_id, participants, messages, context_summary, entities_mentioned,
                 topics_discussed, sentiment, created_at, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                conversation.conversation_id,
                json.dumps(conversation.participants),
                json.dumps(conversation.messages),
                conversation.context_summary,
                json.dumps(conversation.entities_mentioned),
                json.dumps(conversation.topics_discussed),
                conversation.sentiment,
                conversation.created_at.isoformat(),
                conversation.last_updated.isoformat(),
                json.dumps(conversation.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save conversation to database: {e}")

    async def _save_entity_to_db(self, entity: EntityMemory):
        """Save entity to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO entities
                (entity_id, entity_type, name, attributes, relationships, first_seen,
                 last_seen, confidence, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity.entity_id,
                entity.entity_type,
                entity.name,
                json.dumps(entity.attributes),
                json.dumps(entity.relationships),
                entity.first_seen.isoformat(),
                entity.last_seen.isoformat(),
                entity.confidence,
                entity.source,
                json.dumps(entity.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save entity to database: {e}")

    async def _save_context_window_to_db(self, context_window: ContextWindow):
        """Save context window to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO context_windows
                (window_id, conversation_id, messages, max_tokens, current_tokens,
                 created_at, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                context_window.window_id,
                context_window.conversation_id,
                json.dumps(context_window.messages),
                context_window.max_tokens,
                context_window.current_tokens,
                context_window.created_at.isoformat(),
                context_window.last_updated.isoformat(),
                json.dumps(context_window.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save context window to database: {e}")

    async def _update_memory_access(self, memory: MemoryItem):
        """Update memory access statistics in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE memories
                SET last_accessed = ?, access_count = ?
                WHERE memory_id = ?
            ''', (
                memory.last_accessed.isoformat(),
                memory.access_count,
                memory.memory_id
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update memory access: {e}")

    async def _remove_memory_from_db(self, memory_id: str):
        """Remove memory from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM memories WHERE memory_id = ?', (memory_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to remove memory from database: {e}")

    async def _remove_conversation_from_db(self, conversation_id: str):
        """Remove conversation from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM conversations WHERE conversation_id = ?', (conversation_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to remove conversation from database: {e}")

    async def _save_memory_state(self):
        """Save current memory state to database."""
        try:
            # This method can be used to save the entire memory state
            # For now, we'll just log the current state
            logger.info(f"Memory state: {len(self.memories)} memories, {len(self.conversations)} conversations, {len(self.entities)} entities")

        except Exception as e:
            logger.error(f"Failed to save memory state: {e}")

    async def get_memory_statistics(self) -> dict[str, Any]:
        """Get memory system statistics."""
        try:
            # Calculate memory statistics
            total_memories = len(self.memories)
            total_conversations = len(self.conversations)
            total_entities = len(self.entities)

            # Memory type distribution
            memory_types = {}
            for memory in self.memories.values():
                memory_type = memory.memory_type.value
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1

            # Priority distribution
            priority_distribution = {}
            for memory in self.memories.values():
                priority = memory.priority.value
                priority_distribution[priority] = priority_distribution.get(priority, 0) + 1

            # Entity type distribution
            entity_types = {}
            for entity in self.entities.values():
                entity_type = entity.entity_type
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            # Compression statistics
            compressed_count = sum(1 for m in self.memories.values() if m.compressed)
            uncompressed_count = total_memories - compressed_count

            return {
                "total_memories": total_memories,
                "total_conversations": total_conversations,
                "total_entities": total_entities,
                "memory_types": memory_types,
                "priority_distribution": priority_distribution,
                "entity_types": entity_types,
                "compression": {
                    "compressed": compressed_count,
                    "uncompressed": uncompressed_count,
                    "compression_ratio": compressed_count / max(total_memories, 1)
                },
                "indexes": {
                    "memory_indexes": len(self.memory_index),
                    "conversation_indexes": len(self.conversation_index),
                    "entity_indexes": len(self.entity_index)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {}

    async def cleanup(self):
        """Clean up memory manager resources."""
        try:
            # Cancel background tasks
            if self.cleanup_task:
                self.cleanup_task.cancel()

            # Save final state
            await self._save_memory_state()

            logger.info("Memory manager cleaned up")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        if hasattr(self, 'cleanup'):
            asyncio.create_task(self.cleanup())

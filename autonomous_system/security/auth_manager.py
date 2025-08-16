"""
Security and Authentication Manager
Comprehensive security system with JWT, RBAC, and security policies
"""

import asyncio
import hashlib
import json
import logging
import re
import secrets
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import jwt
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for access control"""
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"

class Permission(Enum):
    """System permissions"""
    # Task management
    CREATE_TASKS = "create_tasks"
    READ_TASKS = "read_tasks"
    UPDATE_TASKS = "update_tasks"
    DELETE_TASKS = "delete_tasks"
    EXECUTE_TASKS = "execute_tasks"

    # System management
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    VIEW_METRICS = "view_metrics"

    # Workflow management
    CREATE_WORKFLOWS = "create_workflows"
    READ_WORKFLOWS = "read_workflows"
    UPDATE_WORKFLOWS = "update_workflows"
    DELETE_WORKFLOWS = "delete_workflows"
    EXECUTE_WORKFLOWS = "execute_workflows"

    # AI model management
    MANAGE_MODELS = "manage_models"
    ACCESS_MODELS = "access_models"
    TRAIN_MODELS = "train_models"

    # Data access
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    EXPORT_DATA = "export_data"

class SecurityLevel(Enum):
    """Security levels for operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class User:
    """User account information"""
    user_id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    last_login: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Role:
    """Role definition with permissions"""
    role_id: str
    name: str
    description: str
    permissions: set[Permission] = field(default_factory=set)
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SecurityPolicy:
    """Security policy definition"""
    policy_id: str
    name: str
    description: str
    resource_pattern: str  # Regex pattern for resources
    actions: list[str]     # Allowed actions
    conditions: dict[str, Any] = field(default_factory=dict)  # Additional conditions
    priority: int = 100
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AuditLog:
    """Security audit log entry"""
    log_id: str
    user_id: str
    action: str
    resource: str
    result: str  # success, failure, denied
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

class AuthManager:
    """Comprehensive security and authentication manager"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get("database", {}).get("path", "auth_manager.db"))
        self._init_database()

        # Security configuration
        self.jwt_secret = config.get("security", {}).get("jwt_secret", self._generate_secret())
        self.jwt_algorithm = config.get("security", {}).get("jwt_algorithm", "HS256")
        self.jwt_expiry = config.get("security", {}).get("jwt_expiry", 3600)  # seconds
        self.refresh_token_expiry = config.get("security", {}).get("refresh_token_expiry", 86400)  # 24 hours

        # Password security
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.min_password_length = config.get("security", {}).get("min_password_length", 12)
        self.password_complexity = config.get("security", {}).get("password_complexity", True)

        # Rate limiting
        self.max_login_attempts = config.get("security", {}).get("max_login_attempts", 5)
        self.lockout_duration = config.get("security", {}).get("lockout_duration", 900)  # 15 minutes

        # Session management
        self.active_sessions: dict[str, dict[str, Any]] = {}
        self.failed_login_attempts: dict[str, list[datetime]] = defaultdict(list)
        self.locked_accounts: set[str] = set()

        # Security policies
        self.security_policies: list[SecurityPolicy] = []
        self._load_default_policies()

        # Background tasks
        self.background_tasks = []
        self._start_background_tasks()

        logger.info("Auth Manager initialized")

    def _init_database(self):
        """Initialize authentication database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    is_verified BOOLEAN NOT NULL DEFAULT 0,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    metadata TEXT
                )
            """)

            # Roles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    role_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    permissions TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            # Security policies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_policies (
                    policy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    resource_pattern TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    conditions TEXT,
                    priority INTEGER NOT NULL DEFAULT 100,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL
                )
            """)

            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    result TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # Refresh tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            conn.commit()
            conn.close()

            # Create default roles and admin user
            self._create_default_data()

            logger.info("Authentication database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize authentication database: {e}")
            raise

    def _create_default_data(self):
        """Create default roles and admin user"""
        try:
            # Create default roles
            admin_role = Role(
                role_id="admin",
                name="Administrator",
                description="Full system access",
                permissions=set(Permission),  # All permissions
                security_level=SecurityLevel.CRITICAL
            )

            operator_role = Role(
                role_id="operator",
                name="Operator",
                description="System operation and monitoring",
                permissions={
                    Permission.READ_TASKS, Permission.EXECUTE_TASKS,
                    Permission.READ_WORKFLOWS, Permission.EXECUTE_WORKFLOWS,
                    Permission.VIEW_LOGS, Permission.VIEW_METRICS,
                    Permission.READ_DATA, Permission.WRITE_DATA
                },
                security_level=SecurityLevel.HIGH
            )

            analyst_role = Role(
                role_id="analyst",
                name="Analyst",
                description="Data analysis and reporting",
                permissions={
                    Permission.READ_TASKS, Permission.READ_WORKFLOWS,
                    Permission.VIEW_METRICS, Permission.READ_DATA,
                    Permission.EXPORT_DATA
                },
                security_level=SecurityLevel.MEDIUM
            )

            viewer_role = Role(
                role_id="viewer",
                name="Viewer",
                description="Read-only access",
                permissions={
                    Permission.READ_TASKS, Permission.READ_WORKFLOWS,
                    Permission.VIEW_METRICS
                },
                security_level=SecurityLevel.LOW
            )

            # Store roles
            self._store_role(admin_role)
            self._store_role(operator_role)
            self._store_role(analyst_role)
            self._store_role(viewer_role)

            # Create admin user if none exists
            if not self._user_exists("admin"):
                admin_user = User(
                    user_id="admin",
                    username="admin",
                    email="admin@autonomous-system.com",
                    full_name="System Administrator",
                    role=UserRole.ADMIN,
                    is_verified=True
                )

                # Set default password (should be changed on first login)
                default_password = "Admin123!@#"
                self._store_user(admin_user, default_password)

                logger.info("Default admin user created")

        except Exception as e:
            logger.error(f"Failed to create default data: {e}")

    def _load_default_policies(self):
        """Load default security policies"""
        try:
            # Default policies
            policies = [
                SecurityPolicy(
                    policy_id="admin_full_access",
                    name="Admin Full Access",
                    description="Administrators have full access to all resources",
                    resource_pattern=".*",
                    actions=["*"],
                    priority=1000
                ),
                SecurityPolicy(
                    policy_id="task_management",
                    name="Task Management",
                    description="Task management operations",
                    resource_pattern="/tasks/.*",
                    actions=["GET", "POST", "PUT", "DELETE"],
                    conditions={"role": ["admin", "operator"]}
                ),
                SecurityPolicy(
                    policy_id="system_monitoring",
                    name="System Monitoring",
                    description="System monitoring and metrics access",
                    resource_pattern="/metrics|/status|/health",
                    actions=["GET"],
                    conditions={"role": ["admin", "operator", "analyst"]}
                ),
                SecurityPolicy(
                    policy_id="data_access",
                    name="Data Access Control",
                    description="Data access control policies",
                    resource_pattern="/data/.*",
                    actions=["GET", "POST", "PUT", "DELETE"],
                    conditions={"role": ["admin", "operator"], "security_level": "high"}
                )
            ]

            for policy in policies:
                self._store_policy(policy)

            logger.info("Default security policies loaded")

        except Exception as e:
            logger.error(f"Failed to load default policies: {e}")

    def _start_background_tasks(self):
        """Start background security tasks"""
        self.background_tasks = [
            asyncio.create_task(self._cleanup_expired_sessions()),
            asyncio.create_task(self._cleanup_audit_logs()),
            asyncio.create_task(self._monitor_security_threats())
        ]
        logger.info("Background security tasks started")

    # User management
    async def create_user(self, user_data: dict[str, Any], password: str) -> str | None:
        """Create a new user account"""
        try:
            # Validate user data
            if not self._validate_user_data(user_data):
                return None

            # Check if username or email already exists
            if self._user_exists(user_data["username"]) or self._email_exists(user_data["email"]):
                logger.warning(f"User already exists: {user_data['username']}")
                return None

            # Validate password
            if not self._validate_password(password):
                return None

            # Create user
            user = User(
                user_id=f"user_{int(time.time())}",
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=UserRole(user_data.get("role", "viewer"))
            )

            # Store user
            user_id = self._store_user(user, password)

            if user_id:
                logger.info(f"User created: {user.username}")
                return user_id

            return None

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    def _validate_user_data(self, user_data: dict[str, Any]) -> bool:
        """Validate user registration data"""
        try:
            required_fields = ["username", "email", "full_name"]
            for field in required_fields:
                if not user_data.get(field):
                    logger.error(f"Missing required field: {field}")
                    return False

            # Validate username format
            if not re.match(r"^[a-zA-Z0-9_]{3,20}$", user_data["username"]):
                logger.error("Invalid username format")
                return False

            # Validate email format
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", user_data["email"]):
                logger.error("Invalid email format")
                return False

            return True

        except Exception as e:
            logger.error(f"User data validation failed: {e}")
            return False

    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        try:
            if len(password) < self.min_password_length:
                logger.error(f"Password too short. Minimum length: {self.min_password_length}")
                return False

            if self.password_complexity:
                # Check complexity requirements
                if not re.search(r"[A-Z]", password):  # Uppercase
                    logger.error("Password must contain uppercase letters")
                    return False
                if not re.search(r"[a-z]", password):  # Lowercase
                    logger.error("Password must contain lowercase letters")
                    return False
                if not re.search(r"\d", password):  # Digits
                    logger.error("Password must contain digits")
                    return False
                if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):  # Special chars
                    logger.error("Password must contain special characters")
                    return False

            return True

        except Exception as e:
            logger.error(f"Password validation failed: {e}")
            return False

    def _user_exists(self, username: str) -> bool:
        """Check if user exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            exists = cursor.fetchone() is not None

            conn.close()
            return exists

        except Exception as e:
            logger.error(f"Failed to check user existence: {e}")
            return False

    def _email_exists(self, email: str) -> bool:
        """Check if email exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
            exists = cursor.fetchone() is not None

            conn.close()
            return exists

        except Exception as e:
            logger.error(f"Failed to check email existence: {e}")
            return False

    def _store_user(self, user: User, password: str) -> str | None:
        """Store user in database"""
        try:
            # Hash password
            password_hash = self.password_context.hash(password)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users
                (user_id, username, email, full_name, password_hash, role, is_active, is_verified,
                 last_login, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.user_id,
                user.username,
                user.email,
                user.full_name,
                password_hash,
                user.role.value,
                user.is_active,
                user.is_verified,
                user.last_login,
                user.created_at,
                user.updated_at,
                json.dumps(user.metadata)
            ))

            conn.commit()
            conn.close()

            return user.user_id

        except Exception as e:
            logger.error(f"Failed to store user: {e}")
            return None

    # Authentication
    async def authenticate_user(self, username: str, password: str, ip_address: str, user_agent: str) -> dict[str, Any] | None:
        """Authenticate user and return tokens"""
        try:
            # Check if account is locked
            if username in self.locked_accounts:
                logger.warning(f"Account locked: {username}")
                await self._log_audit_event(username, "login_attempt", "account_locked", ip_address, user_agent, "failure")
                return None

            # Check failed login attempts
            if self._is_account_locked(username):
                logger.warning(f"Account temporarily locked: {username}")
                await self._log_audit_event(username, "login_attempt", "account_locked", ip_address, user_agent, "failure")
                return None

            # Verify credentials
            user = self._verify_credentials(username, password)
            if not user:
                # Record failed attempt
                self._record_failed_login(username)
                await self._log_audit_event(username, "login_attempt", "invalid_credentials", ip_address, user_agent, "failure")
                return None

            # Check if user is active
            if not user.is_active:
                logger.warning(f"User account inactive: {username}")
                await self._log_audit_event(username, "login_attempt", "account_inactive", ip_address, user_agent, "failure")
                return None

            # Generate tokens
            access_token = self._create_access_token(user)
            refresh_token = await self._create_refresh_token(user)

            # Update last login
            self._update_last_login(user.user_id)

            # Clear failed login attempts
            self._clear_failed_logins(username)

            # Log successful login
            await self._log_audit_event(user.user_id, "login", "success", ip_address, user_agent, "success")

            logger.info(f"User authenticated: {username}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.jwt_expiry,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value
                }
            }

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None

    def _verify_credentials(self, username: str, password: str) -> User | None:
        """Verify user credentials"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, username, email, full_name, password_hash, role, is_active, is_verified,
                       last_login, created_at, updated_at, metadata
                FROM users WHERE username = ?
            """, (username,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            # Verify password
            if not self.password_context.verify(password, row[4]):
                return None

            # Create user object
            user = User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                full_name=row[3],
                role=UserRole(row[5]),
                is_active=bool(row[6]),
                is_verified=bool(row[7]),
                last_login=datetime.fromisoformat(row[8]) if row[8] else None,
                created_at=datetime.fromisoformat(row[9]),
                updated_at=datetime.fromisoformat(row[10]),
                metadata=json.loads(row[11]) if row[11] else {}
            )

            return user

        except Exception as e:
            logger.error(f"Credential verification failed: {e}")
            return None

    def _create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        try:
            payload = {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role.value,
                "exp": datetime.utcnow() + timedelta(seconds=self.jwt_expiry),
                "iat": datetime.utcnow()
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            return token

        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise

    async def _create_refresh_token(self, user: User) -> str:
        """Create refresh token"""
        try:
            # Generate random token
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Store in database
            expires_at = datetime.utcnow() + timedelta(seconds=self.refresh_token_expiry)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO refresh_tokens (token_id, user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"refresh_{int(time.time())}",
                user.user_id,
                token_hash,
                expires_at,
                datetime.utcnow()
            ))

            conn.commit()
            conn.close()

            return token

        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise

    # Authorization
    async def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Check if user has permission for resource and action"""
        try:
            # Get user role
            user = self._get_user_by_id(user_id)
            if not user:
                return False

            # Check security policies
            for policy in sorted(self.security_policies, key=lambda x: x.priority, reverse=True):
                if not policy.is_active:
                    continue

                # Check resource pattern
                if not re.match(policy.resource_pattern, resource):
                    continue

                # Check actions
                if "*" in policy.actions or action in policy.actions:
                    # Check conditions
                    if self._check_policy_conditions(policy, user):
                        return True

            # Check role-based permissions
            role = self._get_role_by_name(user.role.value)
            if role:
                # Check if role has the required permission
                # This is a simplified check - in practice, you'd map actions to permissions
                if user.role == UserRole.ADMIN:
                    return True

                # Check specific permissions based on action and resource
                if self._check_role_permissions(role, resource, action):
                    return True

            return False

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    def _check_policy_conditions(self, policy: SecurityPolicy, user: User) -> bool:
        """Check policy conditions"""
        try:
            conditions = policy.conditions

            # Check role condition
            if "role" in conditions:
                if user.role.value not in conditions["role"]:
                    return False

            # Check security level condition
            if "security_level" in conditions:
                user_role = self._get_role_by_name(user.role.value)
                if user_role and user_role.security_level.value != conditions["security_level"]:
                    return False

            return True

        except Exception as e:
            logger.error(f"Policy condition check failed: {e}")
            return False

    def _check_role_permissions(self, role: Role, resource: str, action: str) -> bool:
        """Check if role has required permissions"""
        try:
            # Map actions to permissions (simplified)
            action_permission_map = {
                "GET": Permission.READ_TASKS,
                "POST": Permission.CREATE_TASKS,
                "PUT": Permission.UPDATE_TASKS,
                "DELETE": Permission.DELETE_TASKS
            }

            required_permission = action_permission_map.get(action)
            if required_permission and required_permission in role.permissions:
                return True

            return False

        except Exception as e:
            logger.error(f"Role permission check failed: {e}")
            return False

    # Security monitoring
    def _record_failed_login(self, username: str):
        """Record failed login attempt"""
        try:
            current_time = datetime.now()
            self.failed_login_attempts[username].append(current_time)

            # Clean old attempts
            cutoff_time = current_time - timedelta(minutes=15)
            self.failed_login_attempts[username] = [
                attempt for attempt in self.failed_login_attempts[username]
                if attempt > cutoff_time
            ]

            # Check if account should be locked
            if len(self.failed_login_attempts[username]) >= self.max_login_attempts:
                self.locked_accounts.add(username)
                logger.warning(f"Account locked due to failed login attempts: {username}")

        except Exception as e:
            logger.error(f"Failed to record failed login: {e}")

    def _is_account_locked(self, username: str) -> bool:
        """Check if account is temporarily locked"""
        try:
            if username not in self.failed_login_attempts:
                return False

            attempts = self.failed_login_attempts[username]
            if len(attempts) < self.max_login_attempts:
                return False

            # Check if lockout period has passed
            last_attempt = max(attempts)
            if (datetime.now() - last_attempt).total_seconds() > self.lockout_duration:
                # Clear failed attempts
                self.failed_login_attempts[username].clear()
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check account lock status: {e}")
            return False

    def _clear_failed_logins(self, username: str):
        """Clear failed login attempts for user"""
        try:
            if username in self.failed_login_attempts:
                self.failed_login_attempts[username].clear()

            if username in self.locked_accounts:
                self.locked_accounts.remove(username)

        except Exception as e:
            logger.error(f"Failed to clear failed logins: {e}")

    # Audit logging
    async def _log_audit_event(self, user_id: str, action: str, resource: str, ip_address: str, user_agent: str, result: str):
        """Log security audit event"""
        try:
            log_entry = AuditLog(
                log_id=f"log_{int(time.time())}",
                user_id=user_id,
                action=action,
                resource=resource,
                result=result,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Store in database
            self._store_audit_log(log_entry)

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def _store_audit_log(self, log_entry: AuditLog):
        """Store audit log in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO audit_logs
                (log_id, user_id, action, resource, result, ip_address, user_agent, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_entry.log_id,
                log_entry.user_id,
                log_entry.action,
                log_entry.resource,
                log_entry.result,
                log_entry.ip_address,
                log_entry.user_agent,
                log_entry.timestamp,
                json.dumps(log_entry.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")

    # Background tasks
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions and tokens"""
        while True:
            try:
                # Clean up expired refresh tokens
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM refresh_tokens WHERE expires_at < ?", (datetime.utcnow(),))
                deleted_count = cursor.rowcount

                conn.commit()
                conn.close()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired refresh tokens")

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Session cleanup failed: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_audit_logs(self):
        """Clean up old audit logs"""
        while True:
            try:
                # Keep logs for 90 days
                cutoff_date = datetime.now() - timedelta(days=90)

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff_date,))
                deleted_count = cursor.rowcount

                conn.commit()
                conn.close()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old audit logs")

                await asyncio.sleep(86400)  # Check every day

            except Exception as e:
                logger.error(f"Audit log cleanup failed: {e}")
                await asyncio.sleep(86400)

    async def _monitor_security_threats(self):
        """Monitor for security threats"""
        while True:
            try:
                # Check for suspicious patterns
                current_time = datetime.now()

                # Check for rapid failed login attempts
                for username, attempts in self.failed_login_attempts.items():
                    if len(attempts) >= 3:
                        recent_attempts = [a for a in attempts if (current_time - a).total_seconds() < 300]
                        if len(recent_attempts) >= 3:
                            logger.warning(f"Potential brute force attack detected for user: {username}")
                            # Could trigger additional security measures here

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Security threat monitoring failed: {e}")
                await asyncio.sleep(300)

    # Utility methods
    def _generate_secret(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)

    def _get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, username, email, full_name, password_hash, role, is_active, is_verified,
                       last_login, created_at, updated_at, metadata
                FROM users WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                full_name=row[3],
                role=UserRole(row[5]),
                is_active=bool(row[6]),
                is_verified=bool(row[7]),
                last_login=datetime.fromisoformat(row[8]) if row[8] else None,
                created_at=datetime.fromisoformat(row[9]),
                updated_at=datetime.fromisoformat(row[10]),
                metadata=json.loads(row[11]) if row[11] else {}
            )

        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None

    def _get_role_by_name(self, role_name: str) -> Role | None:
        """Get role by name"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT role_id, name, description, permissions, security_level, created_at, updated_at
                FROM roles WHERE name = ?
            """, (role_name,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return Role(
                role_id=row[0],
                name=row[1],
                description=row[2],
                permissions=set(json.loads(row[3])),
                security_level=SecurityLevel(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6])
            )

        except Exception as e:
            logger.error(f"Failed to get role by name: {e}")
            return None

    def _store_role(self, role: Role):
        """Store role in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO roles
                (role_id, name, description, permissions, security_level, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                role.role_id,
                role.name,
                role.description,
                json.dumps(list(role.permissions)),
                role.security_level.value,
                role.created_at,
                role.updated_at
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store role: {e}")

    def _store_policy(self, policy: SecurityPolicy):
        """Store security policy in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO security_policies
                (policy_id, name, description, resource_pattern, actions, conditions, priority, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                policy.policy_id,
                policy.name,
                policy.description,
                policy.resource_pattern,
                json.dumps(policy.actions),
                json.dumps(policy.conditions),
                policy.priority,
                policy.is_active,
                policy.created_at
            ))

            conn.commit()
            conn.close()

            # Add to active policies
            self.security_policies.append(policy)

        except Exception as e:
            logger.error(f"Failed to store policy: {e}")

    def _update_last_login(self, user_id: str):
        """Update user's last login time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users SET last_login = ?, updated_at = ? WHERE user_id = ?
            """, (datetime.now(), datetime.now(), user_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update last login: {e}")

    # Public API methods
    async def get_user_info(self, user_id: str) -> dict[str, Any] | None:
        """Get user information"""
        try:
            user = self._get_user_by_id(user_id)
            if not user:
                return None

            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def get_security_status(self) -> dict[str, Any]:
        """Get security system status"""
        try:
            return {
                "status": "active",
                "locked_accounts": len(self.locked_accounts),
                "failed_login_attempts": sum(len(attempts) for attempts in self.failed_login_attempts.values()),
                "active_sessions": len(self.active_sessions),
                "security_policies": len(self.security_policies),
                "last_audit_log": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get security status: {e}")
            return {"status": "error", "error": str(e)}

    async def shutdown(self):
        """Shutdown the auth manager"""
        try:
            logger.info("Shutting down Auth Manager...")

            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

            logger.info("Auth Manager shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Example usage
async def main():
    """Example usage of the Auth Manager"""
    config = {
        "database": {"path": "auth_manager.db"},
        "security": {
            "jwt_secret": "your-secret-key-here",
            "jwt_expiry": 3600,
            "refresh_token_expiry": 86400,
            "min_password_length": 12,
            "password_complexity": True,
            "max_login_attempts": 5,
            "lockout_duration": 900
        }
    }

    auth_manager = AuthManager(config)

    # Create a test user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "analyst"
    }

    user_id = await auth_manager.create_user(user_data, "SecurePass123!")

    if user_id:
        print(f"User created: {user_id}")

        # Authenticate user
        auth_result = await auth_manager.authenticate_user(
            "testuser", "SecurePass123!", "192.168.1.100", "Test Browser"
        )

        if auth_result:
            print("Authentication successful!")
            print(f"Access token: {auth_result['access_token'][:50]}...")

            # Verify token
            payload = await auth_manager.verify_token(auth_result['access_token'])
            if payload:
                print(f"Token verified for user: {payload['username']}")

                # Check permissions
                has_permission = await auth_manager.check_permission(
                    payload['user_id'], "/tasks", "GET"
                )
                print(f"Has permission to read tasks: {has_permission}")

    # Get security status
    security_status = await auth_manager.get_security_status()
    print(f"Security status: {security_status}")

    # Shutdown
    await auth_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

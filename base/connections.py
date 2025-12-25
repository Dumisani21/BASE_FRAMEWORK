"""
BASE ORM Database Connection Management

Handles database connections, transactions, and connection pooling.
"""
import sqlite3
import threading
from typing import Optional, Any, Dict
from contextlib import contextmanager
from .exceptions import ConnectionError as ORMConnectionError


class Connection:
    """
    Database connection wrapper with transaction support.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._transaction_depth = 0
        
    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.row_factory = sqlite3.Row
                # Enable foreign key constraints
                self._conn.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error as e:
                raise ORMConnectionError(f"Failed to connect to database: {e}")
        return self._conn
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._transaction_depth = 0
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute SQL query.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            Cursor object
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor
        except sqlite3.Error as e:
            raise ORMConnectionError(f"Query execution failed: {e}\nSQL: {sql}")
    
    def executemany(self, sql: str, params_list: list) -> sqlite3.Cursor:
        """
        Execute SQL query with multiple parameter sets.
        
        Args:
            sql: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Cursor object
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            return cursor
        except sqlite3.Error as e:
            raise ORMConnectionError(f"Batch execution failed: {e}")
    
    def commit(self):
        """Commit current transaction."""
        if self._conn:
            self._conn.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        if self._conn:
            self._conn.rollback()
    
    def begin(self):
        """Begin transaction."""
        self._transaction_depth += 1
        if self._transaction_depth == 1:
            self.execute("BEGIN")
    
    @contextmanager
    def atomic(self):
        """
        Context manager for atomic transactions.
        
        Example:
            with db.atomic():
                user.save()
                profile.save()
        """
        self.begin()
        try:
            yield
            if self._transaction_depth == 1:
                self.commit()
            self._transaction_depth -= 1
        except Exception:
            self._transaction_depth -= 1
            if self._transaction_depth == 0:
                self.rollback()
            raise


class ConnectionManager:
    """
    Singleton connection manager with thread-local connections.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._connections: Dict[str, threading.local] = {}
        self._configs: Dict[str, str] = {}
        self._default_alias = 'default'
        self._initialized = True
    
    def configure(self, db_path: str, alias: str = 'default'):
        """
        Configure database connection.
        
        Args:
            db_path: Path to database file
            alias: Connection alias name
        """
        self._configs[alias] = db_path
        if alias not in self._connections:
            self._connections[alias] = threading.local()
    
    def get_connection(self, alias: str = 'default') -> Connection:
        """
        Get thread-local connection for alias.
        
        Args:
            alias: Connection alias name
            
        Returns:
            Connection object
        """
        if alias not in self._configs:
            raise ORMConnectionError(f"Database '{alias}' not configured")
        
        local = self._connections[alias]
        if not hasattr(local, 'connection') or local.connection is None:
            local.connection = Connection(self._configs[alias])
        
        return local.connection
    
    def close_all(self):
        """Close all connections."""
        for local in self._connections.values():
            if hasattr(local, 'connection') and local.connection:
                local.connection.close()


# Global connection manager instance
connection_manager = ConnectionManager()


class Database:
    """
    Database interface for ORM operations.
    
    Example:
        db = Database('myapp.db')
        db.connect()
    """
    
    def __init__(self, db_path: str, alias: str = 'default'):
        """
        Initialize database.
        
        Args:
            db_path: Path to database file
            alias: Connection alias
        """
        self.db_path = db_path
        self.alias = alias
        connection_manager.configure(db_path, alias)
    
    @property
    def connection(self) -> Connection:
        """Get current connection."""
        return connection_manager.get_connection(self.alias)
    
    def connect(self):
        """Establish connection."""
        self.connection.connect()
        print(f"Connected to database '{self.db_path}'")
    
    def close(self):
        """Close connection."""
        self.connection.close()
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query."""
        return self.connection.execute(sql, params)
    
    def commit(self):
        """Commit transaction."""
        self.connection.commit()
    
    def rollback(self):
        """Rollback transaction."""
        self.connection.rollback()
    
    @contextmanager
    def atomic(self):
        """Atomic transaction context manager."""
        with self.connection.atomic():
            yield

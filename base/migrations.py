"""
BASE ORM Migration System

Automatic migration generation and execution for schema changes.
"""
import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from .exceptions import MigrationError
from .connections import connection_manager


class Operation:
    """Base class for migration operations."""
    
    def apply(self, connection):
        """Apply this operation."""
        raise NotImplementedError
    
    def reverse(self, connection):
        """Reverse this operation."""
        raise NotImplementedError


class CreateTable(Operation):
    """Create a new table."""
    
    def __init__(self, table_name: str, fields: List[tuple]):
        """
        Args:
            table_name: Name of table to create
            fields: List of (column_name, column_definition) tuples
        """
        self.table_name = table_name
        self.fields = fields
    
    def apply(self, connection):
        fields_sql = ', '.join(f"{name} {definition}" for name, definition in self.fields)
        sql = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({fields_sql})"
        connection.execute(sql)
    
    def reverse(self, connection):
        sql = f"DROP TABLE IF EXISTS {self.table_name}"
        connection.execute(sql)


class DropTable(Operation):
    """Drop a table."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    def apply(self, connection):
        sql = f"DROP TABLE IF EXISTS {self.table_name}"
        connection.execute(sql)
    
    def reverse(self, connection):
        raise MigrationError("Cannot reverse DropTable operation without schema backup")


class AddColumn(Operation):
    """Add a column to existing table."""
    
    def __init__(self, table_name: str, column_name: str, column_definition: str):
        self.table_name = table_name
        self.column_name = column_name
        self.column_definition = column_definition
    
    def apply(self, connection):
        sql = f"ALTER TABLE {self.table_name} ADD COLUMN {self.column_name} {self.column_definition}"
        connection.execute(sql)
    
    def reverse(self, connection):
        # SQLite doesn't support DROP COLUMN before 3.35.0
        raise MigrationError("Cannot reverse AddColumn - SQLite limitation")


class Migration:
    """Represents a single migration."""
    
    def __init__(self, name: str, operations: List[Operation]):
        self.name = name
        self.operations = operations
        self.applied_at: Optional[datetime] = None
    
    def apply(self, connection):
        """Apply all operations in this migration."""
        for operation in self.operations:
            operation.apply(connection)
        connection.commit()
    
    def reverse(self, connection):
        """Reverse all operations in this migration."""
        for operation in reversed(self.operations):
            operation.reverse(connection)
        connection.commit()


class MigrationManager:
    """
    Manages database migrations.
    
    Example:
        manager = MigrationManager('migrations', 'default')
        manager.create_migrations_table()
        manager.migrate()
    """
    
    def __init__(self, migrations_dir: str = 'migrations', db_alias: str = 'default'):
        """
        Initialize migration manager.
        
        Args:
            migrations_dir: Directory to store migration files
            db_alias: Database connection alias
        """
        self.migrations_dir = migrations_dir
        self.db_alias = db_alias
        self._ensure_migrations_dir()
    
    def _ensure_migrations_dir(self):
        """Create migrations directory if it doesn't exist."""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
    
    def _get_connection(self):
        """Get database connection."""
        return connection_manager.get_connection(self.db_alias)
    
    def create_migrations_table(self):
        """Create table to track applied migrations."""
        sql = """
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self._get_connection().execute(sql)
        self._get_connection().commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        try:
            cursor = self._get_connection().execute(
                "SELECT name FROM _migrations ORDER BY id"
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []
    
    def mark_migration_applied(self, name: str):
        """Mark a migration as applied."""
        self._get_connection().execute(
            "INSERT INTO _migrations (name) VALUES (?)",
            (name,)
        )
        self._get_connection().commit()
    
    def mark_migration_unapplied(self, name: str):
        """Mark a migration as unapplied."""
        self._get_connection().execute(
            "DELETE FROM _migrations WHERE name = ?",
            (name,)
        )
        self._get_connection().commit()
    
    def generate_migration_name(self, description: str = "auto") -> str:
        """
        Generate migration filename with timestamp.
        
        Args:
            description: Short description of migration
            
        Returns:
            Migration filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{description}"
    
    def create_migration_file(self, name: str, operations: List[Operation]):
        """
        Create a migration file.
        
        Args:
            name: Migration name
            operations: List of operations
        """
        filepath = os.path.join(self.migrations_dir, f"{name}.py")
        
        # Generate Python code for operations
        ops_code = []
        for op in operations:
            if isinstance(op, CreateTable):
                fields_repr = repr(op.fields)
                ops_code.append(f"    CreateTable('{op.table_name}', {fields_repr}),")
            elif isinstance(op, DropTable):
                ops_code.append(f"    DropTable('{op.table_name}'),")
            elif isinstance(op, AddColumn):
                ops_code.append(
                    f"    AddColumn('{op.table_name}', '{op.column_name}', '{op.column_definition}'),"
                )
        
        content = f'''"""
Migration: {name}
Generated: {datetime.now().isoformat()}
"""
from base.migrations import CreateTable, DropTable, AddColumn


operations = [
{chr(10).join(ops_code)}
]
'''
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Created migration: {filepath}")
    
    def auto_detect_changes(self, models: List[Any]) -> List[Operation]:
        """
        Auto-detect schema changes from models.
        
        Args:
            models: List of Model classes
            
        Returns:
            List of operations needed
        """
        operations = []
        conn = self._get_connection()
        
        # Get existing tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '\\_%'"
        )
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        for model in models:
            table_name = model._table_name
            
            if table_name not in existing_tables:
                # New table needed
                fields = []
                for field in model._fields.values():
                    fields.append((field.get_db_column(), field.get_sql_definition().split(' ', 1)[1]))
                operations.append(CreateTable(table_name, fields))
            else:
                # Check for new columns
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {row[1] for row in cursor.fetchall()}
                
                for field in model._fields.values():
                    col_name = field.get_db_column()
                    if col_name not in existing_columns:
                        col_def = field.get_sql_definition().split(' ', 1)[1]
                        operations.append(AddColumn(table_name, col_name, col_def))
        
        return operations
    
    def makemigrations(self, models: List[Any], name: str = "auto"):
        """
        Generate migration file from model changes.
        
        Args:
            models: List of Model classes
            name: Migration description
        """
        operations = self.auto_detect_changes(models)
        
        if not operations:
            print("No changes detected")
            return
        
        migration_name = self.generate_migration_name(name)
        self.create_migration_file(migration_name, operations)
        print(f"Created migration '{migration_name}' with {len(operations)} operations")
    
    def migrate(self):
        """Apply all pending migrations."""
        self.create_migrations_table()
        applied = set(self.get_applied_migrations())
        
        # Get all migration files
        migration_files = sorted([
            f[:-3] for f in os.listdir(self.migrations_dir)
            if f.endswith('.py') and not f.startswith('__')
        ])
        
        pending = [m for m in migration_files if m not in applied]
        
        if not pending:
            print("No pending migrations")
            return
        
        print(f"Applying {len(pending)} migrations...")
        
        for migration_name in pending:
            print(f"  Applying {migration_name}...")
            
            # Load migration module
            filepath = os.path.join(self.migrations_dir, f"{migration_name}.py")
            namespace = {}
            namespace['CreateTable'] = CreateTable
            namespace['DropTable'] = DropTable
            namespace['AddColumn'] = AddColumn
            
            with open(filepath, 'r') as f:
                exec(f.read(), namespace)
            
            operations = namespace.get('operations', [])
            migration = Migration(migration_name, operations)
            
            try:
                migration.apply(self._get_connection())
                self.mark_migration_applied(migration_name)
                print(f"  ✓ Applied {migration_name}")
            except Exception as e:
                print(f"  ✗ Failed to apply {migration_name}: {e}")
                raise MigrationError(f"Migration failed: {e}")
        
        print("All migrations applied successfully")
    
    def rollback(self, steps: int = 1):
        """
        Rollback last N migrations.
        
        Args:
            steps: Number of migrations to rollback
        """
        applied = self.get_applied_migrations()
        
        if not applied:
            print("No migrations to rollback")
            return
        
        to_rollback = applied[-steps:]
        
        print(f"Rolling back {len(to_rollback)} migrations...")
        
        for migration_name in reversed(to_rollback):
            print(f"  Rolling back {migration_name}...")
            
            # Load migration module
            filepath = os.path.join(self.migrations_dir, f"{migration_name}.py")
            namespace = {}
            namespace['CreateTable'] = CreateTable
            namespace['DropTable'] = DropTable
            namespace['AddColumn'] = AddColumn
            
            with open(filepath, 'r') as f:
                exec(f.read(), namespace)
            
            operations = namespace.get('operations', [])
            migration = Migration(migration_name, operations)
            
            try:
                migration.reverse(self._get_connection())
                self.mark_migration_unapplied(migration_name)
                print(f"  ✓ Rolled back {migration_name}")
            except Exception as e:
                print(f"  ✗ Failed to rollback {migration_name}: {e}")
                raise MigrationError(f"Rollback failed: {e}")
        
        print("Rollback completed")

"""
BASE ORM CLI Tool

Command-line interface for managing migrations and database operations.
"""
import sys
import os
import argparse
from .migrations import MigrationManager
from .connections import Database


def makemigrations(args):
    """Generate migration files from model changes."""
    # Import models from user's project
    sys.path.insert(0, os.getcwd())
    
    try:
        # Try to import models module
        if args.models_module:
            module = __import__(args.models_module, fromlist=[''])
            models = [
                getattr(module, name) for name in dir(module)
                if hasattr(getattr(module, name), '_fields')
            ]
        else:
            print("Error: Please specify --models-module")
            return
        
        manager = MigrationManager(args.migrations_dir, args.database)
        manager.makemigrations(models, args.name)
    except ImportError as e:
        print(f"Error importing models: {e}")
        sys.exit(1)


def migrate(args):
    """Apply pending migrations."""
    manager = MigrationManager(args.migrations_dir, args.database)
    manager.migrate()


def rollback(args):
    """Rollback last N migrations."""
    manager = MigrationManager(args.migrations_dir, args.database)
    manager.rollback(args.steps)


def shell(args):
    """Start interactive Python shell with models loaded."""
    import code
    
    # Import models
    sys.path.insert(0, os.getcwd())
    namespace = {'__name__': '__main__'}
    
    if args.models_module:
        try:
            module = __import__(args.models_module, fromlist=[''])
            namespace.update({
                name: getattr(module, name)
                for name in dir(module)
                if not name.startswith('_')
            })
            print(f"Imported models from {args.models_module}")
        except ImportError as e:
            print(f"Warning: Could not import models: {e}")
    
    # Import BASE ORM
    from base import Model, Database, CharField, IntegerField
    namespace.update({
        'Model': Model,
        'Database': Database,
        'CharField': CharField,
        'IntegerField': IntegerField,
    })
    
    print("BASE ORM Interactive Shell")
    print("Available: Model, Database, CharField, IntegerField")
    code.interact(local=namespace, banner='')


def dbshell(args):
    """Start SQLite shell for database."""
    import subprocess
    
    db_path = args.database_path or 'db.sqlite3'
    
    try:
        subprocess.run(['sqlite3', db_path])
    except FileNotFoundError:
        print("Error: sqlite3 command not found. Please install SQLite.")
        sys.exit(1)


def inspectdb(args):
    """Inspect database and generate model code."""
    db = Database(args.database_path)
    db.connect()
    
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '\\_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    
    print("# Generated models from database\n")
    print("from base import Model, CharField, IntegerField, TextField, FloatField\n\n")
    
    for table in tables:
        # Get table info
        cursor = db.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Generate class name
        class_name = ''.join(word.capitalize() for word in table.split('_'))
        if class_name.endswith('s'):
            class_name = class_name[:-1]
        
        print(f"class {class_name}(Model):")
        print(f"    _table_name = '{table}'")
        print()
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_pk = col[5] == 1
            not_null = col[3] == 1
            
            # Map SQL type to field type
            if 'INT' in col_type.upper():
                field_type = 'IntegerField'
            elif 'REAL' in col_type.upper() or 'FLOAT' in col_type.upper():
                field_type = 'FloatField'
            elif 'TEXT' in col_type.upper():
                field_type = 'TextField'
            else:
                field_type = 'CharField'
            
            # Build field definition
            field_args = []
            if is_pk:
                field_args.append('primary_key=True')
            if not not_null:
                field_args.append('null=True')
            
            args_str = ', '.join(field_args) if field_args else ''
            print(f"    {col_name} = {field_type}({args_str})")
        
        print("\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='BASE ORM Management Tool',
        prog='base'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # makemigrations command
    make_parser = subparsers.add_parser(
        'makemigrations',
        help='Generate migration files from model changes'
    )
    make_parser.add_argument(
        '--models-module',
        default='models',
        help='Python module containing models (default: models)'
    )
    make_parser.add_argument(
        '--name',
        default='auto',
        help='Migration name (default: auto)'
    )
    make_parser.add_argument(
        '--migrations-dir',
        default='migrations',
        help='Migrations directory (default: migrations)'
    )
    make_parser.add_argument(
        '--database',
        default='default',
        help='Database alias (default: default)'
    )
    make_parser.set_defaults(func=makemigrations)
    
    # migrate command
    migrate_parser = subparsers.add_parser(
        'migrate',
        help='Apply pending migrations'
    )
    migrate_parser.add_argument(
        '--migrations-dir',
        default='migrations',
        help='Migrations directory (default: migrations)'
    )
    migrate_parser.add_argument(
        '--database',
        default='default',
        help='Database alias (default: default)'
    )
    migrate_parser.set_defaults(func=migrate)
    
    # rollback command
    rollback_parser = subparsers.add_parser(
        'rollback',
        help='Rollback last N migrations'
    )
    rollback_parser.add_argument(
        '--steps',
        type=int,
        default=1,
        help='Number of migrations to rollback (default: 1)'
    )
    rollback_parser.add_argument(
        '--migrations-dir',
        default='migrations',
        help='Migrations directory (default: migrations)'
    )
    rollback_parser.add_argument(
        '--database',
        default='default',
        help='Database alias (default: default)'
    )
    rollback_parser.set_defaults(func=rollback)
    
    # shell command
    shell_parser = subparsers.add_parser(
        'shell',
        help='Start interactive Python shell'
    )
    shell_parser.add_argument(
        '--models-module',
        default='models',
        help='Python module containing models (default: models)'
    )
    shell_parser.set_defaults(func=shell)
    
    # dbshell command
    dbshell_parser = subparsers.add_parser(
        'dbshell',
        help='Start SQLite database shell'
    )
    dbshell_parser.add_argument(
        '--database-path',
        help='Path to database file'
    )
    dbshell_parser.set_defaults(func=dbshell)
    
    # inspectdb command
    inspect_parser = subparsers.add_parser(
        'inspectdb',
        help='Generate models from existing database'
    )
    inspect_parser.add_argument(
        'database_path',
        help='Path to database file'
    )
    inspect_parser.set_defaults(func=inspectdb)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()

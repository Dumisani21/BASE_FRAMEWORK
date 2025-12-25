"""
BASE ORM Framework v3.0.0

A professional, production-ready ORM for Python with SQLite support.

Example:
    from base import Model, CharField, IntegerField, Database
    
    # Define model
    class User(Model):
        id = IntegerField(primary_key=True, auto_increment=True)
        username = CharField(max_length=50, unique=True)
        email = CharField(max_length=100)
    
    # Connect database
    db = Database('myapp.db')
    db.connect()
    
    # Create table
    User._create_table()
    
    # Create and save
    user = User(username='john', email='john@example.com')
    user.save()
    
    # Query
    users = User.objects.filter(username__contains='john')
    user = User.objects.get(id=1)
"""

__version__ = '3.0.0'
__author__ = 'BASE ORM Contributors'

# Core ORM components
from .models import Model, Manager
from .fields import (
    Field,
    IntegerField,
    CharField,
    TextField,
    FloatField,
    BooleanField,
    DateTimeField,
    JSONField,
    ForeignKey,
)
from .query import QuerySet
from .connections import Database, Connection, ConnectionManager, connection_manager
from .migrations import (
    MigrationManager,
    Migration,
    CreateTable,
    DropTable,
    AddColumn,
)
from .exceptions import (
    BaseORMException,
    DoesNotExist,
    MultipleObjectsReturned,
    ValidationError,
    IntegrityError,
    MigrationError,
    ConnectionError,
    FieldError,
    QueryError,
)

# Backward compatibility - import legacy Database class
from .base import Database as LegacyDatabase

__all__ = [
    # Version
    '__version__',
    
    # Models
    'Model',
    'Manager',
    
    # Fields
    'Field',
    'IntegerField',
    'CharField',
    'TextField',
    'FloatField',
    'BooleanField',
    'DateTimeField',
    'JSONField',
    'ForeignKey',
    
    # Query
    'QuerySet',
    
    # Database
    'Database',
    'Connection',
    'ConnectionManager',
    'connection_manager',
    
    # Migrations
    'MigrationManager',
    'Migration',
    'CreateTable',
    'DropTable',
    'AddColumn',
    
    # Exceptions
    'BaseORMException',
    'DoesNotExist',
    'MultipleObjectsReturned',
    'ValidationError',
    'IntegrityError',
    'MigrationError',
    'ConnectionError',
    'FieldError',
    'QueryError',
    
    # Legacy
    'LegacyDatabase',
]

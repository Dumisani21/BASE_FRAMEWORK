"""
BASE ORM Field Types

Field classes for defining model attributes with type validation and SQL mapping.
"""
from typing import Any, Optional, Callable, List
from datetime import datetime
import json


class Field:
    """
    Base field class for all model fields.
    
    Args:
        primary_key: Whether this field is the primary key
        unique: Whether values must be unique
        null: Whether NULL values are allowed
        default: Default value or callable
        db_column: Custom database column name
        validators: List of validator functions
    """
    
    sql_type = "TEXT"
    
    def __init__(
        self,
        primary_key: bool = False,
        unique: bool = False,
        null: bool = True,
        default: Any = None,
        db_column: Optional[str] = None,
        validators: Optional[List[Callable]] = None,
    ):
        self.primary_key = primary_key
        self.unique = unique
        self.null = null
        self.default = default
        self.db_column = db_column
        self.validators = validators or []
        self.name = None  # Set by metaclass
        self.model = None  # Set by metaclass
        
    def get_db_column(self) -> str:
        """Get the database column name."""
        return self.db_column or self.name
    
    def get_default(self) -> Any:
        """Get the default value, calling it if it's callable."""
        if callable(self.default):
            return self.default()
        return self.default
    
    def to_python(self, value: Any) -> Any:
        """Convert database value to Python value."""
        if value is None:
            return None
        return value
    
    def to_db(self, value: Any) -> Any:
        """Convert Python value to database value."""
        if value is None:
            return None
        return value
    
    def validate(self, value: Any) -> None:
        """
        Validate the field value.
        
        Raises:
            ValidationError: If validation fails
        """
        from .exceptions import ValidationError
        
        # Check null constraint
        if value is None and not self.null and not self.primary_key:
            raise ValidationError(f"{self.name} cannot be null")
        
        # Run custom validators
        for validator in self.validators:
            validator(value)
    
    def get_sql_definition(self) -> str:
        """Get SQL column definition."""
        parts = [self.get_db_column(), self.sql_type]
        
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        if not self.null and not self.primary_key:
            parts.append("NOT NULL")
        if self.default is not None and not callable(self.default):
            parts.append(f"DEFAULT {self.to_db(self.default)}")
            
        return " ".join(parts)


class IntegerField(Field):
    """Integer field."""
    
    sql_type = "INTEGER"
    
    def __init__(self, auto_increment: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_increment = auto_increment
        
    def to_python(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        return int(value)
    
    def get_sql_definition(self) -> str:
        parts = [self.get_db_column(), self.sql_type]
        
        if self.primary_key:
            if self.auto_increment:
                parts.append("PRIMARY KEY AUTOINCREMENT")
            else:
                parts.append("PRIMARY KEY")
        else:
            if self.unique:
                parts.append("UNIQUE")
            if not self.null:
                parts.append("NOT NULL")
            if self.default is not None and not callable(self.default):
                parts.append(f"DEFAULT {self.default}")
                
        return " ".join(parts)


class CharField(Field):
    """Character/string field with max length."""
    
    sql_type = "VARCHAR"
    
    def __init__(self, max_length: int = 255, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        
    def to_python(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        from .exceptions import ValidationError
        
        if value is not None and len(str(value)) > self.max_length:
            raise ValidationError(
                f"{self.name} exceeds max length of {self.max_length}"
            )
    
    def get_sql_definition(self) -> str:
        parts = [self.get_db_column(), f"{self.sql_type}({self.max_length})"]
        
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        if not self.null and not self.primary_key:
            parts.append("NOT NULL")
        if self.default is not None and not callable(self.default):
            parts.append(f"DEFAULT '{self.default}'")
            
        return " ".join(parts)


class TextField(Field):
    """Large text field."""
    
    sql_type = "TEXT"
    
    def to_python(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)


class FloatField(Field):
    """Floating point number field."""
    
    sql_type = "REAL"
    
    def to_python(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        return float(value)


class BooleanField(Field):
    """Boolean field (stored as INTEGER 0/1)."""
    
    sql_type = "INTEGER"
    
    def to_python(self, value: Any) -> Optional[bool]:
        if value is None:
            return None
        return bool(value)
    
    def to_db(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        return 1 if value else 0


class DateTimeField(Field):
    """DateTime field."""
    
    sql_type = "TIMESTAMP"
    
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        
        if auto_now or auto_now_add:
            self.default = datetime.now
    
    def to_python(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        # Parse ISO format string
        return datetime.fromisoformat(value)
    
    def to_db(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)


class JSONField(Field):
    """JSON field (stored as TEXT)."""
    
    sql_type = "TEXT"
    
    def to_python(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    def to_db(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)


class ForeignKey(Field):
    """
    Foreign key relationship field.
    
    Args:
        to: Related model class or string name
        on_delete: Behavior when referenced object is deleted
        related_name: Name for reverse relation
    """
    
    sql_type = "INTEGER"
    
    def __init__(
        self,
        to: Any,
        on_delete: str = "CASCADE",
        related_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.to = to
        self.on_delete = on_delete
        self.related_name = related_name
        
    def get_sql_definition(self) -> str:
        parts = [self.get_db_column(), self.sql_type]
        
        if not self.null:
            parts.append("NOT NULL")
            
        # Get referenced table name
        if isinstance(self.to, str):
            ref_table = self.to.lower()
        else:
            ref_table = getattr(self.to, '_table_name', self.to.__name__.lower())
        
        parts.append(f"REFERENCES {ref_table}(id) ON DELETE {self.on_delete}")
        
        return " ".join(parts)

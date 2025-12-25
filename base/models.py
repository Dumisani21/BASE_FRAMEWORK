"""
BASE ORM Model Base Class

Provides the Model base class with metaclass for automatic table mapping and ORM functionality.
"""
from typing import Any, Dict, Optional, Type, ClassVar, List
from .fields import Field
from .query import QuerySet
from .connections import connection_manager
from .utils import camel_to_snake, pluralize
from .exceptions import ValidationError, FieldError
from datetime import datetime


class ModelMeta(type):
    """
    Metaclass for Model that processes field definitions and sets up table mapping.
    """
    
    def __new__(mcs, name, bases, attrs, **kwargs):
        # Don't process the Model base class itself
        if name == 'Model' and not bases:
            return super().__new__(mcs, name, bases, attrs)
        
        # Extract fields from class attributes
        fields = {}
        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                fields[key] = value
                value.name = key
        
        # Store fields in class
        attrs['_fields'] = fields
        
        # Determine table name
        if '_table_name' not in attrs:
            attrs['_table_name'] = pluralize(camel_to_snake(name))
        
        # Determine database alias
        if '_db_alias' not in attrs:
            attrs['_db_alias'] = 'default'
        
        # Create the class
        cls = super().__new__(mcs, name, bases, attrs)
        
        # Set model reference on fields
        for field in fields.values():
            field.model = cls
        
        # Create DoesNotExist exception for this model
        cls.DoesNotExist = type(
            f'{name}DoesNotExist',
            (Exception,),
            {'__module__': cls.__module__}
        )
        
        # Create MultipleObjectsReturned exception
        cls.MultipleObjectsReturned = type(
            f'{name}MultipleObjectsReturned',
            (Exception,),
            {'__module__': cls.__module__}
        )
        
        return cls


class Manager:
    """
    Manager class that provides QuerySet interface.
    """
    
    def __init__(self, model):
        self.model = model
    
    def get_queryset(self) -> QuerySet:
        """Get a new QuerySet for this model."""
        return QuerySet(self.model)
    
    def all(self) -> QuerySet:
        """Return all objects."""
        return self.get_queryset()
    
    def filter(self, **kwargs) -> QuerySet:
        """Filter objects."""
        return self.get_queryset().filter(**kwargs)
    
    def exclude(self, **kwargs) -> QuerySet:
        """Exclude objects."""
        return self.get_queryset().exclude(**kwargs)
    
    def get(self, **kwargs) -> Any:
        """Get single object."""
        return self.get_queryset().get(**kwargs)
    
    def create(self, **kwargs) -> Any:
        """Create and save new object."""
        instance = self.model(**kwargs)
        instance.save()
        return instance
    
    def count(self) -> int:
        """Count all objects."""
        return self.get_queryset().count()
    
    def exists(self) -> bool:
        """Check if any objects exist."""
        return self.get_queryset().exists()
    
    def first(self) -> Optional[Any]:
        """Get first object."""
        return self.get_queryset().first()
    
    def last(self) -> Optional[Any]:
        """Get last object."""
        return self.get_queryset().last()
    
    def order_by(self, *fields) -> QuerySet:
        """Order objects by fields."""
        return self.get_queryset().order_by(*fields)
    
    def values(self, *fields) -> QuerySet:
        """Return dictionaries instead of model instances."""
        return self.get_queryset().values(*fields)
    
    def values_list(self, *fields, **kwargs) -> List:
        """Return tuples of values."""
        return self.get_queryset().values_list(*fields, **kwargs)
    
    def distinct(self) -> QuerySet:
        """Return only distinct results."""
        return self.get_queryset().distinct()


class Model(metaclass=ModelMeta):
    """
    Base class for all ORM models.
    
    Example:
        class User(Model):
            id = IntegerField(primary_key=True, auto_increment=True)
            username = CharField(max_length=50, unique=True)
            email = CharField(max_length=100)
            created_at = DateTimeField(auto_now_add=True)
        
        # Create
        user = User(username='john', email='john@example.com')
        user.save()
        
        # Query
        users = User.objects.filter(username__contains='john')
        user = User.objects.get(id=1)
    """
    
    _fields: ClassVar[Dict[str, Field]] = {}
    _table_name: ClassVar[str] = ''
    _db_alias: ClassVar[str] = 'default'
    
    objects: ClassVar[Manager]
    
    def __init__(self, **kwargs):
        """
        Initialize model instance.
        
        Args:
            **kwargs: Field values
        """
        self._loaded_from_db = False
        
        # Set field values
        for field_name, field in self._fields.items():
            if field_name in kwargs:
                setattr(self, field_name, kwargs[field_name])
            elif field.default is not None:
                setattr(self, field_name, field.get_default())
            else:
                setattr(self, field_name, None)
    
    def __init_subclass__(cls, **kwargs):
        """Called when a subclass is created."""
        super().__init_subclass__(**kwargs)
        # Attach manager to class
        cls.objects = Manager(cls)
    
    @classmethod
    def _get_connection(cls):
        """Get database connection for this model."""
        return connection_manager.get_connection(cls._db_alias)
    
    @classmethod
    def _create_table(cls):
        """Create database table for this model."""
        fields_sql = []
        for field in cls._fields.values():
            fields_sql.append(field.get_sql_definition())
        
        sql = f"CREATE TABLE IF NOT EXISTS {cls._table_name} ({', '.join(fields_sql)})"
        cls._get_connection().execute(sql)
        cls._get_connection().commit()
        print(f"Table '{cls._table_name}' created successfully")
    
    @classmethod
    def _drop_table(cls):
        """Drop database table for this model."""
        sql = f"DROP TABLE IF EXISTS {cls._table_name}"
        cls._get_connection().execute(sql)
        cls._get_connection().commit()
        print(f"Table '{cls._table_name}' dropped successfully")
    
    def _get_pk_field(self) -> Optional[Field]:
        """Get primary key field."""
        for field in self._fields.values():
            if field.primary_key:
                return field
        return None
    
    def _get_pk_value(self) -> Any:
        """Get primary key value."""
        pk_field = self._get_pk_field()
        if pk_field:
            return getattr(self, pk_field.name, None)
        return None
    
    def clean(self):
        """
        Hook for custom model validation.
        Override in subclasses to add custom validation logic.
        
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    def validate(self):
        """
        Validate all fields.
        
        Raises:
            ValidationError: If validation fails
        """
        errors = {}
        
        for field_name, field in self._fields.items():
            value = getattr(self, field_name, None)
            try:
                field.validate(value)
            except ValidationError as e:
                errors[field_name] = str(e)
        
        # Run custom validation
        try:
            self.clean()
        except ValidationError as e:
            if hasattr(e, 'errors'):
                errors.update(e.errors)
            else:
                errors['__all__'] = str(e)
        
        if errors:
            raise ValidationError("Validation failed", errors=errors)
    
    def save(self, validate: bool = True):
        """
        Save model instance to database.
        
        Args:
            validate: Whether to run validation before saving
        """
        if validate:
            self.validate()
        
        # Update auto_now fields
        for field_name, field in self._fields.items():
            if hasattr(field, 'auto_now') and field.auto_now:
                setattr(self, field_name, datetime.now())
        
        pk_field = self._get_pk_field()
        pk_value = self._get_pk_value()
        
        if pk_value is not None and self._loaded_from_db:
            # UPDATE existing record
            self._update()
        else:
            # INSERT new record
            self._insert()
    
    def _insert(self):
        """Insert new record."""
        fields_to_insert = []
        values = []
        
        pk_field = self._get_pk_field()
        
        for field_name, field in self._fields.items():
            # Skip auto-increment primary keys
            if field.primary_key and hasattr(field, 'auto_increment') and field.auto_increment:
                continue
            
            value = getattr(self, field_name, None)
            if value is not None or not field.null:
                fields_to_insert.append(field.get_db_column())
                values.append(field.to_db(value))
        
        placeholders = ', '.join('?' * len(values))
        fields_str = ', '.join(fields_to_insert)
        
        sql = f"INSERT INTO {self._table_name} ({fields_str}) VALUES ({placeholders})"
        cursor = self._get_connection().execute(sql, tuple(values))
        self._get_connection().commit()
        
        # Set primary key if auto-increment
        if pk_field and hasattr(pk_field, 'auto_increment') and pk_field.auto_increment:
            setattr(self, pk_field.name, cursor.lastrowid)
        
        self._loaded_from_db = True
        print(f"Inserted {self.__class__.__name__} with {pk_field.name}={self._get_pk_value()}")
    
    def _update(self):
        """Update existing record."""
        pk_field = self._get_pk_field()
        if not pk_field:
            raise FieldError("Cannot update model without primary key")
        
        pk_value = self._get_pk_value()
        if pk_value is None:
            raise ValueError("Cannot update model with null primary key")
        
        set_parts = []
        values = []
        
        for field_name, field in self._fields.items():
            if field.primary_key:
                continue
            
            value = getattr(self, field_name, None)
            set_parts.append(f"{field.get_db_column()} = ?")
            values.append(field.to_db(value))
        
        values.append(pk_field.to_db(pk_value))
        
        sql = f"UPDATE {self._table_name} SET {', '.join(set_parts)} WHERE {pk_field.get_db_column()} = ?"
        cursor = self._get_connection().execute(sql, tuple(values))
        self._get_connection().commit()
        print(f"Updated {self.__class__.__name__} with {pk_field.name}={pk_value}")
    
    def delete(self):
        """Delete this instance from database."""
        pk_field = self._get_pk_field()
        if not pk_field:
            raise FieldError("Cannot delete model without primary key")
        
        pk_value = self._get_pk_value()
        if pk_value is None:
            raise ValueError("Cannot delete model with null primary key")
        
        sql = f"DELETE FROM {self._table_name} WHERE {pk_field.get_db_column()} = ?"
        cursor = self._get_connection().execute(sql, (pk_field.to_db(pk_value),))
        self._get_connection().commit()
        print(f"Deleted {self.__class__.__name__} with {pk_field.name}={pk_value}")
    
    def refresh(self):
        """Reload instance from database."""
        pk_field = self._get_pk_field()
        if not pk_field:
            raise FieldError("Cannot refresh model without primary key")
        
        pk_value = self._get_pk_value()
        if pk_value is None:
            raise ValueError("Cannot refresh model with null primary key")
        
        instance = self.__class__.objects.get(**{pk_field.name: pk_value})
        
        # Copy field values
        for field_name in self._fields:
            setattr(self, field_name, getattr(instance, field_name))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        result = {}
        for field_name, field in self._fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
                # Convert datetime to ISO format
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                else:
                    result[field_name] = value
            else:
                result[field_name] = None
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Model':
        """Create model instance from dictionary."""
        return cls(**data)
    
    def __repr__(self):
        """String representation."""
        pk_field = self._get_pk_field()
        if pk_field:
            pk_value = self._get_pk_value()
            return f"<{self.__class__.__name__}: {pk_field.name}={pk_value}>"
        return f"<{self.__class__.__name__}>"
    
    def __str__(self):
        """String representation."""
        return self.__repr__()

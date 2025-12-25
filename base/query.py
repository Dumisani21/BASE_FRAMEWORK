"""
BASE ORM Query Builder

Chainable query interface for building and executing database queries.
"""
import sqlite3
from typing import Any, List, Optional, Dict, Union, Tuple
from .utils import parse_lookup, get_operator_sql, format_value_for_operator, escape_sql_identifier
from .exceptions import DoesNotExist, MultipleObjectsReturned, QueryError


class QuerySet:
    """
    Lazy query builder that constructs and executes SQL queries.
    
    Example:
        users = User.objects.filter(age__gte=18).order_by('-created_at')
        user = User.objects.get(id=1)
    """
    
    def __init__(self, model):
        """
        Initialize QuerySet.
        
        Args:
            model: Model class this QuerySet is for
        """
        self.model = model
        self._filters: List[Tuple[str, str, Any]] = []
        self._excludes: List[Tuple[str, str, Any]] = []
        self._order_by: List[str] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._select_related: List[str] = []
        self._distinct: bool = False
        self._values_fields: Optional[List[str]] = None
        self._cache: Optional[List] = None
    
    def _clone(self) -> 'QuerySet':
        """Create a copy of this QuerySet."""
        qs = QuerySet(self.model)
        qs._filters = self._filters.copy()
        qs._excludes = self._excludes.copy()
        qs._order_by = self._order_by.copy()
        qs._limit = self._limit
        qs._offset = self._offset
        qs._select_related = self._select_related.copy()
        qs._distinct = self._distinct
        qs._values_fields = self._values_fields
        return qs
    
    def filter(self, **kwargs) -> 'QuerySet':
        """
        Filter QuerySet by conditions.
        
        Args:
            **kwargs: Field lookups (e.g., age__gte=18)
            
        Returns:
            New QuerySet with filters applied
        """
        qs = self._clone()
        for lookup, value in kwargs.items():
            field_name, operator = parse_lookup(lookup)
            qs._filters.append((field_name, operator, value))
        return qs
    
    def exclude(self, **kwargs) -> 'QuerySet':
        """
        Exclude records matching conditions.
        
        Args:
            **kwargs: Field lookups
            
        Returns:
            New QuerySet with exclusions applied
        """
        qs = self._clone()
        for lookup, value in kwargs.items():
            field_name, operator = parse_lookup(lookup)
            qs._excludes.append((field_name, operator, value))
        return qs
    
    def order_by(self, *fields) -> 'QuerySet':
        """
        Order results by fields.
        
        Args:
            *fields: Field names (prefix with '-' for descending)
            
        Returns:
            New QuerySet with ordering applied
        """
        qs = self._clone()
        qs._order_by = list(fields)
        return qs
    
    def limit(self, n: int) -> 'QuerySet':
        """Limit number of results."""
        qs = self._clone()
        qs._limit = n
        return qs
    
    def offset(self, n: int) -> 'QuerySet':
        """Skip first n results."""
        qs = self._clone()
        qs._offset = n
        return qs
    
    def distinct(self) -> 'QuerySet':
        """Return only distinct results."""
        qs = self._clone()
        qs._distinct = True
        return qs
    
    def values(self, *fields) -> 'QuerySet':
        """Return dictionaries instead of model instances."""
        qs = self._clone()
        qs._values_fields = list(fields) if fields else None
        return qs
    
    def values_list(self, *fields, flat: bool = False) -> List:
        """Return tuples of values instead of model instances."""
        results = []
        for row in self._execute():
            if flat and len(fields) == 1:
                results.append(row[fields[0]])
            else:
                results.append(tuple(row[f] for f in fields))
        return results
    
    def select_related(self, *fields) -> 'QuerySet':
        """Eagerly load related objects (for ForeignKey)."""
        qs = self._clone()
        qs._select_related.extend(fields)
        return qs
    
    def _build_where_clause(self) -> Tuple[str, List[Any]]:
        """Build WHERE clause from filters and exclusions."""
        conditions = []
        params = []
        
        # Add filter conditions
        for field_name, operator, value in self._filters:
            sql_op = get_operator_sql(operator)
            
            if operator == 'isnull':
                if value:
                    conditions.append(f"{field_name} IS NULL")
                else:
                    conditions.append(f"{field_name} IS NOT NULL")
            elif operator == 'in':
                placeholders = ','.join('?' * len(value))
                conditions.append(f"{field_name} {sql_op} ({placeholders})")
                params.extend(value)
            elif operator == 'range':
                conditions.append(f"{field_name} BETWEEN ? AND ?")
                params.extend(value)
            else:
                formatted_value = format_value_for_operator(value, operator)
                conditions.append(f"{field_name} {sql_op} ?")
                params.append(formatted_value)
        
        # Add exclusion conditions
        for field_name, operator, value in self._excludes:
            sql_op = get_operator_sql(operator)
            
            if operator == 'isnull':
                if value:
                    conditions.append(f"{field_name} IS NOT NULL")
                else:
                    conditions.append(f"{field_name} IS NULL")
            elif operator == 'in':
                placeholders = ','.join('?' * len(value))
                conditions.append(f"{field_name} NOT {sql_op} ({placeholders})")
                params.extend(value)
            else:
                formatted_value = format_value_for_operator(value, operator)
                conditions.append(f"NOT ({field_name} {sql_op} ?)")
                params.append(formatted_value)
        
        if conditions:
            return " WHERE " + " AND ".join(conditions), params
        return "", params
    
    def _build_sql(self) -> Tuple[str, List[Any]]:
        """Build complete SQL query."""
        table_name = self.model._table_name
        
        # SELECT clause
        if self._values_fields:
            select_fields = ', '.join(self._values_fields)
        else:
            select_fields = '*'
        
        if self._distinct:
            sql = f"SELECT DISTINCT {select_fields} FROM {table_name}"
        else:
            sql = f"SELECT {select_fields} FROM {table_name}"
        
        # WHERE clause
        where_clause, params = self._build_where_clause()
        sql += where_clause
        
        # ORDER BY clause
        if self._order_by:
            order_parts = []
            for field in self._order_by:
                if field.startswith('-'):
                    order_parts.append(f"{field[1:]} DESC")
                else:
                    order_parts.append(f"{field} ASC")
            sql += " ORDER BY " + ", ".join(order_parts)
        
        # LIMIT and OFFSET
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        if self._offset is not None:
            sql += f" OFFSET {self._offset}"
        
        return sql, params
    
    def _execute(self) -> List[sqlite3.Row]:
        """Execute query and return raw results."""
        if self._cache is not None:
            return self._cache
        
        sql, params = self._build_sql()
        cursor = self.model._get_connection().execute(sql, tuple(params))
        self._cache = cursor.fetchall()
        return self._cache
    
    def _create_instance(self, row: sqlite3.Row) -> Any:
        """Create model instance from database row."""
        if self._values_fields:
            return dict(row)
        
        instance = self.model.__new__(self.model)
        instance._loaded_from_db = True
        
        for field_name, field in self.model._fields.items():
            db_column = field.get_db_column()
            if db_column in row.keys():
                value = row[db_column]
                setattr(instance, field_name, field.to_python(value))
        
        return instance
    
    def all(self) -> List[Any]:
        """Return all results."""
        return [self._create_instance(row) for row in self._execute()]
    
    def get(self, **kwargs) -> Any:
        """
        Get single object matching conditions.
        
        Raises:
            DoesNotExist: If no object found
            MultipleObjectsReturned: If multiple objects found
        """
        qs = self.filter(**kwargs)
        results = qs.all()
        
        if len(results) == 0:
            raise DoesNotExist(f"{self.model.__name__} matching query does not exist")
        if len(results) > 1:
            raise MultipleObjectsReturned(
                f"get() returned {len(results)} {self.model.__name__} objects"
            )
        
        return results[0]
    
    def first(self) -> Optional[Any]:
        """Return first result or None."""
        qs = self.limit(1)
        results = qs.all()
        return results[0] if results else None
    
    def last(self) -> Optional[Any]:
        """Return last result or None."""
        qs = self.order_by(*[f'-{f}' if not f.startswith('-') else f[1:] 
                              for f in (self._order_by or ['id'])]).limit(1)
        results = qs.all()
        return results[0] if results else None
    
    def exists(self) -> bool:
        """Check if any results exist."""
        sql, params = self._build_sql()
        sql = sql.replace('SELECT *', 'SELECT 1', 1)
        cursor = self.model._get_connection().execute(sql, tuple(params))
        return cursor.fetchone() is not None
    
    def count(self) -> int:
        """Return count of results."""
        table_name = self.model._table_name
        where_clause, params = self._build_where_clause()
        sql = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
        cursor = self.model._get_connection().execute(sql, tuple(params))
        return cursor.fetchone()[0]
    
    def delete(self) -> int:
        """Delete all matching records."""
        table_name = self.model._table_name
        where_clause, params = self._build_where_clause()
        
        if not where_clause:
            raise QueryError("Cannot delete without filters (use Model.objects.all().delete())")
        
        sql = f"DELETE FROM {table_name}{where_clause}"
        cursor = self.model._get_connection().execute(sql, tuple(params))
        self.model._get_connection().commit()
        return cursor.rowcount
    
    def update(self, **kwargs) -> int:
        """Update all matching records."""
        if not kwargs:
            return 0
        
        table_name = self.model._table_name
        where_clause, where_params = self._build_where_clause()
        
        # Build SET clause
        set_parts = []
        set_params = []
        for field_name, value in kwargs.items():
            if field_name not in self.model._fields:
                raise QueryError(f"Unknown field: {field_name}")
            field = self.model._fields[field_name]
            set_parts.append(f"{field.get_db_column()} = ?")
            set_params.append(field.to_db(value))
        
        sql = f"UPDATE {table_name} SET {', '.join(set_parts)}{where_clause}"
        params = set_params + where_params
        
        cursor = self.model._get_connection().execute(sql, tuple(params))
        self.model._get_connection().commit()
        return cursor.rowcount
    
    # Python magic methods for slicing
    def __getitem__(self, key):
        """Support slicing: Model.objects[0:10]"""
        if isinstance(key, slice):
            qs = self._clone()
            if key.start is not None:
                qs._offset = key.start
            if key.stop is not None:
                if key.start is not None:
                    qs._limit = key.stop - key.start
                else:
                    qs._limit = key.stop
            return qs.all()
        elif isinstance(key, int):
            qs = self.offset(key).limit(1)
            results = qs.all()
            if not results:
                raise IndexError("QuerySet index out of range")
            return results[0]
        else:
            raise TypeError("QuerySet indices must be integers or slices")
    
    def __iter__(self):
        """Make QuerySet iterable."""
        return iter(self.all())
    
    def __len__(self):
        """Return count when len() is called."""
        return self.count()
    
    def __repr__(self):
        """String representation."""
        return f"<QuerySet [{', '.join(repr(obj) for obj in self.all()[:5])}...]>"

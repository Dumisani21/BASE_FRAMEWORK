"""
BASE ORM Utility Functions

Helper functions for string manipulation, SQL operations, and type conversion.
"""
import re
from typing import Any, List, Tuple


def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase to snake_case.
    
    Args:
        name: CamelCase string
        
    Returns:
        snake_case string
        
    Example:
        >>> camel_to_snake('UserProfile')
        'user_profile'
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name: str) -> str:
    """
    Convert snake_case to CamelCase.
    
    Args:
        name: snake_case string
        
    Returns:
        CamelCase string
        
    Example:
        >>> snake_to_camel('user_profile')
        'UserProfile'
    """
    components = name.split('_')
    return ''.join(x.title() for x in components)


def escape_sql_identifier(identifier: str) -> str:
    """
    Escape SQL identifier (table/column name) to prevent SQL injection.
    
    Args:
        identifier: SQL identifier to escape
        
    Returns:
        Escaped identifier
    """
    # Remove any existing quotes and escape special characters
    identifier = identifier.replace('"', '""')
    return f'"{identifier}"'


def pluralize(word: str) -> str:
    """
    Simple pluralization for table names.
    
    Args:
        word: Singular word
        
    Returns:
        Plural form
        
    Example:
        >>> pluralize('user')
        'users'
        >>> pluralize('category')
        'categories'
    """
    if word.endswith('y'):
        return word[:-1] + 'ies'
    elif word.endswith('s'):
        return word + 'es'
    else:
        return word + 's'


def parse_lookup(lookup: str) -> Tuple[str, str]:
    """
    Parse field lookup expression.
    
    Args:
        lookup: Lookup expression like 'field__gt' or 'field'
        
    Returns:
        Tuple of (field_name, operator)
        
    Example:
        >>> parse_lookup('age__gt')
        ('age', 'gt')
        >>> parse_lookup('name')
        ('name', 'exact')
    """
    if '__' in lookup:
        parts = lookup.split('__')
        return '__'.join(parts[:-1]), parts[-1]
    return lookup, 'exact'


def get_operator_sql(operator: str) -> str:
    """
    Convert lookup operator to SQL operator.
    
    Args:
        operator: Lookup operator (gt, gte, lt, lte, etc.)
        
    Returns:
        SQL operator string
    """
    operators = {
        'exact': '=',
        'gt': '>',
        'gte': '>=',
        'lt': '<',
        'lte': '<=',
        'ne': '!=',
        'in': 'IN',
        'contains': 'LIKE',
        'icontains': 'LIKE',
        'startswith': 'LIKE',
        'istartswith': 'LIKE',
        'endswith': 'LIKE',
        'iendswith': 'LIKE',
        'isnull': 'IS NULL',
        'range': 'BETWEEN',
    }
    return operators.get(operator, '=')


def format_value_for_operator(value: Any, operator: str) -> Any:
    """
    Format value based on operator for SQL query.
    
    Args:
        value: Value to format
        operator: Lookup operator
        
    Returns:
        Formatted value
    """
    if operator in ('contains', 'icontains'):
        return f'%{value}%'
    elif operator in ('startswith', 'istartswith'):
        return f'{value}%'
    elif operator in ('endswith', 'iendswith'):
        return f'%{value}'
    return value

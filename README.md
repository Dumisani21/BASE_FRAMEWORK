# BASE ORM Framework v3.0.0

**A professional, production-ready ORM for Python with SQLite support.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

BASE ORM transforms SQLite database operations into elegant, Pythonic code with a powerful model-based architecture, chainable queries, automatic migrations, and much more.

## ✨ Features

- **🎯 Model-Based Architecture**: Define your database schema using Python classes
- **🔗 Chainable Query Builder**: Intuitive, Django-style query API
- **🔄 Automatic Migrations**: Auto-detect schema changes and generate migrations
- **💾 Connection Management**: Thread-safe connection pooling and transactions
- **✅ Data Validation**: Built-in field validators and custom validation support
- **🔍 Advanced Queries**: Filtering, ordering, aggregation, and joins
- **🛠️ CLI Tools**: Command-line interface for migrations and database management
- **📦 Zero Dependencies**: Pure Python with only SQLite (included in Python)
- **🔙 Backward Compatible**: Legacy API support for smooth migration from v2.x

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/BASE_FRAMEWORK.git
cd BASE_FRAMEWORK

# Or install from PyPI (coming soon)
pip install base-orm
```

### Basic Usage

```python
from base import Model, CharField, IntegerField, Database

# Define your model
class User(Model):
    id = IntegerField(primary_key=True, auto_increment=True)
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100)

# Connect to database
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

# Update
user.email = 'newemail@example.com'
user.save()

# Delete
user.delete()
```

## 📚 Documentation

### Field Types

BASE ORM supports various field types:

- `IntegerField` - Integer values
- `CharField` - String with max length
- `TextField` - Large text
- `FloatField` - Floating point numbers
- `BooleanField` - Boolean values (stored as 0/1)
- `DateTimeField` - Date and time
- `JSONField` - JSON data (stored as TEXT)
- `ForeignKey` - Foreign key relationships

### Query Operations

```python
# Filtering
User.objects.filter(age__gte=18)
User.objects.filter(username__contains='john')
User.objects.exclude(email__endswith='@spam.com')

# Ordering
User.objects.order_by('-created_at')
User.objects.order_by('username', '-age')

# Slicing
User.objects.all()[0:10]
User.objects.filter(active=1).first()

# Aggregation
User.objects.count()
User.objects.filter(age__gte=18).count()

# Chaining
User.objects.filter(active=1).exclude(banned=1).order_by('-created_at')[:10]
```

### Migrations

```python
from base import MigrationManager

# Auto-generate migrations
manager = MigrationManager()
manager.makemigrations([User, Post, Comment])

# Apply migrations
manager.migrate()

# Rollback
manager.rollback(steps=1)
```

### Transactions

```python
with db.atomic():
    user = User(username='john')
    user.save()
    
    profile = Profile(user_id=user.id)
    profile.save()
    # Both saved together or rolled back on error
```

## 🎯 Examples

Check out the `examples/` directory for complete working examples:

- **Blog Application** (`examples/blog_example.py`) - Demonstrates models, relationships, and CRUD operations
- **Todo List** (`examples/todo_example.py`) - Shows filtering, priorities, and status management

Run an example:

```bash
python examples/blog_example.py
```

## 🛠️ CLI Tools

BASE ORM includes a powerful CLI for database management:

```bash
# Generate migrations
python -m base.cli makemigrations --models-module myapp.models

# Apply migrations
python -m base.cli migrate

# Rollback migrations
python -m base.cli rollback --steps 1

# Interactive shell
python -m base.cli shell --models-module myapp.models

# Database shell
python -m base.cli dbshell --database-path myapp.db

# Inspect existing database
python -m base.cli inspectdb myapp.db > models.py
```

## 📖 Migration Guide from v2.x

If you're using BASE v2.x, here's how to migrate:

**Old way (v2.x):**
```python
from base import base

db = base.Database('people.db')
db.create_table('workers', 'firstName text, lastName text')
db.insert_data('workers', ('John', 'Smith'))
```

**New way (v3.x):**
```python
from base import Model, CharField, Database

class Worker(Model):
    firstName = CharField(max_length=100)
    lastName = CharField(max_length=100)

db = Database('people.db')
db.connect()
Worker._create_table()

worker = Worker(firstName='John', lastName='Smith')
worker.save()
```

The legacy API is still available for backward compatibility but will be removed in v4.0.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by Django ORM and SQLAlchemy
- Built with ❤️ for the Python community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/BASE_FRAMEWORK/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/BASE_FRAMEWORK/discussions)

---

**Made with ❤️ by the BASE ORM team**

"""
Tests for BASE ORM Models

Run with: pytest tests/test_models.py
"""
import pytest
import os
from base import Model, CharField, IntegerField, Database


class TestUser(Model):
    """Test model."""
    id = IntegerField(primary_key=True, auto_increment=True)
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100)


@pytest.fixture
def db():
    """Create test database."""
    db_path = 'test.db'
    db = Database(db_path)
    db.connect()
    TestUser._create_table()
    yield db
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_model_creation(db):
    """Test creating and saving a model."""
    user = TestUser(username='john', email='john@example.com')
    user.save()
    
    assert user.id is not None
    assert user.username == 'john'
    assert user.email == 'john@example.com'


def test_model_retrieval(db):
    """Test retrieving a model."""
    user = TestUser(username='jane', email='jane@example.com')
    user.save()
    
    retrieved = TestUser.objects.get(id=user.id)
    assert retrieved.username == 'jane'
    assert retrieved.email == 'jane@example.com'


def test_model_update(db):
    """Test updating a model."""
    user = TestUser(username='bob', email='bob@example.com')
    user.save()
    
    user.email = 'newemail@example.com'
    user.save()
    
    retrieved = TestUser.objects.get(id=user.id)
    assert retrieved.email == 'newemail@example.com'


def test_model_delete(db):
    """Test deleting a model."""
    user = TestUser(username='alice', email='alice@example.com')
    user.save()
    user_id = user.id
    
    user.delete()
    
    with pytest.raises(Exception):  # DoesNotExist
        TestUser.objects.get(id=user_id)


def test_filter_query(db):
    """Test filtering queries."""
    TestUser(username='user1', email='user1@example.com').save()
    TestUser(username='user2', email='user2@example.com').save()
    TestUser(username='admin', email='admin@example.com').save()
    
    users = TestUser.objects.filter(username__contains='user')
    assert len(list(users)) == 2


def test_count_query(db):
    """Test count queries."""
    TestUser(username='user1', email='user1@example.com').save()
    TestUser(username='user2', email='user2@example.com').save()
    
    count = TestUser.objects.count()
    assert count == 2


def test_order_by(db):
    """Test ordering queries."""
    TestUser(username='charlie', email='c@example.com').save()
    TestUser(username='alice', email='a@example.com').save()
    TestUser(username='bob', email='b@example.com').save()
    
    users = TestUser.objects.order_by('username').all()
    assert users[0].username == 'alice'
    assert users[1].username == 'bob'
    assert users[2].username == 'charlie'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

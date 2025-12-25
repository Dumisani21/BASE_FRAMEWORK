"""
BASE ORM Example: Todo List Application

Demonstrates relationships and more advanced ORM features.
"""
from base import (
    Model, Database, CharField, TextField, IntegerField,
    DateTimeField, BooleanField, ForeignKey
)


class User(Model):
    """User model."""
    id = IntegerField(primary_key=True, auto_increment=True)
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)


class TodoList(Model):
    """Todo list model."""
    id = IntegerField(primary_key=True, auto_increment=True)
    name = CharField(max_length=100)
    user_id = ForeignKey(User, on_delete='CASCADE')
    created_at = DateTimeField(auto_now_add=True)


class TodoItem(Model):
    """Todo item model."""
    id = IntegerField(primary_key=True, auto_increment=True)
    title = CharField(max_length=200)
    description = TextField(null=True)
    list_id = ForeignKey(TodoList, on_delete='CASCADE')
    completed = IntegerField(default=0)  # Boolean
    priority = IntegerField(default=1)  # 1=Low, 2=Medium, 3=High
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True)


def main():
    """Run the todo list example."""
    print("BASE ORM Todo List Example\n")
    
    # Setup
    db = Database('todo.db')
    db.connect()
    
    # Create tables
    User._create_table()
    TodoList._create_table()
    TodoItem._create_table()
    
    # Create user
    user = User(username='alice', email='alice@example.com')
    user.save()
    print(f"Created user: {user.username}")
    
    # Create todo lists
    work_list = TodoList(name='Work Tasks', user_id=user.id)
    work_list.save()
    
    personal_list = TodoList(name='Personal', user_id=user.id)
    personal_list.save()
    
    print(f"Created {TodoList.objects.count()} todo lists")
    
    # Create todo items
    items = [
        TodoItem(title='Finish project report', list_id=work_list.id, priority=3),
        TodoItem(title='Review pull requests', list_id=work_list.id, priority=2),
        TodoItem(title='Team meeting at 3pm', list_id=work_list.id, priority=2),
        TodoItem(title='Buy groceries', list_id=personal_list.id, priority=1),
        TodoItem(title='Call dentist', list_id=personal_list.id, priority=2),
    ]
    
    for item in items:
        item.save()
    
    print(f"Created {TodoItem.objects.count()} todo items\n")
    
    # Query examples
    print("High priority work tasks:")
    high_priority = TodoItem.objects.filter(
        list_id=work_list.id,
        priority__gte=2
    ).order_by('-priority')
    
    for item in high_priority:
        print(f"  - {item.title} (Priority: {item.priority})")
    
    # Mark items as complete
    print("\nCompleting tasks...")
    item = TodoItem.objects.get(id=1)
    item.completed = 1
    from datetime import datetime
    item.completed_at = datetime.now()
    item.save()
    print(f"  ✓ {item.title}")
    
    # Statistics
    total = TodoItem.objects.count()
    completed = TodoItem.objects.filter(completed=1).count()
    print(f"\nProgress: {completed}/{total} tasks completed")
    
    db.close()
    print("\nExample completed!")


if __name__ == '__main__':
    main()

"""
BASE ORM Example: Simple Blog Application

Demonstrates the core features of BASE ORM including:
- Model definition with various field types
- Relationships (ForeignKey)
- CRUD operations
- Query filtering and ordering
- Transactions
"""
from base import (
    Model, Database, CharField, TextField, IntegerField,
    DateTimeField, ForeignKey
)


# Define Models
class Author(Model):
    """Author model."""
    id = IntegerField(primary_key=True, auto_increment=True)
    name = CharField(max_length=100)
    email = CharField(max_length=100, unique=True)
    bio = TextField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    
    def __repr__(self):
        return f"<Author: {self.name}>"


class Post(Model):
    """Blog post model."""
    id = IntegerField(primary_key=True, auto_increment=True)
    title = CharField(max_length=200)
    content = TextField()
    author_id = ForeignKey(Author, on_delete='CASCADE')
    published = IntegerField(default=0)  # Boolean as integer
    views = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    def __repr__(self):
        return f"<Post: {self.title}>"


def main():
    """Run the blog example."""
    
    # 1. Setup Database
    print("=" * 60)
    print("BASE ORM Blog Example")
    print("=" * 60)
    
    db = Database('blog.db')
    db.connect()
    
    # 2. Create Tables
    print("\n1. Creating tables...")
    Author._create_table()
    Post._create_table()
    
    # 3. Create Authors
    print("\n2. Creating authors...")
    
    author1 = Author(
        name='John Doe',
        email='john@example.com',
        bio='Software developer and blogger'
    )
    author1.save()
    print(f"   Created: {author1}")
    
    author2 = Author(
        name='Jane Smith',
        email='jane@example.com',
        bio='Tech writer and enthusiast'
    )
    author2.save()
    print(f"   Created: {author2}")
    
    # 4. Create Posts
    print("\n3. Creating blog posts...")
    
    post1 = Post(
        title='Getting Started with BASE ORM',
        content='BASE ORM is a powerful and easy-to-use ORM for Python...',
        author_id=author1.id,
        published=1,
        views=150
    )
    post1.save()
    print(f"   Created: {post1}")
    
    post2 = Post(
        title='Advanced Query Techniques',
        content='Learn how to use complex queries with BASE ORM...',
        author_id=author1.id,
        published=1,
        views=89
    )
    post2.save()
    print(f"   Created: {post2}")
    
    post3 = Post(
        title='Database Migrations Made Easy',
        content='Managing database schema changes has never been easier...',
        author_id=author2.id,
        published=0,
        views=0
    )
    post3.save()
    print(f"   Created: {post3}")
    
    # 5. Query Examples
    print("\n4. Querying data...")
    
    # Get all authors
    print("\n   All authors:")
    for author in Author.objects.all():
        print(f"   - {author.name} ({author.email})")
    
    # Filter published posts
    print("\n   Published posts:")
    published_posts = Post.objects.filter(published=1).order_by('-views')
    for post in published_posts:
        print(f"   - {post.title} ({post.views} views)")
    
    # Get posts by specific author
    print(f"\n   Posts by {author1.name}:")
    author1_posts = Post.objects.filter(author_id=author1.id)
    for post in author1_posts:
        print(f"   - {post.title}")
    
    # Get single post
    print("\n   Get post by ID:")
    post = Post.objects.get(id=1)
    print(f"   {post.title}")
    
    # Count queries
    print("\n   Statistics:")
    print(f"   Total authors: {Author.objects.count()}")
    print(f"   Total posts: {Post.objects.count()}")
    print(f"   Published posts: {Post.objects.filter(published=1).count()}")
    
    # 6. Update Example
    print("\n5. Updating data...")
    post1.views = 200
    post1.save()
    print(f"   Updated {post1.title} views to {post1.views}")
    
    # Bulk update
    Post.objects.filter(author_id=author2.id).update(published=1)
    print(f"   Published all posts by {author2.name}")
    
    # 7. Advanced Queries
    print("\n6. Advanced queries...")
    
    # Posts with views > 100
    popular_posts = Post.objects.filter(views__gte=100)
    print(f"   Popular posts (views >= 100): {popular_posts.count()}")
    
    # Posts with title containing "ORM"
    orm_posts = Post.objects.filter(title__contains='ORM')
    print(f"   Posts about ORM: {orm_posts.count()}")
    
    # Get first and last posts
    first_post = Post.objects.order_by('created_at').first()
    last_post = Post.objects.order_by('-created_at').first()
    print(f"   First post: {first_post.title}")
    print(f"   Last post: {last_post.title}")
    
    # 8. Transaction Example
    print("\n7. Transaction example...")
    
    try:
        with db.atomic():
            new_author = Author(
                name='Bob Wilson',
                email='bob@example.com'
            )
            new_author.save()
            
            new_post = Post(
                title='My First Post',
                content='Hello World!',
                author_id=new_author.id,
                published=1
            )
            new_post.save()
            
            print(f"   Created author and post in transaction")
    except Exception as e:
        print(f"   Transaction failed: {e}")
    
    # 9. Delete Example
    print("\n8. Deleting data...")
    
    # Delete a single post
    post_to_delete = Post.objects.filter(views=0).first()
    if post_to_delete:
        title = post_to_delete.title
        post_to_delete.delete()
        print(f"   Deleted post: {title}")
    
    # 10. Final Statistics
    print("\n9. Final statistics:")
    print(f"   Total authors: {Author.objects.count()}")
    print(f"   Total posts: {Post.objects.count()}")
    print(f"   Published posts: {Post.objects.filter(published=1).count()}")
    
    # 11. Serialization Example
    print("\n10. Serialization example:")
    post_dict = post1.to_dict()
    print(f"   Post as dict: {post_dict}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    
    # Cleanup
    db.close()


if __name__ == '__main__':
    main()

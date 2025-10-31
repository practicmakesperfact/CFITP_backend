# seed.py
import os
import uuid
from faker import Faker
from django.core.management.base import BaseCommand

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# Import models after Django setup
from apps.users.models import User
from apps.issues.models import Issue, IssueHistory
from apps.comments.models import Comment
from apps.feedback.models import Feedback
from apps.notifications.models import Notification

fake = Faker()

print("Seeding database with demo data...")

# 1. Create Demo Users (Clients, Staff, Managers, Admin)
def create_users():
    roles = ['client', 'staff', 'manager', 'admin']
    users = []
    for role in roles:
        for i in range(3):  # 3 users per role
            user = User.objects.create(
                id=uuid.uuid4(),
                email=fake.email(),
                role=role,
                is_active=True
            )
            user.set_password('password123')  # Set default password
            user.save()
            users.append(user)
            print(f"Created {role}: {user.email}")
    return users

# 2. Create Demo Issues
def create_issues(reporter, assignees):
    # ensure assignees is a list and pick safely
    assignees_list = list(assignees) if assignees is not None else []
    assignee = fake.random_element(assignees_list) if assignees_list else None

    issue = Issue.objects.create(
        id=uuid.uuid4(),
        title=fake.sentence(nb_words=6),
        description=fake.paragraph(nb_sentences=3),
        status='open',
        priority='medium',
        reporter=reporter,
        assignee=assignee,
        created_by=reporter,   # <-- set required non-null field
        due_date=fake.date_time_this_month()
    )
    # Log status change
    IssueHistory.objects.create(
        id=uuid.uuid4(),
        issue=issue,
        changed_by=reporter,
        old_status='',
        new_status='open'
    )
    print(f"Created issue: {issue.title}")
    return issue

# 3. Create Demo Comments
def create_comments(issue, author):
    comment = Comment.objects.create(
        id=uuid.uuid4(),
        issue=issue,
        author=author,
        content=fake.sentence(nb_words=10),
        created_at=fake.date_time_this_month()
    )
    print(f"Created comment by {author.email} on issue {issue.title}")
    return comment

# 4. Create Demo Feedback
def create_feedback(user=None):
    feedback = Feedback.objects.create(
        id=uuid.uuid4(),
        title=fake.sentence(nb_words=5),
        description=fake.paragraph(nb_sentences=3),
        status='new',
        user=user
    )
    print(f"Created feedback: {feedback.title}")
    return feedback

# Main Seeding Function
def seed():
    print("Starting seed...\n")
    
    # Create users
    all_users = create_users()
    clients = User.objects.filter(role='client')
    staff = User.objects.filter(role__in=['staff', 'manager'])
    
    # Create 10 issues
    for _ in range(10):
        reporter = fake.random_element(clients)
        issue = create_issues(reporter, staff)
        
        # Add 1–3 comments per issue
        for _ in range(fake.random_int(1, 3)):
            author = fake.random_element(all_users)
            create_comments(issue, author)
    
    # Create 5 feedback entries
    for _ in range(5):
        user = fake.random_element(clients) if fake.boolean(chance_of_getting_true=70) else None
        create_feedback(user)
    
    print("\nSeeding completed!")

# Run the seeder
if __name__ == '__main__':
    seed()
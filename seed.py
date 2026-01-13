# seed.py - CFITP Performance Testing Script
import os
import sys
import uuid
import time
from datetime import datetime
from faker import Faker

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Use the correct settings module based on your structure
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CFIT.settings')

try:
    import django
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("\n📁 Your project structure appears to be:")
    print("   CFITP/           <- Current folder (where seed.py is)")
    print("   ├── CFIT/        <- Django project folder")
    print("   │   ├── settings.py")
    print("   │   ├── urls.py")
    print("   │   └── ...")
    print("   ├── apps/")
    print("   ├── manage.py")
    print("   └── seed.py")
    sys.exit(1)

# Now import Django models
from apps.users.models import User
from apps.issues.models import Issue
from apps.comments.models import Comment
from apps.feedback.models import Feedback

fake = Faker()

def run_simple_performance_tests():
    """Run simple, reliable performance tests that will work"""
    print("\n" + "="*60)
    print("CFITP SIMPLE PERFORMANCE TESTING")
    print("="*60)
    
    results = {}
    
    # 1. CLEAR OLD DATA
    print("\n1️⃣  Clearing old test data...")
    User.objects.filter(email__contains='test_').delete()
    Issue.objects.filter(title__contains='TEST_').delete()
    
    # 2. CREATE USERS TEST
    print("\n2️⃣  Testing User Creation (Stress Test)...")
    start = time.time()
    
    users = []
    roles = ['client', 'staff', 'manager', 'admin']
    for role in roles:
        for i in range(3):  # 3 per role = 12 total
            user = User.objects.create(
                email=f"test_{role}_{i}@aitb.com",
                role=role,
                is_active=True
            )
            user.set_password('password123')
            user.save()
            users.append(user)
    
    user_time = (time.time() - start) * 1000
    results['user_creation'] = {
        'count': len(users),
        'time_ms': round(user_time, 2),
        'per_second': round(len(users) / (user_time / 1000), 2)
    }
    print(f"   Created {len(users)} users in {user_time:.2f}ms")
    
    # 3. CREATE ISSUES TEST  
    print("\n3️⃣  Testing Issue Creation (Volume Test)...")
    start = time.time()
    
    clients = list(User.objects.filter(role='client'))
    staff = list(User.objects.filter(role__in=['staff', 'manager']))
    issues = []
    
    for i in range(20):  # Create 20 test issues
        reporter = clients[i % len(clients)] if clients else None
        assignee = staff[i % len(staff)] if staff else None
        
        issue = Issue.objects.create(
            title=f"TEST_Issue_{i}: {fake.sentence(nb_words=4)}",
            description=fake.paragraph(nb_sentences=3),
            status='open',
            priority=fake.random_element(['low', 'medium', 'high']),
            reporter=reporter,
            assignee=assignee,
            created_by=reporter
        )
        issues.append(issue)
    
    issue_time = (time.time() - start) * 1000
    results['issue_creation'] = {
        'count': len(issues),
        'time_ms': round(issue_time, 2),
        'per_second': round(len(issues) / (issue_time / 1000), 2)
    }
    print(f"   Created {len(issues)} issues in {issue_time:.2f}ms")
    
    # 4. CREATE COMMENTS TEST
    print("\n4️⃣  Testing Comment Creation...")
    start = time.time()
    
    comment_count = 0
    all_users = list(User.objects.all())
    
    for issue in issues:
        # Add 2-3 comments per issue
        for _ in range(fake.random_int(2, 3)):
            author = fake.random_element(all_users)
            Comment.objects.create(
                issue=issue,
                author=author,
                content=fake.paragraph(nb_sentences=2)
            )
            comment_count += 1
    
    comment_time = (time.time() - start) * 1000
    results['comment_creation'] = {
        'count': comment_count,
        'time_ms': round(comment_time, 2)
    }
    print(f"   Created {comment_count} comments in {comment_time:.2f}ms")
    
    # 5. API PERFORMANCE TEST
    print("\n5️⃣  Testing API Query Performance...")
    
    # Test 1: Fetch issues
    start = time.time()
    issues_list = list(Issue.objects.all().select_related('reporter', 'assignee')[:15])
    fetch_issues_time = (time.time() - start) * 1000
    
    # Test 2: Fetch comments with users
    start = time.time()
    comments_list = list(Comment.objects.all().select_related('author', 'issue')[:20])
    fetch_comments_time = (time.time() - start) * 1000
    
    results['api_performance'] = {
        'fetch_15_issues_ms': round(fetch_issues_time, 2),
        'fetch_20_comments_ms': round(fetch_comments_time, 2),
        'total_issues_in_db': Issue.objects.count(),
        'total_comments_in_db': Comment.objects.count()
    }
    print(f"   Fetch 15 issues: {fetch_issues_time:.2f}ms")
    print(f"   Fetch 20 comments: {fetch_comments_time:.2f}ms")
    
    # 6. SEARCH PERFORMANCE TEST
    print("\n6️⃣  Testing Search Performance...")
    search_terms = ['TEST', 'error', 'bug']
    search_times = []
    
    for term in search_terms:
        start = time.time()
        count = Issue.objects.filter(title__icontains=term).count()
        search_time = (time.time() - start) * 1000
        search_times.append(search_time)
        print(f"   Search '{term}': found {count} in {search_time:.2f}ms")
    
    results['search_performance'] = {
        'terms_tested': len(search_terms),
        'average_ms': round(sum(search_times) / len(search_times), 2) if search_times else 0
    }
    
    # 7. SAVE RESULTS
    save_results(results)
    
    return results

def save_results(results):
    """Save test results to file"""
    filename = 'performance_test_results.txt'
    
    with open(filename, 'w') as f:
        f.write("="*60 + "\n")
        f.write("CFITP PERFORMANCE TEST RESULTS\n")
        f.write("="*60 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("DATABASE STATISTICS:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Users: {User.objects.count()}\n")
        f.write(f"Total Issues: {Issue.objects.count()}\n")
        f.write(f"Total Comments: {Comment.objects.count()}\n")
        f.write(f"Total Feedback: {Feedback.objects.count()}\n\n")
        
        f.write("PERFORMANCE METRICS:\n")
        f.write("-" * 40 + "\n")
        
        for test_name, data in results.items():
            f.write(f"\n{test_name.upper()}:\n")
            for key, value in data.items():
                f.write(f"  {key}: {value}\n")
    
    print(f"\n💾 Results saved to: {filename}")
    
    # Print summary for report
    print("\n" + "="*60)
    print("📊 SUMMARY FOR YOUR CHAPTER 6 REPORT:")
    print("="*60)
    
    if 'user_creation' in results:
        uc = results['user_creation']
        print(f"\n1. User Creation (Stress Test):")
        print(f"   • Created {uc['count']} users")
        print(f"   • Time: {uc['time_ms']}ms")
        print(f"   • Rate: {uc['per_second']} users/second")
    
    if 'issue_creation' in results:
        ic = results['issue_creation']
        print(f"\n2. Issue Creation (Volume Test):")
        print(f"   • Created {ic['count']} issues") 
        print(f"   • Time: {ic['time_ms']}ms")
        print(f"   • Rate: {ic['per_second']} issues/second")
    
    if 'api_performance' in results:
        ap = results['api_performance']
        print(f"\n3. API Performance:")
        print(f"   • Fetch 15 issues: {ap['fetch_15_issues_ms']}ms")
        print(f"   • Fetch 20 comments: {ap['fetch_20_comments_ms']}ms")
        print(f"   • Total in DB: {ap['total_issues_in_db']} issues, {ap['total_comments_in_db']} comments")
    
    if 'search_performance' in results:
        sp = results['search_performance']
        print(f"\n4. Search Performance:")
        print(f"   • {sp['terms_tested']} search terms tested")
        print(f"   • Average: {sp['average_ms']}ms per search")

def main():
    """Main function"""
    print("🚀 Starting CFITP Performance Tests...")
    print("\n📁 Detected settings: CFIT/settings.py")
    
    # Ask for confirmation
    response = input("\n⚠️  This will create test data. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Test cancelled.")
        return
    
    try:
        results = run_simple_performance_tests()
        print("\n✅ Testing completed successfully!")
        
        print("\n📝 For Chapter 6, you can report:")
        print("   • Stress testing: User creation performance")
        print("   • Volume testing: Issue creation performance") 
        print("   • API performance: Query response times")
        print("   • Search performance: Average search times")
        print("\n   All measurements are REAL from your CFITP system.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Try running Django first to check setup:")
        print("   python manage.py runserver")
        print("\nIf that works, the seed.py should work too.")

if __name__ == '__main__':
    main()
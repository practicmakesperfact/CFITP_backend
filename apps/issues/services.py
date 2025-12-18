from .models import Issue, IssueHistory
from apps.notifications.services import NotificationService

class IssueService:
    @staticmethod
    def create_issue(user,data):
        data['reporter'] = user
        data['created_by'] = user
        issue = Issue.objects.create(**data)
        IssueHistory.objects.create(issue=issue, changed_by=user,old_status='',new_status='open')
        return issue
    
    @staticmethod
    def assign_issue(issue, assignee,changed_by):
        old_assignee = issue.assignee
        issue.assignee = assignee
        issue.save()
        if old_assignee !=assignee:
            NotificationService.create_notification(
                recipient =assignee,
                message = f'You have been assigned to issue {issue.title}',
                type = 'new_issue',
                issue = issue
            )
    @staticmethod
    def transition_status(issue,new_status,changed_by):
        old_status= issue.status
        if old_status != new_status:
            issue.status = new_status
            issue.save()
            IssueHistory.objects.create(issue=issue,changed_by=changed_by,old_status=old_status,new_status=new_status)
            # Only notify if there's an assignee
            if issue.assignee:
                NotificationService.create_notification(
                    recipient=issue.assignee,
                    message = f'Issue {issue.title} Status changed to {new_status}',
                    type = 'status_change',
                    issue = issue
                )# apps/issues/services.py
from .models import Issue, IssueHistory
from apps.notifications.services import NotificationService
from django.contrib.auth import get_user_model

User = get_user_model()

class IssueService:
    @staticmethod
    def create_issue(user, data):
        """Create issue and notify managers/admins"""
        data['reporter'] = user
        data['created_by'] = user
        issue = Issue.objects.create(**data)
        
        # Create history
        IssueHistory.objects.create(
            issue=issue, 
            changed_by=user,
            old_status='',
            new_status='open'
        )
        
        # NOTIFY MANAGERS AND ADMINS ABOUT NEW ISSUE
        managers_admins = User.objects.filter(
            role__in=['manager', 'admin'], 
            is_active=True
        ).exclude(id=user.id)  # Don't notify the creator if they're manager/admin
        
        for manager_admin in managers_admins:
            NotificationService.create_notification(
                recipient=manager_admin,
                message=f'New issue created: "{issue.title}" by {user.email}',
                type='new_issue',  # or create 'new_issue' type
                issue=issue
            )
        
        # NOTIFY CLIENT (reporter) that their issue was created
        NotificationService.create_notification(
            recipient=user,
            message=f'Your issue "{issue.title}" has been created successfully',
            type='status_change',
            issue=issue
        )
        
        return issue
    
    @staticmethod
    def assign_issue(issue, assignee, changed_by):
        """Assign issue and notify assignee"""
        old_assignee = issue.assignee
        issue.assignee = assignee
        issue.save()
        
        # Notify new assignee
        if old_assignee != assignee:
            NotificationService.create_notification(
                recipient=assignee,
                message=f'You have been assigned to issue: "{issue.title}"',
                type='new_issue',
                issue=issue
            )
            
            # Also notify reporter that issue was assigned
            if issue.reporter and issue.reporter != assignee:
                NotificationService.create_notification(
                    recipient=issue.reporter,
                    message=f'Your issue "{issue.title}" has been assigned to {assignee.email}',
                    type='new_issue',
                    issue=issue
                )
        
        return issue
    
    @staticmethod
    def transition_status(issue, new_status, changed_by):
        """Change issue status and notify relevant parties"""
        old_status = issue.status
        
        if old_status != new_status:
            issue.status = new_status
            issue.save()
            
            # Create history
            IssueHistory.objects.create(
                issue=issue,
                changed_by=changed_by,
                old_status=old_status,
                new_status=new_status
            )
            
            # IMPORTANT NOTIFICATIONS FOR STATUS CHANGES
            
            # 1. Notify assignee (if exists)
            if issue.assignee and issue.assignee != changed_by:
                NotificationService.create_notification(
                    recipient=issue.assignee,
                    message=f'Issue "{issue.title}" status changed from {old_status} to {new_status}',
                    type='status_change',
                    issue=issue
                )
            
            # 2. Notify reporter (client) about status changes
            if issue.reporter and issue.reporter != changed_by:
                NotificationService.create_notification(
                    recipient=issue.reporter,
                    message=f'Your issue "{issue.title}" status changed from {old_status} to {new_status}',
                    type='status_change',
                    issue=issue
                )
            
            # 3. Notify managers/admins for critical status changes
            if new_status in ['resolved', 'closed']:
                managers_admins = User.objects.filter(
                    role__in=['manager', 'admin'], 
                    is_active=True
                ).exclude(id=changed_by.id)  # Don't notify the person making change
                
                for manager_admin in managers_admins:
                    NotificationService.create_notification(
                        recipient=manager_admin,
                        message=f'Issue "{issue.title}" marked as {new_status} by {changed_by.email}',
                        type='status_change',
                        issue=issue
                    )
            
            # 4. Special notification for client when resolved/closed
            if new_status in ['resolved', 'closed'] and issue.reporter:
                action = "resolved" if new_status == 'resolved' else "closed"
                NotificationService.create_notification(
                    recipient=issue.reporter,
                    message=f'Great news! Your issue "{issue.title}" has been {action}',
                    type='status_change',
                    issue=issue
                )
        
        return issue# apps/issues/services.py
from .models import Issue, IssueHistory
from apps.notifications.services import NotificationService
from django.contrib.auth import get_user_model

User = get_user_model()

class IssueService:
    @staticmethod
    def create_issue(user, data):
        """Create issue and notify managers/admins"""
        data['reporter'] = user
        data['created_by'] = user
        issue = Issue.objects.create(**data)
        
        # Create history
        IssueHistory.objects.create(
            issue=issue, 
            changed_by=user,
            old_status='',
            new_status='open'
        )
        
        # NOTIFY MANAGERS AND ADMINS ABOUT NEW ISSUE
        managers_admins = User.objects.filter(
            role__in=['manager', 'admin'], 
            is_active=True
        ).exclude(id=user.id)  # Don't notify the creator if they're manager/admin
        
        for manager_admin in managers_admins:
            NotificationService.create_notification(
                recipient=manager_admin,
                message=f'New issue created: "{issue.title}" by {user.email}',
                type='new_issue',  
                issue=issue
            )
        
        # NOTIFY CLIENT (reporter) that their issue was created
        NotificationService.create_notification(
            recipient=user,
            message=f'Your issue "{issue.title}" has been created successfully',
            type='status_change',
            issue=issue
        )
        
        return issue
    
    @staticmethod
    def assign_issue(issue, assignee, changed_by):
        """Assign issue and notify assignee"""
        old_assignee = issue.assignee
        issue.assignee = assignee
        issue.save()
        
        # Notify new assignee
        if old_assignee != assignee:
            NotificationService.create_notification(
                recipient=assignee,
                message=f'You have been assigned to issue: "{issue.title}"',
                type='new_issue',
                issue=issue
            )
            
            # Also notify reporter that issue was assigned
            if issue.reporter and issue.reporter != assignee:
                NotificationService.create_notification(
                    recipient=issue.reporter,
                    message=f'Your issue "{issue.title}" has been assigned to {assignee.email}',
                    type='new_issue',
                    issue=issue
                )
        
        return issue
    
    @staticmethod
    def transition_status(issue, new_status, changed_by):
        """Change issue status and notify relevant parties"""
        old_status = issue.status
        
        if old_status != new_status:
            issue.status = new_status
            issue.save()
            
            # Create history
            IssueHistory.objects.create(
                issue=issue,
                changed_by=changed_by,
                old_status=old_status,
                new_status=new_status
            )
            
            # IMPORTANT NOTIFICATIONS FOR STATUS CHANGES
            
            # 1. Notify assignee (if exists)
            if issue.assignee and issue.assignee != changed_by:
                NotificationService.create_notification(
                    recipient=issue.assignee,
                    message=f'Issue "{issue.title}" status changed from {old_status} to {new_status}',
                    type='status_change',
                    issue=issue
                )
            
            # 2. Notify reporter (client) about status changes
            if issue.reporter and issue.reporter != changed_by:
                NotificationService.create_notification(
                    recipient=issue.reporter,
                    message=f'Your issue "{issue.title}" status changed from {old_status} to {new_status}',
                    type='status_change',
                    issue=issue
                )
            
            # 3. Notify managers/admins for critical status changes
            if new_status in ['resolved', 'closed']:
                managers_admins = User.objects.filter(
                    role__in=['manager', 'admin'], 
                    is_active=True
                ).exclude(id=changed_by.id)  # Don't notify the person making change
                
                for manager_admin in managers_admins:
                    NotificationService.create_notification(
                        recipient=manager_admin,
                        message=f'Issue "{issue.title}" marked as {new_status} by {changed_by.email}',
                        type='status_change',
                        issue=issue
                    )
            
            # 4. Special notification for client when resolved/closed
            if new_status in ['resolved', 'closed'] and issue.reporter:
                action = "resolved" if new_status == 'resolved' else "closed"
                NotificationService.create_notification(
                    recipient=issue.reporter,
                    message=f'Great news! Your issue "{issue.title}" has been {action}',
                    type='status_change',
                    issue=issue
                )
        
        return issue
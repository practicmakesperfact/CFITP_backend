from .models import User

class UserService:
    @staticmethod
    def get_current_user(request):
        return request.user
    
    @staticmethod
    def update_profile(user,data):
        user.email = data.get('email',user.email)
        user.save()
        return user
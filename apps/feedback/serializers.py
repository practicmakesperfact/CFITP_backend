
from rest_framework import serializers
from .models import Feedback
from apps.users.serializers import UserSerializer

class FeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'title', 'description', 'status', 'user', 
            'user_email', 'converted_to', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'converted_to', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Remove user_email from validated_data
        user_email = validated_data.pop('user_email', None)
        
        # Get the authenticated user if exists
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        elif user_email:
            # Try to find user by email for non-authenticated feedback
            try:
                from apps.users.models import User
                user = User.objects.get(email=user_email)
                validated_data['user'] = user
            except User.DoesNotExist:
                # Leave user as None for anonymous feedback
                pass
        
        return super().create(validated_data)
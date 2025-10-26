from rest_framework import serializers
from .models import Comment
from apps.users.serializers import UserSerializer

class CommentSeerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields ='__all__'
        read_only_fields = ['id','created_at','update_at']
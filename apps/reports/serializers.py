
from rest_framework import serializers
from .models import Report
from apps.users.serializers import UserSerializer

class ReportSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'type', 'type_display', 'format', 'format_display',
            'user', 'user_email', 'user_name', 'status', 'status_display',
            'parameters', 'result_path', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'status_display', 'result_path', 
            'error_message', 'created_at', 'updated_at',
            'user_email', 'user_name', 'type_display', 'format_display'
        ]
    
    def to_representation(self, instance):
        """Custom representation to ensure all fields are properly serialized"""
        representation = super().to_representation(instance)
        
        # Convert result_path to full URL if it exists
        if instance.result_path and hasattr(instance.result_path, 'url'):
            representation['result_path'] = instance.result_path.url
        else:
            representation['result_path'] = None
            
        return representation
    
    def validate_parameters(self, value):
        """Validate report parameters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a JSON object")
        
        # Validate required parameters
        required_params = ['start_date', 'end_date', 'report_type']
        for param in required_params:
            if param not in value:
                raise serializers.ValidationError(f"Missing required parameter: {param}")
                
        return value
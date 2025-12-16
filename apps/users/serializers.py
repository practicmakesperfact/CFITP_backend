
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# ------------------------------------------------------------
# REGISTRATION SERIALIZER (FIXED)
# ------------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'role': {'required': True}
        }

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_role(self, value):
        valid_roles = ['client', 'staff', 'manager', 'admin']
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(valid_roles)}"
            )
        
        # Restrict self-registration to client role only
        if value != 'client':
            raise serializers.ValidationError(
                "Only client accounts can be self-registered. "
                "Staff, Manager, and Admin roles require administrator approval."
            )
        
        return value

    def validate_password(self, value):
        # Use Django's password validation
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        # Password confirmation
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Password fields didn't match."
            })
        
        # Additional password complexity (optional)
        password = attrs['password']
        errors = []
        
        if not any(char.isupper() for char in password):
            errors.append("At least one uppercase letter")
        
        if not any(char.islower() for char in password):
            errors.append("At least one lowercase letter")
        
        if not any(char.isdigit() for char in password):
            errors.append("At least one number")
        
        if not any(char in '@$!%*?&' for char in password):
            errors.append("At least one special character (@$!%*?&)")
        
        if errors:
            raise serializers.ValidationError({
                "password": f"Password requirements: {'; '.join(errors)}"
            })
        
        return attrs

    def create(self, validated_data):
        # Remove confirm_password before creating user
        validated_data.pop('confirm_password')
        
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


# ------------------------------------------------------------
# JWT LOGIN SERIALIZER
# ------------------------------------------------------------
class LoginSerializer(TokenObtainPairSerializer):
    """
    Overrides default JWT login response to include user info
    """
    role = serializers.CharField(required=False, write_only=True)
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['role'] = user.role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Optional: Validate role if provided
        requested_role = attrs.get('role')
        if requested_role and requested_role != self.user.role:
            raise serializers.ValidationError({
                "role": f"Please login as {self.user.role} role"
            })
        
        # Add user details to the response
        data['user'] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "role": self.user.role,
            "is_active": self.user.is_active,
            "last_login": self.user.last_login,
        }
        return data


# ------------------------------------------------------------
# PROFILE SERIALIZER
# ------------------------------------------------------------
class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined', 'last_login',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'is_active', 'date_joined', 
            'last_login', 'created_at', 'updated_at'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


# ------------------------------------------------------------
# USER SERIALIZER (Simplified to match your existing structure)
# ------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ------------------------------------------------------------
# PASSWORD CHANGE SERIALIZER (FIXED)
# ------------------------------------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        # Use Django's built-in password validation
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Password fields didn't match."
            })
        return attrs
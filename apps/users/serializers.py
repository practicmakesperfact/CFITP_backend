from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# ------------------------------------------------------------
# REGISTRATION SERIALIZER (UPDATED FOR ADMIN SUPPORT)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the request from context
        self.request = self.context.get('request', None)

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
        
        # Get request context
        request = self.context.get('request')
        
        # If request exists and user is admin, allow any role
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.role == 'admin':
                return value
            elif request.user.role == 'manager' and value != 'admin':
                # Managers can create staff and clients, but not admins
                return value
        
        # For public registration or non-admin users, restrict to client only
        if value != 'client':
            if not request or not request.user.is_authenticated:
                raise serializers.ValidationError(
                    "Only client accounts can be self-registered. "
                    "Staff, Manager, and Admin roles require administrator approval."
                )
            else:
                raise serializers.ValidationError(
                    "You don't have permission to create staff, manager, or admin accounts. "
                    "Only administrators can create these roles."
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
            "date_joined": self.user.date_joined,
        }
        return data


# ------------------------------------------------------------
# PROFILE SERIALIZER (For detailed user view)
# ------------------------------------------------------------
class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined', 'last_login',
            'created_at', 'updated_at', 'avatar_url'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'is_active', 'date_joined', 
            'last_login', 'created_at', 'updated_at', 'avatar_url'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_avatar_url(self, obj):
        return obj.avatar_url
    
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance


# ------------------------------------------------------------
# USER LIST SERIALIZER (For listing users with all needed fields)
# ------------------------------------------------------------
class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined', 'last_login',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields  # All fields are read-only for list view
    
    def get_full_name(self, obj):
        return obj.get_full_name()


# ------------------------------------------------------------
# USER DETAIL SERIALIZER (For single user retrieval)
# ------------------------------------------------------------
class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined', 'last_login',
            'created_at', 'updated_at', 'avatar_url'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_avatar_url(self, obj):
        return obj.avatar_url


# ------------------------------------------------------------
# USER UPDATE SERIALIZER (For updating users)
# ------------------------------------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'is_active']
        
    def validate_role(self, value):
        valid_roles = ['client', 'staff', 'manager', 'admin']
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(valid_roles)}"
            )
        
        # Get request context
        request = self.context.get('request')
        
        # Only admins can assign admin role
        if value == 'admin' and request and request.user.is_authenticated:
            if request.user.role != 'admin':
                raise serializers.ValidationError(
                    "Only administrators can assign admin role."
                )
        
        # Managers can assign staff and client roles only
        if request and request.user.is_authenticated and request.user.role == 'manager':
            if value == 'admin':
                raise serializers.ValidationError(
                    "Managers cannot assign admin role."
                )
        
        return value


# ------------------------------------------------------------
# USER BASIC SERIALIZER (Minimal fields - keep for backward compatibility)
# ------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']


# ------------------------------------------------------------
# PASSWORD CHANGE SERIALIZER
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


# ------------------------------------------------------------
# ADMIN CREATE SERIALIZER (For admin-only user creation)
# ------------------------------------------------------------
class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name', 'role', 'is_active']
    
    def validate(self, attrs):
        # Password confirmation
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Password fields didn't match."
            })
        
        # Email validation
        if User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "A user with this email already exists."
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user
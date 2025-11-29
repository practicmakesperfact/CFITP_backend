# from rest_framework import serializers
# from django.contrib.auth import get_user_model

# User = get_user_model()


# class UserSerializer(serializers.ModelSerializer):
#     """
#     General user representation (for lists, etc.)
#     """
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'role', 'created_at', 'updated_at']
#         read_only_fields = ['id', 'created_at', 'updated_at']


# class RegisterSerializer(serializers.ModelSerializer):
#     """
#     Used for user registration: email + password + role
#     Password is write-only and hashed on save
#     """
#     password = serializers.CharField(
#         write_only=True,
#         required=True,
#         style={'input_type': 'password'},
#         help_text="Leave empty to keep current password"
#     )

#     class Meta:
#         model = User
#         fields = ['email', 'password', 'role']
#         extra_kwargs = {
#             'email': {'required': True},
#             'role': {'required': True}
#         }

#     def validate_email(self, value):
#         if User.objects.filter(email=value).exists():
#             raise serializers.ValidationError("A user with this email already exists.")
#         return value

#     def validate_role(self, value):
#         valid_roles = ['client', 'staff', 'manager', 'admin']
#         if value not in valid_roles:
#             raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}")
#         return value

#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = User(**validated_data)
#         user.set_password(password)  # Hash password
#         user.save()
#         return user


# class ProfileSerializer(serializers.ModelSerializer):
#     """
#     For /me endpoint: show current user profile
#     Includes last_login
#     """
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'role', 'last_login']
#         read_only_fields = ['id', 'last_login']

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# ------------------------------------------------------------
# GENERAL USER SERIALIZER
# ------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ------------------------------------------------------------
# REGISTRATION SERIALIZER
# ------------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'role']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_role(self, value):
        valid_roles = ['client', 'staff', 'manager', 'admin']
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(valid_roles)}"
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ------------------------------------------------------------
# JWT LOGIN SERIALIZER (INCLUDES USER ROLE)
# ------------------------------------------------------------
class LoginSerializer(TokenObtainPairSerializer):
    """
    Overrides default JWT login response to include user info (role, email)
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user details to the response
        data['user'] = {
            "id": self.user.id,
            "email": self.user.email,
            "role": self.user.role
        }
        return data


# ------------------------------------------------------------
# PROFILE SERIALIZER (FOR /auth/me/)
# ------------------------------------------------------------
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'last_login']
        read_only_fields = ['id', 'last_login']

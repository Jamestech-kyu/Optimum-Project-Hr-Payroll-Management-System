from rest_framework import serializers
from .models import CustomUser, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "password",
            "phone_number",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = CustomUser(**validated_data)
        user.set_password(password)

        user.is_approved = False
        user.is_active = True

        user.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "role",
            "is_approved",
            "is_active",
            "created_at",
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "email",
            "phone_number",
            "profile_picture",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
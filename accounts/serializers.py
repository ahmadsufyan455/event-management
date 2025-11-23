from rest_framework import serializers
from .models import User, Group, AssignRole
from django.shortcuts import get_object_or_404
from loguru import logger


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    # show roles as an array of group names
    roles = serializers.SerializerMethodField(read_only=True)
    # accept password on create/update (write-only)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "created_at",
            "updated_at",
            "roles",
            "password",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "email": {"required": False},
            "username": {"required": False},
        }

    def get_roles(self, obj):
        # obj.roles -> AssignRole, follow to Group names
        return list(obj.roles.select_related("group").values_list("group__name", flat=True))

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        username = validated_data.get("username")
        email = validated_data.get("email")
        logger.info(f"Creating user: username={username}, email={email}")
        try:
            user = User(**validated_data)
            if password:
                user.set_password(password)
                logger.info(f"Password set for user: {username}")
            else:
                # default to unusable password if none provided
                user.set_unusable_password()
                logger.warning(f"No password provided for user: {username}, setting unusable password")
            user.save()
            logger.info(f"User created successfully: {user.id}, username={username}")
            return user
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}", exc_info=True)
            raise

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        logger.info(f"Updating user: {instance.id}, username={instance.username}")
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            if password is not None and password != "":
                instance.set_password(password)
                logger.info(f"Password updated for user: {instance.username}")
            instance.save()
            logger.info(f"User updated successfully: {instance.id}")
            return instance
        except Exception as e:
            logger.error(f"Error updating user {instance.id}: {e}", exc_info=True)
            raise


class AssignRoleSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    group_id = serializers.IntegerField(write_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    group = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AssignRole
        fields = ["id", "user_id", "group_id", "user", "group", "created_at"]
        read_only_fields = ["id", "user", "group", "created_at"]

    def get_user(self, obj):
        return {"id": str(obj.user_id), "username": obj.user.username, "email": obj.user.email}

    def get_group(self, obj):
        return {"id": obj.group_id, "name": obj.group.name}

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        group_id = attrs.get("group_id")
        logger.info(f"Validating AssignRole: user_id={user_id}, group_id={group_id}")
        try:
            user = get_object_or_404(User, pk=user_id)
            group = get_object_or_404(Group, pk=group_id)
            if AssignRole.objects.filter(user=user, group=group).exists():
                logger.warning(f"User {user_id} already has role {group_id}")
                raise serializers.ValidationError("This user already has that role.")
            attrs["_user_obj"] = user
            attrs["_group_obj"] = group
            logger.info(f"AssignRole validation successful: user_id={user_id}, group_id={group_id}")
            return attrs
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating AssignRole: {e}", exc_info=True)
            raise

    def create(self, validated_data):
        user = validated_data["_user_obj"]
        group = validated_data["_group_obj"]
        logger.info(f"Creating AssignRole: user_id={user.id}, group_id={group.id}")
        try:
            assign_role = AssignRole.objects.create(user=user, group=group)
            logger.info(f"AssignRole created successfully: {assign_role.id}")
            return assign_role
        except Exception as e:
            logger.error(f"Error creating AssignRole: {e}", exc_info=True)
            raise

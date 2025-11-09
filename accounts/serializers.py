from rest_framework import serializers
from .models import User, Group, AssignRole
from django.shortcuts import get_object_or_404


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
        read_only_fields = ["id", "created_at", "updated_at", "roles"]

    def get_roles(self, obj):
        # obj.roles -> AssignRole, follow to Group names
        return list(obj.roles.select_related("group").values_list("group__name", flat=True))

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            # default to unusable password if none provided
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None and password != "":
            instance.set_password(password)
        instance.save()
        return instance


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
        user = get_object_or_404(User, pk=attrs["user_id"])
        group = get_object_or_404(Group, pk=attrs["group_id"])
        if AssignRole.objects.filter(user=user, group=group).exists():
            raise serializers.ValidationError("This user already has that role.")
        attrs["_user_obj"] = user
        attrs["_group_obj"] = group
        return attrs

    def create(self, validated_data):
        user = validated_data["_user_obj"]
        group = validated_data["_group_obj"]
        return AssignRole.objects.create(user=user, group=group)

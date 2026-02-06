from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (UserProfile, GMUDVersion, TestPlan, TestCase, TestExecution, Evidence, AuditLog)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',)

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'role', 'active', 'created_at')

class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='profile', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')

class GMUDVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField (source='created_by.get_full_name', read_only=True)

    class Meta:
        model = GMUDVersion
        fields = ('id', 'version', 'description', 'created_by', 'created_by_name', 'created_at')

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ('id', 'test_plan', 'description', 'order_index', 'active', 'created_at')

class TestPlanListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    test_case_count = serializers.SerializerMethodField()

    class Meta:
        model = TestPlan
        fields = (
            'id', 'name', 'division', 'system', 'environment', 'status', 'validation_type', 
            'created_by', 'created_by_name', 'responsible', 'responsible_name', 'test_case_count', 'created_at'
        )

        def get_test_cases_count(self, obj):
            return obj.test_cases.count()
        
class TestPlanDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    test_cases = TestCaseSerializer(many=True, read_only=True)

    class Meta:
        model = TestPlan
        fields = (
            'id', 'name', 'description', 'division', 'system', 'environment', 'validation_type'
            'status', 'access_key', 'gmud_version', 'created_by', 'created_by_name', 'responsible'
            'responsible', 'responsible_name', 'test_cases', 'created_at', 'updated_at'
        )

class TestExecutionSerializer(serializers.ModelSerializer):
    executed_by_name = serializers.CharField(source='executed_by.get_full_name', read_only=True)

    class Meta:
        model = TestExecution
        fields = ('id', 'test_case', 'executed_by', 'executed_by_name', 'status', 'comment', 'executed_at')

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ('id', 'test_execution', 'file', 'file_type', 'created_at')

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            'id', 'user', 'user_name', 'action', 'entity', 'entity_id', 'details', 'created_at'
        )
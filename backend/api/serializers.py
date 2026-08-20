from rest_framework import serializers
from .models import (
    Conversation, Message, ToolCall, ApprovalRequest,
    AuditLog, UserPreference, KnowledgeDocument
)

class ToolCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolCall
        fields = ['id', 'tool_name', 'tool_display_name', 'arguments', 'result', 'status', 'created_at']


class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = [
            'id', 'tool_call_id', 'tool_name', 'tool_display_name',
            'description', 'risk_level', 'arguments', 'impact_summary',
            'status', 'created_at', 'resolved_at', 'rejection_reason'
        ]


class MessageSerializer(serializers.ModelSerializer):
    tool_calls = ToolCallSerializer(many=True, read_only=True)
    approval_request = ApprovalRequestSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation_id', 'role', 'content', 'status', 'created_at', 'tool_calls', 'approval_request']


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count', 'last_message_preview']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = '__all__'


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = '__all__'

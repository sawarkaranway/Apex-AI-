from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet, MessageViewSet, send_message,
    create_task_endpoint, stream_task_events_endpoint,
    resolve_approval, preferences_endpoint, briefing_endpoint,
    meeting_intel_endpoint, voice_stt_endpoint, voice_tts_endpoint,
    list_integrations_endpoint, connect_integration_endpoint,
    callback_integration_endpoint, disconnect_integration_endpoint,
    sync_integration_endpoint, link_token_endpoint,
    guest_login_endpoint,
    scheduled_tasks_endpoint, clipboard_endpoint,
    workflows_endpoint, trigger_workflow_endpoint,
    screen_analyze_endpoint, wakeword_status_endpoint
)

from .calculator_views import evaluate_math_endpoint, calculation_history_endpoint
from .knowledge_views import (
    list_knowledge_endpoint,
    upload_knowledge_file_endpoint,
    create_knowledge_note_endpoint,
    get_document_chunks_endpoint,
    reindex_document_endpoint,
    delete_document_endpoint,
    search_knowledge_endpoint
)

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', send_message, name='send_message'),
    path('tasks/', create_task_endpoint, name='create_task_endpoint'),
    path('tasks/<str:task_id>/stream/', stream_task_events_endpoint, name='stream_task_events_endpoint'),
    path('approvals/<str:approval_id>/resolve/', resolve_approval, name='resolve_approval'),
    path('preferences/', preferences_endpoint, name='preferences_endpoint'),
    path('briefing/generate/', briefing_endpoint, name='briefing_endpoint'),
    path('meeting/mom/', meeting_intel_endpoint, name='meeting_intel_endpoint'),
    path('voice/stt/', voice_stt_endpoint, name='voice_stt_endpoint'),
    path('voice/tts/', voice_tts_endpoint, name='voice_tts_endpoint'),
    path('auth/guest/', guest_login_endpoint, name='guest_login_endpoint'),

    # Phase 1: Integrations Endpoints
    path('integrations/', list_integrations_endpoint, name='list_integrations_endpoint'),
    path('integrations/<str:provider>/connect/', connect_integration_endpoint, name='connect_integration_endpoint'),
    path('integrations/<str:provider>/callback/', callback_integration_endpoint, name='callback_integration_endpoint'),
    path('integrations/<str:provider>/disconnect/', disconnect_integration_endpoint, name='disconnect_integration_endpoint'),
    path('integrations/<str:provider>/sync/', sync_integration_endpoint, name='sync_integration_endpoint'),
    path('integrations/<str:provider>/link-token/', link_token_endpoint, name='link_token_endpoint'),

    # Phase 2: Scheduler & Clipboard
    path('scheduler/', scheduled_tasks_endpoint, name='scheduled_tasks_endpoint'),
    path('scheduler/<str:task_id>/', scheduled_tasks_endpoint, name='scheduled_task_detail_endpoint'),
    path('clipboard/', clipboard_endpoint, name='clipboard_endpoint'),

    # Phase 3 & 4: Background Workflows, Screen Vision & Wake Word
    path('workflows/', workflows_endpoint, name='workflows_endpoint'),
    path('workflows/<str:workflow_id>/', workflows_endpoint, name='workflow_detail_endpoint'),
    path('workflows/<str:workflow_id>/trigger/', trigger_workflow_endpoint, name='trigger_workflow_endpoint'),
    path('screen/analyze/', screen_analyze_endpoint, name='screen_analyze_endpoint'),
    path('voice/wakeword/', wakeword_status_endpoint, name='wakeword_status_endpoint'),

    # Scientific Calculator Endpoints
    path('calculator/evaluate/', evaluate_math_endpoint, name='evaluate_math_endpoint'),
    path('calculator/history/', calculation_history_endpoint, name='calculation_history_endpoint'),
    path('calculator/history/<str:item_id>/', calculation_history_endpoint, name='calculation_history_delete_endpoint'),

    # Knowledge Base Endpoints
    path('knowledge/', list_knowledge_endpoint, name='list_knowledge_endpoint'),
    path('knowledge/upload/', upload_knowledge_file_endpoint, name='upload_knowledge_file_endpoint'),
    path('knowledge/create/', create_knowledge_note_endpoint, name='create_knowledge_note_endpoint'),
    path('knowledge/search/', search_knowledge_endpoint, name='search_knowledge_endpoint'),
    path('knowledge/<str:doc_id>/chunks/', get_document_chunks_endpoint, name='get_document_chunks_endpoint'),
    path('knowledge/<str:doc_id>/reindex/', reindex_document_endpoint, name='reindex_document_endpoint'),
    path('knowledge/<str:doc_id>/', delete_document_endpoint, name='delete_document_endpoint'),
]



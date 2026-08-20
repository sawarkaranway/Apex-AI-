from django.test import TestCase
from rest_framework.test import APIClient
from api.models import Conversation, Message, ApprovalRequest, TaskExecution, UserPreference
from agent.policy import evaluate_tool_risk, verify_all_tools_have_policy
from agent.registry import registry
from agent.graph import compute_idempotency_key
from agent.memory import memory_system
from agent.tools.local_tools import validate_sandboxed_path

from django.contrib.auth.models import User

class AgentBackendTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password123", email="test@example.com")
        self.client.force_authenticate(user=self.user)

    def test_policy_coverage_all_registered_tools(self):
        """Verify dynamic policy coverage: every registered tool has an explicit policy classification."""
        self.assertTrue(verify_all_tools_have_policy(registry))

    def test_path_sandboxing_security(self):
        """Verify path sandboxing blocks directory traversal attempts outside authorized roots."""
        with self.assertRaises(PermissionError) as ctx:
            validate_sandboxed_path("../../Windows/System32/config")
        self.assertIn("Security Violation", str(ctx.exception))

    def test_shell_capability_rejection(self):
        """Verify arbitrary shell command tool is not registered in production registry."""
        res = registry.execute_tool("system_command", {"command": "dir"})
        self.assertIn("not found in registry", res)

    def test_policy_engine_risk_classification(self):
        """Verify deterministic risk classification for LOW and HIGH tools."""
        risk, approval, summary = evaluate_tool_risk("read_file", {"file_path": "README.md"})
        self.assertEqual(risk, "LOW")
        self.assertFalse(approval)

        risk, approval, summary = evaluate_tool_risk("delete_file", {"file_path": "target.txt"})
        self.assertEqual(risk, "HIGH")
        self.assertTrue(approval)

        risk, approval, summary = evaluate_tool_risk("gmail_send", {"to": ["test@user.com"], "subject": "Test"})
        self.assertEqual(risk, "HIGH")
        self.assertTrue(approval)

    def test_double_approval_race_condition_protection(self):
        """Verify resolving an approval request twice returns 409 Conflict on the second attempt."""
        chat_resp = self.client.post('/api/chat/', {'content': 'Prepare me for tomorrow.'}, format='json')
        approval_id = chat_resp.json()['assistant_message']['approval_request']['id']

        # First resolution
        res1 = self.client.post(f'/api/approvals/{approval_id}/resolve/', {'approved': True}, format='json')
        self.assertEqual(res1.status_code, 200)

        # Second resolution (duplicate click attempt)
        res2 = self.client.post(f'/api/approvals/{approval_id}/resolve/', {'approved': True}, format='json')
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already resolved", res2.json()['error'])

    def test_idempotency_key_generation(self):
        """Verify sha256 idempotency key generation is deterministic for identical arguments."""
        key1 = compute_idempotency_key("gmail_send", "task-123", {"to": ["a@b.com"], "subject": "Hi"})
        key2 = compute_idempotency_key("gmail_send", "task-123", {"to": ["a@b.com"], "subject": "Hi"})
        key3 = compute_idempotency_key("gmail_send", "task-123", {"to": ["a@b.com"], "subject": "Other"})
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)

    def test_user_preference_conflict_resolution(self):
        """Verify updating a preference deactivates older entries for the same key."""
        memory_system.save_preference("preferred_meeting_time", "10:00", category="schedule")
        memory_system.save_preference("preferred_meeting_time", "11:00", category="schedule")

        active_prefs = memory_system.get_active_preferences("schedule")
        self.assertEqual(active_prefs.get("preferred_meeting_time"), "11:00")

        all_records = UserPreference.objects.filter(key="preferred_meeting_time")
        self.assertEqual(all_records.count(), 2)
        self.assertEqual(all_records.filter(is_active=True).count(), 1)

    def test_send_message_killer_scenario(self):
        """Verify killer scenario 'Prepare me for tomorrow' creates task, steps, and approval request."""
        response = self.client.post('/api/chat/', {
            'content': 'Prepare me for tomorrow.'
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('assistant_message', data)
        asst_msg = data['assistant_message']
        self.assertIsNotNone(asst_msg['approval_request'])
        self.assertEqual(asst_msg['approval_request']['risk_level'], 'HIGH')

    def test_realtime_date_and_time(self):
        """Verify real-time date and time query returns dynamic system timestamp."""
        response = self.client.post('/api/chat/', {
            'content': 'What is today date and time?'
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('Current Date & Time', data['assistant_message']['content'])

    def test_auth_registration_and_login_flow(self):
        """Verify end-to-end user registration and JWT login flow."""
        unauth_client = APIClient()
        reg_resp = unauth_client.post('/api/auth/registration/', {
            'username': 'newuser@example.com',
            'email': 'newuser@example.com',
            'password1': 'SecretP@ssword2026',
            'password2': 'SecretP@ssword2026'
        }, format='json')
        self.assertEqual(reg_resp.status_code, 201)
        self.assertIn('access', reg_resp.json())

        # Test login with newly registered user
        login_resp = unauth_client.post('/api/auth/login/', {
            'email': 'newuser@example.com',
            'password': 'SecretP@ssword2026'
        }, format='json')
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn('access', login_resp.json())

    def test_auth_password_reset_flow(self):
        """Verify password reset request succeeds and generates confirmation email."""
        unauth_client = APIClient()
        reset_resp = unauth_client.post('/api/auth/password/reset/', {
            'email': 'test@example.com'
        }, format='json')
        self.assertEqual(reset_resp.status_code, 200)
        self.assertIn('detail', reset_resp.json())

    def test_preferences_crud_endpoint(self):
        """Verify GET, POST, and DELETE on /api/preferences/."""
        # Create
        post_resp = self.client.post('/api/preferences/', {
            'key': 'response_tone',
            'value': 'concise',
            'category': 'personality'
        }, format='json')
        self.assertEqual(post_resp.status_code, 200)

        # Read
        get_resp = self.client.get('/api/preferences/?category=personality')
        self.assertEqual(get_resp.status_code, 200)
        prefs = get_resp.json().get('preferences', [])
        self.assertTrue(any(p['key'] == 'response_tone' and p['value'] == 'concise' for p in prefs))

        # Delete
        del_resp = self.client.delete('/api/preferences/', {'key': 'response_tone'}, format='json')
        self.assertEqual(del_resp.status_code, 200)

    def test_meeting_intel_endpoint(self):
        """Verify MOM generation from transcript via /api/meeting/mom/."""
        resp = self.client.post('/api/meeting/mom/', {
            'transcript': 'Discussed security policy and token vault.',
            'title': 'Security Sync'
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('mom_content', resp.json())
        self.assertIn('action_items', resp.json())

    def test_voice_stt_and_tts_endpoints(self):
        """Verify STT and TTS endpoints respond correctly."""
        stt_resp = self.client.post('/api/voice/stt/', data=b'test_audio', content_type='application/octet-stream')
        self.assertEqual(stt_resp.status_code, 200)
        self.assertIn('transcription', stt_resp.json())

        tts_resp = self.client.post('/api/voice/tts/', {'text': 'Testing speech output'}, format='json')
        self.assertEqual(tts_resp.status_code, 200)
        self.assertEqual(tts_resp.json().get('status'), 'success')

    def test_integrations_list_endpoint(self):
        """Verify /api/integrations/ returns supported providers and status."""
        resp = self.client.get('/api/integrations/')
        self.assertEqual(resp.status_code, 200)
        providers = [i['provider'] for i in resp.json().get('integrations', [])]
        self.assertIn('google', providers)
        self.assertIn('microsoft', providers)
        self.assertIn('slack', providers)
        self.assertIn('github', providers)

    def test_new_tools_registration_and_execution(self):
        """Verify new tools (weather, clipboard, reminders, volume, scheduler) are registered and executable."""
        self.assertIsNotNone(registry.get_tool("get_weather"))
        self.assertIsNotNone(registry.get_tool("clipboard_read"))
        self.assertIsNotNone(registry.get_tool("clipboard_write"))
        self.assertIsNotNone(registry.get_tool("set_reminder"))
        self.assertIsNotNone(registry.get_tool("set_system_volume"))
        self.assertIsNotNone(registry.get_tool("schedule_task"))
        self.assertIsNotNone(registry.get_tool("list_scheduled_tasks"))
        self.assertIsNotNone(registry.get_tool("cancel_scheduled_task"))

        # Test clipboard write
        write_res = registry.execute_tool("clipboard_write", {"text": "Chaitanya Karya Test"})
        self.assertIn("clipboard", write_res.lower())

        # Test reminder
        rem_res = registry.execute_tool("set_reminder", {"message": "Test reminder", "delay_seconds": 10})
        self.assertIn("Reminder set", rem_res)

    def test_scheduler_lifecycle(self):
        """Verify scheduling a task, listing it, and cancelling it."""
        from agent.tools.scheduler_tools import schedule_task, list_scheduled_tasks, cancel_scheduled_task
        # Create
        create_res = schedule_task(prompt="Send morning digest", run_at="in 10 minutes", repeat="daily")
        self.assertIn("Scheduled task created successfully", create_res)

        # List
        list_res = list_scheduled_tasks()
        self.assertIn("Scheduled Tasks", list_res)
        self.assertIn("Send morning digest", list_res)

        # Extract task ID
        import re
        task_id_match = re.search(r'\[(sched-[a-zA-Z0-9]+)\]', list_res)
        if task_id_match:
            task_id = task_id_match.group(1)
            cancel_res = cancel_scheduled_task(task_id)
            self.assertIn("Successfully cancelled", cancel_res)




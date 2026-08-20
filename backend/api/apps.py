from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Start APScheduler proactive background worker when Django starts
        try:
            from agent.proactive import start_proactive_scheduler
            start_proactive_scheduler()
        except Exception as e:
            print(f"[Proactive Scheduler] Startup notice: {e}")

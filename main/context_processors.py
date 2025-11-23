from django.conf import settings
def chat_settings(request):
    return {"CHAT_API_URL": getattr(settings, "CHAT_API_URL", "")}

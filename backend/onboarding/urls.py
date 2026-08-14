from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("sessions/", views.create_or_get_session, name="sessions"),
    path("sessions/<str:visitor_id>/", views.session_detail, name="session-detail"),
    path("sessions/<str:visitor_id>/profile/", views.update_profile, name="profile"),
    path("sessions/<str:visitor_id>/integration/", views.connect_integration_view, name="integration"),
    path("sessions/<str:visitor_id>/campaigns/", views.create_campaign_view, name="campaign"),
    path("sessions/<str:visitor_id>/steps/", views.complete_onboarding_step, name="complete-step"),
    path("sessions/<str:visitor_id>/imports/", views.upload_customers, name="upload-customers"),
    path("sessions/<str:visitor_id>/imports/<int:import_id>/", views.import_status, name="import-status"),
    path("sessions/<str:visitor_id>/copilot/", views.copilot, name="copilot"),
    path("events/recent/", views.recent_events, name="recent-events"),
    path("metrics/", views.metrics, name="metrics"),
]

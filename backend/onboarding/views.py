from collections import OrderedDict
from statistics import mean

from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import CustomerImport, OnboardingSession, OnboardingStep, ProductEvent
from .serializers import (
    CampaignCreateSerializer,
    CompleteStepSerializer,
    CopilotRequestSerializer,
    CustomerImportSerializer,
    ImportStatusSerializer,
    IntegrationSerializer,
    ProfileSerializer,
    SessionCreateSerializer,
    SessionSerializer,
)
from .services import (
    assign_variant,
    complete_step,
    connect_integration,
    create_campaign,
    get_copilot_recommendations,
    process_customer_import,
    sample_ratio_mismatch,
    track_event,
    two_proportion_test,
)


@api_view(["GET"])
def health(request):
    return Response(
        {
            "status": "ok",
            "service": "activationlab-api",
            "database": settings.DATABASES["default"]["ENGINE"].split(".")[-1],
            "async_imports": settings.USE_CELERY,
            "copilot": "openai" if settings.OPENAI_API_KEY else "rules",
        }
    )


@api_view(["POST"])
def create_or_get_session(request):
    serializer = SessionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    visitor_id = serializer.validated_data["visitor_id"]
    session, created = OnboardingSession.objects.get_or_create(
        visitor_id=visitor_id,
        defaults={"variant": assign_variant(visitor_id)},
    )
    if created:
        track_event(session, "signup_completed", {"variant": session.variant})
    return Response(
        SessionSerializer(session).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["GET"])
def session_detail(request, visitor_id):
    session = get_object_or_404(OnboardingSession, visitor_id=visitor_id)
    return Response(SessionSerializer(session).data)


@api_view(["PATCH"])
def update_profile(request, visitor_id):
    session = get_object_or_404(OnboardingSession, visitor_id=visitor_id)
    serializer = ProfileSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    session.company_name = serializer.validated_data["company_name"]
    session.business_type = serializer.validated_data["business_type"]
    session.save(update_fields=["company_name", "business_type"])
    complete_step(session, OnboardingStep.STEP_WORKSPACE, {"business_type": session.business_type})
    session.refresh_from_db()
    return Response(SessionSerializer(session).data)


@api_view(["POST"])
def connect_integration_view(request, visitor_id):
    session = get_object_or_404(OnboardingSession, visitor_id=visitor_id)
    serializer = IntegrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    integration = connect_integration(session, **serializer.validated_data)
    session.refresh_from_db()
    return Response({"integration": {"provider": integration.provider}, "session": SessionSerializer(session).data})


@api_view(["POST"])
def create_campaign_view(request, visitor_id):
    session = get_object_or_404(OnboardingSession, visitor_id=visitor_id)
    serializer = CampaignCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    campaign = create_campaign(session, **serializer.validated_data)
    session.refresh_from_db()
    return Response({"campaign": {"id": campaign.id, "name": campaign.name}, "session": SessionSerializer(session).data}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def complete_onboarding_step(request, visitor_id):
    """Generic endpoint retained for demos/tests; specialized endpoints are preferred."""
    session = get_object_or_404(OnboardingSession, visitor_id=visitor_id)
    serializer = CompleteStepSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    _, created = complete_step(session, serializer.validated_data["step"], serializer.validated_data.get("metadata", {}))
    session.refresh_from_db()
    return Response({"created": created, "session": SessionSerializer(session).data})


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_customers(request, visitor_id):
    session = get_object_or_404(OnboardingSession, visitor_id=visitor_id)
    serializer = CustomerImportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    uploaded = serializer.validated_data["file"]
    job = CustomerImport.objects.create(session=session, source_filename=uploaded.name, file=uploaded)
    track_event(session, "customer_import_started", {"import_id": job.id, "filename": uploaded.name})

    if settings.USE_CELERY:
        from .tasks import process_customer_import_task
        process_customer_import_task.delay(job.id)
    else:
        process_customer_import(job.id)
        job.refresh_from_db()

    return Response(ImportStatusSerializer(job).data, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
def import_status(request, visitor_id, import_id):
    job = get_object_or_404(CustomerImport, id=import_id, session__visitor_id=visitor_id)
    return Response(ImportStatusSerializer(job).data)


@api_view(["POST"])
def copilot(request, visitor_id):
    session = get_object_or_404(OnboardingSession, visitor_id=visitor_id)
    serializer = CopilotRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(get_copilot_recommendations(session, serializer.validated_data["goal"]))


@api_view(["GET"])
def recent_events(request):
    events = ProductEvent.objects.select_related("session").order_by("-created_at")[:30]
    return Response(
        [
            {
                "visitor_id": event.session.visitor_id,
                "variant": event.session.variant,
                "name": event.name,
                "metadata": event.metadata,
                "created_at": event.created_at,
            }
            for event in events
        ]
    )


@api_view(["GET"])
def metrics(request):
    total = OnboardingSession.objects.count()
    activated = OnboardingSession.objects.filter(activated_at__isnull=False).count()

    variant_map = {}
    variants = []
    for key, label in OnboardingSession.VARIANT_CHOICES:
        qs = OnboardingSession.objects.filter(variant=key)
        variant_total = qs.count()
        variant_activated = qs.filter(activated_at__isnull=False).count()
        row = {
            "variant": key,
            "label": label,
            "sessions": variant_total,
            "activated": variant_activated,
            "activation_rate": round((variant_activated / variant_total * 100) if variant_total else 0, 1),
        }
        variant_map[key] = row
        variants.append(row)

    control = variant_map.get(OnboardingSession.VARIANT_CONTROL, {"sessions": 0, "activated": 0})
    guided = variant_map.get(OnboardingSession.VARIANT_GUIDED, {"sessions": 0, "activated": 0})
    experiment = two_proportion_test(control["sessions"], control["activated"], guided["sessions"], guided["activated"])
    experiment["sample_ratio_mismatch"] = sample_ratio_mismatch(control["sessions"], guided["sessions"])

    funnel = []
    for step_key, label in OnboardingStep.STEP_CHOICES:
        count = OnboardingStep.objects.filter(key=step_key).count()
        by_variant = {}
        for variant_key, _ in OnboardingSession.VARIANT_CHOICES:
            variant_total = variant_map[variant_key]["sessions"]
            variant_count = OnboardingStep.objects.filter(key=step_key, session__variant=variant_key).count()
            by_variant[variant_key] = {
                "count": variant_count,
                "rate": round((variant_count / variant_total * 100) if variant_total else 0, 1),
            }
        funnel.append({
            "step": step_key,
            "label": label,
            "count": count,
            "rate": round((count / total * 100) if total else 0, 1),
            "by_variant": by_variant,
        })

    event_counts = OrderedDict()
    for row in ProductEvent.objects.values("name").annotate(count=Count("id")).order_by("name"):
        event_counts[row["name"]] = row["count"]

    activation_seconds = [
        (session.activated_at - session.created_at).total_seconds()
        for session in OnboardingSession.objects.filter(activated_at__isnull=False)
    ]
    avg_activation_minutes = round(mean(activation_seconds) / 60, 2) if activation_seconds else 0.0

    imports = CustomerImport.objects.values("status").annotate(count=Count("id"))
    import_summary = {row["status"]: row["count"] for row in imports}

    return Response(
        {
            "sessions": total,
            "activated": activated,
            "activation_rate": round((activated / total * 100) if total else 0, 1),
            "average_time_to_activation_minutes": avg_activation_minutes,
            "variants": variants,
            "experiment": experiment,
            "funnel": funnel,
            "event_counts": event_counts,
            "import_summary": import_summary,
        }
    )

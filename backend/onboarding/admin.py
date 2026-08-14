from django.contrib import admin
from .models import Campaign, CopilotInteraction, Customer, CustomerImport, Integration, OnboardingSession, OnboardingStep, ProductEvent

admin.site.register(OnboardingSession)
admin.site.register(OnboardingStep)
admin.site.register(ProductEvent)
admin.site.register(Integration)
admin.site.register(Campaign)
admin.site.register(Customer)
admin.site.register(CustomerImport)
admin.site.register(CopilotInteraction)

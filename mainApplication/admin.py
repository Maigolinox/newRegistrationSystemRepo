from django.contrib import admin
from .models import UserProfile,PaymentProof,Place,CongressDate,Event,Registration

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(PaymentProof)
admin.site.register(Place)
admin.site.register(CongressDate)
admin.site.register(Event)
admin.site.register(Registration)

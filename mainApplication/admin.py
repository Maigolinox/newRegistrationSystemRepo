from django.contrib import admin
from .models import UserProfile,PaymentProof,Place,CongressDate,Event,Registration,CustomUser,adminPermissions,Author,Submission,SubmissionFile

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(PaymentProof)
admin.site.register(Place)
admin.site.register(CongressDate)
admin.site.register(CustomUser)
admin.site.register(adminPermissions)
admin.site.register(Author)
admin.site.register(Submission)
admin.site.register(SubmissionFile)

class EventAdmin(admin.ModelAdmin):
    # List all fields in the admin panel for each event
    list_display = (
        'title', 
        'description', 
        'date', 
        'start_time', 
        'end_time', 
        'place', 
        'event_type', 
        'ponent_name', 
        'affiliation', 
        'moderator', 
        'banner', 
        'links',
        'requisites',
        'allEvent',
        'fileDiplomas'
    )
    # Add a search bar for specific fields
    search_fields = ('title', 'ponent_name', 'affiliation', 'moderator', 'event_type')

    # Optional: Add filters for certain fields to make it easier to sort events
    list_filter = ('event_type', 'date', 'place')
admin.site.register(Event, EventAdmin)

class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'event', 
        'created_at', 
        'assisted', 
        'counter', 
        'receivedDiploma'
    )
    search_fields = ('user__username', 'event__title')
    list_filter = ('assisted', 'receivedDiploma', 'event')
admin.site.register(Registration, RegistrationAdmin)

from . import views
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path,include
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('',views.index,name='index'),
    path('dashboard/',views.dashboard,name="dashboard"),
    path('completeProfile/',views.complete_profile,name="complete_profile"),
    path('payment/',views.payment,name="payment"),
    path('schedule/',views.schedule,name="schedule"),
    path('validatePayment/',views.validPay,name="validatePayment"),
    path('registerintoEvent/', views.registerintoEvent, name='registerintoEvent'),
    path('seeSchedule/', views.seeMySchedule, name='seeMySchedule'),
    path('assist/<int:user_id>/<int:registration_id>/', views.assistanceControl, name='assistanceControl'),#admin/staff
    path('registerPlace/', views.register_place, name='registerPlace'),#admin/staff
    path('registerEvent/', views.register_event, name='registerEvent'),#admin/staff
    path('edit-event/<int:event_id>/', views.edit_event, name='editEvent'),#admin/staff
    path('delete-event/<int:event_id>/', views.delete_event, name='deleteEvent'),#admin/staff
    path('events/', views.list_events, name='listEvents'),#admin/staff
    path('manageCongressDates/', views.manage_congress_dates, name='manageCongressDates'),#admin/staff
    path('editCongressDate/<int:date_id>/', views.edit_congress_date, name='editCongressDate'),#admin/staff
    path('deleteCongressDate/<int:date_id>/', views.delete_congress_date, name='deleteCongressDate'),#admin/staff
    path('checkAssistance/', views.assistanceList, name='assistanceList'),#admin/staff
    path('validatePaymentAdmin/',views.validatePayment,name="validatePaymentAdmin")

]
urlpatterns += staticfiles_urlpatterns() 
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
    path('schedulePublic/',views.schedulePublic,name="schedulePublic"),
    path('validatePayment/',views.validPay,name="validatePayment"),
    path('registerintoEvent/', views.registerintoEvent, name='registerintoEvent'),
    path('seeSchedule/', views.seeMySchedule, name='seeMySchedule'),
    path('seeDiplomas/', views.seeMyDiplomas, name='seeMyDiplomas'),
    path('assist/<int:user_id>/<int:registration_id>/', views.assistanceControl, name='assistanceControl'),#admin/staff
    path('welcomeKit/<int:user_id>/', views.welcomeKit, name='welcomeKit'),#admin/staff control de kits de bienvenida
    path('registerPlace/', views.register_place, name='registerPlace'),#admin/staff
    path('registerStaff/', views.registerStaff, name='registerStaff'),#admin/staff
    path('registerEvent/', views.register_event, name='registerEvent'),#admin/staff
    path('edit-event/<int:event_id>/', views.edit_event, name='editEvent'),#admin/staff
    path('delete-event/<int:event_id>/', views.delete_event, name='deleteEvent'),#admin/staff
    path('events/', views.list_events, name='listEvents'),#admin/staff
    path('manageCongressDates/', views.manage_congress_dates, name='manageCongressDates'),#admin/staff
    path('editCongressDate/<int:date_id>/', views.edit_congress_date, name='editCongressDate'),#admin/staff
    path('deleteCongressDate/<int:date_id>/', views.delete_congress_date, name='deleteCongressDate'),#admin/staff
    path('checkAssistance/', views.assistanceList, name='assistanceList'),#admin/staff
    path('validatePaymentAdmin/',views.validatePayment,name="validatePaymentAdmin"),#admin/staff
    path('kitAlreadyReceived/', views.kitAlreadyReceived,name="kitAlreadyReceived"),#admin/staff
    path('kitReceivedSuccessfully/', views.kitReceivedSuccessfully,name="kitReceivedSuccessfully"),#admin/staff
    path('consultWelcomeKit/', views.listarRecibioKit, name='consultWelcomeKit'),#admin/staff
    path('scholarshipAssignations/', views.scholarshipAssignations, name='scholarshipAssignations'),#admin/staff

]
urlpatterns += staticfiles_urlpatterns() 
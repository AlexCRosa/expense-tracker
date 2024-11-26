from django.urls import path
from .views import (
    SignupView, CustomLoginView, CustomLogoutView, CustomPasswordChangeView,
    CustomPasswordChangeDoneView, CustomPasswordResetView, CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView, CustomPasswordResetCompleteView
)

app_name = 'accounts'

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Password Change URLs
    path('password_change/', 
         CustomPasswordChangeView.as_view(template_name='registration/password_change.html'), 
         name='password_change'),
    path('password_change/done/', 
         CustomPasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), 
         name='password_change_done'),

    # Password Reset URLs
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

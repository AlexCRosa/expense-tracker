from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.views import (LoginView, LogoutView, PasswordChangeView, 
                                       PasswordChangeDoneView, PasswordResetView, 
                                       PasswordResetDoneView, PasswordResetConfirmView, 
                                       PasswordResetCompleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin


# Signup View
class SignupView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        """Save the form and add a success message."""
        form.save()
        messages.success(self.request, 'Account created successfully! Please log in.')
        return super().form_valid(form)


# Custom Login View
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        return reverse_lazy('core:dashboard')


# Custom Logout View
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')


# Password Change View
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'registration/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')


# Password Change Done View
class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'


# Password Reset View
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')


# Password Reset Done View
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


# Password Reset Confirm View
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


# Password Reset Complete View
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'

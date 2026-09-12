from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from core.models import User


class BootstrapFieldsMixin:
    """Puts the Bootstrap form-control class on every field widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class CustomUserCreationForm(BootstrapFieldsMixin, UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]


class CustomAuthenticationForm(BootstrapFieldsMixin, AuthenticationForm):
    pass


class CustomPasswordChangeForm(BootstrapFieldsMixin, PasswordChangeForm):
    pass


class CustomPasswordResetForm(BootstrapFieldsMixin, PasswordResetForm):
    pass


class CustomSetPasswordForm(BootstrapFieldsMixin, SetPasswordForm):
    pass

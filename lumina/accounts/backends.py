# accounts/backends.py
# Lets members log in with their email address in ANY letter case.
# (Django's default ModelBackend compares the email exactly, so "Ada@Mail.com"
#  and "ada@mail.com" would be treated as two different people.)

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        # Django passes the login field as "username" even though ours is the email
        email = username or kwargs.get(User.USERNAME_FIELD)
        if email is None or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=email.strip())
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            # Run the hasher once anyway so timing does not reveal which emails exist
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

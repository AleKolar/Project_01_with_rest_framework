# from django.contrib.auth import user_logged_in
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import CustomUser
# from .tasks import send_one_time_code_email, send_confirmation_code
#
#
# @receiver(post_save, sender=CustomUser)
# def send_one_time_code_email(sender, instance, created, **kwargs):
#     if created:
#         send_one_time_code_email.delay(instance.pk)
#
#
# @receiver(user_logged_in)
# def send_confirmation_code(sender, user, request, **kwargs):
#     send_confirmation_code.delay(user.pk)

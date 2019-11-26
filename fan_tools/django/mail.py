from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.module_loading import import_string


class Mail:
    template_subject_suffix = '_subject.txt'
    template_message_suffix = '_body.txt'
    template_message_html_suffix = '_body.html'

    def __init__(self, *args, **kwargs):

        self.sender = kwargs.get(
            'sender',
            getattr(
                settings,
                'DEFAULT_FROM_EMAIL',
                None,
            ),
        )
        self.recipient_list = kwargs.get('recipient_list', [])

        self.template_name = kwargs.get('template_name')
        self.context = kwargs.get('context', {})

        self.fail_silently = kwargs.get('fail_silently', False)

    def send(self):

        mail = EmailMultiAlternatives(
            render_to_string(
                self.template_name + Mail.template_subject_suffix,
                self.context,
            ).strip(),
            render_to_string(
                self.template_name + Mail.template_message_suffix,
                self.context,
            ),
            self.sender,
            self.recipient_list,
            connection=import_string(settings.EMAIL_BACKEND)(
                fail_silently=self.fail_silently,
            ),
        )
        mail.attach_alternative(
            render_to_string(
                self.template_name + Mail.template_message_html_suffix,
                self.context,
            ),
            'text/html',
        )
        return mail.send()

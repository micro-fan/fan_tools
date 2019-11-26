from fan_tools.django.mail import Mail


def test_mail():
    Mail(
        recipient_list=['test@test.com', ],
        template_name='test_email',
    ).send()

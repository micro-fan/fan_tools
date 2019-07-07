import os
import uuid


class UploadNameGenerator(object):

    def __init__(self, model_name, field_name):
        self.model_name = model_name
        self.field_name = field_name

    def deconstruct(self):
        return (
            'tipsi_tools.django.UploadNameGenerator',
            (),
            {
                'model_name': self.model_name,
                'field_name': self.field_name,
            },
        )

    def __call__(self, instance, filename):
        return os.path.join(
            'static',
            self.model_name,
            '%s-%s-%s%s' % (
                self.model_name,
                self.field_name,
                uuid.uuid1(),
                os.path.splitext(filename)[1],
            ),
        )

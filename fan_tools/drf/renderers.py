from rest_framework.renderers import JSONRenderer


class ApiRenderer(JSONRenderer):

    def render(
        self,
        data,
        media_type=None,
        renderer_context=None,
    ):
        wrapper = {
            'version': '001',
        }
        # move error to the root level
        if hasattr(data, 'get') and data.get('error'):
            wrapper['error'] = data['error']
            # UserWrapper support
            wrapper['status_code'] = data['error']['status']
            wrapper['error_message'] = data['error']['message']

            del data['error']

        if data is not None:
            wrapper['data'] = data

        return super().render(
            wrapper,
            media_type,
            renderer_context,
        )

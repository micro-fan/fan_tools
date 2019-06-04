from rest_framework.pagination import PageNumberPagination
from rest_framework.pagination import _positive_int


class ApiPageNumberPagination(PageNumberPagination):
    ''' Allow turn off pagination by specifying zero page_zize.'''

    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        """
        Disable pagination by 'listening' for a zero value for
        page_size_query_param
        """
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=False,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size

from fan_tools.django.url import build_absolute_uri


class FakeRequest():

    scheme = 'https'

    def get_host(self):
        return 'google.com'


def test_build_absolute_uri():
    assert build_absolute_uri(FakeRequest()) == 'https://google.com'

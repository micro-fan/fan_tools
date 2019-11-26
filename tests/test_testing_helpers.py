import pytest
from fan_tools.testing import ApiUrls


@pytest.fixture(scope='session')
def api_v_base():
    yield 'http://localhost/v001'


@pytest.fixture(scope='session')
def api(api_v_base):
    yield ApiUrls(
        '{}/'.format(api_v_base),
        {
            'password_reset_request': 'password/request/code/',
            'password_reset': 'password/reset/',
            'user_review_list': 'user/{user_id}/review/',
            'user_review': 'user/{user_id}/review/{review_id}/',
            'wine_review': 'wine/{wine_id}/review/',
            'drink_review': 'drink/{drink_id}/review/',
        },
    )


def test_review_list(api):
    user_id = 'user_1'
    assert api.user_review_list(user_id=user_id) == 'http://localhost/v001/user/user_1/review/'
    with pytest.raises(KeyError):
        api.user_review_list()
    assert api.password_reset(user_id=user_id) == 'http://localhost/v001/password/reset/'

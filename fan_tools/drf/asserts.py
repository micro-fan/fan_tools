def assert_validation_error(response, field, code):
    assert 'error' in response
    error = response['error']

    assert 'detail' in error
    detail = error['detail']

    assert field in detail
    items = detail[field]

    found = False
    for item in items:
        if item['code'] == code:
            found = True

    assert found

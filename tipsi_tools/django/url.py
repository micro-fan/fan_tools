def build_absolute_uri(request):

    return '{scheme}://{host}'.format(
        scheme=request.scheme,
        host=request.get_host(),
    )

class ApiUrls:
    def __init__(self, base, urls):
        self.base = base
        self.urls = urls

    def __getattr__(self, name):
        url_tpl = self.urls.get(name)
        if url_tpl is None:
            raise AttributeError
        return '{}{}'.format(self.base, url_tpl).format

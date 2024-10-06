from django.middleware.csrf import CsrfViewMiddleware

class CustomCsrfMiddleware(CsrfViewMiddleware):
    def _set_token(self, request, response):
        super()._set_token(request, response)
        response.cookies['csrftoken']['samesite'] = 'None'
        response.cookies['csrftoken']['secure'] = True

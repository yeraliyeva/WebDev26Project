from django.urls import get_script_prefix, set_script_prefix


class ForwardedPrefixMiddleware:
    """
    Middleware that sets the script prefix (subpath) based on the 
    X-Forwarded-Prefix header sent by the reverse proxy (Traefik).
    
    This ensures that Django correctly generates absolute URLs, redirects,
    and asset links behind a subpath proxy.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        previous_prefix = get_script_prefix()
        forwarded_prefix = request.META.get("HTTP_X_FORWARDED_PREFIX", "").split(",")[0].strip()

        if forwarded_prefix:
            prefix = "/" + forwarded_prefix.strip("/")
            request.META['SCRIPT_NAME'] = prefix
            request.path = prefix + request.path_info
            set_script_prefix(prefix + "/")
        else:
            set_script_prefix("/")

        try:
            return self.get_response(request)
        finally:
            set_script_prefix(previous_prefix)
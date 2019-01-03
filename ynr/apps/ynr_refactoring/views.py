from django.views.defaults import page_not_found, ERROR_404_TEMPLATE_NAME
from .models import PageNotFoundLog


def logged_page_not_found_wrapper(request, *args, **kwargs):
    # Log stuff
    PageNotFoundLog(url=request.path).save()
    return page_not_found(request, *args, **kwargs)

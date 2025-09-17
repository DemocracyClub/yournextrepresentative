from django.db import connection
from django.db.utils import OperationalError
from django.http import HttpResponse


def trigger_error(request):
    return 1 / 0


def status_check(request):
    try:
        connection.cursor()
    except OperationalError:
        return HttpResponse("service unavailable", status=503)

    return HttpResponse("OK", status=200)

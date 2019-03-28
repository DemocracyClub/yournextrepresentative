from frontend.models import SiteBanner


def site_wide_banner(request):
    """Add a site wide banner"""

    try:
        banner = SiteBanner.objects.live().latest()
    except SiteBanner.DoesNotExist:
        banner = None

    return {"site_wide_banner": banner}

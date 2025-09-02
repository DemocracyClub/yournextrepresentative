from django.conf import settings
from django.core.management import call_command
from django_q.models import Schedule
from django_q_registry import register_task


@register_task(
    name="Process images in moderation queue",
    schedule_type=Schedule.CRON,
    cron="* * * * *",
)
def moderation_queue_process_queued_images():
    if settings.ENABLE_SCHEDULED_JOBS:
        call_command("moderation_queue_process_queued_images")


@register_task(
    name="Parse raw data from SOPNs",
    schedule_type=Schedule.CRON,
    cron="* * * * *",
)
def sopn_parsing_process_unparsed():
    if settings.ENABLE_SCHEDULED_JOBS:
        call_command("sopn_parsing_process_unparsed")


@register_task(
    name="Update parties from EC",
    schedule_type=Schedule.CRON,
    cron="6 2 * * *",
)
def parties_import_from_ec():
    if settings.ENABLE_SCHEDULED_JOBS:
        call_command("parties_import_from_ec", post_to_slack=True)


@register_task(
    name="Look for recent changes in EE",
    schedule_type=Schedule.CRON,
    cron="*/5 * * * *",
)
def uk_create_elections_from_every_election_recently_updated():
    if settings.ENABLE_SCHEDULED_JOBS:
        call_command(
            "uk_create_elections_from_every_election",
            recently_updated=True,
        )


@register_task(
    name="Check for current elections",
    schedule_type=Schedule.CRON,
    cron="23 23 * * *",
)
def uk_create_elections_from_every_election_check_current():
    if settings.ENABLE_SCHEDULED_JOBS:
        call_command(
            "uk_create_elections_from_every_election", check_current=True
        )


@register_task(
    name="Mop up any missed recently modified elections",
    schedule_type=Schedule.CRON,
    cron="23 23 * * *",
)
def uk_create_elections_from_every_election_mop_up():
    if settings.ENABLE_SCHEDULED_JOBS:
        call_command(
            "uk_create_elections_from_every_election",
            recently_updated=True,
            recently_updated_delta=25,
        )


@register_task(
    name="Update materialized view",
    schedule_type=Schedule.CRON,
    cron="*/5 * * * *",
)
def update_data_export_view():
    if settings.ENABLE_SCHEDULED_JOBS:
        call_command("update_data_export_view")

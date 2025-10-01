from django.conf import settings
from django.core.management import call_command as core_call_command
from django_q.models import Schedule
from django_q_registry import register_task


def call_command(*args, **kwargs):
    if settings.ENABLE_SCHEDULED_JOBS:
        core_call_command(*args, **kwargs)


@register_task(
    name="Look for recent changes in EE",
    schedule_type=Schedule.CRON,
    cron="0-59/5 * * * *",
)
def uk_create_elections_from_every_election_recently_updated():
    call_command(
        "uk_create_elections_from_every_election",
        recently_updated=True,
    )


@register_task(
    name="Process images in moderation queue",
    schedule_type=Schedule.CRON,
    cron="1-59/5 * * * *",
)
def moderation_queue_process_queued_images():
    call_command("moderation_queue_process_queued_images")


@register_task(
    name="Parse raw data from SOPNs",
    schedule_type=Schedule.CRON,
    cron="2-59/5 * * * *",
)
def sopn_parsing_process_unparsed():
    call_command("sopn_parsing_process_unparsed")


@register_task(
    name="Update materialized view",
    schedule_type=Schedule.CRON,
    cron="3-59/5 * * * *",
)
def update_data_export_view():
    call_command("update_data_export_view")


@register_task(
    name="Update parties from EC",
    schedule_type=Schedule.CRON,
    cron="6 2 * * *",
)
def parties_import_from_ec():
    call_command("parties_import_from_ec", post_to_slack=True)


@register_task(
    name="Check for current elections",
    schedule_type=Schedule.CRON,
    cron="23 23 * * *",
)
def uk_create_elections_from_every_election_check_current():
    call_command("uk_create_elections_from_every_election", check_current=True)


@register_task(
    name="Mop up any missed recently modified elections",
    schedule_type=Schedule.CRON,
    cron="23 23 * * *",
)
def uk_create_elections_from_every_election_mop_up():
    call_command(
        "uk_create_elections_from_every_election",
        recently_updated=True,
        recently_updated_delta=25,
    )

import ast
import pathlib
import re

from django.conf import settings

TASKS_PATH = pathlib.Path(__file__).parent / "tasks.py"


def parse_cron_from_decorator(decorator):
    for kw in decorator.keywords:
        if kw.arg == "cron":
            return kw.value.value
    return None


def cron_is_too_frequent(cron_expr):
    """
    Returns True if a cron expression runs more frequently than
    every settings.MINIMUM_CRON_INTERVAL_MINUTES
    Only supports simple minute fields like '*/N', '0-59/N', or explicit lists
    """
    minute_field = cron_expr.split()[0]

    # Patterns for every N minutes
    match = re.match(r"^(?:\*/|\d+-\d+/)(\d+)$", minute_field)

    if match:
        interval = int(match.group(1))
        return interval < settings.MINIMUM_CRON_INTERVAL_MINUTES

    # Explicit list of minutes (e.g., "0,5,10,15,...")
    if "," in minute_field:
        minutes = [int(m) for m in minute_field.split(",") if m.isdigit()]
        if len(minutes) > (60 // settings.MINIMUM_CRON_INTERVAL_MINUTES):
            return True

    # If it's just '*', that's every minute
    if minute_field.strip() == "*":
        return settings.MINIMUM_CRON_INTERVAL_MINUTES > 1

    return False


def test_task_intervals():
    with open(TASKS_PATH) as f:
        tree = ast.parse(f.read(), filename=str(TASKS_PATH))

    failures = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and getattr(decorator.func, "id", None) == "register_task"
                ):
                    cron = parse_cron_from_decorator(decorator)
                    if cron and cron_is_too_frequent(cron):
                        failures.append(f"{node.name}: cron={cron}")

    assert not failures, (
        f"Some scheduled tasks run more frequently than every {settings.MINIMUM_CRON_INTERVAL_MINUTES} minutes:\n"
        + "\n".join(failures)
    )

"""Constants for notion_todo."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "Notion ToDo"
DOMAIN = "notion_todo"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by https://api.notion.com/v1"
NOTION_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-02-22"
CONF_DATABASE_ID = "database_id"

# Property NAMES specific to the "✅ Aufgaben" database in the Hausanierung
# Notion workspace (not Notion's native Task-List template properties -
# this DB uses plain Select fields instead). Looked up by name rather than
# Notion's internal property ID, since that ID differs between the internal
# Notion UI representation and what the public REST API actually returns.
TASK_TITLE_PROPERTY = "Aufgabe"
TASK_STATUS_PROPERTY = "Status"  # select: Blockiert/Zu erledigen/.../Erledigt/wont do
TASK_IMPORTANCE_PROPERTY = "Art"  # select: Kernaufgabe/Lückenfüller

# Values of the "Status" select used to mark completion in HA <-> Notion.
STATUS_DONE_VALUES = ("Erledigt", "wont do")
STATUS_REOPEN_VALUE = "Zu erledigen"

# Only surface important, still-open tasks: Art = Kernaufgabe.
IMPORTANCE_FILTER_VALUE = "Kernaufgabe"

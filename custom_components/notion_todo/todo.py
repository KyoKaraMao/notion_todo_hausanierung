"""A todo platform for Notion."""

from typing import cast

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, TASK_TITLE_PROPERTY, TASK_STATUS_PROPERTY, STATUS_DONE_VALUES, STATUS_REOPEN_VALUE
from .coordinator import NotionDataUpdateCoordinator
from .notion_property_helper import NotionPropertyHelper as propHelper

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the todo platform config entry."""
    coordinator: NotionDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = ['Sanierungsaufgaben']
    async_add_entities(
        NotionTodoListEntity(coordinator, e)
        for e in entities
    )

class NotionTodoListEntity(CoordinatorEntity[NotionDataUpdateCoordinator], TodoListEntity):
    """A Notion TodoListEntity."""

    # Read + check off only: new tasks and their importance/topic are still
    # managed in Notion itself, HA is just the "at a glance, tick it off" view.
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(
        self,
        coordinator: NotionDataUpdateCoordinator,
        user: str,
    ) -> None:
        """Initialize TodoListEntity."""
        super().__init__(coordinator=coordinator)
        self._attr_unique_id = f"{user}-{user}"
        self._attr_name = user

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data is None:
            self._attr_todo_items = None
        else:
            items = []
            for task in self.coordinator.data['results']:
                id = task['id']
                notion_status = propHelper.get_property_by_name(TASK_STATUS_PROPERTY, task)
                status = (
                    TodoItemStatus.COMPLETED
                    if notion_status in STATUS_DONE_VALUES
                    else TodoItemStatus.NEEDS_ACTION
                )

                items.append(
                    TodoItem(
                        summary=propHelper.get_property_by_name(TASK_TITLE_PROPERTY, task),
                        uid=id,
                        status=status,
                    )
                )
            self._attr_todo_items = items
        super()._handle_coordinator_update()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a To-do item (checking it off writes back to Notion)."""
        uid: str = cast(str, item.uid)
        status = (
            STATUS_DONE_VALUES[0]
            if item.status == TodoItemStatus.COMPLETED
            else STATUS_REOPEN_VALUE
        )

        await self.coordinator.client.update_task(
            task_id=uid,
            title=item.summary,
            status=status,
        )

        await self.coordinator.async_refresh()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass update state from existing coordinator data."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

"""Notion API Client."""
from __future__ import annotations

import asyncio
import socket
import aiohttp
import async_timeout

from .const import (
    NOTION_URL,
    NOTION_VERSION,
    TASK_TITLE_PROPERTY,
    TASK_STATUS_PROPERTY,
    TASK_IMPORTANCE_PROPERTY,
    IMPORTANCE_FILTER_VALUE,
    STATUS_DONE_VALUES,
)


class NotionApiClientError(Exception):
    """Exception to indicate a general API error."""


class NotionApiClientCommunicationError(
    NotionApiClientError
):
    """Exception to indicate a communication error."""


class NotionApiClientAuthenticationError(
    NotionApiClientError
):
    """Exception to indicate an authentication error."""


class NotionApiClient:
    """Notion API Client."""

    _headers = {
        'Authorization': 'Bearer <TOKEN>',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION
        }

    def __init__(
        self,
        token: str,
        database_id: str,
        session: aiohttp.ClientSession
    ) -> None:
        """Notion API Client.

        Args:
            token (str): Notion token with access to ToDo database
            database_id (str): id of the ToDo database
            session (aiohttp.ClientSession): the session

        """
        self._token = token
        self._session = session
        self._headers['Authorization'] = f'Bearer {token}'
        self._database_id = database_id

    async def async_get_data(self) -> any:
        """Get data from the API.

        Only important, still-open tasks: Art = Kernaufgabe and Status not
        in the completed states (Erledigt/wont do stay excluded so old
        finished tasks don't clutter the HA todo list).
        """
        done_filters = [
            {"property": TASK_STATUS_PROPERTY, "select": {"does_not_equal": value}}
            for value in STATUS_DONE_VALUES
        ]
        query = {
            "filter": {
                "and": [
                    {"property": TASK_IMPORTANCE_PROPERTY, "select": {"equals": IMPORTANCE_FILTER_VALUE}},
                    *done_filters,
                ]
            }
        }
        return await self._api_wrapper(
            method="post",
            url=f"{NOTION_URL}/databases/{self._database_id}/query",
            headers=self._headers,
            data=query,
        )

    async def update_task(
        self,
        task_id: str,
        title: str,
        status: str,
    ) -> any:
        """Update task in Notion (title + Status select only).

        Args:
            task_id (str): id of the task
            title: (str): Title of the task
            status (str): value of the "Status" select property

        """
        properties = {
            TASK_TITLE_PROPERTY: {"title": [{"type": "text", "text": {"content": title}}]},
            TASK_STATUS_PROPERTY: {"select": {"name": status}},
        }
        return await self._api_wrapper(
            method="patch",
            url=f"{NOTION_URL}/pages/{task_id}",
            headers=self._headers,
            data={"properties": properties}
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                if response.status in (401, 403):
                    raise NotionApiClientAuthenticationError(
                        "Invalid credentials",
                    )
                response.raise_for_status()
                return await response.json()

        except asyncio.TimeoutError as exception:
            raise NotionApiClientCommunicationError(
                "Timeout error fetching information",
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise NotionApiClientCommunicationError(
                "Error fetching information",
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise NotionApiClientError(
                "Something really wrong happened!"
            ) from exception

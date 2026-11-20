import asyncio
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, time
from uuid import UUID

import httpx
from fastapi import FastAPI
from nicegui import app as nicegui_app
from nicegui import ui
from pydantic import BaseModel, ValidationError

from src.config.default import get_settings
from src.models.enums import ResourceOperationType, Status
from src.models.pydantic_models import (
    ClaimRequest,
    LeaseRequest,
    ReleaseRequest,
    RenewRequest,
    ResourceIn,
    ResourceLeaseOut,
    ResourceOut,
    ResourcesOperationsOut,
    ResourcesOut,
    Variable,
)

PAGE_SIZE = 10
SURFACE = "rounded-xl border border-[#273044] bg-[#141b29]"
FIELD = "outlined dense hide-bottom-space"
BUTTON = "unelevated no-caps"
WIDTH = "w-full max-w-[1160px] mx-auto px-4 sm:px-8"
DIALOG = "w-[min(520px,calc(100vw-32px))] max-w-full rounded-2xl bg-[#141b29] p-5 sm:p-6 gap-4"
STATUS_LABELS = {Status.FREE: "Free", Status.BLOCKED: "Booked"}
OPERATION_LABELS = {
    ResourceOperationType.BLOCK: "Reserved",
    ResourceOperationType.RENEW: "Extended",
    ResourceOperationType.RELEASE: "Released",
    ResourceOperationType.EXPIRE: "Expired",
}


class ApiError(Exception):
    pass


async def api(method, path, *, params=None, body: BaseModel | None = None, response_model=None):
    try:
        response = await nicegui_app.state.api_client.request(
            method, path, params=params, json=body.model_dump(mode="json", exclude_none=True) if body else None
        )
    except httpx.RequestError as exc:
        raise ApiError("Could not reach the API. Check the connection and try again.") from exc

    if response.is_error:
        try:
            detail = response.json().get("detail")
        except ValueError, AttributeError:
            detail = None
        if response.status_code == 409:
            raise ApiError("The resource state changed or the lease token is invalid. Refresh and check the lease.")
        if response.status_code == 404:
            raise ApiError("This resource no longer exists.")
        if response.status_code < 500 and isinstance(detail, str):
            raise ApiError(detail)
        raise ApiError(f"The API returned HTTP {response.status_code}.")

    if response.status_code == 204 or response_model is None:
        return None
    try:
        return response_model.model_validate_json(response.content)
    except ValidationError as exc:
        raise ApiError("The API returned an unexpected response.") from exc


def split_tags(value: str) -> list[str]:
    return list(dict.fromkeys(tag.strip() for tag in value.split(",") if tag.strip()))


def format_time(value: datetime | None) -> str:
    return value.astimezone(UTC).strftime("%d %b %Y, %H:%M") if value else "—"


def badge(label: str, colors: str) -> None:
    ui.label(label).classes(f"w-fit whitespace-nowrap rounded-full px-2.5 py-1 text-sm font-medium {colors}")


def status_badge(status: Status) -> None:
    colors = "bg-emerald-400/10 text-emerald-300" if status == Status.FREE else "bg-amber-400/10 text-amber-300"
    badge(STATUS_LABELS[status], colors)


def metric(label: str, icon: str, colors: str):
    with ui.row().classes(f"{SURFACE} min-w-0 flex-nowrap items-start justify-between gap-2 px-4 py-4 sm:px-5"):
        with ui.column().classes("gap-2"):
            ui.label(label).classes("text-sm font-medium text-slate-300")
            value = ui.label("—").classes("text-3xl leading-none font-semibold tabular-nums tracking-tight")
        ui.icon(icon).classes(f"rounded-lg p-2 text-lg {colors}")
    return value


def form_actions(dialog, label: str, submit: Callable[[], Awaitable[None]], color: str = "primary") -> None:
    error = ui.label().classes("text-sm text-rose-300").set_visibility(False)

    async def save() -> None:
        if not button.enabled:
            return
        button.disable()
        cancel.disable()
        error.set_visibility(False)
        try:
            await submit()
        except ValidationError as exc:
            issue = exc.errors()[0]
            field = str(issue["loc"][0]).replace("_", " ").capitalize()
            error.set_text(f"{field} · {issue['msg']}")
            error.set_visibility(True)
        except (ApiError, ValueError) as exc:
            error.set_text(str(exc))
            error.set_visibility(True)
        finally:
            if not button.is_deleted:
                button.enable()
                cancel.enable()

    with ui.row().classes("w-full justify-end gap-2 pt-2"):
        cancel = ui.button("Cancel", on_click=dialog.close, color=None).props("flat no-caps")
        button = ui.button(label, on_click=save, color=color).props(BUTTON)


class PagedTable:
    def __init__(self, headers, fetch, render_row, empty_message):
        self.headers = headers
        self.fetch = fetch
        self.render_row = render_row
        self.empty_message = empty_message
        self.skip = 0
        self.load_id = 0
        with ui.column().classes("w-full gap-0") as self.content:
            ui.label("Loading…").classes("px-5 py-8 text-slate-400").props("role=status")

    async def load(self, skip: int = 0) -> bool:
        self.load_id += 1
        current = self.load_id
        try:
            result = await self.fetch(skip)
            if skip and result.filtered_count <= skip:
                skip = max(0, (result.filtered_count - 1) // PAGE_SIZE * PAGE_SIZE)
                result = await self.fetch(skip)
        except (ApiError, ValueError) as exc:
            if current == self.load_id:
                self.content.clear()
                with self.content:
                    ui.label(str(exc)).classes("px-5 py-8 text-rose-300").props("role=alert")
            return False
        if current != self.load_id:
            return False
        self.skip = skip
        self.content.clear()
        with self.content:
            if result.items:
                self.table(result.items)
                self.pagination(len(result.items), result.filtered_count)
            else:
                ui.label(self.empty_message).classes("px-5 py-12 text-sm text-slate-400").props("role=status")
        return True

    def table(self, items):
        with (
            ui.element("div").classes("w-full overflow-x-auto"),
            ui.element("table").classes("w-full min-w-[660px] border-collapse text-left text-sm"),
        ):
            with ui.element("thead").classes("border-y border-[#273044] bg-slate-950/30 text-slate-400"):
                with ui.element("tr"):
                    for header in self.headers:
                        with ui.element("th").props("scope=col").classes("whitespace-nowrap px-4 py-3 font-medium"):
                            ui.label(header)
            with ui.element("tbody"):
                for item in items:
                    with ui.element("tr").classes("border-b border-[#273044] hover:bg-white/[0.025]"):
                        self.render_row(item)

    def pagination(self, size: int, total: int) -> None:
        async def previous() -> None:
            await self.load(self.skip - PAGE_SIZE)

        async def next_page() -> None:
            await self.load(self.skip + PAGE_SIZE)

        with ui.row().classes("w-full items-center justify-between gap-2 px-4 py-2.5"):
            ui.label(f"{self.skip + 1}-{self.skip + size} of {total}").classes("text-sm tabular-nums text-slate-400")
            with ui.row().classes("gap-2"):
                prev = ui.button(icon="chevron_left", on_click=previous, color=None).props(
                    'flat round dense aria-label="Previous page"'
                )
                following = ui.button(icon="chevron_right", on_click=next_page, color=None).props(
                    'flat round dense aria-label="Next page"'
                )
                prev.set_enabled(self.skip > 0)
                following.set_enabled(self.skip + size < total)


def cell():
    return ui.element("td").classes("px-4 py-3 align-middle")


@ui.page("/")
async def dashboard():
    tokens: dict[UUID, UUID] = {}
    resource_names: dict[UUID, str] = {}

    async def update_health() -> None:
        try:
            await api("GET", "/healthcheck")
        except ApiError:
            health.set_text("API offline")
            health.classes(add="text-rose-300", remove="text-emerald-300")
        else:
            health.set_text("API online")
            health.classes(add="text-emerald-300", remove="text-rose-300")

    async def update_counts() -> None:
        async def set_count(label, resource_status=None):
            params = {"limit": 1}
            if resource_status:
                params["status"] = resource_status
            try:
                result = await api("GET", "/resources", params=params, response_model=ResourcesOut)
            except ApiError:
                label.set_text("—")
            else:
                label.set_text(f"{result.filtered_count:,}")

        await asyncio.gather(set_count(total), set_count(free, Status.FREE), set_count(booked, Status.BLOCKED))

    async def refresh() -> None:
        refresh_button.disable()
        try:
            if tabs.value == "Activity":
                await asyncio.gather(activity_table.load(activity_table.skip), update_health())
            else:
                await asyncio.gather(resource_table.load(resource_table.skip), update_counts(), update_health())
        finally:
            refresh_button.enable()

    async def fetch_resources(skip: int) -> ResourcesOut:
        params = [("skip", skip), ("limit", PAGE_SIZE)]
        if status_filter.value:
            params.append(("status", status_filter.value))
        params.extend(("tags", tag) for tag in split_tags(tag_filter.value))
        result = await api("GET", "/resources", params=params, response_model=ResourcesOut)
        resource_names.update((item.id, item.resource_name) for item in result.items)
        return result

    async def fetch_activity(skip: int) -> ResourcesOperationsOut:
        params = {"skip": skip, "limit": PAGE_SIZE}
        if resource_filter.value.strip():
            try:
                params["resource_id"] = str(UUID(resource_filter.value.strip()))
            except ValueError:
                raise ValueError("Enter a valid resource UUID.") from None
        if operation_filter.value:
            params["operation"] = operation_filter.value
        start = date.fromisoformat(from_filter.value) if from_filter.value else None
        end = date.fromisoformat(to_filter.value) if to_filter.value else None
        if start and end and start > end:
            raise ValueError("The start date must be on or before the end date.")
        if start:
            params["start_date"] = datetime.combine(start, time.min, UTC).isoformat()
        if end:
            params["end_date"] = datetime.combine(end, time.max, UTC).isoformat()
        return await api("GET", "/resources/actions", params=params, response_model=ResourcesOperationsOut)

    async def display_resource(resource_id: UUID) -> None:
        try:
            resource = await api("GET", f"/resources/{resource_id}", response_model=ResourceOut)
        except ApiError as exc:
            ui.notify(str(exc), type="negative")
            return
        open_resource(resource)

    def render_resource(resource: ResourceOut) -> None:
        async def open_details() -> None:
            await display_resource(resource.id)

        with cell():
            ui.button(resource.resource_name, on_click=open_details, color=None).props(
                "flat no-caps padding=none"
            ).classes("text-left text-sm font-semibold text-slate-100")
        with cell():
            with ui.row().classes("items-center gap-1.5"):
                for tag in resource.tags:
                    ui.label(tag).classes("rounded-md bg-slate-800 px-2 py-0.5 text-sm text-slate-300")
                if not resource.tags:
                    ui.label("—").classes("text-slate-500")
        with cell():
            status_badge(resource.status)
        with cell():
            ui.label(resource.lease_owner or "—").classes("text-slate-300")
        with cell():
            ui.label(format_time(resource.lease_expires_at)).classes("whitespace-nowrap tabular-nums text-slate-400")

    def render_activity(event) -> None:
        async def open_details() -> None:
            await display_resource(event.resource_id)

        with cell():
            ui.label(format_time(event.created_at)).classes("whitespace-nowrap tabular-nums text-slate-300")
        with cell():
            badge(OPERATION_LABELS[event.operation], "bg-slate-800 text-slate-200")
        with cell():
            ui.button(
                resource_names.get(event.resource_id, str(event.resource_id)), on_click=open_details, color=None
            ).props("flat no-caps padding=none").classes("text-left text-sm text-slate-200")
        with cell():
            ui.label(event.description or "—").classes("break-words text-slate-400")

    async def change_tab(event) -> None:
        if event.value == "Activity":
            await activity_table.load()

    def show_dialog(dialog) -> None:
        dialog.on("hide", dialog.delete)
        dialog.open()

    def open_resource(resource: ResourceOut) -> None:
        async def show_history() -> None:
            resource_filter.set_value(str(resource.id))
            dialog.close()
            if tabs.value == "Activity":
                await activity_table.load()
            else:
                tabs.set_value("Activity")

        def show_action(action: str) -> None:
            dialog.close()
            if action == "Delete":
                delete_dialog(resource)
            else:
                lease_dialog(action, resource)

        with overlays, ui.dialog() as dialog, ui.card().classes(DIALOG):
            with ui.row().classes("w-full flex-nowrap items-start justify-between gap-3"):
                ui.label(resource.resource_name).classes("min-w-0 break-words text-2xl font-semibold tracking-tight")
                status_badge(resource.status)
            ui.label(str(resource.id)).classes("break-all font-mono text-xs text-slate-400")
            if resource.description:
                ui.label(resource.description).classes("break-words text-base text-slate-200")
            if resource.tags:
                with ui.row().classes("gap-2"):
                    for tag in resource.tags:
                        badge(tag, "bg-slate-800 text-slate-300")
            if resource.status == Status.BLOCKED:
                with ui.row().classes("w-full gap-x-8 gap-y-3 rounded-lg bg-slate-950/40 p-3"):
                    with ui.column().classes("gap-1"):
                        ui.label("Lease owner").classes("text-sm text-slate-400")
                        ui.label(resource.lease_owner or "—").classes("break-all")
                    with ui.column().classes("gap-1"):
                        ui.label("Expires · UTC").classes("text-sm text-slate-400")
                        ui.label(format_time(resource.lease_expires_at))
            if resource.variables:
                with ui.expansion("Variables", icon="data_object").classes("w-full rounded-lg bg-slate-950/40"):
                    for variable in resource.variables:
                        with ui.row().classes("w-full items-baseline gap-2 px-3 py-1.5"):
                            ui.label(variable.name).classes("break-all font-medium")
                            ui.label(variable.value).classes("break-all font-mono text-sm text-slate-300")
            unlocked = resource.status == Status.FREE
            actions = ("Reserve",) if unlocked else ("Release", "Extend")
            with ui.row().classes("w-full items-center justify-between gap-2"):
                ui.button("History", icon="history", on_click=show_history, color=None).props("flat no-caps")
                with ui.row().classes("gap-2"):
                    ui.button("Close", on_click=dialog.close, color=None).props("flat no-caps")
                    for action in actions:
                        ui.button(action, on_click=lambda _, action=action: show_action(action)).props(BUTTON)
            if unlocked:
                ui.separator()
                ui.button("Delete resource", on_click=lambda: show_action("Delete"), color="negative").props(
                    "flat no-caps"
                ).classes("self-start")
        show_dialog(dialog)

    async def update_after_change(dialog, message: str) -> None:
        dialog.close()
        ui.notify(message, type="positive")
        if tabs.value == "Activity":
            await asyncio.gather(activity_table.load(), resource_table.load(resource_table.skip), update_counts())
        else:
            await asyncio.gather(resource_table.load(resource_table.skip), update_counts())

    def create_dialog() -> None:
        variables = []

        def add_variable() -> None:
            with variable_rows, ui.row().classes("w-full flex-nowrap items-center gap-2") as row:
                name = ui.input("Name").props(f"{FIELD} maxlength=255").classes("min-w-0 flex-1")
                value = ui.input("Value").props(f"{FIELD} maxlength=255").classes("min-w-0 flex-1")
                pair = (name, value)
                variables.append(pair)

                def remove() -> None:
                    variables.remove(pair)
                    row.delete()

                ui.button(icon="close", on_click=remove, color=None).props(
                    'flat round dense aria-label="Remove variable"'
                )

        async def submit() -> None:
            body = ResourceIn(
                resource_name=name.value.strip(),
                description=description.value.strip() or None,
                tags=split_tags(tags.value),
                variables=[
                    Variable(name=key.value.strip(), value=value.value)
                    for key, value in variables
                    if key.value.strip() or value.value
                ],
            )
            if any(not variable.name for variable in body.variables):
                raise ValueError("Enter a name for every variable.")
            created = await api("POST", "/resources", body=body, response_model=ResourceOut)
            await update_after_change(dialog, f"Created {created.resource_name}.")
            open_resource(created)

        with overlays, ui.dialog().props("persistent") as dialog, ui.card().classes(DIALOG):
            ui.label("New resource").classes("text-xl font-semibold")
            name = ui.input("Name").props(f"{FIELD} maxlength=100").classes("w-full")
            description = ui.textarea("Description").props(f"{FIELD} maxlength=255 autogrow").classes("w-full")
            tags = ui.input("Tags · comma-separated").props(FIELD).classes("w-full")
            with ui.column().classes("w-full gap-2") as variable_rows:
                pass
            ui.button("Add variable", icon="add", on_click=add_variable, color=None).props("flat no-caps")
            form_actions(dialog, "Create resource", submit)
        show_dialog(dialog)

    def lease_dialog(action: str, resource: ResourceOut | None = None) -> None:
        existing = action in ("Release", "Extend")
        resource_path = f"/resources/{resource.id}" if resource else "/resources"

        async def submit() -> None:
            note = description.value.strip() or None
            if existing:
                try:
                    lease_token = UUID(token.value.strip())
                except ValueError:
                    raise ValueError("Enter a valid lease token.") from None
                if action == "Release":
                    await api(
                        "PUT",
                        f"{resource_path}/release",
                        body=ReleaseRequest(lease_token=lease_token, description=note),
                    )
                    tokens.pop(resource.id, None)
                    await update_after_change(dialog, "Resource released.")
                    return
                body = RenewRequest(lease_token=lease_token, ttl_minutes=ttl.value, description=note)
                leased = await api("PUT", f"{resource_path}/renew", body=body, response_model=ResourceLeaseOut)
            else:
                lease = LeaseRequest(lease_owner=owner.value.strip() or None, ttl_minutes=ttl.value, description=note)
                if resource:
                    leased = await api("PUT", f"{resource_path}/block", body=lease, response_model=ResourceLeaseOut)
                else:
                    tags_value = split_tags(tags.value)
                    if not tags_value:
                        raise ValueError("Enter at least one tag.")
                    body = ClaimRequest(tags=tags_value, **lease.model_dump())
                    leased = await api("POST", "/resources/claim", body=body, response_model=ResourceLeaseOut)
                    if leased is None:
                        raise ValueError("No free resource matches these tags.")
            tokens[leased.id] = leased.lease_token
            resource_names[leased.id] = leased.resource_name
            await update_after_change(dialog, "Lease extended." if existing else "Resource reserved.")
            show_lease(leased)

        with overlays, ui.dialog().props("persistent") as dialog, ui.card().classes(DIALOG):
            ui.label(f"{action} resource" if resource else "Claim by tags").classes("text-xl font-semibold")
            if resource:
                ui.label(resource.resource_name).classes("break-words text-slate-300")
            else:
                tags = (
                    ui.input("Required tags · comma-separated", value=tag_filter.value).props(FIELD).classes("w-full")
                )
            if existing:
                token = (
                    ui.input("Lease token", value=str(tokens.get(resource.id, "")), password=True)
                    .props(FIELD)
                    .classes("w-full")
                )
            else:
                owner = ui.input("Lease owner · optional").props(f"{FIELD} maxlength=255").classes("w-full")
            if action != "Release":
                ttl = ui.number("Duration in minutes · optional", min=1, step=1).props(FIELD).classes("w-full")
            description = ui.input("Note · optional").props(f"{FIELD} maxlength=255").classes("w-full")
            form_actions(dialog, action, submit)
        show_dialog(dialog)

    def show_lease(resource: ResourceLeaseOut) -> None:
        with overlays, ui.dialog() as dialog, ui.card().classes(DIALOG):
            ui.label(resource.resource_name).classes("break-words text-xl font-semibold")
            ui.label(f"Booked until {format_time(resource.lease_expires_at)} UTC").classes("text-amber-300")
            ui.input("Lease token", value=str(resource.lease_token)).props(f"{FIELD} readonly").classes(
                "w-full font-mono"
            )
            ui.label("Keep the token to extend or release this lease from another session.").classes(
                "text-sm text-slate-400"
            )

            def copy() -> None:
                ui.clipboard.write(str(resource.lease_token))

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Copy token", icon="content_copy", on_click=copy, color=None).props("flat no-caps")
                ui.button("Done", on_click=dialog.close).props(BUTTON)
        show_dialog(dialog)

    def delete_dialog(resource: ResourceOut) -> None:
        async def submit() -> None:
            await api("DELETE", f"/resources/{resource.id}")
            tokens.pop(resource.id, None)
            resource_names.pop(resource.id, None)
            await update_after_change(dialog, "Resource deleted.")

        with overlays, ui.dialog().props("persistent") as dialog, ui.card().classes(DIALOG):
            ui.label("Delete resource?").classes("text-xl font-semibold")
            ui.label(f"{resource.resource_name} and its activity will be permanently deleted.").classes("break-words")
            form_actions(dialog, "Delete resource", submit, color="negative")
        show_dialog(dialog)

    ui.colors(primary="#315ed6", negative="#be3f56")
    ui.query("body").classes("bg-[#0d121d] text-slate-100")
    ui.query(".nicegui-content").classes("!p-0 !gap-0")
    overlays = ui.element("div")

    with ui.element("header").classes("w-full border-b border-[#273044] bg-[#101725]"):
        with ui.row().classes(f"{WIDTH} min-h-[68px] items-center justify-between gap-3 py-3"):
            with ui.row().classes("flex-nowrap items-center gap-3"):
                ui.icon("layers").classes("rounded-lg bg-blue-400/15 p-2 text-xl text-blue-300")
                ui.label("Resource Coordinator").classes("text-base font-semibold tracking-tight sm:text-lg")
            with ui.row().classes("items-center gap-2"):
                health = ui.label("Checking API…").classes("text-sm text-slate-400").props("role=status")
                refresh_button = (
                    ui.button(icon="refresh", on_click=refresh, color=None)
                    .props('flat round dense aria-label="Refresh dashboard"')
                    .tooltip("Refresh")
                )
        with ui.row().classes(WIDTH):
            with (
                ui.tabs()
                .props("align=left dense inline-label narrow-indicator no-caps")
                .props("active-color=blue-3 indicator-color=blue-3")
                .classes("h-11 text-slate-400") as tabs
            ):
                resources_tab = ui.tab("Resources", icon="inventory_2")
                activity_tab = ui.tab("Activity", icon="history")

    with ui.element("main").classes(f"{WIDTH} pb-10 pt-6 sm:pt-9"):
        with ui.tab_panels(tabs, value=resources_tab).classes("w-full !bg-transparent"):
            with ui.tab_panel(resources_tab).classes("!p-0"):
                with ui.row().classes("mb-5 w-full items-center justify-between gap-3"):
                    ui.label("Resources").props("role=heading aria-level=1").classes(
                        "text-3xl font-semibold tracking-tight"
                    )
                    with ui.row().classes("gap-2"):
                        ui.button(
                            "Claim by tags", icon="sell", on_click=lambda: lease_dialog("Claim"), color=None
                        ).props("outline no-caps").classes("text-blue-200")
                        ui.button("New resource", icon="add", on_click=create_dialog).props(BUTTON)
                with ui.element("div").classes("mb-5 grid w-full grid-cols-1 gap-3 sm:grid-cols-3"):
                    total = metric("Total resources", "inventory_2", "bg-blue-400/10 text-blue-300")
                    free = metric("Available", "check_circle_outline", "bg-emerald-400/10 text-emerald-300")
                    booked = metric("Booked", "lock_outline", "bg-amber-400/10 text-amber-300")
                with ui.column().classes(f"{SURFACE} w-full gap-0 overflow-hidden"):
                    with ui.row().classes("w-full items-center gap-3 p-4"):
                        status_filter = (
                            ui.select(STATUS_LABELS, label="Status", clearable=True)
                            .props(FIELD)
                            .classes("w-full sm:w-36")
                        )
                        tag_filter = ui.input("Tags · comma-separated").props(FIELD).classes("w-full sm:w-64")
                        ui.button("Filter", on_click=lambda: resource_table.load(), color=None).props(
                            f"{BUTTON} outline"
                        ).classes("text-slate-200")
                    resource_table = PagedTable(
                        ["Name", "Tags", "Status", "Owner", "Expires · UTC"],
                        fetch_resources,
                        render_resource,
                        "No resources match. Change the filters or add a resource.",
                    )
                    tag_filter.on("keydown.enter", lambda: resource_table.load())
            with ui.tab_panel(activity_tab).classes("!p-0"):
                ui.label("Activity").props("role=heading aria-level=1").classes(
                    "mb-5 text-3xl font-semibold tracking-tight"
                )
                with ui.column().classes(f"{SURFACE} w-full gap-0 overflow-hidden"):
                    with ui.row().classes("w-full items-center gap-3 p-4"):
                        resource_filter = ui.input("Resource UUID").props(FIELD).classes("w-full sm:w-72")
                        operation_filter = (
                            ui.select(OPERATION_LABELS, label="Operation", clearable=True)
                            .props(FIELD)
                            .classes("w-full sm:w-36")
                        )
                        from_filter = (
                            ui.input("From · UTC").props(f"{FIELD} type=date stack-label").classes("min-w-0 w-40")
                        )
                        to_filter = ui.input("To · UTC").props(f"{FIELD} type=date stack-label").classes("min-w-0 w-40")
                        ui.button("Filter", on_click=lambda: activity_table.load(), color=None).props(
                            f"{BUTTON} outline"
                        ).classes("text-slate-200")
                    activity_table = PagedTable(
                        ["Time · UTC", "Operation", "Resource", "Note"],
                        fetch_activity,
                        render_activity,
                        "No activity matches the current filters.",
                    )
                    resource_filter.on("keydown.enter", lambda: activity_table.load())

    tabs.on_value_change(change_tab)
    ui.timer(0, refresh, once=True)


def install_ui(fastapi_app: FastAPI) -> None:
    def open_api_client() -> None:
        base_url = os.getenv("API_BASE_URL", f"http://127.0.0.1:{get_settings().app_port}")
        nicegui_app.state.api_client = httpx.AsyncClient(base_url=base_url, timeout=8, trust_env=False)

    async def close_api_client() -> None:
        await nicegui_app.state.api_client.aclose()

    nicegui_app.on_startup(open_api_client)
    nicegui_app.on_shutdown(close_api_client)
    ui.run_with(fastapi_app, mount_path="/ui", title="Resource Coordinator", dark=True, show_welcome_message=False)

"""Clients management area UI component."""

from datetime import date

from nicegui import ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.services.client_service import ClientService


class ClientsAreaPage:
    """Clients management page component."""

    def __init__(self) -> None:
        """Initialize the clients area page."""
        self.clients: list[Client] = []
        self.clients_table: ui.table | None = None
        self.name_input: ui.input | None = None
        self.cpf_input: ui.input | None = None
        self.birth_date_input: ui.input | None = None
        self.add_client_dialog: ui.dialog | None = None
        self.editing_client: Client | None = None

    def create(self) -> None:
        """Create the clients area page UI."""
        # Check authentication
        if not AuthManager.require_auth():
            return

        current_user = AuthManager.get_current_user()

        with ui.column().classes("w-full max-w-6xl mx-auto mt-10 p-6"):
            # Header
            with ui.row().classes("w-full justify-between items-center mb-8"):
                with ui.row().classes("items-center gap-4"):
                    ui.button(
                        "← Dashboard", on_click=lambda: ui.navigate.to("/dashboard")
                    ).classes(
                        "bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                    )
                    ui.label("Gerenciamento de Clientes").classes("text-3xl font-bold")

                with ui.row().classes("items-center gap-4"):
                    ui.label(f"Olá, {current_user['username']}").classes("text-lg")
                    ui.button("Sair", on_click=self._handle_logout).classes(
                        "bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                    )

            # Action buttons
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.button(
                    "Adicionar Cliente",
                    on_click=self._show_add_client_dialog,
                    icon="person_add",
                ).classes(
                    "bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                )

                ui.button(
                    "Atualizar Lista", on_click=self._load_clients, icon="refresh"
                ).classes("bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600")

            # Clients table
            self._create_clients_table()

            # Add client dialog
            self._create_add_client_dialog()

        # Load initial data
        ui.timer(0.1, self._load_clients, once=True)

    def _create_clients_table(self) -> None:
        """Create the clients table."""
        columns = [
            {
                "name": "name",
                "label": "Nome",
                "field": "name",
                "required": True,
                "align": "left",
            },
            {"name": "cpf", "label": "CPF", "field": "formatted_cpf", "align": "left"},
            {
                "name": "birth_date",
                "label": "Data de Nascimento",
                "field": "birth_date",
                "align": "left",
            },
            {
                "name": "actions",
                "label": "Ações",
                "field": "actions",
                "align": "center",
            },
        ]

        self.clients_table = ui.table(columns=columns, rows=[], row_key="id").classes(
            "w-full"
        )
        self.clients_table.add_slot(
            "body-cell-actions",
            """
            <q-td key="actions" :props="props">
                <q-btn flat round icon="visibility" size="sm" color="info" @click="$parent.$emit('view_details', props.row)" title="Ver Detalhes" />
                <q-btn flat round icon="upload_file" size="sm" color="positive" @click="$parent.$emit('upload_document', props.row)" title="Upload de Documento" />
                <q-btn flat round icon="edit" size="sm" color="primary" @click="$parent.$emit('edit', props.row)" title="Editar Cliente" />
                <q-btn flat round icon="delete" size="sm" color="negative" @click="$parent.$emit('delete', props.row)" title="Excluir Cliente" />
            </q-td>
        """,
        )

        # Handle table events
        self.clients_table.on("view_details", self._handle_view_details)
        self.clients_table.on("edit", self._handle_edit_client)
        self.clients_table.on("delete", self._handle_delete_client)
        self.clients_table.on("upload_document", self._handle_upload_document)

    def _create_add_client_dialog(self) -> None:
        """Create the add/edit client dialog."""
        with ui.dialog() as self.add_client_dialog:
            with ui.card().classes("w-96"):
                ui.label("Adicionar Cliente").classes(
                    "text-xl font-bold mb-4"
                ).bind_visibility_from(self, "editing_client", lambda x: x is None)
                ui.label("Editar Cliente").classes(
                    "text-xl font-bold mb-4"
                ).bind_visibility_from(self, "editing_client", lambda x: x is not None)

                with ui.column().classes("w-full gap-4"):
                    self.name_input = ui.input(
                        label="Nome completo",
                        placeholder="Digite o nome completo do cliente",
                    ).classes("w-full")

                    self.cpf_input = ui.input(
                        label="CPF", placeholder="000.000.000-00"
                    ).classes("w-full")

                    # Date input
                    self.birth_date_input = ui.input(
                        label="Data de Nascimento",
                        placeholder="DD/MM/AAAA (ex: 15/01/1990)",
                    ).classes("w-full")

                    # Add date picker button
                    with ui.row().classes("w-full gap-2 -mt-2"):
                        ui.button(
                            "📅 Selecionar Data",
                            on_click=lambda: self._show_date_picker(),
                        ).classes(
                            "text-sm bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        )
                        ui.label("ou digite no formato DD/MM/AAAA").classes(
                            "text-sm text-gray-500"
                        )

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancelar", on_click=self._close_dialog).classes(
                        "bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                    )

                    ui.button("Salvar", on_click=self._handle_save_client).classes(
                        "bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    )

    async def _load_clients(self) -> None:
        """Load all clients from database."""
        try:
            async for db_session in get_async_db():
                client_repository = ClientRepository(db_session)
                client_service = ClientService(client_repository)

                self.clients = await client_service.get_all_clients()

                # Update table data
                rows = []
                for client in self.clients:
                    rows.append(
                        {
                            "id": str(client.id),
                            "name": client.name,
                            "formatted_cpf": client.formatted_cpf,
                            "birth_date": (
                                client.birth_date.strftime("%d/%m/%Y")
                                if client.birth_date
                                else ""
                            ),
                        }
                    )

                self.clients_table.rows = rows

                if not self.clients:
                    ui.notify("Nenhum cliente cadastrado ainda", type="info")
                else:
                    ui.notify(
                        f"Carregados {len(self.clients)} clientes", type="positive"
                    )

        except Exception as e:
            ui.notify(f"Erro ao carregar clientes: {str(e)}", type="negative")

    def _show_add_client_dialog(self) -> None:
        """Show the add client dialog."""
        self.editing_client = None
        self._clear_form()
        self.add_client_dialog.open()

    def _handle_view_details(self, event) -> None:
        """Handle view client details action."""
        client_id = event.args["id"]
        ui.navigate.to(f"/client/{client_id}")

    def _handle_edit_client(self, event) -> None:
        """Handle edit client action."""
        client_id = event.args["id"]
        self.editing_client = next(
            (c for c in self.clients if str(c.id) == client_id), None
        )

        if self.editing_client:
            self.name_input.value = self.editing_client.name
            self.cpf_input.value = self.editing_client.formatted_cpf
            # Format date in Brazilian format DD/MM/YYYY for editing
            self.birth_date_input.value = self.editing_client.birth_date.strftime(
                "%d/%m/%Y"
            )
            self.add_client_dialog.open()

    async def _handle_delete_client(self, event) -> None:
        """Handle delete client action."""
        client_id = event.args["id"]
        client = next((c for c in self.clients if str(c.id) == client_id), None)

        if not client:
            ui.notify("Cliente não encontrado", type="negative")
            return

        # Confirm deletion
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Confirmar exclusão do cliente {client.name}?").classes(
                "text-lg mb-4"
            )
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=dialog.close).classes(
                    "bg-gray-500 text-white px-4 py-2 rounded"
                )
                ui.button(
                    "Excluir",
                    on_click=lambda: self._confirm_delete_client(client.id, dialog),
                ).classes("bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600")

        dialog.open()

    async def _confirm_delete_client(self, client_id, dialog) -> None:
        """Confirm and execute client deletion."""
        try:
            async for db_session in get_async_db():
                client_repository = ClientRepository(db_session)
                client_service = ClientService(client_repository)

                success = await client_service.delete_client(client_id)

                if success:
                    ui.notify("Cliente excluído com sucesso", type="positive")
                    await self._load_clients()
                else:
                    ui.notify("Cliente não encontrado", type="negative")

                dialog.close()

        except Exception as e:
            ui.notify(f"Erro ao excluir cliente: {str(e)}", type="negative")
            dialog.close()

    async def _handle_save_client(self) -> None:
        """Handle save client action."""
        try:
            # Validate form
            if not self._validate_form():
                return

            name = self.name_input.value.strip()
            cpf = self.cpf_input.value.strip()
            birth_date_str = self.birth_date_input.value

            # Parse birth date - accept multiple formats
            try:
                birth_date = self._parse_date(birth_date_str)
            except ValueError:
                ui.notify(
                    "Data de nascimento inválida. Use o formato DD/MM/AAAA ou AAAA-MM-DD",
                    type="negative",
                )
                return

            async for db_session in get_async_db():
                client_repository = ClientRepository(db_session)
                client_service = ClientService(client_repository)

                if self.editing_client:
                    # Update existing client
                    await client_service.update_client(
                        self.editing_client.id,
                        name=name,
                        cpf=cpf,
                        birth_date=birth_date,
                    )
                    ui.notify("Cliente atualizado com sucesso", type="positive")
                else:
                    # Create new client
                    await client_service.create_client(name, cpf, birth_date)
                    ui.notify("Cliente criado com sucesso", type="positive")

                self._close_dialog()
                await self._load_clients()

        except Exception as e:
            ui.notify(f"Erro ao salvar cliente: {str(e)}", type="negative")

    def _validate_form(self) -> bool:
        """Validate the client form."""
        if not self.name_input.value or len(self.name_input.value.strip()) < 2:
            ui.notify("Nome deve ter pelo menos 2 caracteres", type="negative")
            return False

        if not self.cpf_input.value:
            ui.notify("CPF é obrigatório", type="negative")
            return False

        if not self.birth_date_input.value:
            ui.notify("Data de nascimento é obrigatória", type="negative")
            return False

        return True

    def _clear_form(self) -> None:
        """Clear the form fields."""
        if self.name_input:
            self.name_input.value = ""
        if self.cpf_input:
            self.cpf_input.value = ""
        if self.birth_date_input:
            self.birth_date_input.value = ""

    def _close_dialog(self) -> None:
        """Close the add/edit dialog."""
        self.add_client_dialog.close()
        self._clear_form()
        self.editing_client = None

    def _show_date_picker(self) -> None:
        """Show date picker dialog."""
        with ui.dialog() as date_dialog, ui.card().style("width: 340px; padding: 20px"):
            with ui.column().classes("w-full items-center"):
                ui.label("Selecione a Data de Nascimento").classes(
                    "text-lg font-bold mb-4"
                )

                # Date picker with Brazilian Portuguese locale
                date_picker = ui.date(value="1990-01-01").props('locale="pt-br"')

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancelar", on_click=date_dialog.close).classes(
                        "bg-gray-500 text-white px-4 py-2 rounded"
                    )
                    ui.button(
                        "Selecionar",
                        on_click=lambda: self._set_selected_date(
                            date_picker.value, date_dialog
                        ),
                    ).classes("bg-blue-500 text-white px-4 py-2 rounded")

        date_dialog.open()

    def _set_selected_date(self, selected_date: str, dialog) -> None:
        """Set selected date in Brazilian format."""
        try:
            # Handle different date formats and convert to DD/MM/YYYY
            if selected_date and len(selected_date) >= 8:
                # Remove any extra formatting and get just the date part
                clean_date = selected_date.split("T")[0]  # Remove time if present

                if "-" in clean_date and len(clean_date.split("-")) == 3:
                    # ISO format YYYY-MM-DD
                    parts = clean_date.split("-")
                    if len(parts[0]) == 4:  # Year first
                        year, month, day = parts
                    else:  # Day first DD-MM-YYYY
                        day, month, year = parts

                    # Format as DD/MM/YYYY
                    brazilian_format = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    self.birth_date_input.value = brazilian_format
                    ui.notify(f"Data selecionada: {brazilian_format}", type="positive")
                else:
                    ui.notify("Formato de data não reconhecido", type="negative")
            else:
                ui.notify("Data inválida selecionada", type="negative")

            dialog.close()
        except Exception as e:
            ui.notify(f"Erro ao selecionar data: {str(e)}", type="negative")
            dialog.close()

    def _parse_date(self, date_str: str) -> date:
        """Parse date string in multiple formats."""
        if not date_str:
            raise ValueError("Date string is empty")

        date_str = date_str.strip()

        # Try ISO format first (AAAA-MM-DD) - from date picker
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            pass

        # Try Brazilian format (DD/MM/AAAA)
        try:
            day, month, year = date_str.split("/")
            return date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            pass

        # Try Brazilian format with dashes (DD-MM-AAAA)
        try:
            parts = date_str.split("-")
            if len(parts) == 3 and len(parts[0]) <= 2:  # DD-MM-AAAA format
                day, month, year = parts
                return date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            pass

        raise ValueError(f"Invalid date format: {date_str}")

    def _handle_upload_document(self, event) -> None:
        """Handle document upload for a client."""
        client_id = event.args["id"]
        client = next((c for c in self.clients if str(c.id) == client_id), None)

        if not client:
            ui.notify("Cliente não encontrado", type="negative")
            return

        # Import here to avoid circular imports
        from app.ui_components.document_upload import DocumentUploadDialog

        # Show document upload dialog for this client
        upload_dialog = DocumentUploadDialog(client)
        upload_dialog.show()

    def _handle_logout(self) -> None:
        """Handle user logout."""
        AuthManager.logout_user()
        ui.notify("Saída realizada com sucesso", type="positive")
        ui.navigate.to("/login")


def clients_area_page() -> None:
    """Create and display the clients area page."""
    page = ClientsAreaPage()
    page.create()

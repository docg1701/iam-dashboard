"""Questionnaire Writer UI component for judicial questionnaire generation."""

from nicegui import ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.client_service import ClientService
from app.services.questionnaire_draft_service import get_questionnaire_draft_service


class QuestionnaireWriterPage:
    """Questionnaire Writer page component."""

    def __init__(self) -> None:
        """Initialize the questionnaire writer page."""
        self.clients: list[Client] = []
        self.selected_client: Client | None = None
        self.client_select: ui.select | None = None
        self.profession_input: ui.input | None = None
        self.disease_input: ui.input | None = None
        self.incident_date_input: ui.input | None = None
        self.medical_date_input: ui.input | None = None
        self.result_area: ui.textarea | None = None

    def create(self) -> None:
        """Create the questionnaire writer page UI."""
        # Check authentication
        if not AuthManager.require_auth():
            return

        current_user = AuthManager.get_current_user()

        with ui.column().classes("w-full max-w-6xl mx-auto mt-10 p-6"):
            # Header
            with ui.row().classes("w-full justify-between items-center mb-8"):
                with ui.row().classes("items-center gap-4"):
                    ui.button(
                        icon="arrow_back",
                        on_click=lambda: ui.navigate.to("/dashboard"),
                    ).classes("bg-gray-500 text-white rounded hover:bg-gray-600")
                    ui.label("Redator de Quesitos Judiciais").classes(
                        "text-3xl font-bold"
                    )

                with ui.row().classes("items-center gap-4"):
                    ui.label(f"Usuário: {current_user['username']}").classes("text-lg")

            # Main content
            with ui.card().classes("w-full p-6"):
                ui.label("Geração de Quesitos Judiciais").classes(
                    "text-xl font-semibold mb-6"
                )

                # Client selection section
                with ui.card().classes("w-full p-4 mb-6"):
                    ui.label("1. Seleção do Cliente").classes(
                        "text-lg font-semibold mb-4"
                    )

                    with ui.row().classes("w-full items-center gap-4"):
                        self.client_select = ui.select(
                            options=[],
                            label="Selecione um cliente com documentos processados",
                            on_change=self._on_client_selected,
                        ).classes("flex-1")

                        ui.button(
                            "Atualizar Lista",
                            icon="refresh",
                            on_click=self._load_clients_with_documents,
                        ).classes(
                            "bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        )

                # Form section
                with ui.card().classes("w-full p-4 mb-6"):
                    ui.label("2. Informações Específicas").classes(
                        "text-lg font-semibold mb-4"
                    )

                    with ui.row().classes("w-full gap-4"):
                        with ui.column().classes("flex-1"):
                            self.profession_input = ui.input(
                                label="Profissão do Cliente",
                                placeholder="Ex: Enfermeiro, Médico, Engenheiro...",
                            ).classes("w-full")

                            self.disease_input = ui.input(
                                label="Doença/Condição",
                                placeholder="Ex: Lesão por esforço repetitivo, Burnout...",
                            ).classes("w-full")

                        with ui.column().classes("flex-1"):
                            self.incident_date_input = ui.input(
                                label="Data do Incidente", placeholder="dd/mm/aaaa"
                            ).classes("w-full")

                            self.medical_date_input = ui.input(
                                label="Data do Primeiro Atendimento Médico",
                                placeholder="dd/mm/aaaa",
                            ).classes("w-full")

                # Generate button
                with ui.row().classes("w-full justify-center mb-6"):
                    ui.button(
                        "Gerar Quesitos",
                        icon="auto_awesome",
                        on_click=self._generate_questionnaire,
                    ).classes(
                        "bg-green-500 text-white px-8 py-3 rounded-lg text-lg hover:bg-green-600"
                    )

                # Result section
                with ui.card().classes("w-full p-4"):
                    ui.label("3. Quesitos Gerados").classes(
                        "text-lg font-semibold mb-4"
                    )

                    self.result_area = ui.textarea(
                        label="Resultado",
                        placeholder="Os quesitos aparecerão aqui após a geração...",
                        value="",
                    ).classes("w-full min-h-96")

                    with ui.row().classes("w-full justify-end gap-4 mt-4"):
                        ui.button(
                            "Copiar Texto",
                            icon="content_copy",
                            on_click=self._copy_result,
                        ).classes(
                            "bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        )

        # Load clients on page initialization
        ui.timer(0.1, self._load_clients_with_documents, once=True)

    async def _load_clients_with_documents(self) -> None:
        """Load clients that have processed documents."""
        try:
            async for db_session in get_async_db():
                client_repository = ClientRepository(db_session)
                client_service = ClientService(client_repository)

                # Get all clients for now - TODO: filter by processed documents
                all_clients = await client_service.get_all_clients()
                self.clients = all_clients

                # Update select options
                if self.client_select:
                    options = {}
                    for client in self.clients:
                        options[str(client.id)] = (
                            f"{client.name} - {client.formatted_cpf}"
                        )

                    self.client_select.options = options

                    if not options:
                        ui.notify("Nenhum cliente encontrado", type="warning")
                    else:
                        ui.notify(
                            f"{len(options)} cliente(s) carregado(s)", type="positive"
                        )

        except Exception as e:
            ui.notify(f"Erro ao carregar clientes: {str(e)}", type="negative")

    def _on_client_selected(self, event) -> None:
        """Handle client selection."""
        if not event.value:
            self.selected_client = None
            return

        # Find selected client
        for client in self.clients:
            if str(client.id) == event.value:
                self.selected_client = client
                ui.notify(f"Cliente selecionado: {client.name}", type="positive")
                break

    async def _generate_questionnaire(self) -> None:
        """Generate judicial questionnaire using RAG + Gemini."""
        if not self.selected_client:
            ui.notify("Por favor, selecione um cliente", type="warning")
            return

        if not all(
            [
                self.profession_input and self.profession_input.value,
                self.disease_input and self.disease_input.value,
                self.incident_date_input and self.incident_date_input.value,
                self.medical_date_input and self.medical_date_input.value,
            ]
        ):
            ui.notify(
                "Por favor, preencha todos os campos obrigatórios", type="warning"
            )
            return

        try:
            # Show loading state
            ui.notify("Gerando quesitos... Aguarde.", type="info")

            # Get service instance
            async for db_session in get_async_db():
                chunk_repository = DocumentChunkRepository(db_session)
                questionnaire_service = get_questionnaire_draft_service(
                    chunk_repository
                )

                # Generate questionnaire
                result = await questionnaire_service.generate_questionnaire(
                    client=self.selected_client,
                    profession=self.profession_input.value,
                    disease=self.disease_input.value,
                    incident_date=self.incident_date_input.value,
                    medical_date=self.medical_date_input.value,
                )

                if result["success"]:
                    if self.result_area:
                        self.result_area.value = result["questionnaire"]

                    context_info = (
                        f" (baseado em {result['context_chunks']} documento(s))"
                        if result["context_chunks"] > 0
                        else " (sem documentos disponíveis)"
                    )
                    ui.notify(
                        f"Quesitos gerados com sucesso{context_info}!", type="positive"
                    )
                else:
                    ui.notify(
                        f"Erro ao gerar quesitos: {result.get('error', 'Erro desconhecido')}",
                        type="negative",
                    )

                break  # Exit the async for loop

        except Exception as e:
            ui.notify(f"Erro ao gerar quesitos: {str(e)}", type="negative")

    def _copy_result(self) -> None:
        """Copy result to clipboard."""
        if self.result_area and self.result_area.value:
            ui.run_javascript(
                f"navigator.clipboard.writeText(`{self.result_area.value}`)"
            )
            ui.notify("Texto copiado para a área de transferência!", type="positive")
        else:
            ui.notify("Nenhum conteúdo para copiar", type="warning")


def questionnaire_writer_page() -> None:
    """Create and display the questionnaire writer page."""
    page = QuestionnaireWriterPage()
    page.create()

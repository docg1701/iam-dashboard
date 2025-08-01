# Section 6: User Interface Integration

```python
# Key UI Integration: Replace placeholders with real agent connections
class DashboardPage:
    def __init__(self):
        self.agent_service = AgentService()
        self.document_service = DocumentProcessingService()
    
    def create(self) -> None:
        if not AuthManager.require_auth():
            return
        current_user = AuthManager.get_current_user()
        
        with ui.column().classes("w-full max-w-6xl mx-auto mt-10 p-6"):
            # Real-time agent status cards
            self._create_agent_status_section()
            # Feature cards with backend integration
            self._create_feature_cards()
    
    def _create_agent_status_section(self):
        with ui.card().classes("w-full p-6 mb-6"):
            ui.label("Agent System Status").classes("text-xl font-semibold mb-4")
            with ui.row().classes("w-full gap-4"):
                for agent_id, name in [("pdf_processor", "PDF Processor"), ("questionnaire_writer", "Questionnaire Writer")]:
                    with ui.card().classes("flex-1 p-4"):
                        status_container = ui.column()
                        ui.timer(1.0, lambda c=status_container, a=agent_id, n=name: self._update_agent_status(c, a, n), once=False)
    
    async def _update_agent_status(self, container, agent_id: str, agent_name: str):
        try:
            agent_health = await self.agent_service.get_agent_health(agent_id)
            with container:
                container.clear()
                status_color = "green" if agent_health["healthy"] else "red"
                ui.icon("circle", size="sm").classes(f"text-{status_color}-500")
                ui.label(agent_name).classes("font-medium")
        except Exception as e:
            with container:
                container.clear()
                ui.label(f"Error: {str(e)}").classes("text-red-500 text-sm")
    
    async def _handle_pdf_upload(self, upload_event):
        try:
            current_user = AuthManager.get_current_user()
            result = await self.document_service.process_document(
                file_data=upload_event.content.read(), filename=upload_event.name, 
                client_id=1, user_id=current_user["id"]
            )
            if result.success:
                ui.notify("Documento processado com sucesso!", type="positive")
            else:
                ui.notify(f"Erro: {result.error_message}", type="negative")
        except Exception as e:
            ui.notify(f"Erro: {str(e)}", type="negative")
```
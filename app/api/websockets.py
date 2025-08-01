"""WebSocket handlers for real-time agent status updates."""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.agent_initialization import get_agent_manager, get_system_status

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentStatusWebSocketManager:
    """Manages WebSocket connections for agent status updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._monitoring_task: asyncio.Task[None] | None = None
        self._running = False

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")

        # Start monitoring if this is the first connection
        if len(self.active_connections) == 1 and not self._running:
            await self.start_monitoring()

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

            # Stop monitoring if no connections remain
            if len(self.active_connections) == 0 and self._running:
                asyncio.create_task(self.stop_monitoring())

    async def broadcast_status(self, status_data: dict[str, Any]) -> None:
        """Broadcast status update to all connected clients."""
        if not self.active_connections:
            return

        message = json.dumps({
            "type": "agent_status_update",
            "timestamp": status_data.get("timestamp"),
            "data": status_data
        })

        # Send to all connections, remove any that fail
        failed_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket connection: {str(e)}")
                failed_connections.append(connection)

        # Remove failed connections
        for failed in failed_connections:
            self.disconnect(failed)

    async def start_monitoring(self) -> None:
        """Start the monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started WebSocket agent status monitoring")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring task."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        logger.info("Stopped WebSocket agent status monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for sending status updates."""
        while self._running:
            try:
                if self.active_connections:
                    # Get current system status
                    status = await get_system_status()

                    # Add timestamp
                    from datetime import UTC, datetime
                    status["timestamp"] = datetime.now(UTC).isoformat()

                    # Broadcast to all connections
                    await self.broadcast_status(status)

                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                logger.info("WebSocket monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying


# Global WebSocket manager instance
ws_manager = AgentStatusWebSocketManager()


@router.websocket("/ws/agents/status")
async def agent_status_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time agent status updates."""
    await ws_manager.connect(websocket)

    try:
        # Send initial status
        initial_status = await get_system_status()
        from datetime import UTC, datetime
        initial_status["timestamp"] = datetime.now(UTC).isoformat()

        await websocket.send_text(json.dumps({
            "type": "initial_status",
            "data": initial_status
        }))

        # Keep connection alive
        while True:
            try:
                # Wait for client messages (ping/pong or commands)
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_status":
                    # Send current status on demand
                    current_status = await get_system_status()
                    current_status["timestamp"] = datetime.now(UTC).isoformat()

                    await websocket.send_text(json.dumps({
                        "type": "status_response",
                        "data": current_status
                    }))

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/agents/{agent_id}")
async def agent_specific_websocket(websocket: WebSocket, agent_id: str) -> None:
    """WebSocket endpoint for specific agent status updates."""
    await websocket.accept()

    try:
        agent_manager = get_agent_manager()

        # Check if agent exists
        metadata = agent_manager.get_agent_metadata(agent_id)
        if not metadata:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Agent {agent_id} not found"
            }))
            return

        # Send initial agent status
        from datetime import UTC, datetime
        agent_status = {
            "agent_id": agent_id,
            "name": metadata.name,
            "status": metadata.status.value,
            "health_status": metadata.health_status,
            "last_health_check": metadata.last_health_check.isoformat() if metadata.last_health_check else None,
            "error_message": metadata.error_message,
            "capabilities": metadata.capabilities,
            "timestamp": datetime.now(UTC).isoformat()
        }

        await websocket.send_text(json.dumps({
            "type": "agent_status",
            "data": agent_status
        }))

        # Monitor specific agent status
        while True:
            try:
                # Wait for client messages or timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "health_check":
                    # Perform health check on agent
                    await agent_manager.health_check(agent_id)
                    updated_metadata = agent_manager.get_agent_metadata(agent_id)

                    if updated_metadata:
                        agent_status = {
                            "agent_id": agent_id,
                            "name": updated_metadata.name,
                            "status": updated_metadata.status.value,
                            "health_status": updated_metadata.health_status,
                            "last_health_check": updated_metadata.last_health_check.isoformat() if updated_metadata.last_health_check else None,
                            "error_message": updated_metadata.error_message,
                            "capabilities": updated_metadata.capabilities,
                            "timestamp": datetime.now(UTC).isoformat()
                        }

                        await websocket.send_text(json.dumps({
                            "type": "health_check_result",
                            "data": agent_status
                        }))

            except TimeoutError:
                # Send periodic status update
                updated_metadata = agent_manager.get_agent_metadata(agent_id)
                if updated_metadata:
                    agent_status = {
                        "agent_id": agent_id,
                        "name": updated_metadata.name,
                        "status": updated_metadata.status.value,
                        "health_status": updated_metadata.health_status,
                        "last_health_check": updated_metadata.last_health_check.isoformat() if updated_metadata.last_health_check else None,
                        "error_message": updated_metadata.error_message,
                        "capabilities": updated_metadata.capabilities,
                        "timestamp": datetime.now(UTC).isoformat()
                    }

                    await websocket.send_text(json.dumps({
                        "type": "periodic_update",
                        "data": agent_status
                    }))

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in agent-specific WebSocket: {str(e)}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from agent {agent_id}")
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {str(e)}")


class DocumentProcessingWebSocketManager:
    """Manages WebSocket connections for document processing progress updates."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}  # document_id -> connections
        self.processing_status: dict[str, dict[str, Any]] = {}  # document_id -> status

    async def connect(self, websocket: WebSocket, document_id: str = None) -> None:
        """Accept and register a new WebSocket connection for document processing."""
        await websocket.accept()

        if document_id:
            if document_id not in self.active_connections:
                self.active_connections[document_id] = []
            self.active_connections[document_id].append(websocket)
            logger.info(f"WebSocket connected for document {document_id}. Total connections: {len(self.active_connections[document_id])}")
        else:
            # Global processing updates
            if "global" not in self.active_connections:
                self.active_connections["global"] = []
            self.active_connections["global"].append(websocket)
            logger.info("Global document processing WebSocket connected")

    def disconnect(self, websocket: WebSocket, document_id: str = None) -> None:
        """Remove a WebSocket connection."""
        connection_key = document_id if document_id else "global"

        if connection_key in self.active_connections and websocket in self.active_connections[connection_key]:
            self.active_connections[connection_key].remove(websocket)
            logger.info(f"WebSocket disconnected for {connection_key}")

            # Clean up empty connection lists
            if not self.active_connections[connection_key]:
                del self.active_connections[connection_key]

    async def broadcast_progress(
        self,
        document_id: str,
        progress_data: dict[str, Any],
        global_broadcast: bool = True
    ) -> None:
        """Broadcast processing progress to connected clients."""
        # Update internal status
        self.processing_status[document_id] = progress_data

        message = json.dumps({
            "type": "document_progress",
            "document_id": document_id,
            "timestamp": progress_data.get("timestamp"),
            "data": progress_data
        })

        # Send to document-specific connections
        if document_id in self.active_connections:
            await self._send_to_connections(self.active_connections[document_id], message)

        # Send to global connections if enabled
        if global_broadcast and "global" in self.active_connections:
            await self._send_to_connections(self.active_connections["global"], message)

    async def _send_to_connections(self, connections: list[WebSocket], message: str) -> None:
        """Send message to a list of connections, removing failed ones."""
        failed_connections = []
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {str(e)}")
                failed_connections.append(connection)

        # Remove failed connections
        for failed in failed_connections:
            if failed in connections:
                connections.remove(failed)


# Global WebSocket managers
ws_manager = AgentStatusWebSocketManager()
doc_ws_manager = DocumentProcessingWebSocketManager()


@router.websocket("/ws/documents/processing")
async def document_processing_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for global document processing updates."""
    await doc_ws_manager.connect(websocket)

    try:
        # Send initial status of all active processing
        initial_data = {
            "type": "initial_processing_status",
            "active_documents": doc_ws_manager.processing_status,
            "timestamp": datetime.now(UTC).isoformat()
        }

        await websocket.send_text(json.dumps(initial_data))

        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_status":
                    # Send current processing status
                    status_data = {
                        "type": "processing_status_response",
                        "active_documents": doc_ws_manager.processing_status,
                        "timestamp": datetime.now(UTC).isoformat()
                    }
                    await websocket.send_text(json.dumps(status_data))

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in document processing WebSocket: {str(e)}")
                break

    except WebSocketDisconnect:
        logger.info("Document processing WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Document processing WebSocket error: {str(e)}")
    finally:
        doc_ws_manager.disconnect(websocket)


@router.websocket("/ws/documents/{document_id}/progress")
async def document_specific_progress_websocket(websocket: WebSocket, document_id: str) -> None:
    """WebSocket endpoint for specific document processing progress."""
    await doc_ws_manager.connect(websocket, document_id)

    try:
        # Send initial status for this document if available
        if document_id in doc_ws_manager.processing_status:
            initial_data = {
                "type": "document_status",
                "document_id": document_id,
                "data": doc_ws_manager.processing_status[document_id],
                "timestamp": datetime.now(UTC).isoformat()
            }
            await websocket.send_text(json.dumps(initial_data))

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_status":
                    # Send current status for this document
                    status_data = doc_ws_manager.processing_status.get(document_id, {})
                    response = {
                        "type": "document_status_response",
                        "document_id": document_id,
                        "data": status_data,
                        "timestamp": datetime.now(UTC).isoformat()
                    }
                    await websocket.send_text(json.dumps(response))

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in document progress WebSocket for {document_id}: {str(e)}")
                break

    except WebSocketDisconnect:
        logger.info(f"Document progress WebSocket client disconnected for {document_id}")
    except Exception as e:
        logger.error(f"Document progress WebSocket error for {document_id}: {str(e)}")
    finally:
        doc_ws_manager.disconnect(websocket, document_id)


# Function to get the WebSocket managers for external use
def get_websocket_manager() -> AgentStatusWebSocketManager:
    """Get the global WebSocket manager instance."""
    return ws_manager

def get_document_websocket_manager() -> DocumentProcessingWebSocketManager:
    """Get the document processing WebSocket manager instance."""
    return doc_ws_manager

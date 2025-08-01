# Section 5: API Design and Agent Integration

### 5.1 Agent Management API Endpoints

**Complete Agent Management REST API**:

```python
# app/api/agents.py - CRITICAL MISSING ROUTER
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.agent_manager import agent_manager
from app.core.auth import AuthManager

router = APIRouter()

@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(agent_request: AgentCreateRequest, current_user: dict = Depends(AuthManager.get_current_user)):
    if not AuthManager.check_permission(current_user, "agent_management", "create"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        agent_id = await agent_manager.create_agent(agent_request.agent_type, agent_request.agent_id, agent_request.config)
        return AgentResponse(agent_id=agent_id, status="created", message="Agent created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, execution_request: AgentExecutionRequest, current_user: dict = Depends(AuthManager.get_current_user)):
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        result = await agent.process(execution_request.input_data)
        return AgentExecutionResponse(execution_id=result["execution_id"], status="completed", output_data=result["output_data"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/agents/{agent_id}/hot-deploy")
async def hot_deploy_agent(agent_id: str, deployment_request: HotDeploymentRequest, current_user: dict = Depends(AuthManager.get_current_user)):
    if not AuthManager.check_permission(current_user, "agent_management", "configure"):
        raise HTTPException(status_code=403, detail="Admin permissions required")
    
    success = await agent_manager.hot_deploy_agent(agent_id, deployment_request.config, deployment_request.strategy)
    return DeploymentResponse(agent_id=agent_id, success=success, deployment_strategy=deployment_request.strategy)

@router.get("/agents/{agent_id}/health")
async def get_agent_health(agent_id: str):
    agent = await agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    health_status = await agent.health_check()
    metrics = await agent_manager.get_agent_metrics(agent_id)
    return AgentHealthResponse(agent_id=agent_id, healthy=health_status, metrics=metrics, last_check=datetime.now(UTC))
```

### 5.2 WebSocket Integration for Real-time Updates

**Real-time Agent Status Updates**:

```python
# app/api/websockets.py
from fastapi import WebSocket, WebSocketDisconnect
from app.core.agent_manager import agent_manager

class AgentStatusWebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.agent_subscriptions: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if agent_id:
            if agent_id not in self.agent_subscriptions:
                self.agent_subscriptions[agent_id] = []
            self.agent_subscriptions[agent_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        for agent_id, connections in self.agent_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
    
    async def broadcast_agent_status(self, agent_id: str, status_data: dict):
        if agent_id in self.agent_subscriptions:
            dead_connections = []
            for connection in self.agent_subscriptions[agent_id]:
                try:
                    await connection.send_json({
                        "type": "agent_status", "agent_id": agent_id, "data": status_data,
                        "timestamp": datetime.now(UTC).isoformat()
                    })
                except:
                    dead_connections.append(connection)
            for conn in dead_connections:
                self.agent_subscriptions[agent_id].remove(conn)

websocket_manager = AgentStatusWebSocketManager()

@router.websocket("/ws/agents/{agent_id}")
async def agent_status_websocket(websocket: WebSocket, agent_id: str):
    await websocket_manager.connect(websocket, agent_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "get_status":
                agent = await agent_manager.get_agent(agent_id)
                if agent:
                    status = await agent.health_check()
                    await websocket.send_json({
                        "type": "current_status", "agent_id": agent_id, "healthy": status,
                        "timestamp": datetime.now(UTC).isoformat()
                    })
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
```
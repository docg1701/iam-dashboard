"""Tests for agent registry system."""

import tempfile
from pathlib import Path

import pytest

from app.core.agent_manager import AgentMetadata, AgentStatus
from app.core.agent_registry import (
    AgentCapability,
    AgentDependency,
    AgentRegistry,
    RegistryEntry,
)


class TestAgentCapability:
    """Test AgentCapability class."""

    def test_capability_creation(self):
        """Test creating agent capability."""
        capability = AgentCapability(
            name="document_processing",
            description="Process documents",
            category="processing",
            version="2.0.0",
        )

        assert capability.name == "document_processing"
        assert capability.description == "Process documents"
        assert capability.category == "processing"
        assert capability.version == "2.0.0"

    def test_capability_defaults(self):
        """Test capability with default values."""
        capability = AgentCapability("test_capability")

        assert capability.name == "test_capability"
        assert capability.description == ""
        assert capability.category == "general"
        assert capability.version == "1.0.0"


class TestAgentDependency:
    """Test AgentDependency class."""

    def test_dependency_creation(self):
        """Test creating agent dependency."""
        dependency = AgentDependency(
            name="document_parser",
            version_requirement=">=1.0.0",
            required=True,
            description="Document parsing dependency",
        )

        assert dependency.name == "document_parser"
        assert dependency.version_requirement == ">=1.0.0"
        assert dependency.required is True
        assert dependency.description == "Document parsing dependency"

    def test_dependency_defaults(self):
        """Test dependency with default values."""
        dependency = AgentDependency("test_dep")

        assert dependency.name == "test_dep"
        assert dependency.version_requirement == "*"
        assert dependency.required is True
        assert dependency.description == ""


class TestRegistryEntry:
    """Test RegistryEntry class."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample agent metadata."""
        return AgentMetadata(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent for registry",
            capabilities=["test"],
            dependencies=[],
        )

    @pytest.fixture
    def sample_capabilities(self):
        """Create sample capabilities."""
        return [
            AgentCapability("test_capability", "Test capability"),
            AgentCapability("data_processing", "Process data"),
        ]

    @pytest.fixture
    def sample_dependencies(self):
        """Create sample dependencies."""
        return [AgentDependency("dep1", ">=1.0.0"), AgentDependency("dep2", "*", False)]

    def test_registry_entry_creation(
        self, sample_metadata, sample_capabilities, sample_dependencies
    ):
        """Test creating registry entry."""
        entry = RegistryEntry(
            agent_id="test_agent",
            metadata=sample_metadata,
            capabilities=sample_capabilities,
            dependencies=sample_dependencies,
        )

        assert entry.agent_id == "test_agent"
        assert entry.metadata == sample_metadata
        assert len(entry.capabilities) == 2
        assert len(entry.dependencies) == 2
        assert entry.usage_count == 0
        assert entry.last_used is None

    def test_registry_entry_to_dict(
        self, sample_metadata, sample_capabilities, sample_dependencies
    ):
        """Test converting registry entry to dictionary."""
        entry = RegistryEntry(
            agent_id="test_agent",
            metadata=sample_metadata,
            capabilities=sample_capabilities,
            dependencies=sample_dependencies,
        )

        entry_dict = entry.to_dict()

        assert entry_dict["agent_id"] == "test_agent"
        assert entry_dict["metadata"]["name"] == "Test Agent"
        assert len(entry_dict["capabilities"]) == 2
        assert len(entry_dict["dependencies"]) == 2
        assert entry_dict["usage_count"] == 0


class TestAgentRegistry:
    """Test AgentRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create registry instance for testing."""
        return AgentRegistry()

    @pytest.fixture
    def registry_with_persistence(self):
        """Create registry with temporary persistence file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        registry = AgentRegistry(persistence_path=temp_path)
        yield registry

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample agent metadata."""
        return AgentMetadata(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent",
            capabilities=["test_capability"],
            dependencies=[],
        )

    @pytest.mark.asyncio
    async def test_register_agent_success(self, registry, sample_metadata):
        """Test successful agent registration."""
        result = await registry.register_agent(
            agent_id="test_agent",
            metadata=sample_metadata,
            capabilities=["test_capability"],
            dependencies=[],
        )

        assert result is True
        assert "test_agent" in registry._entries

        entry = registry._entries["test_agent"]
        assert entry.agent_id == "test_agent"
        assert len(entry.capabilities) == 1
        assert entry.capabilities[0].name == "test_capability"

    @pytest.mark.asyncio
    async def test_register_agent_with_dependencies(self, registry, sample_metadata):
        """Test registering agent with dependencies."""
        # Register dependency first
        dep_metadata = AgentMetadata("dep_agent", "Dependency", "", [], [])
        await registry.register_agent("dep_agent", dep_metadata)

        # Register agent with dependency
        result = await registry.register_agent(
            agent_id="test_agent",
            metadata=sample_metadata,
            capabilities=["test_capability"],
            dependencies=["dep_agent"],
        )

        assert result is True

        # Check dependency graph
        dependencies = registry.get_agent_dependencies("test_agent")
        assert "dep_agent" in dependencies

        dependents = registry.get_agent_dependents("dep_agent")
        assert "test_agent" in dependents

    @pytest.mark.asyncio
    async def test_register_agent_circular_dependency(self, registry):
        """Test prevention of circular dependencies."""
        # Create metadata
        metadata1 = AgentMetadata("agent1", "Agent 1", "", [], [])
        metadata2 = AgentMetadata("agent2", "Agent 2", "", [], [])

        # Register first agent
        await registry.register_agent("agent1", metadata1, dependencies=["agent2"])

        # Try to register second agent with circular dependency
        result = await registry.register_agent(
            "agent2", metadata2, dependencies=["agent1"]
        )

        # Should fail due to circular dependency
        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_agent(self, registry, sample_metadata):
        """Test agent unregistration."""
        # Register agent first
        await registry.register_agent("test_agent", sample_metadata)
        assert "test_agent" in registry._entries

        # Unregister agent
        result = await registry.unregister_agent("test_agent")

        assert result is True
        assert "test_agent" not in registry._entries

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_agent(self, registry):
        """Test unregistering non-existent agent."""
        result = await registry.unregister_agent("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_agent_status(self, registry, sample_metadata):
        """Test updating agent status."""
        # Register agent first
        await registry.register_agent("test_agent", sample_metadata)

        # Update status
        result = await registry.update_agent_status("test_agent", AgentStatus.DISABLED)

        assert result is True
        entry = registry._entries["test_agent"]
        assert entry.metadata.status == AgentStatus.DISABLED

    def test_get_agent_info(self, registry):
        """Test getting agent information."""
        # Create and add entry manually
        metadata = AgentMetadata("test_agent", "Test", "", [], [])
        entry = RegistryEntry("test_agent", metadata)
        registry._entries["test_agent"] = entry

        # Get info
        result = registry.get_agent_info("test_agent")

        assert result is not None
        assert result.agent_id == "test_agent"

        # Non-existent agent
        result = registry.get_agent_info("nonexistent")
        assert result is None

    def test_list_agents(self, registry):
        """Test listing agents."""
        # Create entries
        metadata1 = AgentMetadata("agent1", "Agent 1", "", [], [])
        metadata1.status = AgentStatus.ACTIVE  # Explicitly set to active
        metadata2 = AgentMetadata("agent2", "Agent 2", "", [], [])
        metadata2.status = AgentStatus.DISABLED

        entry1 = RegistryEntry("agent1", metadata1)
        entry2 = RegistryEntry("agent2", metadata2)

        registry._entries["agent1"] = entry1
        registry._entries["agent2"] = entry2

        # List all agents
        all_agents = registry.list_agents()
        assert len(all_agents) == 2

        # List active agents only
        active_agents = registry.list_agents(status_filter=AgentStatus.ACTIVE)
        assert len(active_agents) == 1
        assert active_agents[0].agent_id == "agent1"

    def test_find_agents_by_capability(self, registry):
        """Test finding agents by capability."""
        # Create entries with capabilities
        metadata1 = AgentMetadata("agent1", "Agent 1", "", ["cap1", "cap2"], [])
        metadata2 = AgentMetadata("agent2", "Agent 2", "", ["cap2", "cap3"], [])

        entry1 = RegistryEntry("agent1", metadata1)
        entry2 = RegistryEntry("agent2", metadata2)

        registry._entries["agent1"] = entry1
        registry._entries["agent2"] = entry2

        # Update capability index
        registry._capability_index["cap1"] = {"agent1"}
        registry._capability_index["cap2"] = {"agent1", "agent2"}
        registry._capability_index["cap3"] = {"agent2"}

        # Find agents
        agents_with_cap1 = registry.find_agents_by_capability("cap1")
        assert "agent1" in agents_with_cap1
        assert len(agents_with_cap1) == 1

        agents_with_cap2 = registry.find_agents_by_capability("cap2")
        assert "agent1" in agents_with_cap2
        assert "agent2" in agents_with_cap2
        assert len(agents_with_cap2) == 2

    def test_get_capabilities_summary(self, registry):
        """Test getting capabilities summary."""
        registry._capability_index = {
            "cap1": {"agent1"},
            "cap2": {"agent1", "agent2"},
            "cap3": {"agent2"},
        }

        summary = registry.get_capabilities_summary()

        assert summary["cap1"] == ["agent1"]
        assert set(summary["cap2"]) == {"agent1", "agent2"}
        assert summary["cap3"] == ["agent2"]

    def test_get_dependency_graph(self, registry):
        """Test getting dependency graph."""
        registry._dependency_graph = {"agent1": {"dep1", "dep2"}, "agent2": {"dep1"}}

        graph = registry.get_dependency_graph()

        assert set(graph["agent1"]) == {"dep1", "dep2"}
        assert graph["agent2"] == ["dep1"]

    @pytest.mark.asyncio
    async def test_validate_dependency_chain_success(self, registry):
        """Test successful dependency chain validation."""
        # Setup dependency chain: agent1 -> agent2 -> agent3
        registry._dependency_graph = {
            "agent1": {"agent2"},
            "agent2": {"agent3"},
            "agent3": set(),
        }

        # Add entries to registry
        for agent_id in ["agent1", "agent2", "agent3"]:
            metadata = AgentMetadata(agent_id, f"Agent {agent_id}", "", [], [])
            registry._entries[agent_id] = RegistryEntry(agent_id, metadata)

        result = await registry.validate_dependency_chain("agent1")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_dependency_chain_circular(self, registry):
        """Test detection of circular dependencies."""
        # Setup circular dependency: agent1 -> agent2 -> agent1
        registry._dependency_graph = {"agent1": {"agent2"}, "agent2": {"agent1"}}

        result = await registry.validate_dependency_chain("agent1")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_dependency_chain_missing(self, registry):
        """Test detection of missing dependencies."""
        # Setup dependency to non-existent agent
        registry._dependency_graph = {"agent1": {"nonexistent"}}

        # Add agent1 to registry but not the dependency
        metadata = AgentMetadata("agent1", "Agent 1", "", [], [])
        registry._entries["agent1"] = RegistryEntry("agent1", metadata)

        result = await registry.validate_dependency_chain("agent1")
        assert result is False

    @pytest.mark.asyncio
    async def test_record_agent_usage(self, registry, sample_metadata):
        """Test recording agent usage."""
        # Register agent first
        await registry.register_agent("test_agent", sample_metadata)

        entry = registry._entries["test_agent"]
        initial_count = entry.usage_count

        # Record usage
        await registry.record_agent_usage("test_agent")

        assert entry.usage_count == initial_count + 1
        assert entry.last_used is not None

    @pytest.mark.asyncio
    async def test_persistence(self, registry_with_persistence, sample_metadata):
        """Test registry persistence."""
        # Register agent
        await registry_with_persistence.register_agent("test_agent", sample_metadata)

        # Check that persistence file was created
        persistence_path = Path(registry_with_persistence._persistence_path)
        assert persistence_path.exists()

        # Load registry should work
        result = await registry_with_persistence.load_registry()
        assert result is True

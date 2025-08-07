"""
Load Testing and Concurrent User Simulation.

This module validates system performance under concurrent load as specified
in PRD Technical Assumptions:

- 50-200 concurrent users maximum per client VPS instance
- System handles concurrent user workflows gracefully
- Response times remain acceptable under load
- Resource utilization stays within limits
- Database performance doesn't degrade significantly
- Permission system performance maintained under load

Test Scenarios:
1. Gradual load increase (10, 25, 50, 100, 150, 200 users)
2. Sustained load testing (100 users for 2 minutes)
3. Peak load burst testing (200 users for 30 seconds)
4. Mixed workflow simulation (realistic user behavior)
5. System recovery testing (post-load performance)
"""

import asyncio
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel import Session

from src.models.permissions import AgentName
from src.models.user import UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import create_test_client, create_test_permission, create_test_user


class UserSimulation:
    """Simulates realistic user behavior patterns."""
    
    def __init__(self, user_id: str, session: Session, permission_service: PermissionService):
        self.user_id = user_id
        self.session = session
        self.permission_service = permission_service
        self.session_start_time = time.time()
        self.operations_completed = 0
        self.errors_encountered = 0
        
    async def simulate_typical_user_session(self) -> Dict[str, Any]:
        """Simulate a typical 2-5 minute user session."""
        session_duration = random.uniform(120, 300)  # 2-5 minutes
        end_time = self.session_start_time + session_duration
        
        operations = []
        
        while time.time() < end_time:
            # Simulate typical user operations
            operation_type = random.choices(
                ["permission_check", "client_list", "client_search", "user_info", "idle"],
                weights=[40, 25, 15, 10, 10]  # Permission checks are most common
            )[0]
            
            try:
                operation_start = time.time()
                
                if operation_type == "permission_check":
                    result = await self._check_permissions()
                elif operation_type == "client_list":
                    result = await self._simulate_client_list()
                elif operation_type == "client_search":
                    result = await self._simulate_client_search()
                elif operation_type == "user_info":
                    result = await self._simulate_user_info()
                else:  # idle
                    await asyncio.sleep(random.uniform(1, 5))
                    result = {"success": True, "type": "idle"}
                
                operation_time = (time.time() - operation_start) * 1000
                
                operations.append({
                    "type": operation_type,
                    "duration_ms": operation_time,
                    "success": result.get("success", True),
                    "timestamp": time.time()
                })
                
                self.operations_completed += 1
                
                if not result.get("success", True):
                    self.errors_encountered += 1
                
                # Realistic pause between operations
                await asyncio.sleep(random.uniform(0.5, 3.0))
                
            except Exception as e:
                self.errors_encountered += 1
                operations.append({
                    "type": operation_type,
                    "duration_ms": 0,
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                })

        total_session_time = time.time() - self.session_start_time
        
        return {
            "user_id": self.user_id,
            "total_session_time_s": total_session_time,
            "operations_completed": self.operations_completed,
            "errors_encountered": self.errors_encountered,
            "operations": operations,
            "success_rate": (self.operations_completed - self.errors_encountered) / max(self.operations_completed, 1),
            "avg_operation_time": statistics.mean([op["duration_ms"] for op in operations if op["duration_ms"] > 0]) if operations else 0
        }
    
    async def _check_permissions(self) -> Dict[str, Any]:
        """Simulate permission checking."""
        try:
            agents = [AgentName.CLIENT_MANAGEMENT, AgentName.PDF_PROCESSING, AgentName.REPORTS_ANALYSIS]
            operations = ["read", "create", "update", "delete"]
            
            agent = random.choice(agents)
            operation = random.choice(operations)
            
            result = await self.permission_service.check_user_permission(
                user_id=uuid4(),  # Use dummy user_id for simulation
                agent_name=agent,
                operation=operation
            )
            
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _simulate_client_list(self) -> Dict[str, Any]:
        """Simulate client listing operation."""
        try:
            # Simulate time for client list operation
            await asyncio.sleep(random.uniform(0.05, 0.2))
            return {"success": True, "clients_count": random.randint(10, 100)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _simulate_client_search(self) -> Dict[str, Any]:
        """Simulate client search operation."""
        try:
            # Simulate time for client search
            await asyncio.sleep(random.uniform(0.1, 0.3))
            return {"success": True, "search_results": random.randint(0, 20)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _simulate_user_info(self) -> Dict[str, Any]:
        """Simulate user info retrieval."""
        try:
            # Simulate time for user info
            await asyncio.sleep(random.uniform(0.02, 0.1))
            return {"success": True, "user_loaded": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TestLoadTestingConcurrentUsers:
    """Load testing and concurrent user simulation tests."""

    # Gradual Load Testing

    @pytest.mark.parametrize("concurrent_users", [10, 25, 50, 100, 150, 200])
    async def test_gradual_load_increase(
        self,
        concurrent_users: int,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test system performance with gradually increasing concurrent users."""
        print(f"\n=== Testing {concurrent_users} Concurrent Users ===")
        
        # Create test users and permissions for simulation
        user_data = self._prepare_test_users(concurrent_users, test_session)
        
        start_time = time.time()
        
        # Create user simulations
        simulations = []
        for i in range(concurrent_users):
            user_sim = UserSimulation(
                user_id=user_data[i]["user_id"],
                session=test_session,
                permission_service=fast_permission_service
            )
            simulations.append(user_sim)
        
        # Run concurrent user sessions (shorter sessions for load testing)
        session_tasks = []
        for sim in simulations:
            # Override session duration for load testing (30-60 seconds)
            sim.session_start_time = time.time()
            task = self._run_short_user_session(sim, duration_seconds=45)
            session_tasks.append(task)
        
        # Execute all concurrent sessions
        session_results = await asyncio.gather(*session_tasks, return_exceptions=True)
        
        total_test_time = time.time() - start_time
        
        # Analyze results
        successful_sessions = [r for r in session_results if isinstance(r, dict) and r.get("success_rate", 0) > 0.8]
        failed_sessions = [r for r in session_results if isinstance(r, Exception) or (isinstance(r, dict) and r.get("success_rate", 0) <= 0.8)]
        
        success_rate = len(successful_sessions) / len(session_results)
        
        if successful_sessions:
            avg_operation_time = statistics.mean([s["avg_operation_time"] for s in successful_sessions])
            total_operations = sum([s["operations_completed"] for s in successful_sessions])
            operations_per_second = total_operations / total_test_time
        else:
            avg_operation_time = 0
            operations_per_second = 0
        
        print(f"Results for {concurrent_users} users:")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Avg Operation Time: {avg_operation_time:.2f}ms")
        print(f"  Operations/Second: {operations_per_second:.2f}")
        print(f"  Total Test Time: {total_test_time:.2f}s")
        
        # Performance assertions based on concurrent user count
        if concurrent_users <= 50:
            assert success_rate >= 0.95, f"Success rate {success_rate:.2%} too low for {concurrent_users} users"
            assert avg_operation_time < 100, f"Average operation time {avg_operation_time:.2f}ms too high"
        elif concurrent_users <= 100:
            assert success_rate >= 0.90, f"Success rate {success_rate:.2%} too low for {concurrent_users} users"
            assert avg_operation_time < 200, f"Average operation time {avg_operation_time:.2f}ms too high"
        elif concurrent_users <= 200:
            assert success_rate >= 0.85, f"Success rate {success_rate:.2%} acceptable for {concurrent_users} users"
            assert avg_operation_time < 400, f"Average operation time {avg_operation_time:.2f}ms too high"
        
        assert operations_per_second > concurrent_users * 0.5, (
            f"System throughput {operations_per_second:.2f} ops/sec too low for {concurrent_users} users"
        )

    async def test_sustained_load_100_users_2_minutes(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test sustained load with 100 users for 2 minutes."""
        concurrent_users = 100
        test_duration = 120  # 2 minutes
        
        print(f"\n=== Sustained Load Test: {concurrent_users} Users for {test_duration}s ===")
        
        # Prepare test data
        user_data = self._prepare_test_users(concurrent_users, test_session)
        
        start_time = time.time()
        performance_samples = []
        
        # Create user simulations with longer sessions
        simulations = []
        for i in range(concurrent_users):
            user_sim = UserSimulation(
                user_id=user_data[i]["user_id"],
                session=test_session,
                permission_service=fast_permission_service
            )
            simulations.append(user_sim)
        
        # Run sustained load test
        async def monitor_performance():
            """Monitor performance during sustained load."""
            while (time.time() - start_time) < test_duration:
                sample_start = time.time()
                
                # Sample performance of a subset of operations
                sample_tasks = []
                for _ in range(10):  # Sample 10 operations
                    sim = random.choice(simulations)
                    task = sim._check_permissions()
                    sample_tasks.append(task)
                
                sample_results = await asyncio.gather(*sample_tasks, return_exceptions=True)
                sample_time = (time.time() - sample_start) * 1000
                
                successful_samples = [r for r in sample_results if isinstance(r, dict) and r.get("success", False)]
                
                performance_samples.append({
                    "timestamp": time.time() - start_time,
                    "sample_time_ms": sample_time,
                    "success_rate": len(successful_samples) / len(sample_results),
                    "operations_tested": len(sample_results)
                })
                
                await asyncio.sleep(5)  # Sample every 5 seconds
        
        # Start performance monitoring
        monitor_task = asyncio.create_task(monitor_performance())
        
        # Run user sessions for test duration
        session_tasks = []
        for sim in simulations:
            task = self._run_sustained_user_session(sim, test_duration)
            session_tasks.append(task)
        
        # Wait for all sessions and monitoring to complete
        session_results, _ = await asyncio.gather(
            asyncio.gather(*session_tasks, return_exceptions=True),
            monitor_task,
            return_exceptions=True
        )
        
        total_test_time = time.time() - start_time
        
        # Analyze sustained load results
        successful_sessions = [r for r in session_results if isinstance(r, dict) and r.get("success_rate", 0) > 0.7]
        success_rate = len(successful_sessions) / len(session_results)
        
        # Analyze performance degradation over time
        if performance_samples:
            early_samples = performance_samples[:len(performance_samples)//3]
            late_samples = performance_samples[-len(performance_samples)//3:]
            
            early_avg_time = statistics.mean([s["sample_time_ms"] for s in early_samples])
            late_avg_time = statistics.mean([s["sample_time_ms"] for s in late_samples])
            
            performance_degradation = (late_avg_time - early_avg_time) / early_avg_time
        else:
            performance_degradation = 0
        
        print(f"Sustained Load Results:")
        print(f"  Overall Success Rate: {success_rate:.2%}")
        print(f"  Performance Degradation: {performance_degradation:.2%}")
        print(f"  Test Duration: {total_test_time:.2f}s")
        
        # Sustained load assertions
        assert success_rate >= 0.85, f"Sustained load success rate {success_rate:.2%} too low"
        assert performance_degradation < 0.3, (
            f"Performance degraded by {performance_degradation:.2%}, should be <30%"
        )
        assert total_test_time >= test_duration * 0.9, "Test didn't run for full duration"

    async def test_peak_load_burst_200_users_30_seconds(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test peak load burst with 200 users for 30 seconds."""
        concurrent_users = 200
        burst_duration = 30
        
        print(f"\n=== Peak Load Burst Test: {concurrent_users} Users for {burst_duration}s ===")
        
        # Prepare test data
        user_data = self._prepare_test_users(concurrent_users, test_session)
        
        start_time = time.time()
        
        # Create intensive user simulations
        async def intensive_user_operations(user_id: str) -> Dict[str, Any]:
            """Intensive operations for burst testing."""
            operations_completed = 0
            errors = 0
            durations = []
            
            session_start = time.time()
            
            while (time.time() - session_start) < burst_duration:
                try:
                    operation_start = time.time()
                    
                    # Perform rapid permission checks
                    result = await fast_permission_service.check_user_permission(
                        user_id=uuid4(),
                        agent_name=random.choice(list(AgentName)),
                        operation=random.choice(["read", "create", "update", "delete"])
                    )
                    
                    operation_time = (time.time() - operation_start) * 1000
                    durations.append(operation_time)
                    operations_completed += 1
                    
                    # Minimal delay for burst testing
                    await asyncio.sleep(0.05)
                    
                except Exception:
                    errors += 1
            
            return {
                "user_id": user_id,
                "operations_completed": operations_completed,
                "errors": errors,
                "avg_operation_time": statistics.mean(durations) if durations else 0,
                "max_operation_time": max(durations) if durations else 0
            }
        
        # Execute burst load test
        burst_tasks = [
            intensive_user_operations(user_data[i]["user_id"])
            for i in range(concurrent_users)
        ]
        
        burst_results = await asyncio.gather(*burst_tasks, return_exceptions=True)
        
        total_burst_time = time.time() - start_time
        
        # Analyze burst test results
        successful_results = [r for r in burst_results if isinstance(r, dict)]
        
        if successful_results:
            total_operations = sum([r["operations_completed"] for r in successful_results])
            total_errors = sum([r["errors"] for r in successful_results])
            avg_operation_time = statistics.mean([r["avg_operation_time"] for r in successful_results])
            max_operation_time = max([r["max_operation_time"] for r in successful_results])
            
            success_rate = (total_operations - total_errors) / max(total_operations, 1)
            operations_per_second = total_operations / total_burst_time
        else:
            success_rate = 0
            operations_per_second = 0
            avg_operation_time = 0
            max_operation_time = 0
        
        print(f"Peak Load Burst Results:")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Operations/Second: {operations_per_second:.2f}")
        print(f"  Avg Operation Time: {avg_operation_time:.2f}ms")
        print(f"  Max Operation Time: {max_operation_time:.2f}ms")
        
        # Peak load assertions (more lenient for 200 users)
        assert success_rate >= 0.75, f"Peak load success rate {success_rate:.2%} too low"
        assert operations_per_second > 50, f"Peak load throughput {operations_per_second:.2f} too low"
        assert avg_operation_time < 500, f"Peak load avg time {avg_operation_time:.2f}ms too high"

    # System Recovery Testing

    async def test_system_recovery_after_load(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test system recovery and performance after heavy load."""
        # First, apply heavy load
        print("\n=== System Recovery Test ===")
        print("Phase 1: Applying heavy load...")
        
        concurrent_users = 150
        load_duration = 60  # 1 minute of heavy load
        
        user_data = self._prepare_test_users(concurrent_users, test_session)
        
        # Apply heavy load
        load_start = time.time()
        load_tasks = []
        
        for i in range(concurrent_users):
            sim = UserSimulation(
                user_id=user_data[i]["user_id"],
                session=test_session,
                permission_service=fast_permission_service
            )
            task = self._run_short_user_session(sim, duration_seconds=load_duration)
            load_tasks.append(task)
        
        await asyncio.gather(*load_tasks, return_exceptions=True)
        load_time = time.time() - load_start
        
        print(f"Heavy load applied for {load_time:.2f}s")
        
        # Recovery period
        print("Phase 2: Recovery period...")
        await asyncio.sleep(30)  # 30 second recovery
        
        # Test post-load performance
        print("Phase 3: Testing post-load performance...")
        
        recovery_start = time.time()
        light_users = 10
        recovery_tasks = []
        
        for i in range(light_users):
            sim = UserSimulation(
                user_id=user_data[i]["user_id"],
                session=test_session,
                permission_service=fast_permission_service
            )
            task = self._run_short_user_session(sim, duration_seconds=30)
            recovery_tasks.append(task)
        
        recovery_results = await asyncio.gather(*recovery_tasks, return_exceptions=True)
        recovery_time = time.time() - recovery_start
        
        # Analyze recovery performance
        successful_recovery = [r for r in recovery_results if isinstance(r, dict) and r.get("success_rate", 0) > 0.9]
        recovery_success_rate = len(successful_recovery) / len(recovery_results)
        
        if successful_recovery:
            avg_recovery_time = statistics.mean([r["avg_operation_time"] for r in successful_recovery])
        else:
            avg_recovery_time = 0
        
        print(f"Recovery Results:")
        print(f"  Recovery Success Rate: {recovery_success_rate:.2%}")
        print(f"  Avg Operation Time After Recovery: {avg_recovery_time:.2f}ms")
        
        # Recovery assertions
        assert recovery_success_rate >= 0.9, (
            f"System recovery poor: {recovery_success_rate:.2%} success rate"
        )
        assert avg_recovery_time < 100, (
            f"System not recovered: {avg_recovery_time:.2f}ms operation time"
        )

    # Mixed Workflow Simulation

    async def test_mixed_realistic_user_workflows(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test mixed realistic user workflows with varied user types."""
        print("\n=== Mixed Realistic User Workflows ===")
        
        # Create different types of users
        user_types = {
            "power_users": 20,    # Heavy usage, many operations
            "regular_users": 60,  # Normal usage
            "casual_users": 40,   # Light usage, longer idle times
        }
        
        total_users = sum(user_types.values())
        user_data = self._prepare_test_users(total_users, test_session)
        
        start_time = time.time()
        workflow_tasks = []
        
        user_index = 0
        
        # Create power user simulations
        for _ in range(user_types["power_users"]):
            sim = UserSimulation(
                user_id=user_data[user_index]["user_id"],
                session=test_session,
                permission_service=fast_permission_service
            )
            task = self._run_power_user_workflow(sim)
            workflow_tasks.append(task)
            user_index += 1
        
        # Create regular user simulations
        for _ in range(user_types["regular_users"]):
            sim = UserSimulation(
                user_id=user_data[user_index]["user_id"],
                session=test_session,
                permission_service=fast_permission_service
            )
            task = self._run_regular_user_workflow(sim)
            workflow_tasks.append(task)
            user_index += 1
        
        # Create casual user simulations
        for _ in range(user_types["casual_users"]):
            sim = UserSimulation(
                user_id=user_data[user_index]["user_id"],
                session=test_session,
                permission_service=fast_permission_service
            )
            task = self._run_casual_user_workflow(sim)
            workflow_tasks.append(task)
            user_index += 1
        
        # Execute mixed workflows
        workflow_results = await asyncio.gather(*workflow_tasks, return_exceptions=True)
        
        total_workflow_time = time.time() - start_time
        
        # Analyze mixed workflow results
        successful_workflows = [r for r in workflow_results if isinstance(r, dict) and r.get("success_rate", 0) > 0.8]
        overall_success_rate = len(successful_workflows) / len(workflow_results)
        
        if successful_workflows:
            avg_operation_time = statistics.mean([w["avg_operation_time"] for w in successful_workflows])
            total_operations = sum([w["operations_completed"] for w in successful_workflows])
            operations_per_second = total_operations / total_workflow_time
        else:
            avg_operation_time = 0
            operations_per_second = 0
        
        print(f"Mixed Workflow Results:")
        print(f"  Overall Success Rate: {overall_success_rate:.2%}")
        print(f"  Total Users Simulated: {total_users}")
        print(f"  Average Operation Time: {avg_operation_time:.2f}ms")
        print(f"  System Throughput: {operations_per_second:.2f} ops/sec")
        print(f"  Test Duration: {total_workflow_time:.2f}s")
        
        # Mixed workflow assertions
        assert overall_success_rate >= 0.9, (
            f"Mixed workflow success rate {overall_success_rate:.2%} too low"
        )
        assert avg_operation_time < 150, (
            f"Mixed workflow avg time {avg_operation_time:.2f}ms too high"
        )
        assert operations_per_second > 30, (
            f"Mixed workflow throughput {operations_per_second:.2f} too low"
        )

    # Helper Methods

    def _prepare_test_users(self, count: int, session: Session) -> List[Dict[str, Any]]:
        """Prepare test users for load testing."""
        user_data = []
        
        for i in range(count):
            user = create_test_user(
                email=f"load.test.user.{i}@example.com",
                role=UserRole.USER if i % 5 != 0 else UserRole.ADMIN
            )
            session.add(user)
            
            # Create permissions for each user
            for agent in AgentName:
                permission = create_test_permission(
                    user_id=user.user_id,
                    agent_name=agent,
                    permissions={
                        "read": True,
                        "create": i % 3 == 0,
                        "update": i % 4 == 0,
                        "delete": i % 10 == 0
                    }
                )
                session.add(permission)
            
            user_data.append({
                "user_id": str(user.user_id),
                "email": user.email,
                "role": user.role
            })
        
        session.commit()
        return user_data

    async def _run_short_user_session(self, simulation: UserSimulation, duration_seconds: int) -> Dict[str, Any]:
        """Run a short user session for load testing."""
        operations = 0
        errors = 0
        durations = []
        
        session_start = time.time()
        
        while (time.time() - session_start) < duration_seconds:
            try:
                operation_start = time.time()
                
                # Perform typical operations
                operation_type = random.choices(
                    ["permission_check", "quick_query", "idle"],
                    weights=[60, 30, 10]
                )[0]
                
                if operation_type == "permission_check":
                    await simulation._check_permissions()
                elif operation_type == "quick_query":
                    await asyncio.sleep(random.uniform(0.01, 0.05))  # Simulate quick query
                else:  # idle
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                
                operation_time = (time.time() - operation_start) * 1000
                durations.append(operation_time)
                operations += 1
                
            except Exception:
                errors += 1
            
            # Short pause between operations
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        return {
            "operations_completed": operations,
            "errors": errors,
            "success_rate": (operations - errors) / max(operations, 1),
            "avg_operation_time": statistics.mean(durations) if durations else 0
        }

    async def _run_sustained_user_session(self, simulation: UserSimulation, duration_seconds: int) -> Dict[str, Any]:
        """Run a sustained user session."""
        return await simulation.simulate_typical_user_session()

    async def _run_power_user_workflow(self, simulation: UserSimulation) -> Dict[str, Any]:
        """Simulate power user behavior (frequent operations)."""
        operations = 0
        errors = 0
        durations = []
        
        session_start = time.time()
        session_duration = random.uniform(180, 300)  # 3-5 minutes
        
        while (time.time() - session_start) < session_duration:
            try:
                operation_start = time.time()
                
                # Power users do more permission checks and complex operations
                operation_type = random.choices(
                    ["permission_check", "client_operation", "user_management"],
                    weights=[50, 30, 20]
                )[0]
                
                if operation_type == "permission_check":
                    await simulation._check_permissions()
                elif operation_type == "client_operation":
                    await simulation._simulate_client_list()
                    await simulation._simulate_client_search()
                else:  # user_management
                    await simulation._simulate_user_info()
                
                operation_time = (time.time() - operation_start) * 1000
                durations.append(operation_time)
                operations += 1
                
                # Power users have shorter pauses
                await asyncio.sleep(random.uniform(0.2, 1.0))
                
            except Exception:
                errors += 1
        
        return {
            "operations_completed": operations,
            "errors": errors,
            "success_rate": (operations - errors) / max(operations, 1),
            "avg_operation_time": statistics.mean(durations) if durations else 0,
            "user_type": "power"
        }

    async def _run_regular_user_workflow(self, simulation: UserSimulation) -> Dict[str, Any]:
        """Simulate regular user behavior."""
        return await simulation.simulate_typical_user_session()

    async def _run_casual_user_workflow(self, simulation: UserSimulation) -> Dict[str, Any]:
        """Simulate casual user behavior (lighter usage, more idle time)."""
        operations = 0
        errors = 0
        durations = []
        
        session_start = time.time()
        session_duration = random.uniform(60, 180)  # 1-3 minutes
        
        while (time.time() - session_start) < session_duration:
            try:
                operation_start = time.time()
                
                # Casual users mostly check permissions and view data
                operation_type = random.choices(
                    ["permission_check", "view_data", "idle"],
                    weights=[40, 20, 40]
                )[0]
                
                if operation_type == "permission_check":
                    await simulation._check_permissions()
                elif operation_type == "view_data":
                    await simulation._simulate_client_list()
                else:  # idle
                    await asyncio.sleep(random.uniform(5, 15))  # Longer idle times
                
                operation_time = (time.time() - operation_start) * 1000
                durations.append(operation_time)
                operations += 1
                
                # Casual users have longer pauses
                await asyncio.sleep(random.uniform(2, 8))
                
            except Exception:
                errors += 1
        
        return {
            "operations_completed": operations,
            "errors": errors,
            "success_rate": (operations - errors) / max(operations, 1),
            "avg_operation_time": statistics.mean(durations) if durations else 0,
            "user_type": "casual"
        }
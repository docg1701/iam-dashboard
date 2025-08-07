"""
Critical Performance SLA Tests.

This module validates that the system meets all critical performance SLAs
as defined in the PRD and CLAUDE.md requirements:

- Permission validation: <10ms per PRD NFR11
- API response times: <200ms per PRD NFR2
- Concurrent user capacity: 50-200 users per Technical Assumptions
- Database query performance: <50ms for most operations

Priority Order:
1. Permission System Performance (<100ms total for 100 checks)
2. API Response Times (<200ms per endpoint)
3. Database Query Performance (<50ms per query)
4. Load Testing (50-200 concurrent users)
"""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel import Session, select, text

from src.core.exceptions import DatabaseError
from src.models.permissions import AgentName
from src.models.user import User, UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import create_test_permission, create_test_user


class TestCriticalPerformanceSLA:
    """Critical Performance SLA validation tests."""

    # Permission System Performance Tests - Priority 1

    async def test_permission_check_under_100ms_for_100_checks(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """
        CRITICAL: Test 100 parallel permission checks complete in <100ms total.
        
        This validates PRD requirement for high-performance permission checking.
        Each individual check should be <10ms, total batch <100ms.
        """
        user_ids = [uuid4() for _ in range(100)]
        
        # Create real users and permissions in database
        for user_id in user_ids:
            user = create_test_user(role=UserRole.USER)
            user.user_id = user_id
            test_session.add(user)
            
            permission = create_test_permission(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions={"read": True, "create": True, "update": False, "delete": False}
            )
            test_session.add(permission)
        
        test_session.commit()

        # Test 100 parallel permission checks
        start_time = time.time()
        
        tasks = [
            fast_permission_service.check_user_permission(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                operation="read"
            )
            for user_id in user_ids
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        avg_duration_ms = total_duration_ms / len(tasks)

        # Assertions based on PRD requirements
        assert all(results), "All permission checks should succeed"
        assert total_duration_ms < 100, (
            f"CRITICAL SLA VIOLATION: 100 permission checks took {total_duration_ms}ms, "
            f"must be <100ms per PRD requirement"
        )
        assert avg_duration_ms < 10, (
            f"SLA VIOLATION: Average permission check took {avg_duration_ms}ms, "
            f"should be <10ms per PRD NFR11"
        )

    async def test_cached_permission_performance_under_5ms(
        self,
        fast_permission_service: PermissionService,
        mock_redis,
    ) -> None:
        """Test cached permission checks are extremely fast (<5ms)."""
        import json
        
        user_id = uuid4()
        
        # Mock Redis cache hit
        permissions = {"create": True, "read": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)

        # Test multiple cached lookups for statistical accuracy
        durations = []
        for _ in range(50):
            start_time = time.time()
            
            result = await fast_permission_service.check_user_permission(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                operation="read"
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert result is True

        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        p95_duration = sorted(durations)[int(0.95 * len(durations))]

        assert avg_duration < 5, (
            f"Average cached permission check took {avg_duration:.2f}ms, should be <5ms"
        )
        assert p95_duration < 10, (
            f"95th percentile cached check took {p95_duration:.2f}ms, should be <10ms"
        )
        assert max_duration < 15, (
            f"Max cached permission check took {max_duration:.2f}ms, should be <15ms"
        )

    async def test_permission_system_concurrent_load(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test permission system under 200 concurrent users simulating load."""
        num_users = 200
        user_ids = []
        
        # Create 200 users with permissions
        for _ in range(num_users):
            user_id = uuid4()
            user_ids.append(user_id)
            
            user = create_test_user(role=UserRole.USER)
            user.user_id = user_id
            test_session.add(user)
            
            # Create permissions for multiple agents
            for agent in [AgentName.CLIENT_MANAGEMENT, AgentName.PDF_PROCESSING]:
                permission = create_test_permission(
                    user_id=user_id,
                    agent_name=agent,
                    permissions={"read": True, "create": False, "update": False, "delete": False}
                )
                test_session.add(permission)
        
        test_session.commit()

        # Simulate 200 concurrent users each making 3 permission checks
        start_time = time.time()
        
        tasks = []
        for user_id in user_ids:
            # Each user checks 3 different operations
            for operation in ["read", "create", "update"]:
                task = fast_permission_service.check_user_permission(
                    user_id=user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    operation=operation
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_duration_s = end_time - start_time
        total_checks = len(tasks)
        checks_per_second = total_checks / total_duration_s

        # Performance assertions
        assert total_duration_s < 5, (
            f"600 concurrent permission checks took {total_duration_s:.2f}s, should be <5s"
        )
        assert checks_per_second > 200, (
            f"System handled {checks_per_second:.2f} checks/sec, should be >200/sec"
        )
        
        # Validate results
        read_results = results[::3]  # Every 3rd result (read operations)
        assert all(read_results), "All users should have read permissions"

    # API Response Time Tests - Priority 2

    async def test_auth_api_response_times_under_200ms(
        self,
        async_client: AsyncClient,
        test_session: Session,
    ) -> None:
        """Test authentication endpoints meet <200ms SLA per PRD NFR2."""
        # Create test user for login
        user = create_test_user(
            email="performance.test@example.com",
            role=UserRole.USER,
            is_active=True
        )
        test_session.add(user)
        test_session.commit()

        endpoints_to_test = [
            {
                "method": "POST",
                "url": "/api/v1/auth/login",
                "payload": {
                    "email": "performance.test@example.com",
                    "password": "TestPassword123!"
                },
                "expected_status": [200, 422],  # 422 if 2FA required
                "description": "User login"
            }
        ]

        for endpoint in endpoints_to_test:
            durations = []
            
            # Test each endpoint 10 times for statistical accuracy
            for _ in range(10):
                start_time = time.time()
                
                if endpoint["method"] == "POST":
                    response = await async_client.post(
                        endpoint["url"], 
                        json=endpoint["payload"]
                    )
                else:
                    response = await async_client.get(endpoint["url"])
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                durations.append(duration_ms)
                
                assert response.status_code in endpoint["expected_status"]

            avg_duration = statistics.mean(durations)
            max_duration = max(durations)
            p95_duration = sorted(durations)[int(0.95 * len(durations))]

            assert avg_duration < 200, (
                f"SLA VIOLATION: {endpoint['description']} average response time "
                f"{avg_duration:.2f}ms, must be <200ms per PRD NFR2"
            )
            assert p95_duration < 300, (
                f"Performance degradation: {endpoint['description']} 95th percentile "
                f"{p95_duration:.2f}ms, should be <300ms"
            )

    async def test_client_api_response_times_under_200ms(
        self,
        async_client: AsyncClient,
        test_session: Session,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test client management endpoints meet <200ms SLA."""
        endpoints_to_test = [
            {
                "method": "GET",
                "url": "/api/v1/clients",
                "description": "List clients"
            },
            {
                "method": "POST", 
                "url": "/api/v1/clients",
                "payload": {
                    "name": "Performance Test Client",
                    "ssn": "12345678901",
                    "birth_date": "1990-01-01"
                },
                "description": "Create client"
            }
        ]

        for endpoint in endpoints_to_test:
            durations = []
            
            for _ in range(5):  # Fewer iterations for POST requests
                start_time = time.time()
                
                if endpoint["method"] == "POST":
                    # Generate unique SSN for each request
                    payload = endpoint["payload"].copy()
                    payload["ssn"] = f"{uuid4().hex[:11]}"
                    
                    response = await async_client.post(
                        endpoint["url"],
                        json=payload,
                        headers=authenticated_headers
                    )
                else:
                    response = await async_client.get(
                        endpoint["url"],
                        headers=authenticated_headers
                    )
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                durations.append(duration_ms)

            avg_duration = statistics.mean(durations)
            
            assert avg_duration < 200, (
                f"SLA VIOLATION: {endpoint['description']} average response time "
                f"{avg_duration:.2f}ms, must be <200ms per PRD NFR2"
            )

    # Database Query Performance Tests - Priority 3

    async def test_database_query_performance_under_50ms(
        self,
        test_session: Session,
    ) -> None:
        """Test critical database queries complete in <50ms."""
        # Create test data
        user_ids = []
        for i in range(100):
            user = create_test_user(
                email=f"perf.user.{i}@example.com",
                role=UserRole.USER
            )
            test_session.add(user)
            user_ids.append(user.user_id)
        
        test_session.commit()

        queries_to_test = [
            {
                "description": "User lookup by ID",
                "query": lambda uid: test_session.get(User, uid),
                "target_ms": 25
            },
            {
                "description": "User lookup by email", 
                "query": lambda email: test_session.exec(
                    select(User).where(User.email == email)
                ).first(),
                "target_ms": 50
            },
            {
                "description": "Count active users",
                "query": lambda _: test_session.exec(
                    text("SELECT COUNT(*) FROM users WHERE is_active = true")
                ).scalar(),
                "target_ms": 30
            }
        ]

        for query_test in queries_to_test:
            durations = []
            
            # Test each query 20 times
            for i in range(20):
                start_time = time.time()
                
                if "User lookup by ID" in query_test["description"]:
                    result = query_test["query"](user_ids[i % len(user_ids)])
                elif "User lookup by email" in query_test["description"]:
                    email = f"perf.user.{i % 100}@example.com"
                    result = query_test["query"](email)
                else:
                    result = query_test["query"](None)
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                durations.append(duration_ms)
                
                # Verify query returned result
                assert result is not None

            avg_duration = statistics.mean(durations)
            max_duration = max(durations)
            
            assert avg_duration < query_test["target_ms"], (
                f"Database performance issue: {query_test['description']} "
                f"average {avg_duration:.2f}ms, target <{query_test['target_ms']}ms"
            )
            assert max_duration < query_test["target_ms"] * 2, (
                f"Database performance spike: {query_test['description']} "
                f"max {max_duration:.2f}ms, should be <{query_test['target_ms'] * 2}ms"
            )

    # Concurrent User Load Tests - Priority 4

    def test_concurrent_user_simulation_50_users(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test system handles 50 concurrent users gracefully."""
        self._run_concurrent_user_test(fast_permission_service, test_session, 50)

    def test_concurrent_user_simulation_100_users(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test system handles 100 concurrent users gracefully."""
        self._run_concurrent_user_test(fast_permission_service, test_session, 100)

    def test_concurrent_user_simulation_200_users_max_capacity(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test system handles 200 concurrent users (max capacity per PRD)."""
        self._run_concurrent_user_test(fast_permission_service, test_session, 200)

    def _run_concurrent_user_test(
        self,
        permission_service: PermissionService,
        test_session: Session,
        num_users: int,
    ) -> None:
        """Helper method to run concurrent user simulation."""
        
        def simulate_user_session() -> Dict[str, Any]:
            """Simulate a typical user session with permission checks."""
            user_id = uuid4()
            session_start = time.time()
            
            # Create user in database
            user = create_test_user(role=UserRole.USER)
            user.user_id = user_id
            test_session.add(user)
            
            # Create permissions
            permission = create_test_permission(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions={"read": True, "create": True, "update": False, "delete": False}
            )
            test_session.add(permission)
            test_session.commit()
            
            # Simulate typical user workflow with asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # User typically checks permissions 5-10 times per session
                check_tasks = []
                for _ in range(5):
                    task = permission_service.check_user_permission(
                        user_id=user_id,
                        agent_name=AgentName.CLIENT_MANAGEMENT,
                        operation="read"
                    )
                    check_tasks.append(task)
                
                results = loop.run_until_complete(asyncio.gather(*check_tasks))
                session_duration = time.time() - session_start
                
                return {
                    "user_id": user_id,
                    "success": all(results),
                    "duration_s": session_duration,
                    "permission_checks": len(results)
                }
            finally:
                loop.close()

        # Run concurrent user sessions using ThreadPoolExecutor
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=min(num_users, 50)) as executor:
            futures = [
                executor.submit(simulate_user_session)
                for _ in range(num_users)
            ]
            
            results = [future.result() for future in futures]
        
        total_duration = time.time() - start_time
        
        # Performance assertions
        successful_sessions = sum(1 for r in results if r["success"])
        avg_session_duration = statistics.mean([r["duration_s"] for r in results])
        max_session_duration = max([r["duration_s"] for r in results])
        
        assert successful_sessions == num_users, (
            f"Only {successful_sessions}/{num_users} sessions succeeded"
        )
        
        assert total_duration < 30, (
            f"Concurrent test with {num_users} users took {total_duration:.2f}s, "
            f"should complete in <30s"
        )
        
        assert avg_session_duration < 5, (
            f"Average user session took {avg_session_duration:.2f}s, should be <5s"
        )
        
        # System throughput validation
        total_permission_checks = sum(r["permission_checks"] for r in results)
        checks_per_second = total_permission_checks / total_duration
        
        assert checks_per_second > 50, (
            f"System processed {checks_per_second:.2f} permission checks/sec, "
            f"should be >50/sec under load"
        )

    # Error Handling Performance Tests

    async def test_error_handling_performance_impact(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test that error handling doesn't significantly impact performance."""
        # Test performance with database errors
        from unittest.mock import patch
        
        durations_normal = []
        durations_with_errors = []
        
        # Measure normal operation performance
        user_id = uuid4()
        user = create_test_user()
        user.user_id = user_id
        test_session.add(user)
        
        permission = create_test_permission(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True}
        )
        test_session.add(permission)
        test_session.commit()
        
        # Normal operations
        for _ in range(10):
            start = time.time()
            result = await fast_permission_service.check_user_permission(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                operation="read"
            )
            durations_normal.append((time.time() - start) * 1000)
            assert result is True
        
        # Operations with database errors
        with patch.object(test_session, "execute", side_effect=DatabaseError("Timeout")):
            for _ in range(10):
                start = time.time()
                try:
                    await fast_permission_service.check_user_permission(
                        user_id=user_id,
                        agent_name=AgentName.CLIENT_MANAGEMENT,
                        operation="read"
                    )
                except DatabaseError:
                    pass  # Expected
                durations_with_errors.append((time.time() - start) * 1000)
        
        avg_normal = statistics.mean(durations_normal)
        avg_with_errors = statistics.mean(durations_with_errors)
        
        # Error handling should not add more than 100% overhead
        assert avg_with_errors < avg_normal * 2, (
            f"Error handling adds too much overhead: normal {avg_normal:.2f}ms, "
            f"with errors {avg_with_errors:.2f}ms"
        )
        
        # Both should still be reasonably fast
        assert avg_normal < 50, f"Normal operations too slow: {avg_normal:.2f}ms"
        assert avg_with_errors < 100, f"Error handling too slow: {avg_with_errors:.2f}ms"

    # Memory Usage and Resource Efficiency Tests

    async def test_memory_usage_under_large_datasets(
        self,
        fast_permission_service: PermissionService,
        mock_redis,
    ) -> None:
        """Test memory efficiency with large permission datasets."""
        import json
        import sys
        
        # Create large dataset simulation
        user_ids = [uuid4() for _ in range(1000)]
        permissions = {"read": True, "create": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)
        
        # Measure memory usage before
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        # Process large number of permission checks
        tasks = []
        for user_id in user_ids:
            for agent in AgentName:
                task = fast_permission_service.check_user_permission(
                    user_id=user_id,
                    agent_name=agent,
                    operation="read"
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Measure memory usage after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        total_checks = len(tasks)
        checks_per_second = total_checks / duration
        
        # Performance assertions
        assert all(results), "All permission checks should succeed"
        assert duration < 10, f"Large dataset processing took {duration:.2f}s, should be <10s"
        assert checks_per_second > 500, (
            f"Throughput {checks_per_second:.2f} checks/sec too low, should be >500/sec"
        )
        
        # Memory efficiency assertions
        assert memory_increase < 100, (
            f"Memory usage increased by {memory_increase:.2f}MB, should be <100MB"
        )
        
        # Check memory doesn't grow linearly with dataset size
        memory_per_check = memory_increase / total_checks
        assert memory_per_check < 0.01, (
            f"Memory per check {memory_per_check:.4f}MB too high, should be <0.01MB"
        )
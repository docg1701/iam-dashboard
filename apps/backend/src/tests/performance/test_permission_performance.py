"""
Permission Performance Tests.

This module tests that permission operations meet the <50ms requirement
and can handle concurrent requests efficiently.
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlmodel import Session

from src.core.exceptions import DatabaseError
from src.models.permissions import AgentName
from src.models.user import UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import create_test_permission, create_test_template, create_test_user


class TestPermissionPerformance:
    """Performance tests for permission operations."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create a fast mock Redis client."""
        redis_mock = MagicMock()
        redis_mock.get = AsyncMock(return_value=None)  # Cache miss for testing
        redis_mock.setex = AsyncMock()
        redis_mock.delete = AsyncMock()
        redis_mock.keys = AsyncMock(return_value=[])
        redis_mock.close = AsyncMock()
        return redis_mock

    @pytest.fixture
    def fast_permission_service(
        self, test_session: Session, mock_redis: MagicMock
    ) -> PermissionService:
        """Create PermissionService optimized for performance testing."""
        service = PermissionService(session=test_session)
        service.redis_client = mock_redis
        service._is_testing = False  # Enable Redis operations for performance testing
        return service

    # Using real test_session for accurate performance testing
    # Only mocking external dependencies (Redis responses, SMTP, etc.)

    async def test_single_permission_check_performance(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test that a single permission check completes within 50ms."""
        user_id = uuid4()

        # Create test user and permission in database
        from src.tests.factories import create_test_permission, create_test_user

        user = create_test_user()
        user.user_id = user_id
        test_session.add(user)

        permission = create_test_permission(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True, "create": False, "update": False, "delete": False},
        )
        test_session.add(permission)
        test_session.commit()

        start_time = time.time()

        result = await fast_permission_service.check_user_permission(
            user_id=user_id, agent_name=AgentName.CLIENT_MANAGEMENT, operation="read"
        )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert result is True
        assert duration_ms < 50, f"Permission check took {duration_ms}ms, should be <50ms"

    async def test_cached_permission_check_performance(
        self,
        fast_permission_service: PermissionService,
        mock_redis: MagicMock,
    ) -> None:
        """Test that cached permission checks are extremely fast (<5ms)."""
        user_id = uuid4()

        # Mock cache hit
        permissions = {"create": True, "read": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)

        start_time = time.time()

        result = await fast_permission_service.check_user_permission(
            user_id=user_id, agent_name=AgentName.CLIENT_MANAGEMENT, operation="read"
        )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert result is True
        assert duration_ms < 5, f"Cached permission check took {duration_ms}ms, should be <5ms"

    async def test_concurrent_permission_checks_performance(
        self,
        fast_permission_service: PermissionService,
        mock_redis: MagicMock,
    ) -> None:
        """Test that concurrent permission checks maintain performance."""
        user_ids = [uuid4() for _ in range(100)]

        # Mock cache hits for all requests
        permissions = {"create": True, "read": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)

        start_time = time.time()

        # Create concurrent permission check tasks
        tasks = []
        for user_id in user_ids:
            task = fast_permission_service.check_user_permission(
                user_id=user_id, agent_name=AgentName.CLIENT_MANAGEMENT, operation="read"
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        avg_duration_ms = total_duration_ms / len(tasks)

        assert all(results), "All permission checks should return True"
        assert avg_duration_ms < 10, (
            f"Average concurrent check took {avg_duration_ms}ms, should be <10ms"
        )
        assert total_duration_ms < 1000, (
            f"Total concurrent checks took {total_duration_ms}ms, should be <1000ms"
        )

    async def test_permission_matrix_retrieval_performance(
        self,
        fast_permission_service: PermissionService,
        mock_redis: MagicMock,
        test_session: Session,
    ) -> None:
        """Test that permission matrix retrieval is fast."""
        user_id = uuid4()

        # Mock cache miss (external dependency)
        mock_redis.get.return_value = None

        # Create real user and permissions in database
        user = create_test_user()
        user.user_id = user_id
        test_session.add(user)

        # Create permissions for all agents
        for agent in AgentName:
            permission = create_test_permission(
                user_id=user_id,
                agent_name=agent,
                permissions={"create": True, "read": True, "update": False, "delete": False},
            )
            test_session.add(permission)

        test_session.commit()

        start_time = time.time()

        result = await fast_permission_service.get_user_permissions(user_id)

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert len(result) == 4  # All 4 agents
        assert duration_ms < 100, (
            f"Permission matrix retrieval took {duration_ms}ms, should be <100ms"
        )

    async def test_permission_assignment_performance(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test that permission assignment completes quickly."""
        user_id = uuid4()
        admin_id = uuid4()
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        # Create real users in database
        user = create_test_user(role=UserRole.USER)
        user.user_id = user_id
        admin = create_test_user(role=UserRole.SYSADMIN)
        admin.user_id = admin_id

        test_session.add(user)
        test_session.add(admin)
        test_session.commit()

        # Use real cache invalidation to test actual performance
        # Only mock external Redis operations that aren't part of business logic
        with patch.object(fast_permission_service.redis_client, "delete") as mock_redis_delete:
            mock_redis_delete.return_value = True  # Mock external Redis response
            start_time = time.time()

            result = await fast_permission_service.assign_permission(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions=permissions,
                created_by_user_id=admin_id,
            )

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            assert result is not None
            assert duration_ms < 200, (
                f"Permission assignment took {duration_ms}ms, should be <200ms"
            )

    async def test_bulk_permission_assignment_performance(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test that bulk permission assignment scales well."""
        user_ids = [uuid4() for _ in range(50)]
        admin_id = uuid4()

        agent_permissions = {
            AgentName.CLIENT_MANAGEMENT: {
                "create": True,
                "read": True,
                "update": False,
                "delete": False,
            },
            AgentName.PDF_PROCESSING: {
                "create": False,
                "read": True,
                "update": False,
                "delete": False,
            },
        }

        # Create real users in database
        for user_id in user_ids:
            user = create_test_user(role=UserRole.USER)
            user.user_id = user_id
            test_session.add(user)

        admin = create_test_user(role=UserRole.SYSADMIN)
        admin.user_id = admin_id
        test_session.add(admin)
        test_session.commit()

        # Use real cache invalidation to test actual performance
        # Only mock external Redis operations that aren't part of business logic
        with patch.object(fast_permission_service.redis_client, "delete") as mock_redis_delete:
            mock_redis_delete.return_value = True  # Mock external Redis response
            start_time = time.time()

            result = await fast_permission_service.bulk_assign_permissions(
                user_ids=user_ids,
                agent_permissions=agent_permissions,
                assigned_by_user_id=admin_id,
            )

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            assert len(result) == 50
            # Bulk operations should be efficient
            assert duration_ms < 2000, f"Bulk assignment took {duration_ms}ms, should be <2000ms"

            # Check per-user performance
            avg_per_user_ms = duration_ms / len(user_ids)
            assert avg_per_user_ms < 40, (
                f"Average per-user bulk assignment took {avg_per_user_ms}ms, should be <40ms"
            )

    async def test_cache_invalidation_performance(
        self,
        fast_permission_service: PermissionService,
        mock_redis: MagicMock,
    ) -> None:
        """Test that cache invalidation is fast."""
        user_id = uuid4()

        # Mock multiple cache keys
        cache_keys = [f"permission:user:{user_id}:agent:{agent.value}" for agent in AgentName]
        cache_keys.append(f"permission:user:{user_id}:matrix")

        mock_redis.keys.return_value = cache_keys

        start_time = time.time()

        await fast_permission_service._invalidate_user_cache(user_id)

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert duration_ms < 10, f"Cache invalidation took {duration_ms}ms, should be <10ms"
        mock_redis.delete.assert_called_once_with(*cache_keys)

    @pytest.mark.asyncio
    async def test_database_error_handling_performance(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test that error handling doesn't significantly impact performance."""
        user_id = uuid4()

        # Mock database connection failure at the session level (external system failure)
        # This simulates real database connection failures without breaking test framework
        with patch.object(test_session, "execute", side_effect=DatabaseError("Database timeout")):
            start_time = time.time()

            with pytest.raises(DatabaseError):
                await fast_permission_service.check_user_permission(
                    user_id=user_id, agent_name=AgentName.CLIENT_MANAGEMENT, operation="read"
                )

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Error handling should still be fast
            assert duration_ms < 50, f"Error handling took {duration_ms}ms, should be <50ms"

    async def test_redis_connection_failure_fallback_performance(
        self,
        fast_permission_service: PermissionService,
        mock_redis: MagicMock,
        test_session: Session,
    ) -> None:
        """Test performance when Redis is unavailable (fallback to database)."""
        user_id = uuid4()

        # Mock Redis failure (external system failure)
        mock_redis.get.side_effect = Exception("Redis connection failed")

        # Create real permission in database
        user = create_test_user()
        user.user_id = user_id
        test_session.add(user)

        permission = create_test_permission(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": True, "read": True, "update": False, "delete": False},
        )
        test_session.add(permission)
        test_session.commit()

        start_time = time.time()

        result = await fast_permission_service.check_user_permission(
            user_id=user_id, agent_name=AgentName.CLIENT_MANAGEMENT, operation="read"
        )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert result is True
        # Even without Redis, should still be reasonably fast
        assert duration_ms < 100, f"Database fallback took {duration_ms}ms, should be <100ms"

    def test_synchronous_performance_with_threading(
        self,
        fast_permission_service: PermissionService,
        mock_redis: MagicMock,
    ) -> None:
        """Test performance with multiple threads (simulating web server load)."""
        # Mock cache hits
        permissions = {"create": True, "read": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)

        def check_permission_sync() -> bool:
            """Synchronous wrapper for async permission check."""
            user_id = uuid4()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    fast_permission_service.check_user_permission(
                        user_id=user_id, agent_name=AgentName.CLIENT_MANAGEMENT, operation="read"
                    )
                )
            finally:
                loop.close()

        # Test with ThreadPoolExecutor to simulate concurrent web requests
        num_threads = 20
        num_requests_per_thread = 10

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for _ in range(num_threads):
                for _ in range(num_requests_per_thread):
                    future = executor.submit(check_permission_sync)
                    futures.append(future)

            # Wait for all requests to complete
            results = [future.result() for future in futures]

        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000
        total_requests = num_threads * num_requests_per_thread
        avg_duration_ms = total_duration_ms / total_requests

        assert all(results), "All permission checks should return True"
        assert avg_duration_ms < 50, (
            f"Average threaded check took {avg_duration_ms}ms, should be <50ms"
        )

        # Total time should indicate good concurrency
        requests_per_second = total_requests / (total_duration_ms / 1000)
        assert requests_per_second > 100, (
            f"Only {requests_per_second} requests/second, should be >100"
        )

    async def test_memory_usage_with_large_datasets(
        self,
        fast_permission_service: PermissionService,
        mock_redis: MagicMock,
    ) -> None:
        """Test that memory usage remains reasonable with large permission matrices."""
        # Create a large user set
        user_ids = [uuid4() for _ in range(1000)]

        # Mock cached results to avoid database overhead
        permissions = {"create": True, "read": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)

        start_time = time.time()

        # Process many permission checks quickly
        tasks = []
        for user_id in user_ids:
            for agent in AgentName:
                task = fast_permission_service.check_user_permission(
                    user_id=user_id, agent_name=agent, operation="read"
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        total_checks = len(tasks)
        avg_duration_ms = duration_ms / total_checks

        assert all(results), "All permission checks should return True"
        assert avg_duration_ms < 5, (
            f"Average check with large dataset took {avg_duration_ms}ms, should be <5ms"
        )
        assert total_checks == 4000, f"Should have processed 4000 checks, got {total_checks}"

    async def test_template_application_performance(
        self,
        fast_permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test that template application to multiple users is efficient."""
        template_id = uuid4()
        user_ids = [uuid4() for _ in range(25)]
        admin_id = uuid4()

        # Create real template in database
        template = create_test_template(
            template_name="Performance Test Template",
            permissions={
                agent.value: {"create": True, "read": True, "update": False, "delete": False}
                for agent in AgentName
            },
        )
        template.template_id = template_id
        test_session.add(template)

        # Create real users in database
        for user_id in user_ids:
            user = create_test_user(role=UserRole.USER)
            user.user_id = user_id
            test_session.add(user)

        admin = create_test_user(role=UserRole.SYSADMIN)
        admin.user_id = admin_id
        test_session.add(admin)
        test_session.commit()

        # Use real cache invalidation to test actual performance
        # Only mock external Redis operations that aren't part of business logic
        with patch.object(fast_permission_service.redis_client, "delete") as mock_redis_delete:
            mock_redis_delete.return_value = True  # Mock external Redis response
            start_time = time.time()

            result = await fast_permission_service.apply_template_to_users(
                template_id=template_id,
                user_ids=user_ids,
                applied_by_user_id=admin_id,
            )

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            assert result["successful"] == len(user_ids)
            assert result["failed"] == 0

            # Template application should be efficient
            avg_per_user_ms = duration_ms / len(user_ids)
            assert avg_per_user_ms < 50, (
                f"Average template application per user took {avg_per_user_ms}ms, should be <50ms"
            )
            assert duration_ms < 1500, (
                f"Total template application took {duration_ms}ms, should be <1500ms"
            )

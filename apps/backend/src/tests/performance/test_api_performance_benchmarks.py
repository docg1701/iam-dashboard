"""
API Performance Benchmark Tests.

This module comprehensively tests all API endpoints to ensure they meet
the <200ms SLA requirement per PRD NFR2. Tests include:

- Authentication API performance (login, 2FA, token refresh)
- Client management API performance (CRUD operations)
- User management API performance
- Permission management API performance
- Error handling performance
- API rate limiting validation

Each test validates against production-level performance requirements.
"""

import asyncio
import statistics
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel import Session

from src.models.user import UserRole
from src.tests.factories import create_test_client, create_test_user


class TestAPIPerformanceBenchmarks:
    """Comprehensive API performance benchmark tests."""

    # Authentication API Performance Tests

    async def test_auth_login_performance_under_200ms(
        self,
        async_client: AsyncClient,
        test_session: Session,
    ) -> None:
        """Test login endpoint meets <200ms SLA."""
        # Create test user
        test_user = create_test_user(
            email="auth.perf.test@example.com",
            role=UserRole.USER,
            is_active=True
        )
        test_session.add(test_user)
        test_session.commit()

        login_payload = {
            "email": "auth.perf.test@example.com",
            "password": "TestPassword123!"
        }

        # Test login performance multiple times for accuracy
        durations = []
        for _ in range(20):
            start_time = time.time()
            
            response = await async_client.post(
                "/api/v1/auth/login",
                json=login_payload
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            # Should either succeed or require 2FA
            assert response.status_code in [200, 422]

        avg_duration = statistics.mean(durations)
        p95_duration = sorted(durations)[int(0.95 * len(durations))]
        max_duration = max(durations)

        assert avg_duration < 200, (
            f"SLA VIOLATION: Login average response time {avg_duration:.2f}ms, "
            f"must be <200ms per PRD NFR2"
        )
        assert p95_duration < 300, (
            f"Login 95th percentile {p95_duration:.2f}ms should be <300ms"
        )
        assert max_duration < 500, (
            f"Login max response time {max_duration:.2f}ms should be <500ms"
        )

    async def test_auth_token_refresh_performance(
        self,
        async_client: AsyncClient,
        authenticated_user,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test token refresh endpoint performance."""
        durations = []
        
        for _ in range(15):
            start_time = time.time()
            
            response = await async_client.post(
                "/api/v1/auth/refresh",
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)

        avg_duration = statistics.mean(durations)
        
        assert avg_duration < 100, (
            f"Token refresh too slow: {avg_duration:.2f}ms, should be <100ms"
        )

    async def test_auth_logout_performance(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test logout endpoint performance."""
        durations = []
        
        for _ in range(10):
            start_time = time.time()
            
            response = await async_client.post(
                "/api/v1/auth/logout",
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)

        avg_duration = statistics.mean(durations)
        
        assert avg_duration < 150, (
            f"Logout too slow: {avg_duration:.2f}ms, should be <150ms"
        )

    # Client Management API Performance Tests

    async def test_client_list_performance_under_200ms(
        self,
        async_client: AsyncClient,
        test_session: Session,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test client listing performance with various dataset sizes."""
        # Create different sized datasets
        dataset_sizes = [10, 50, 100]
        
        for size in dataset_sizes:
            # Clean up and create fresh dataset
            test_session.query("DELETE FROM clients")
            test_session.commit()
            
            # Create test clients
            for i in range(size):
                client = create_test_client(
                    name=f"Performance Client {i}",
                    ssn=f"1234567890{i:02d}"
                )
                test_session.add(client)
            test_session.commit()

            durations = []
            
            for _ in range(10):
                start_time = time.time()
                
                response = await async_client.get(
                    "/api/v1/clients",
                    headers=authenticated_headers
                )
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                durations.append(duration_ms)
                
                assert response.status_code == 200

            avg_duration = statistics.mean(durations)
            
            assert avg_duration < 200, (
                f"SLA VIOLATION: Client list with {size} items took "
                f"{avg_duration:.2f}ms, must be <200ms"
            )

    async def test_client_create_performance_under_200ms(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test client creation performance."""
        durations = []
        
        for i in range(15):
            client_data = {
                "name": f"Performance Test Client {i}",
                "ssn": f"9876543210{i:02d}",
                "birth_date": "1990-01-01"
            }
            
            start_time = time.time()
            
            response = await async_client.post(
                "/api/v1/clients",
                json=client_data,
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 201

        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        
        assert avg_duration < 200, (
            f"SLA VIOLATION: Client creation average {avg_duration:.2f}ms, "
            f"must be <200ms per PRD NFR2"
        )
        assert max_duration < 500, (
            f"Client creation max {max_duration:.2f}ms should be <500ms"
        )

    async def test_client_get_performance_under_50ms(
        self,
        async_client: AsyncClient,
        test_session: Session,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test individual client retrieval performance."""
        # Create a test client
        client = create_test_client(
            name="Performance Retrieval Test Client",
            ssn="5555555555"
        )
        test_session.add(client)
        test_session.commit()

        durations = []
        
        for _ in range(25):
            start_time = time.time()
            
            response = await async_client.get(
                f"/api/v1/clients/{client.client_id}",
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 200

        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        
        # Individual client retrieval should be very fast
        assert avg_duration < 50, (
            f"Client retrieval too slow: {avg_duration:.2f}ms, should be <50ms"
        )
        assert max_duration < 100, (
            f"Client retrieval max {max_duration:.2f}ms should be <100ms"
        )

    async def test_client_update_performance_under_200ms(
        self,
        async_client: AsyncClient,
        test_session: Session,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test client update performance."""
        # Create test client
        client = create_test_client(
            name="Update Performance Test Client",
            ssn="4444444444"
        )
        test_session.add(client)
        test_session.commit()

        durations = []
        
        for i in range(10):
            update_data = {
                "name": f"Updated Performance Client {i}",
                "birth_date": "1991-02-02"
            }
            
            start_time = time.time()
            
            response = await async_client.put(
                f"/api/v1/clients/{client.client_id}",
                json=update_data,
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 200

        avg_duration = statistics.mean(durations)
        
        assert avg_duration < 200, (
            f"Client update too slow: {avg_duration:.2f}ms, should be <200ms"
        )

    # User Management API Performance Tests

    async def test_user_list_performance_under_200ms(
        self,
        async_client: AsyncClient,
        test_session: Session,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test user listing performance."""
        # Create multiple test users
        for i in range(50):
            user = create_test_user(
                email=f"perf.user.{i}@example.com",
                role=UserRole.USER
            )
            test_session.add(user)
        test_session.commit()

        durations = []
        
        for _ in range(10):
            start_time = time.time()
            
            response = await async_client.get(
                "/api/v1/users",
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 200

        avg_duration = statistics.mean(durations)
        
        assert avg_duration < 200, (
            f"User list performance: {avg_duration:.2f}ms, should be <200ms"
        )

    async def test_user_create_performance_under_200ms(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test user creation performance."""
        durations = []
        
        for i in range(10):
            user_data = {
                "email": f"new.perf.user.{i}@example.com",
                "password": "TestPassword123!",
                "role": "user",
                "is_active": True
            }
            
            start_time = time.time()
            
            response = await async_client.post(
                "/api/v1/users",
                json=user_data,
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 201

        avg_duration = statistics.mean(durations)
        
        assert avg_duration < 200, (
            f"User creation performance: {avg_duration:.2f}ms, should be <200ms"
        )

    # Permission API Performance Tests

    async def test_permission_list_performance_under_100ms(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test permission listing performance."""
        durations = []
        
        for _ in range(15):
            start_time = time.time()
            
            response = await async_client.get(
                "/api/v1/permissions/templates",
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)

        avg_duration = statistics.mean(durations)
        
        assert avg_duration < 100, (
            f"Permission list performance: {avg_duration:.2f}ms, should be <100ms"
        )

    # Concurrent API Request Tests

    async def test_concurrent_api_requests_performance(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test API performance under concurrent load."""
        
        async def make_request(endpoint: str) -> float:
            """Make a single API request and return duration."""
            start_time = time.time()
            response = await async_client.get(endpoint, headers=authenticated_headers)
            duration = (time.time() - start_time) * 1000
            assert response.status_code in [200, 404]  # 404 acceptable for some endpoints
            return duration

        # Define endpoint groups for concurrent testing
        endpoints = [
            "/api/v1/clients",
            "/api/v1/users", 
            "/api/v1/permissions/templates",
        ] * 10  # 30 total concurrent requests

        start_time = time.time()
        
        # Execute all requests concurrently
        durations = await asyncio.gather(
            *[make_request(endpoint) for endpoint in endpoints]
        )
        
        total_time = (time.time() - start_time) * 1000
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        
        # Performance assertions for concurrent load
        assert avg_duration < 300, (
            f"Concurrent API average {avg_duration:.2f}ms too high under load"
        )
        assert max_duration < 1000, (
            f"Concurrent API max {max_duration:.2f}ms too high under load"
        )
        assert total_time < 5000, (
            f"30 concurrent requests took {total_time:.2f}ms, should be <5000ms"
        )

    # Error Response Performance Tests

    async def test_404_error_response_performance(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test that 404 errors are returned quickly."""
        durations = []
        
        for _ in range(20):
            start_time = time.time()
            
            response = await async_client.get(
                f"/api/v1/clients/{uuid4()}",  # Non-existent client
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 404

        avg_duration = statistics.mean(durations)
        
        # Error responses should be very fast
        assert avg_duration < 50, (
            f"404 error responses too slow: {avg_duration:.2f}ms, should be <50ms"
        )

    async def test_validation_error_response_performance(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test validation error response performance."""
        durations = []
        
        invalid_client_data = {
            "name": "",  # Invalid: empty name
            "ssn": "invalid",  # Invalid: wrong format
            "birth_date": "not-a-date"  # Invalid: wrong format
        }
        
        for _ in range(15):
            start_time = time.time()
            
            response = await async_client.post(
                "/api/v1/clients",
                json=invalid_client_data,
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 422

        avg_duration = statistics.mean(durations)
        
        # Validation errors should be fast
        assert avg_duration < 100, (
            f"Validation error responses too slow: {avg_duration:.2f}ms, should be <100ms"
        )

    # API Rate Limiting Performance Tests

    async def test_rate_limiting_does_not_impact_normal_performance(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test that rate limiting doesn't impact normal request performance."""
        # Make requests at normal frequency (not hitting rate limits)
        durations = []
        
        for _ in range(10):
            start_time = time.time()
            
            response = await async_client.get(
                "/api/v1/clients",
                headers=authenticated_headers
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)
            
            assert response.status_code == 200
            
            # Small delay to avoid hitting rate limits
            await asyncio.sleep(0.1)

        avg_duration = statistics.mean(durations)
        
        # Rate limiting middleware should not significantly impact performance
        assert avg_duration < 250, (
            f"Rate limiting impacting performance: {avg_duration:.2f}ms, should be <250ms"
        )

    # Pagination Performance Tests

    async def test_paginated_results_performance(
        self,
        async_client: AsyncClient,
        test_session: Session,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Test pagination performance with large datasets."""
        # Create a large dataset
        for i in range(200):
            client = create_test_client(
                name=f"Pagination Test Client {i}",
                ssn=f"8888{i:06d}"
            )
            test_session.add(client)
        test_session.commit()

        # Test different page sizes
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            durations = []
            
            # Test first, middle, and last pages
            pages_to_test = [1, 5, 200 // page_size]
            
            for page in pages_to_test:
                start_time = time.time()
                
                response = await async_client.get(
                    f"/api/v1/clients?page={page}&size={page_size}",
                    headers=authenticated_headers
                )
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                durations.append(duration_ms)
                
                assert response.status_code == 200

            avg_duration = statistics.mean(durations)
            
            # Pagination should not significantly impact performance
            assert avg_duration < 300, (
                f"Pagination with page_size={page_size} too slow: "
                f"{avg_duration:.2f}ms, should be <300ms"
            )

    # Performance Summary and Reporting

    async def test_api_performance_summary_report(
        self,
        async_client: AsyncClient,
        authenticated_headers: Dict[str, str],
    ) -> None:
        """Generate a comprehensive API performance summary."""
        
        performance_results = {}
        
        # Test key endpoints and collect metrics
        endpoints_to_test = [
            {"url": "/api/v1/clients", "method": "GET", "name": "List Clients"},
            {"url": "/api/v1/users", "method": "GET", "name": "List Users"},
            {"url": "/api/v1/permissions/templates", "method": "GET", "name": "List Permission Templates"},
        ]
        
        for endpoint in endpoints_to_test:
            durations = []
            
            for _ in range(10):
                start_time = time.time()
                
                if endpoint["method"] == "GET":
                    response = await async_client.get(
                        endpoint["url"],
                        headers=authenticated_headers
                    )
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                durations.append(duration_ms)

            performance_results[endpoint["name"]] = {
                "average_ms": statistics.mean(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "p95_ms": sorted(durations)[int(0.95 * len(durations))],
                "sla_compliance": statistics.mean(durations) < 200
            }

        # Validate overall API performance
        all_compliant = all(result["sla_compliance"] for result in performance_results.values())
        avg_response_time = statistics.mean([result["average_ms"] for result in performance_results.values()])
        
        # Log performance summary for analysis
        print("\n=== API Performance Summary ===")
        for name, metrics in performance_results.items():
            print(f"{name}:")
            print(f"  Average: {metrics['average_ms']:.2f}ms")
            print(f"  P95: {metrics['p95_ms']:.2f}ms")
            print(f"  Max: {metrics['max_ms']:.2f}ms")
            print(f"  SLA Compliant: {metrics['sla_compliance']}")
        
        print(f"\nOverall Average Response Time: {avg_response_time:.2f}ms")
        print(f"Overall SLA Compliance: {all_compliant}")
        
        # Performance assertions
        assert all_compliant, "Some API endpoints failed to meet 200ms SLA requirement"
        assert avg_response_time < 150, (
            f"Overall API performance {avg_response_time:.2f}ms should be <150ms average"
        )
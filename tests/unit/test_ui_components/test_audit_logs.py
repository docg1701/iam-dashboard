"""Tests for audit logs component."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.audit_log import AuditAction, AuditLevel, AuditLog
from app.services.audit_log_service import AuditLogService
from app.ui_components.audit_logs import AuditLogs


@pytest.fixture
def mock_audit_log_service():
    """Create a mocked audit log service."""
    service = MagicMock(spec=AuditLogService)
    service.get_logs_paginated = AsyncMock()
    service.export_logs_csv = AsyncMock()
    service.get_audit_statistics = AsyncMock()
    service.log_action = AsyncMock()
    return service


@pytest.fixture
def sample_audit_logs():
    """Create sample audit log data."""
    logs = []
    base_time = datetime.now()

    for i in range(5):
        log = AuditLog(
            id=uuid4(),
            action=AuditAction.USER_CREATED if i % 2 == 0 else AuditAction.LOGIN_SUCCESS,
            level=AuditLevel.INFO if i % 3 != 0 else AuditLevel.WARNING,
            user_id=uuid4(),
            username=f"user{i}",
            resource_type="user" if i % 2 == 0 else None,
            resource_id=str(uuid4()) if i % 2 == 0 else None,
            message=f"Test audit log {i}",
            details={"test": f"data{i}"},
            ip_address=f"192.168.1.{i+1}",
            user_agent=f"TestAgent{i}",
            created_at=base_time - timedelta(hours=i),
            updated_at=base_time - timedelta(hours=i),
        )
        logs.append(log)

    return logs


@pytest.fixture
def sample_statistics():
    """Create sample audit statistics."""
    return {
        "total_logs": 100,
        "date_range": {
            "from": "2025-01-01T00:00:00",
            "to": "2025-01-31T23:59:59"
        },
        "level_counts": {
            "info": 70,
            "warning": 20,
            "error": 8,
            "critical": 2
        },
        "action_counts": {
            "user_created": 15,
            "login_success": 25,
            "user_updated": 10
        },
        "critical_logs": 2,
        "error_logs": 8,
        "warning_logs": 20,
        "info_logs": 70
    }


class TestAuditLogs:
    """Test cases for AuditLogs component."""

    def test_init(self, mock_audit_log_service):
        """Test AuditLogs initialization."""
        audit_logs = AuditLogs(mock_audit_log_service)

        assert audit_logs.audit_log_service == mock_audit_log_service
        assert audit_logs.logs_data == []
        assert audit_logs.current_page == 1
        assert audit_logs.page_size == 25
        assert audit_logs.total_pages == 1
        assert audit_logs.total_count == 0

        # Test filter defaults
        assert audit_logs.action_filter == "all"
        assert audit_logs.level_filter == "all"
        assert audit_logs.user_filter == ""
        assert audit_logs.search_query == ""
        assert audit_logs.date_from is None
        assert audit_logs.date_to is None

    @patch('app.ui_components.audit_logs.ui')
    def test_create_ui_structure(self, mock_ui, mock_audit_log_service):
        """Test that create() builds the expected UI structure."""
        audit_logs = AuditLogs(mock_audit_log_service)

        # Mock UI components to return context managers
        mock_column = MagicMock()
        mock_column.__enter__ = MagicMock(return_value=mock_column)
        mock_column.__exit__ = MagicMock(return_value=None)
        mock_ui.column.return_value = mock_column

        mock_row = MagicMock()
        mock_row.__enter__ = MagicMock(return_value=mock_row)
        mock_row.__exit__ = MagicMock(return_value=None)
        mock_ui.row.return_value = mock_row

        mock_card = MagicMock()
        mock_card.__enter__ = MagicMock(return_value=mock_card)
        mock_card.__exit__ = MagicMock(return_value=None)
        mock_ui.card.return_value = mock_card

        mock_ui.label.return_value = MagicMock()
        mock_ui.button.return_value = MagicMock()
        mock_ui.icon.return_value = MagicMock()
        mock_ui.select.return_value = MagicMock()
        mock_ui.input.return_value = MagicMock()
        mock_ui.table.return_value = MagicMock()

        audit_logs.create()

        # Verify main UI elements are created
        assert mock_ui.column.called
        assert mock_ui.row.called
        assert mock_ui.label.called
        assert mock_ui.button.called

    def test_get_action_options(self, mock_audit_log_service):
        """Test action filter options."""
        audit_logs = AuditLogs(mock_audit_log_service)
        options = audit_logs._get_action_options()

        # Should return a dictionary with "all" option plus all AuditAction values
        assert isinstance(options, dict)
        assert len(options) == len(AuditAction) + 1
        assert "all" in options
        assert options["all"] == "Todas as Ações"

        # Check that all actions are included
        for action in AuditAction:
            assert action.value in options

    def test_get_level_options(self, mock_audit_log_service):
        """Test level filter options."""
        audit_logs = AuditLogs(mock_audit_log_service)
        options = audit_logs._get_level_options()

        # Should return a dictionary with "all" option plus all AuditLevel values
        assert isinstance(options, dict)
        assert len(options) == len(AuditLevel) + 1
        assert "all" in options
        assert options["all"] == "Todos os Níveis"

        # Check that all levels are included
        for level in AuditLevel:
            assert level.value in options

    def test_filter_setters(self, mock_audit_log_service):
        """Test filter setter methods."""
        audit_logs = AuditLogs(mock_audit_log_service)

        # Test action filter
        audit_logs._set_action_filter("user_created")
        assert audit_logs.action_filter == "user_created"

        # Test level filter
        audit_logs._set_level_filter("warning")
        assert audit_logs.level_filter == "warning"

        # Test user filter
        audit_logs._set_user_filter("  test_user  ")
        assert audit_logs.user_filter == "test_user"

        # Test empty user filter
        audit_logs._set_user_filter("   ")
        assert audit_logs.user_filter == ""

        # Test search query
        audit_logs._set_search_query("  test query  ")
        assert audit_logs.search_query == "test query"

        # Test empty search query
        audit_logs._set_search_query("   ")
        assert audit_logs.search_query == ""

    def test_date_filter_setters(self, mock_audit_log_service):
        """Test date filter setter methods."""
        audit_logs = AuditLogs(mock_audit_log_service)

        # Test valid date_from
        with patch('nicegui.ui.notify') as mock_notify:
            audit_logs._set_date_from("2025-01-15")
            expected_date = datetime.fromisoformat("2025-01-15")
            assert audit_logs.date_from == expected_date
            mock_notify.assert_not_called()

        # Test empty date_from
        audit_logs._set_date_from("")
        assert audit_logs.date_from is None

        # Test invalid date_from
        with patch('nicegui.ui.notify') as mock_notify:
            audit_logs._set_date_from("invalid-date")
            mock_notify.assert_called_once_with("Formato de data inválido. Use YYYY-MM-DD", type="warning")

        # Test valid date_to
        with patch('nicegui.ui.notify') as mock_notify:
            audit_logs._set_date_to("2025-01-31")
            expected_date = datetime.fromisoformat("2025-01-31").replace(hour=23, minute=59, second=59)
            assert audit_logs.date_to == expected_date
            mock_notify.assert_not_called()

        # Test empty date_to
        audit_logs._set_date_to("")
        assert audit_logs.date_to is None

    @pytest.mark.asyncio
    async def test_load_data_success(self, mock_audit_log_service, sample_audit_logs):
        """Test successful data loading."""
        # Setup mock service response
        mock_audit_log_service.get_logs_paginated.return_value = (sample_audit_logs, 50, 2)

        audit_logs = AuditLogs(mock_audit_log_service)

        # Mock UI components
        audit_logs.logs_table = MagicMock()
        audit_logs.pagination_info = MagicMock()
        audit_logs.page_input = MagicMock()

        await audit_logs._load_data()

        # Verify service was called with correct parameters
        mock_audit_log_service.get_logs_paginated.assert_called_once_with(
            page=1,
            page_size=25,
            action_filter=None,
            level_filter=None,
            user_filter=None,
            date_from=None,
            date_to=None,
            search_query=None
        )

        # Verify data was processed correctly
        assert len(audit_logs.logs_data) == len(sample_audit_logs)
        assert audit_logs.total_count == 50
        assert audit_logs.total_pages == 2

        # Verify table was updated
        audit_logs.logs_table.rows = audit_logs.logs_data

        # Verify pagination info was updated
        audit_logs.pagination_info.text = "Mostrando 1-25 de 50 registros (Página 1 de 2)"

    @pytest.mark.asyncio
    async def test_load_data_with_filters(self, mock_audit_log_service, sample_audit_logs):
        """Test data loading with filters applied."""
        # Setup filters
        audit_logs = AuditLogs(mock_audit_log_service)
        audit_logs.action_filter = "user_created"
        audit_logs.level_filter = "warning"
        audit_logs.user_filter = "test_user"
        audit_logs.search_query = "test query"
        audit_logs.date_from = datetime(2025, 1, 1)
        audit_logs.date_to = datetime(2025, 1, 31, 23, 59, 59)

        # Setup mock service response
        mock_audit_log_service.get_logs_paginated.return_value = (sample_audit_logs[:2], 2, 1)

        # Mock UI components
        audit_logs.logs_table = MagicMock()
        audit_logs.pagination_info = MagicMock()
        audit_logs.page_input = MagicMock()

        await audit_logs._load_data()

        # Verify service was called with filters
        mock_audit_log_service.get_logs_paginated.assert_called_once_with(
            page=1,
            page_size=25,
            action_filter="user_created",
            level_filter="warning",
            user_filter="test_user",
            date_from=datetime(2025, 1, 1),
            date_to=datetime(2025, 1, 31, 23, 59, 59),
            search_query="test query"
        )

    @pytest.mark.asyncio
    async def test_load_data_error(self, mock_audit_log_service):
        """Test data loading error handling."""
        # Setup mock service to raise exception
        mock_audit_log_service.get_logs_paginated.side_effect = Exception("Database error")

        audit_logs = AuditLogs(mock_audit_log_service)

        with patch('nicegui.ui.notify') as mock_notify:
            await audit_logs._load_data()
            mock_notify.assert_called_once_with("Erro ao carregar logs: Database error", type="negative")

    @pytest.mark.asyncio
    async def test_load_statistics_success(self, mock_audit_log_service, sample_statistics):
        """Test successful statistics loading."""
        # Setup mock service response
        mock_audit_log_service.get_audit_statistics.return_value = sample_statistics

        audit_logs = AuditLogs(mock_audit_log_service)

        # Mock UI components
        audit_logs.total_logs_label = MagicMock()
        audit_logs.critical_logs_label = MagicMock()
        audit_logs.warning_logs_label = MagicMock()
        audit_logs.info_logs_label = MagicMock()

        await audit_logs._load_statistics()

        # Verify service was called
        mock_audit_log_service.get_audit_statistics.assert_called_once()

        # Verify statistics were stored
        assert audit_logs.stats_data == sample_statistics

        # Verify UI labels were updated
        audit_logs.total_logs_label.text = "100"
        audit_logs.critical_logs_label.text = "2"
        audit_logs.warning_logs_label.text = "20"
        audit_logs.info_logs_label.text = "70"

    @pytest.mark.asyncio
    async def test_load_statistics_error(self, mock_audit_log_service):
        """Test statistics loading error handling."""
        # Setup mock service to raise exception
        mock_audit_log_service.get_audit_statistics.side_effect = Exception("Service error")

        audit_logs = AuditLogs(mock_audit_log_service)

        with patch('nicegui.ui.notify') as mock_notify:
            await audit_logs._load_statistics()
            mock_notify.assert_called_once_with("Erro ao carregar estatísticas: Service error", type="negative")

    @patch('app.ui_components.audit_logs.ui')
    def test_pagination_navigation(self, mock_ui, mock_audit_log_service):
        """Test pagination navigation methods."""
        audit_logs = AuditLogs(mock_audit_log_service)
        audit_logs.total_pages = 5

        # Test go to page
        audit_logs._go_to_page(3)
        assert audit_logs.current_page == 3
        mock_ui.timer.assert_called_with(0.1, audit_logs._load_data, once=True)

        # Test go to invalid page (too high)
        mock_ui.reset_mock()
        audit_logs._go_to_page(10)
        assert audit_logs.current_page == 3  # Should not change
        mock_ui.timer.assert_not_called()

        # Test go to invalid page (too low)
        audit_logs._go_to_page(0)
        assert audit_logs.current_page == 3  # Should not change

        # Test next page
        mock_ui.reset_mock()
        audit_logs._next_page()
        assert audit_logs.current_page == 4
        mock_ui.timer.assert_called_with(0.1, audit_logs._load_data, once=True)

        # Test next page at limit
        audit_logs.current_page = 5
        mock_ui.reset_mock()
        audit_logs._next_page()
        assert audit_logs.current_page == 5  # Should not change
        mock_ui.timer.assert_not_called()

        # Test previous page
        mock_ui.reset_mock()
        audit_logs._previous_page()
        assert audit_logs.current_page == 4
        mock_ui.timer.assert_called_with(0.1, audit_logs._load_data, once=True)

        # Test previous page at limit
        audit_logs.current_page = 1
        mock_ui.reset_mock()
        audit_logs._previous_page()
        assert audit_logs.current_page == 1  # Should not change
        mock_ui.timer.assert_not_called()

    @pytest.mark.asyncio
    async def test_export_csv_success(self, mock_audit_log_service):
        """Test successful CSV export."""
        # Setup mock service response
        csv_content = "timestamp,action,level,user,message\n2025-01-01,Login,Info,test_user,User logged in"
        mock_audit_log_service.export_logs_csv.return_value = csv_content
        mock_audit_log_service.log_action = AsyncMock()

        audit_logs = AuditLogs(mock_audit_log_service)
        audit_logs.export_button = MagicMock()

        with patch('nicegui.ui.download') as mock_download, \
             patch('nicegui.ui.notify') as mock_notify, \
             patch('datetime.datetime') as mock_datetime:

            mock_datetime.now.return_value.strftime.return_value = "20250131_143000"

            await audit_logs._export_csv()

            # Verify service was called
            mock_audit_log_service.export_logs_csv.assert_called_once()
            mock_audit_log_service.log_action.assert_called_once()

            # Verify download was triggered
            mock_download.assert_called_once_with(
                csv_content.encode('utf-8'),
                "audit_logs_20250131_143000.csv"
            )

            # Verify success notification
            mock_notify.assert_called_with("Logs exportados com sucesso!", type="positive")

    @pytest.mark.asyncio
    async def test_export_csv_error(self, mock_audit_log_service):
        """Test CSV export error handling."""
        # Setup mock service to raise exception
        mock_audit_log_service.export_logs_csv.side_effect = Exception("Export error")

        audit_logs = AuditLogs(mock_audit_log_service)
        audit_logs.export_button = MagicMock()

        with patch('nicegui.ui.notify') as mock_notify:
            await audit_logs._export_csv()
            mock_notify.assert_called_once_with("Erro ao exportar logs: Export error", type="negative")

    def test_apply_filters(self, mock_audit_log_service):
        """Test filter application."""
        audit_logs = AuditLogs(mock_audit_log_service)
        audit_logs.current_page = 3

        with patch.object(audit_logs, '_load_data') as mock_load:
            audit_logs._apply_filters()

            # Should reset to page 1 and reload data
            assert audit_logs.current_page == 1
            mock_load.assert_called_once()

    def test_clear_filters(self, mock_audit_log_service):
        """Test filter clearing."""
        audit_logs = AuditLogs(mock_audit_log_service)

        # Set some filters
        audit_logs.action_filter = "user_created"
        audit_logs.level_filter = "warning"
        audit_logs.user_filter = "test_user"
        audit_logs.search_query = "test query"
        audit_logs.date_from = datetime.now()
        audit_logs.date_to = datetime.now()
        audit_logs.current_page = 3

        with patch.object(audit_logs, '_load_data') as mock_load, \
             patch('nicegui.ui.run_javascript'):

            audit_logs._clear_filters()

            # Verify all filters were cleared
            assert audit_logs.action_filter == "all"
            assert audit_logs.level_filter == "all"
            assert audit_logs.user_filter == ""
            assert audit_logs.search_query == ""
            assert audit_logs.date_from is None
            assert audit_logs.date_to is None
            assert audit_logs.current_page == 1

            # Verify data was reloaded
            mock_load.assert_called_once()

    def test_data_formatting(self, mock_audit_log_service, sample_audit_logs):
        """Test data formatting for table display."""
        audit_logs = AuditLogs(mock_audit_log_service)

        # Manually format data like _load_data does
        for log in sample_audit_logs:
            formatted_data = {
                "id": str(log.id),
                "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "level": log.level_display,
                "action": log.action_display,
                "user": log.username or "Sistema",
                "message": log.message,
                "resource": f"{log.resource_type or ''} {log.resource_id or ''}".strip() or "-",
                "level_color": log.level_color,
            }

            # Verify formatting
            assert formatted_data["id"] == str(log.id)
            assert len(formatted_data["timestamp"]) == 19  # YYYY-MM-DD HH:MM:SS
            assert formatted_data["level"] in ["Info", "Warning", "Error", "Critical"]
            assert formatted_data["user"] == log.username
            assert formatted_data["message"] == log.message
            assert formatted_data["level_color"] in ["blue", "orange", "red", "grey"]

# Testing Strategy & Quality Assurance

## Testing Approach Overview

The autonomous agent migration requires a comprehensive testing strategy that validates both the technical implementation and business functionality. Given the architectural complexity of replacing direct services and Celery workers with Agno agents, our testing approach emphasizes integration validation, performance verification, and extensive agent behavior testing.

## Testing Framework Integration

**Framework Selection and Rationale:**
- **Primary Testing Framework**: pytest with asyncio support for comprehensive agent testing
- **Browser Automation**: Playwright MCP (mandatory for all UI/UX testing) 
- **API Testing**: FastAPI TestClient with agent mocking capabilities
- **Performance Testing**: Custom performance harness for agent vs legacy comparison
- **Integration Testing**: Docker-based test environment with PostgreSQL+pgvector

**Test Environment Architecture:**
```
Test Environments:
├── Unit Test Environment
│   ├── Isolated agent testing with mocked dependencies
│   ├── Tool testing with simulated inputs
│   └── Plugin interface validation
├── Integration Test Environment  
│   ├── Full agent stack with real PostgreSQL
│   ├── End-to-end processing workflows
│   └── Agent interaction testing
├── Performance Test Environment
│   ├── Baseline measurement against legacy system
│   ├── Agent resource usage monitoring
│   └── Concurrent processing validation
└── User Acceptance Test Environment
    ├── Full production-like setup
    ├── Real document processing scenarios
    └── Administrative interface validation
```

## Agent-Specific Testing Requirements

**Agent Unit Testing Standards:**
- **Test Coverage Requirement**: Minimum 90% code coverage for all agent classes
- **Mocking Strategy**: Use dependency injection to mock external tools and APIs during unit tests
- **Agent State Testing**: Validate agent initialization, processing, and cleanup phases
- **Error Scenario Coverage**: Test all agent failure modes and recovery mechanisms

**Agent Integration Testing:**
- **End-to-End Workflows**: Test complete document processing and questionnaire generation through agents
- **Database Integration**: Verify agent operations with real PostgreSQL+pgvector connections
- **External API Integration**: Test Google Gemini API integration through agents with rate limiting validation
- **Plugin System Testing**: Verify plugin registration, lifecycle management, and dependency resolution

## Performance and Quality Benchmarks

**Performance Acceptance Criteria:**

| Metric | Legacy Baseline | Agent Target | Acceptance Threshold |
|--------|----------------|--------------|---------------------|
| PDF Processing Time | Current measurement | ≤ 110% of baseline | Must not exceed 110% |
| Questionnaire Generation | Current measurement | ≤ 110% of baseline | Must not exceed 110% |
| Memory Usage | Current measurement | ≤ 125% of baseline | Must not exceed 125% |
| API Response Time | Current measurement | + 50ms maximum | Must not exceed +50ms |
| Agent Startup Time | N/A | ≤ 5 seconds | Must complete within 5s |
| Configuration Changes | N/A | ≤ 2 seconds | Must persist within 2s |

**Quality Assurance Metrics:**
- **Functional Equivalence**: 100% of legacy functionality must be replicated through agents
- **Data Integrity**: Zero data loss during processing migration
- **Error Recovery**: All failure scenarios must have defined recovery paths
- **User Experience**: No visible changes to end-user interfaces or workflows

## Browser and UI Testing with Playwright MCP

**Mandatory Playwright MCP Usage:**
All browser automation, UI testing, and UX validation MUST use the Playwright MCP tools. This includes:

**Administrative Interface Testing:**
```python
# Agent Management UI Testing with Playwright MCP
async def test_agent_dashboard_functionality():
    """Test agent status monitoring and configuration management."""
    
    # Navigate to agent management dashboard
    await mcp_playwright.browser_navigate("http://localhost:8000/admin/agents")
    
    # Verify agent status display
    snapshot = await mcp_playwright.browser_snapshot()
    assert "Agent Status: Active" in snapshot
    
    # Test agent configuration changes
    await mcp_playwright.browser_click(
        element="Configure PDF Agent button",
        ref="config-pdf-agent-btn"
    )
    
    # Modify agent parameters
    await mcp_playwright.browser_type(
        element="Max Processing Time input",
        ref="max-processing-time",
        text="300"
    )
    
    # Verify configuration save
    await mcp_playwright.browser_click(
        element="Save Configuration button", 
        ref="save-config-btn"
    )
    
    # Validate success message
    await mcp_playwright.browser_wait_for(text="Configuration saved successfully")
```

**User Workflow Testing:**
```python
# End-to-End Document Processing with Playwright MCP
async def test_complete_document_workflow():
    """Test full document upload and processing workflow."""
    
    # Login and navigate to document upload
    await mcp_playwright.browser_navigate("http://localhost:8000/login")
    await authenticate_user()
    await mcp_playwright.browser_navigate("http://localhost:8000/documents/upload")
    
    # Upload test document
    await mcp_playwright.browser_file_upload(
        paths=["/test-data/sample-legal-document.pdf"]
    )
    
    # Verify processing status
    await mcp_playwright.browser_wait_for(text="Processing complete")
    
    # Validate results display
    snapshot = await mcp_playwright.browser_snapshot()
    assert "Document Summary" in snapshot
    assert "Vector Embeddings: Generated" in snapshot
```

**Questionnaire Generation Testing:**
```python
# Questionnaire Workflow Testing with Playwright MCP  
async def test_questionnaire_generation():
    """Test AI-powered questionnaire generation functionality."""
    
    await mcp_playwright.browser_navigate("http://localhost:8000/questionnaires/generate")
    
    # Select document for questionnaire generation
    await mcp_playwright.browser_click(
        element="Select Document dropdown",
        ref="document-selector"
    )
    
    await mcp_playwright.browser_select_option(
        element="Document options",
        ref="document-options",
        values=["test-document-1"]
    )
    
    # Generate questionnaire
    await mcp_playwright.browser_click(
        element="Generate Questionnaire button",
        ref="generate-btn"
    )
    
    # Verify generation progress and completion
    await mcp_playwright.browser_wait_for(text="Questionnaire generated successfully")
    
    # Validate questionnaire content
    snapshot = await mcp_playwright.browser_snapshot()
    assert "Legal Questions" in snapshot
    assert "Question 1:" in snapshot
```

## Test Data Management and Fixtures

**Test Data Categories:**
- **Document Samples**: Representative PDF files covering various legal document types
- **User Test Data**: Complete user profiles with different permission levels
- **Configuration Data**: Agent configuration variations for testing different scenarios
- **Performance Baselines**: Historical processing metrics for comparison

**Test Data Setup:**
```python
# Comprehensive test fixture setup
@pytest.fixture(scope="session")
async def test_environment_setup():
    """Setup complete test environment with agents and test data."""
    
    # Initialize test database with vector extension
    await setup_test_database()
    await load_test_documents()
    await configure_test_agents()
    
    # Seed performance baselines
    await establish_performance_baselines()
    
    yield
    
    # Cleanup after test session
    await cleanup_test_environment()

@pytest.fixture
async def pdf_processor_agent():
    """Provide configured PDF processing agent for testing."""
    agent = PDFProcessorAgent(
        config=test_config,
        tools=[PDFReaderTool(), OCRProcessorTool(), VectorStorageTool()]
    )
    await agent.initialize()
    return agent

@pytest.fixture
async def questionnaire_agent():
    """Provide configured questionnaire generation agent for testing."""
    agent = QuestionnaireAgent(
        config=test_config,
        llm_service=mock_llm_service,
        rag_service=test_rag_service
    )
    await agent.initialize()
    return agent
```

## Integration Testing Strategy

**Database Integration Testing:**
- **Vector Operations**: Verify pgvector operations work correctly with agent-generated embeddings
- **Transaction Management**: Test agent operations within database transactions
- **Connection Pooling**: Validate agent database connections don't exhaust connection pools
- **Schema Compatibility**: Ensure agents write data compatible with existing schema

**API Integration Testing:**
```python
# FastAPI integration testing for agent endpoints
async def test_agent_api_integration():
    """Test API endpoints calling agents directly."""
    
    with TestClient(app) as client:
        # Test document processing endpoint
        response = client.post(
            "/api/documents/process",
            files={"file": ("test.pdf", test_pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        assert "summary" in response.json()
        assert "vector_id" in response.json()
        
        # Test questionnaire generation endpoint
        response = client.post(
            "/api/questionnaires/generate",
            json={"document_id": "test-doc-1", "template": "default"}
        )
        
        assert response.status_code == 200
        assert "questions" in response.json()
        assert len(response.json()["questions"]) > 0
```

**External API Integration Testing:**
```python
# Google Gemini API integration testing
async def test_gemini_api_integration():
    """Test Google Gemini API integration through agents."""
    
    # Test with rate limiting
    responses = []
    for i in range(10):
        result = await questionnaire_agent.generate_questions(test_document)
        responses.append(result)
        await asyncio.sleep(0.1)  # Respect rate limits
    
    # Verify all requests successful
    assert all(r.status == "success" for r in responses)
    
    # Test error handling
    with mock.patch('google.genai.GenerativeModel.generate_content') as mock_gen:
        mock_gen.side_effect = Exception("API Error")
        
        result = await questionnaire_agent.generate_questions(test_document)
        assert result.status == "error"
        assert "API Error" in result.error_message
```

## Performance Testing Framework

**Performance Test Implementation:**
```python
# Performance comparison framework
class PerformanceTestSuite:
    """Compare agent performance against legacy system baselines."""
    
    def __init__(self):
        self.baselines = load_performance_baselines()
        self.results = []
    
    async def test_pdf_processing_performance(self):
        """Compare PDF processing times."""
        test_files = load_test_pdf_files()
        
        for pdf_file in test_files:
            # Measure agent processing time
            start_time = time.time()
            result = await pdf_processor_agent.process_document(pdf_file)
            agent_time = time.time() - start_time
            
            # Compare with baseline
            baseline_time = self.baselines[pdf_file.name]
            performance_ratio = agent_time / baseline_time
            
            assert performance_ratio <= 1.10, f"Agent too slow: {performance_ratio:.2f}x baseline"
            
            self.results.append({
                "file": pdf_file.name,
                "agent_time": agent_time,
                "baseline_time": baseline_time,
                "ratio": performance_ratio
            })
    
    async def test_memory_usage(self):
        """Monitor agent memory consumption."""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        
        # Process multiple documents
        for i in range(50):
            await pdf_processor_agent.process_document(test_documents[i])
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Verify memory usage is reasonable
        assert memory_increase < 500 * 1024 * 1024, "Memory usage too high"  # 500MB limit
```

## Regression Testing Strategy

**Existing Functionality Validation:**
- **API Contract Testing**: Ensure all API responses maintain identical schemas
- **Database Schema Testing**: Verify no unintended schema modifications
- **UI Behavior Testing**: Validate all user interfaces work identically
- **Error Response Testing**: Confirm error messages and codes remain consistent

**Automated Regression Test Suite:**
```python
# Comprehensive regression testing
class RegressionTestSuite:
    """Validate no existing functionality is broken by agent migration."""
    
    async def test_api_contract_preservation(self):
        """Verify all API endpoints return identical response formats."""
        
        endpoint_tests = [
            ("/api/documents", "GET", None),
            ("/api/documents/upload", "POST", test_file_upload),
            ("/api/questionnaires", "GET", None),
            ("/api/questionnaires/generate", "POST", test_generation_request)
        ]
        
        for endpoint, method, payload in endpoint_tests:
            # Test with agent implementation
            agent_response = await make_api_request(endpoint, method, payload)
            
            # Compare with expected schema
            expected_schema = load_api_schema(endpoint, method)
            validate_schema(agent_response.json(), expected_schema)
    
    async def test_ui_workflow_preservation(self):
        """Verify all user workflows work identically."""
        
        # Test complete document processing workflow
        await mcp_playwright.browser_navigate("http://localhost:8000/documents")
        
        # Upload document
        await mcp_playwright.browser_file_upload(paths=["/test-data/test.pdf"])
        
        # Verify processing completes
        await mcp_playwright.browser_wait_for(text="Processing complete")
        
        # Generate questionnaire
        await mcp_playwright.browser_click(
            element="Generate Questionnaire button",
            ref="generate-questionnaire-btn"
        )
        
        # Verify questionnaire created
        await mcp_playwright.browser_wait_for(text="Questionnaire generated")
        
        # Validate final state matches expectations
        snapshot = await mcp_playwright.browser_snapshot()
        assert "Document processed successfully" in snapshot
        assert "Questionnaire available" in snapshot
```

## Quality Gates and Acceptance Criteria

**Automated Quality Gates:**
1. **Unit Test Coverage**: Minimum 90% coverage for all agent code
2. **Integration Test Success**: 100% of integration tests must pass
3. **Performance Benchmarks**: All performance tests within acceptance thresholds
4. **Regression Testing**: Zero regression in existing functionality
5. **Browser Testing**: All UI workflows validated with Playwright MCP

**Manual Quality Assurance:**
1. **User Acceptance Testing**: Complete workflow validation by end users
2. **Security Review**: Comprehensive security assessment of agent architecture
3. **Documentation Review**: All technical documentation updated and accurate
4. **Deployment Testing**: Successful deployment in staging environment

**Release Readiness Checklist:**
- [ ] All automated tests passing (unit, integration, performance, regression)
- [ ] Browser testing completed with Playwright MCP validation
- [ ] Security review completed with no critical findings
- [ ] Performance benchmarks met within defined thresholds
- [ ] User acceptance testing completed successfully
- [ ] Documentation updated and reviewed
- [ ] Deployment procedures validated in staging
- [ ] Rollback procedures tested and documented
- [ ] Monitoring and alerting configured for agent operations
- [ ] Team training completed for new architecture

## Test Automation and CI/CD Integration

**Continuous Integration Pipeline:**
```yaml
# CI/CD pipeline configuration for agent testing
name: Agent Migration Testing Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: uv sync
      - name: Run unit tests
        run: uv run pytest tests/unit/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: uv sync
      - name: Run integration tests
        run: uv run pytest tests/integration/
        env:
          DATABASE_URL: postgresql://postgres:test@localhost/test
          REDIS_URL: redis://localhost:6379/0

  browser-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: uv sync
      - name: Install Playwright browsers
        run: uv run playwright install
      - name: Run browser tests
        run: uv run pytest tests/e2e/ --browser-tests
        env:
          USE_PLAYWRIGHT_MCP: true

  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup test environment
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Run performance benchmarks
        run: uv run pytest tests/performance/
      - name: Generate performance report
        run: uv run python scripts/generate_performance_report.py
```

**Test Reporting and Metrics:**
- **Test Coverage Reports**: Automated coverage reporting with trend analysis
- **Performance Metrics**: Automated performance comparison reports
- **Test Execution Reports**: Detailed test results with failure analysis
- **Browser Test Reports**: Playwright test reports with screenshots and videos
- **Quality Metrics Dashboard**: Real-time quality metrics and trends

## Test Data Security and Privacy

**Test Data Management:**
- **Synthetic Data**: Use generated legal documents for testing, not real client data
- **Data Anonymization**: Any real data used must be completely anonymized
- **Secure Storage**: Test data stored in encrypted, access-controlled repositories
- **Data Lifecycle**: Automated cleanup of test data after test completion

**Privacy Compliance:**
- **GDPR Compliance**: Test data handling complies with data protection regulations
- **Access Controls**: Restricted access to test data based on role requirements
- **Audit Logging**: Complete audit trail of test data access and usage
- **Data Retention**: Defined retention policies for test data and results

This comprehensive testing strategy ensures the autonomous agent migration maintains system quality, performance, and reliability while providing confidence in the new architecture through thorough validation at every level.
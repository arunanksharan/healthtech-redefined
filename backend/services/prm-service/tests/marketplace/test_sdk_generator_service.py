"""
Unit tests for SDKGeneratorService
"""

import pytest
from modules.marketplace.services.sdk_generator_service import SDKGeneratorService
from modules.marketplace.schemas import SDKLanguage


@pytest.fixture
def sdk_service():
    return SDKGeneratorService()


class TestAuthenticationSamples:
    """Tests for authentication code sample generation."""

    def test_generate_typescript_auth(self, sdk_service):
        """Test TypeScript authentication sample generation."""
        samples = sdk_service.generate_authentication_samples(
            client_id="test_client_123",
            redirect_uri="https://app.test.com/callback",
            scopes=["patient/Patient.read", "openid"],
            language=SDKLanguage.TYPESCRIPT
        )

        assert len(samples) == 1
        sample = samples[0]
        assert sample.language == SDKLanguage.TYPESCRIPT
        assert "test_client_123" in sample.code
        assert "PRMClient" in sample.code
        assert "@healthtech-prm/sdk" in sample.dependencies

    def test_generate_python_auth(self, sdk_service):
        """Test Python authentication sample generation."""
        samples = sdk_service.generate_authentication_samples(
            client_id="test_client_123",
            redirect_uri="https://app.test.com/callback",
            scopes=["patient/Patient.read"],
            language=SDKLanguage.PYTHON
        )

        assert len(samples) == 1
        sample = samples[0]
        assert sample.language == SDKLanguage.PYTHON
        assert "healthtech_prm_sdk" in sample.code
        assert "test_client_123" in sample.code

    def test_generate_java_auth(self, sdk_service):
        """Test Java authentication sample generation."""
        samples = sdk_service.generate_authentication_samples(
            client_id="test_client_123",
            redirect_uri="https://app.test.com/callback",
            scopes=["patient/Patient.read"],
            language=SDKLanguage.JAVA
        )

        assert len(samples) == 1
        sample = samples[0]
        assert sample.language == SDKLanguage.JAVA
        assert "com.healthtech.prm" in sample.code
        assert "test_client_123" in sample.code

    def test_generate_csharp_auth(self, sdk_service):
        """Test C# authentication sample generation."""
        samples = sdk_service.generate_authentication_samples(
            client_id="test_client_123",
            redirect_uri="https://app.test.com/callback",
            scopes=["patient/Patient.read"],
            language=SDKLanguage.CSHARP
        )

        assert len(samples) == 1
        sample = samples[0]
        assert sample.language == SDKLanguage.CSHARP
        assert "HealthTech.PRM.SDK" in sample.code
        assert "test_client_123" in sample.code

    def test_generate_all_languages_auth(self, sdk_service):
        """Test generating authentication samples for all languages."""
        samples = sdk_service.generate_authentication_samples(
            client_id="test_client_123",
            redirect_uri="https://app.test.com/callback",
            scopes=["patient/Patient.read"]
        )

        assert len(samples) == 4
        languages = {s.language for s in samples}
        assert languages == {
            SDKLanguage.TYPESCRIPT,
            SDKLanguage.PYTHON,
            SDKLanguage.JAVA,
            SDKLanguage.CSHARP
        }


class TestFHIRSamples:
    """Tests for FHIR operation code sample generation."""

    def test_generate_fhir_read_typescript(self, sdk_service):
        """Test TypeScript FHIR read sample."""
        samples = sdk_service.generate_fhir_samples(
            resource_type="Patient",
            operation="read",
            resource_id="123",
            language=SDKLanguage.TYPESCRIPT
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "Patient" in sample.code
        assert "read" in sample.code.lower()
        assert "fhir" in sample.code.lower()

    def test_generate_fhir_search_python(self, sdk_service):
        """Test Python FHIR search sample."""
        samples = sdk_service.generate_fhir_samples(
            resource_type="Observation",
            operation="search",
            search_params={"patient": "123", "category": "vital-signs"},
            language=SDKLanguage.PYTHON
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "Observation" in sample.code
        assert "search" in sample.code.lower()

    def test_generate_fhir_create_java(self, sdk_service):
        """Test Java FHIR create sample."""
        samples = sdk_service.generate_fhir_samples(
            resource_type="Encounter",
            operation="create",
            language=SDKLanguage.JAVA
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "Encounter" in sample.code

    def test_generate_fhir_all_languages(self, sdk_service):
        """Test generating FHIR samples for all languages."""
        samples = sdk_service.generate_fhir_samples(
            resource_type="Patient",
            operation="read",
            resource_id="456"
        )

        assert len(samples) == 4


class TestWebhookSamples:
    """Tests for webhook handler code sample generation."""

    def test_generate_webhook_typescript(self, sdk_service):
        """Test TypeScript webhook handler sample."""
        samples = sdk_service.generate_webhook_samples(
            event_types=["patient.created", "appointment.scheduled"],
            language=SDKLanguage.TYPESCRIPT
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "webhook" in sample.code.lower()
        assert "patient.created" in sample.code
        assert "express" in sample.dependencies

    def test_generate_webhook_python(self, sdk_service):
        """Test Python webhook handler sample."""
        samples = sdk_service.generate_webhook_samples(
            event_types=["patient.created"],
            language=SDKLanguage.PYTHON
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "fastapi" in sample.code.lower() or "FastAPI" in sample.code
        assert "verify" in sample.code.lower()

    def test_generate_webhook_java(self, sdk_service):
        """Test Java webhook handler sample."""
        samples = sdk_service.generate_webhook_samples(
            event_types=["patient.created"],
            language=SDKLanguage.JAVA
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "WebhookController" in sample.code or "webhook" in sample.code.lower()

    def test_generate_webhook_all_languages(self, sdk_service):
        """Test generating webhook samples for all languages."""
        samples = sdk_service.generate_webhook_samples(
            event_types=["patient.created", "patient.updated"]
        )

        assert len(samples) == 4


class TestSMARTLaunchSamples:
    """Tests for SMART on FHIR launch code sample generation."""

    def test_generate_smart_ehr_launch_typescript(self, sdk_service):
        """Test TypeScript SMART EHR launch sample."""
        samples = sdk_service.generate_smart_launch_samples(
            client_id="smart_app_123",
            scopes=["launch", "patient/Patient.read", "openid"],
            launch_type="ehr",
            language=SDKLanguage.TYPESCRIPT
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "SMART" in sample.code or "smart" in sample.code.lower()
        assert "EHR" in sample.code or "ehr" in sample.code.lower()

    def test_generate_smart_standalone_launch_python(self, sdk_service):
        """Test Python SMART standalone launch sample."""
        samples = sdk_service.generate_smart_launch_samples(
            client_id="smart_app_123",
            scopes=["patient/Patient.read"],
            launch_type="standalone",
            language=SDKLanguage.PYTHON
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "SMARTClient" in sample.code or "smart" in sample.code.lower()


class TestAPISamples:
    """Tests for generic API call code sample generation."""

    def test_generate_api_call_get(self, sdk_service):
        """Test GET API call sample."""
        samples = sdk_service.generate_api_call_samples(
            endpoint="/api/v1/patients",
            method="GET",
            resource_type="Patient",
            language=SDKLanguage.TYPESCRIPT
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "GET" in sample.code
        assert "/api/v1/patients" in sample.code

    def test_generate_api_call_post(self, sdk_service):
        """Test POST API call sample."""
        samples = sdk_service.generate_api_call_samples(
            endpoint="/api/v1/appointments",
            method="POST",
            resource_type="Appointment",
            request_body={"patient_id": "123", "date": "2024-01-15"},
            language=SDKLanguage.PYTHON
        )

        assert len(samples) == 1
        sample = samples[0]
        assert "POST" in sample.code


class TestSDKDocumentation:
    """Tests for SDK documentation retrieval."""

    def test_get_typescript_documentation(self, sdk_service):
        """Test TypeScript SDK documentation."""
        docs = sdk_service.get_sdk_documentation(SDKLanguage.TYPESCRIPT)

        assert docs is not None
        assert docs.language == SDKLanguage.TYPESCRIPT
        assert docs.package_name == "@healthtech-prm/sdk"
        assert "npm install" in docs.installation
        assert docs.quick_start is not None
        assert docs.api_reference_url is not None

    def test_get_python_documentation(self, sdk_service):
        """Test Python SDK documentation."""
        docs = sdk_service.get_sdk_documentation(SDKLanguage.PYTHON)

        assert docs is not None
        assert docs.language == SDKLanguage.PYTHON
        assert "pip install" in docs.installation
        assert docs.github_url is not None

    def test_get_java_documentation(self, sdk_service):
        """Test Java SDK documentation."""
        docs = sdk_service.get_sdk_documentation(SDKLanguage.JAVA)

        assert docs is not None
        assert docs.language == SDKLanguage.JAVA
        assert "<dependency>" in docs.installation
        assert "com.healthtech.prm" in docs.package_name

    def test_get_csharp_documentation(self, sdk_service):
        """Test C# SDK documentation."""
        docs = sdk_service.get_sdk_documentation(SDKLanguage.CSHARP)

        assert docs is not None
        assert docs.language == SDKLanguage.CSHARP
        assert "dotnet add package" in docs.installation
        assert "HealthTech.PRM.SDK" in docs.package_name


class TestCodeSampleStructure:
    """Tests for code sample structure and quality."""

    def test_sample_has_title(self, sdk_service):
        """Test that samples have descriptive titles."""
        samples = sdk_service.generate_authentication_samples(
            client_id="test",
            redirect_uri="https://test.com/callback",
            scopes=["openid"],
            language=SDKLanguage.TYPESCRIPT
        )

        for sample in samples:
            assert sample.title is not None
            assert len(sample.title) > 0

    def test_sample_has_description(self, sdk_service):
        """Test that samples have descriptions."""
        samples = sdk_service.generate_fhir_samples(
            resource_type="Patient",
            operation="read",
            language=SDKLanguage.PYTHON
        )

        for sample in samples:
            assert sample.description is not None
            assert len(sample.description) > 0

    def test_sample_has_dependencies(self, sdk_service):
        """Test that samples list dependencies."""
        samples = sdk_service.generate_webhook_samples(
            event_types=["patient.created"],
            language=SDKLanguage.TYPESCRIPT
        )

        for sample in samples:
            assert sample.dependencies is not None
            assert len(sample.dependencies) > 0

    def test_sample_code_is_valid_syntax(self, sdk_service):
        """Test that generated code appears syntactically valid."""
        samples = sdk_service.generate_authentication_samples(
            client_id="test_client",
            redirect_uri="https://test.com/callback",
            scopes=["patient/Patient.read"],
            language=SDKLanguage.TYPESCRIPT
        )

        for sample in samples:
            # Basic syntax checks
            assert sample.code is not None
            assert len(sample.code) > 50  # Should be substantial code

            # TypeScript should have imports and async
            if sample.language == SDKLanguage.TYPESCRIPT:
                assert "import" in sample.code
                assert "async" in sample.code

    def test_sample_includes_client_id(self, sdk_service):
        """Test that samples properly include provided client_id."""
        client_id = "my_special_client_id_12345"
        samples = sdk_service.generate_authentication_samples(
            client_id=client_id,
            redirect_uri="https://test.com/callback",
            scopes=["openid"]
        )

        for sample in samples:
            assert client_id in sample.code

    def test_sample_includes_scopes(self, sdk_service):
        """Test that samples properly include provided scopes."""
        scopes = ["patient/Patient.read", "patient/Observation.read"]
        samples = sdk_service.generate_authentication_samples(
            client_id="test",
            redirect_uri="https://test.com/callback",
            scopes=scopes
        )

        for sample in samples:
            # At least one scope should appear in the code
            assert any(scope in sample.code for scope in scopes)

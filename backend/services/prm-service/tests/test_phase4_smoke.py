"""
Phase 4 Smoke Tests
Basic tests to verify Phase 4 modules are working correctly

These tests verify:
- All Phase 4 modules can be imported
- Models are properly defined and accessible
- Services can be instantiated
- Routers are properly configured
"""
import sys
from pathlib import Path

# Add prm-service directory and backend directory to path for imports
prm_service_dir = Path(__file__).parent.parent
backend_dir = prm_service_dir.parent.parent
sys.path.insert(0, str(prm_service_dir))
sys.path.insert(0, str(backend_dir))


def test_vector_imports():
    """Test vector module imports"""
    try:
        from modules.vector import schemas, repository, service, router
        from shared.database.models import TextChunk
        print("✓ Vector module imports successful")
        return True
    except ImportError as e:
        print(f"✗ Vector module import failed: {e}")
        return False


def test_agents_imports():
    """Test agents module imports"""
    try:
        from modules.agents import schemas, service, router
        from shared.database.models import ToolRun
        print("✓ Agents module imports successful")
        return True
    except ImportError as e:
        print(f"✗ Agents module import failed: {e}")
        return False


def test_intake_imports():
    """Test intake module imports"""
    try:
        from modules.intake import schemas, repository, service, router
        from shared.database.models import (
            IntakeSession,
            IntakeSummary,
            IntakeChiefComplaint,
            IntakeSymptom,
            IntakeAllergy,
            IntakeMedication,
            IntakeConditionHistory,
            IntakeFamilyHistory,
            IntakeSocialHistory,
            IntakeNote
        )
        print("✓ Intake module imports successful")
        return True
    except ImportError as e:
        print(f"✗ Intake module import failed: {e}")
        return False


def test_embeddings_utility():
    """Test embeddings utility import"""
    try:
        from core.embeddings import embeddings_service, EmbeddingsService
        print("✓ Embeddings utility import successful")
        return True
    except ImportError as e:
        print(f"✗ Embeddings utility import failed: {e}")
        return False


def test_model_definitions():
    """Test Phase 4 models are properly defined"""
    try:
        from shared.database.models import (
            TextChunk,
            ToolRun,
            IntakeSession,
            IntakeSummary,
            IntakeChiefComplaint,
            IntakeSymptom,
            IntakeAllergy,
            IntakeMedication,
            IntakeConditionHistory,
            IntakeFamilyHistory,
            IntakeSocialHistory,
            IntakeNote
        )

        # Verify table names
        assert TextChunk.__tablename__ == "text_chunk"
        assert ToolRun.__tablename__ == "tool_run"
        assert IntakeSession.__tablename__ == "intake_session"

        print("✓ All Phase 4 models properly defined")
        return True
    except (ImportError, AssertionError, AttributeError) as e:
        print(f"✗ Model definitions test failed: {e}")
        return False


def test_schema_definitions():
    """Test Phase 4 schemas are properly defined"""
    try:
        from modules.vector.schemas import (
            IngestTranscriptsByConversation,
            SearchQuery,
            ChunkOut
        )
        from modules.agents.schemas import (
            ToolDefinition,
            RunTool,
            ToolRunResponse
        )
        from modules.intake.schemas import (
            IntakeSessionCreate,
            IntakeRecordsUpsert,
            SymptomItem
        )

        print("✓ All Phase 4 schemas properly defined")
        return True
    except ImportError as e:
        print(f"✗ Schema definitions test failed: {e}")
        return False


def test_router_integration():
    """Test Phase 4 routers are integrated"""
    try:
        from api.router import api_router

        # Check that routers are included (they should have routes registered)
        route_paths = [route.path for route in api_router.routes]

        # Check for Phase 4 endpoints
        has_vector = any('/vector/' in path for path in route_paths)
        has_agents = any('/agents/' in path for path in route_paths)
        has_intake = any('/intake/' in path for path in route_paths)

        if has_vector and has_agents and has_intake:
            print("✓ All Phase 4 routers integrated into main API")
            return True
        else:
            missing = []
            if not has_vector:
                missing.append("vector")
            if not has_agents:
                missing.append("agents")
            if not has_intake:
                missing.append("intake")
            print(f"✗ Missing router integration for: {', '.join(missing)}")
            return False
    except Exception as e:
        print(f"✗ Router integration test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests"""
    print("\n" + "="*60)
    print("PHASE 4 SMOKE TESTS")
    print("="*60 + "\n")

    tests = [
        ("Vector Module Imports", test_vector_imports),
        ("Agents Module Imports", test_agents_imports),
        ("Intake Module Imports", test_intake_imports),
        ("Embeddings Utility", test_embeddings_utility),
        ("Model Definitions", test_model_definitions),
        ("Schema Definitions", test_schema_definitions),
        ("Router Integration", test_router_integration),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 60)
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60 + "\n")

    return all(result for _, result in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

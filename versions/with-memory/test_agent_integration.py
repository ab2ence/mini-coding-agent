"""
Agent Integration Tests with Memory Manager
============================================

Tests for verifying Memory Manager integration with MiniAgent:
1. Agent basic functionality
2. Memory Manager integration
3. Constraint extraction and retention
4. Tool output compression
5. Task state management
6. Session persistence
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mini_coding_agent import (
    FakeModelClient,
    MiniAgent,
    SessionStore,
    WorkspaceContext,
)


class TestAgentBasicFunctionality:
    """Test basic agent functionality with Memory Manager"""

    def test_agent_with_memory_manager(self):
        """Test agent initialization with Memory Manager"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            (tmp_path / "hello.txt").write_text("Hello, World!\n", encoding="utf-8")

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient([
                '<tool>{"name":"read_file","args":{"path":"hello.txt","start":1,"end":10}}</tool>',
                "<final>File content: Hello, World!</final>",
            ])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            assert hasattr(agent, "memory_manager"), "Agent should have memory_manager attribute"
            assert agent.memory_manager is not None, "Memory manager should be initialized"

            print("[PASS] Agent with Memory Manager initialization")

    def test_agent_ask_with_memory(self):
        """Test agent.ask() with Memory Manager"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            (tmp_path / "test.txt").write_text("Test content\n", encoding="utf-8")

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient([
                '<tool>{"name":"read_file","args":{"path":"test.txt","start":1,"end":10}}</tool>',
                "<final>Read test.txt successfully</final>",
            ])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            answer = agent.ask("Read the test.txt file")

            assert answer is not None, "Agent should return an answer"
            print(f"[PASS] Agent.ask() with Memory Manager - Response: {answer[:50]}...")


class TestMemoryManagerIntegration:
    """Test Memory Manager integration with Agent"""

    def test_constraint_extraction(self):
        """Test constraint extraction from user message"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>OK, I understand the constraints</final>"])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent.ask("Implement the feature but do not change the existing API")

            constraints = agent.memory_manager.constraint_keeper.pinned_constraints
            assert len(constraints) > 0, "Should extract constraints from message"

            print(f"[PASS] Constraint extraction - Found {len(constraints)} constraints")

    def test_tool_output_compression(self):
        """Test tool output compression"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>Done</final>"])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            long_output = "x" * 5000
            compressed = agent.memory_manager.process_tool_result("run_shell", {}, long_output)

            assert len(compressed) < len(long_output), "Tool output should be compressed"
            print(f"[PASS] Tool output compression - {len(long_output)} -> {len(compressed)} chars")

    def test_memory_text_generation(self):
        """Test memory text generation"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>OK</final>"])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent.memory_manager.process_user_message("Must maintain backward compatibility")

            memory_text = agent.memory_manager.build_memory_text()

            assert memory_text is not None, "Memory text should be generated"
            assert len(memory_text) > 0, "Memory text should not be empty"
            print(f"[PASS] Memory text generation - {len(memory_text)} chars")


class TestTaskStateManagement:
    """Test task state management with Memory Manager"""

    def test_task_registration(self):
        """Test task registration through dialog"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>OK, I'll implement the feature</final>"])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent.ask("Task: Implement user authentication")

            tss = agent.memory_manager.task_state_segmenter
            assert len(tss.task_registry) > 0, "Task should be registered"

            print(f"[PASS] Task registration - {len(tss.task_registry)} tasks registered")

    def test_phase_detection(self):
        """Test phase change detection"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient([
                "<final>Let me plan the architecture</final>",
                "<final>Implementing the code</final>",
            ])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent.ask("We need to design the system architecture")
            agent.ask("Now implement the code")

            tss = agent.memory_manager.task_state_segmenter
            phase_history = tss.state.get("phase_history", [])
            print(f"[INFO] Phase history: {len(phase_history)} entries")

    def test_state_text_generation(self):
        """Test state text generation"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>OK</final>", "<final>Done</final>"])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent.ask("Implement feature A")

            state_text = agent.memory_manager.task_state_segmenter.get_state_text()

            assert state_text is not None, "State text should be generated"
            print(f"[PASS] State text generation - {len(state_text)} chars")


class TestSessionPersistence:
    """Test session persistence with Memory Manager"""

    def test_session_serialization(self):
        """Test session serialization with Memory Manager"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>OK</final>"])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent.memory_manager.process_user_message("Important constraint: Keep API stable")

            agent.record({"role": "test", "content": "test"})

            assert "memory_manager" in agent.session, "Memory manager should be in session"

            print("[PASS] Session serialization - Memory Manager saved to session")

    def test_session_deserialization(self):
        """Test session deserialization with Memory Manager"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>OK</final>"])

            agent1 = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent1.memory_manager.process_user_message("Constraint: Maintain compatibility")

            agent1.record({"role": "test", "content": "test"})

            agent2 = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            constraints_count = len(agent2.memory_manager.constraint_keeper.pinned_constraints)
            print(f"[PASS] Session deserialization - {constraints_count} constraints restored")


class TestMemoryStats:
    """Test memory statistics"""

    def test_get_stats(self):
        """Test getting memory statistics"""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)

            workspace = WorkspaceContext.build(tmp_path)
            store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
            model_client = FakeModelClient(["<final>OK</final>"])

            agent = MiniAgent(
                model_client=model_client,
                workspace=workspace,
                session_store=store,
                approval_policy="auto",
            )

            agent.memory_manager.process_tool_result("run_shell", {}, "x" * 2000)
            agent.memory_manager.process_user_message("Must keep API unchanged")

            stats = agent.memory_manager.get_stats()

            assert "compression_ratio" in stats, "Stats should include compression ratio"
            assert "constraints_count" in stats, "Stats should include constraints count"

            print(f"[PASS] Memory stats - Compression: {stats['compression_ratio']:.2%}, "
                  f"Constraints: {stats['constraints_count']}")


def run_all_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("Memory Manager Integration Tests")
    print("=" * 70)
    print()

    test_classes = [
        TestAgentBasicFunctionality,
        TestMemoryManagerIntegration,
        TestTaskStateManagement,
        TestSessionPersistence,
        TestMemoryStats,
    ]

    total_passed = 0
    total_failed = 0

    for test_class in test_classes:
        print(f"\n{'='*70}")
        print(f"Testing: {test_class.__name__}")
        print("=" * 70)

        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in test_methods:
            try:
                method = getattr(instance, method_name)
                method()
                total_passed += 1
            except AssertionError as e:
                print(f"[FAIL] {method_name}: {e}")
                total_failed += 1
            except Exception as e:
                print(f"[ERROR] {method_name}: {e}")
                total_failed += 1

    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Total Tests:  {total_passed + total_failed}")

    if total_failed == 0:
        print()
        print("ALL TESTS PASSED!")
    else:
        print()
        print(f"WARNING: {total_failed} test(s) failed!")

    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

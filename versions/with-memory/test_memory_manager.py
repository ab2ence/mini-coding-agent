"""
Unit Tests for Memory Manager
=============================

Tests for all 8 Memory Manager components:
1. TriggerManager
2. IncrementalRollingSummary
3. ConstraintKeeper
4. ToolOutputCompressor
5. ToolPairProtector
6. ProjectMemoryLoader
7. SummaryPriorityCompressor
8. TaskStateSegmenter
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from memory_manager import (
    TriggerManager,
    IncrementalRollingSummary,
    ConstraintKeeper,
    ToolOutputCompressor,
    ToolPairProtector,
    ProjectMemoryLoader,
    SummaryPriorityCompressor,
    TaskStateSegmenter,
    MemoryManager,
    DEFAULT_MEMORY_MANAGER_CONFIG,
)


class FakeModelClient:
    """Fake model client for testing"""
    def __init__(self, outputs=None):
        self.outputs = list(outputs) if outputs else []
        self.prompts = []

    def complete(self, prompt, max_new_tokens):
        self.prompts.append(prompt)
        if not self.outputs:
            return "[摘要] 这是一个测试摘要"
        return self.outputs.pop(0)


def now():
    return datetime.now(timezone.utc).isoformat()


class TestTriggerManager:
    """Test TriggerManager"""

    def test_fixed_step_trigger(self):
        """Test fixed step trigger"""
        tm = TriggerManager({"trigger": {"fixed_step_trigger": 5}})

        messages = [{"role": "user", "content": f"message {i}"} for i in range(4)]
        should_compact, reason = tm.should_compact(messages)
        assert should_compact is False

        messages.append({"role": "user", "content": "message 5"})
        should_compact, reason = tm.should_compact(messages)
        assert should_compact is True
        assert reason == "fixed_step"

    def test_token_threshold_trigger(self):
        """Test token threshold trigger"""
        tm = TriggerManager({"trigger": {
            "fixed_step_trigger": 100,
            "token_threshold": 500,
            "preserve_count": 2
        }})

        messages = [{"role": "user", "content": "x" * 400}] * 5
        should_compact, reason = tm.should_compact(messages, estimated_tokens=50)
        assert should_compact is False

        should_compact, reason = tm.should_compact(messages, estimated_tokens=600)
        assert should_compact is True
        assert reason == "token_threshold"

    def test_force_compact_trigger(self):
        """Test force compact trigger"""
        tm = TriggerManager({"trigger": {
            "fixed_step_trigger": 100,
            "force_compact_at": 1000
        }})

        messages = [{"role": "user", "content": "x" * 400}] * 2
        should_compact, reason = tm.should_compact(messages, estimated_tokens=1200)
        assert should_compact is True
        assert reason == "forced"

    def test_estimate_tokens(self):
        """Test token estimation"""
        tm = TriggerManager()
        tokens = tm.estimate_tokens("你好世界hello")
        assert tokens > 0

    def test_get_preserve_count(self):
        """Test preserve count calculation"""
        tm = TriggerManager({"trigger": {"preserve_count": 4}})
        messages = [{"content": "x" * 10000}] * 10
        preserve = tm.get_preserve_count(messages)
        assert preserve == 6

        messages = [{"content": "x"}] * 10
        preserve = tm.get_preserve_count(messages)
        assert preserve == 4


class TestConstraintKeeper:
    """Test ConstraintKeeper"""

    def test_extract_chinese_constraints(self):
        """Test extracting Chinese constraints"""
        ck = ConstraintKeeper()

        text = "我需要你实现这个功能，但不能改变现有的API接口。必须保持向后兼容性。"
        constraints = ck.extract_constraints(text)
        assert len(constraints) >= 2

    def test_extract_english_constraints(self):
        """Test extracting English constraints"""
        ck = ConstraintKeeper()

        text = "You must implement this feature but don't change the existing API. Must maintain backward compatibility."
        constraints = ck.extract_constraints(text)
        assert len(constraints) >= 1

    def test_add_constraints(self):
        """Test adding constraints"""
        ck = ConstraintKeeper()
        ck.add_constraints(["约束1", "约束2"])
        assert len(ck.pinned_constraints) == 2

        ck.add_constraints(["约束1", "约束3"])
        assert len(ck.pinned_constraints) == 3
        assert "约束1" in ck.pinned_constraints

    def test_max_constraints(self):
        """Test max constraints limit"""
        ck = ConstraintKeeper({"constraint_keeper": {"max_constraints": 3}})
        for i in range(5):
            ck.add_constraints([f"约束{i}"])
        assert len(ck.pinned_constraints) <= 3

    def test_get_constraints_text(self):
        """Test getting constraints text"""
        ck = ConstraintKeeper()
        ck.add_constraints(["约束1", "约束2"])
        text = ck.get_constraints_text()
        assert "[关键约束]" in text
        assert "约束1" in text
        assert "约束2" in text

    def test_deduplicate_constraints(self):
        """Test constraint deduplication"""
        ck = ConstraintKeeper()
        constraints = ["约束1", "约束1", "约束2"]
        deduped = ck.deduplicate_and_limit(constraints)
        assert len(deduped) == 2


class TestToolOutputCompressor:
    """Test ToolOutputCompressor"""

    def test_compress_test_output(self):
        """Test compressing test output"""
        toc = ToolOutputCompressor({"tool_compression": {
            "enabled": True,
            "auto_compress": True,
            "threshold_length": 100,
            "test_output_max": 50
        }})

        test_output = "100 passed, 5 failed, 3 errors\nFAILED test_1\nFAILED test_2\nERROR test_3"
        compressed = toc.compress_shell_output(test_output)
        assert "[测试统计]" in compressed
        assert "passed: 100" in compressed

    def test_compress_log_output(self):
        """Test compressing log output"""
        toc = ToolOutputCompressor()

        log_output = "[INFO] Starting\n[INFO] Processing\n[ERROR] Failed\n[WARNING] Warning message"
        compressed = toc.compress_log_output(log_output)
        assert "[ERROR]" in compressed
        assert "[WARNING]" in compressed

    def test_compress_repeated_lines(self):
        """Test compressing repeated lines"""
        toc = ToolOutputCompressor()

        repeated = "line1\nline1\nline1\nline2"
        compressed = toc.compress_repeated_lines(repeated)
        assert "[上条内容重复 3 次]" in compressed

    def test_smart_truncate(self):
        """Test smart truncation"""
        toc = ToolOutputCompressor()

        long_text = "a" * 1000 + "error occurred" + "b" * 1000
        truncated = toc.smart_truncate(long_text, 200)
        assert len(truncated) <= 500
        assert "error" in truncated

    def test_never_compress_read_file(self):
        """Test that read_file is never compressed"""
        toc = ToolOutputCompressor({"tool_compression": {
            "never_compress_tools": ["read_file"],
            "threshold_length": 10
        }})

        content = "x" * 1000
        compressed = toc.compress("read_file", content)
        assert compressed == content

    def test_compression_stats(self):
        """Test compression statistics"""
        toc = ToolOutputCompressor()

        toc.update_stats(1000, 500)
        toc.update_stats(2000, 400)

        ratio = toc.get_compression_ratio()
        assert 0 < ratio < 1


class TestToolPairProtector:
    """Test ToolPairProtector"""

    def test_safe_compact_simple(self):
        """Test simple safe compact"""
        tpp = ToolPairProtector()

        history = [{"role": "user", "content": "test"}] * 5
        preserved = tpp.safe_compact_history(history, 3)
        assert len(preserved) == 3

    def test_safe_compact_with_tool_pair(self):
        """Test safe compact with tool pair"""
        tpp = ToolPairProtector()

        history = [
            {"role": "assistant", "content": '<tool>{"name":"run_shell"}</tool>'},
            {"role": "tool", "name": "run_shell", "content": "result"}
        ] + [{"role": "user", "content": "test"}] * 5

        preserved = tpp.safe_compact_history(history, 6)
        has_tool_result = any(item.get("role") == "tool" and item.get("name") == "run_shell" for item in preserved)
        assert has_tool_result


class TestIncrementalRollingSummary:
    """Test IncrementalRollingSummary"""

    def test_should_summarize(self):
        """Test should summarize check"""
        irs = IncrementalRollingSummary(FakeModelClient(), {"rolling_summary": {
            "trigger_steps": 5
        }})

        history = [{"role": "user", "content": f"msg {i}"} for i in range(4)]
        assert irs.should_summarize(history) is False

        history.append({"role": "user", "content": "msg 5"})
        assert irs.should_summarize(history) is True

    def test_generate_summary(self):
        """Test summary generation"""
        fake_client = FakeModelClient(["[摘要] 测试摘要内容"])
        irs = IncrementalRollingSummary(fake_client, {"rolling_summary": {
            "min_steps_before_summary": 2,
            "overlap_steps": 2
        }})

        history = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
        summary = irs.generate_summary(history, "测试任务")

        assert summary is not None
        assert len(irs.summary_history) == 1

    def test_fallback_summary(self):
        """Test fallback summary generation"""
        fake_client = FakeModelClient([])
        irs = IncrementalRollingSummary(fake_client, {"rolling_summary": {
            "min_steps_before_summary": 2,
            "overlap_steps": 2
        }})

        history = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
        summary = irs.generate_summary(history, "测试任务")

        assert summary is not None
        assert len(summary) > 0

    def test_compress_history(self):
        """Test history compression"""
        irs = IncrementalRollingSummary(FakeModelClient())

        history = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
        compressed = irs.compress_history(history, "测试摘要")

        assert len(compressed) < len(history)
        assert compressed[0]["role"] == "system"
        assert "测试摘要" in compressed[0]["content"]


class TestProjectMemoryLoader:
    """Test ProjectMemoryLoader"""

    def test_load_empty_instructions(self):
        """Test loading with no instruction files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pml = ProjectMemoryLoader(tmpdir)
            result = pml.load_project_instructions()

            assert result["instructions"] == ""
            assert len(result["paths_checked"]) > 0

    def test_load_claude_md(self):
        """Test loading CLAUDE.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            claude_file.write_text("Test instruction content")

            pml = ProjectMemoryLoader(tmpdir)
            result = pml.load_project_instructions()

            assert "Test instruction content" in result["instructions"]

    def test_load_claude_local_md(self):
        """Test loading CLAUDE.local.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            local_file = Path(tmpdir) / "CLAUDE.local.md"
            local_file.write_text("Local instructions")

            pml = ProjectMemoryLoader(tmpdir)
            result = pml.load_project_instructions()

            assert "Local instructions" in result["instructions"]
            assert "本地" in result["instructions"]

    def test_inherit_parent_instructions(self):
        """Test inheriting parent instructions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_dir = Path(tmpdir)
            child_dir = parent_dir / "child"

            (parent_dir / "CLAUDE.md").write_text("Parent instructions")
            child_dir.mkdir()
            (child_dir / "CLAUDE.md").write_text("Child instructions")

            pml = ProjectMemoryLoader(child_dir)
            result = pml.load_project_instructions()

            assert "Parent instructions" in result["instructions"]
            assert "Child instructions" in result["instructions"]


class TestSummaryPriorityCompressor:
    """Test SummaryPriorityCompressor"""

    def test_classify_priority(self):
        """Test priority classification"""
        spc = SummaryPriorityCompressor()

        assert spc.classify_priority("- work item") == 0
        assert spc.classify_priority("- regular item") == 1
        assert spc.classify_priority("## Title") == 2
        assert spc.classify_priority("normal text") == 3

    def test_compress_with_budget(self):
        """Test compression with budget"""
        spc = SummaryPriorityCompressor({"summary_compression": {
            "max_chars": 100,
            "max_lines": 5,
            "max_line_chars": 50
        }})

        lines = [
            "- work item 1",
            "- work item 2",
            "- regular item",
            "## Title",
            "normal text",
            "extra line"
        ]

        compressed = spc.compress("\n".join(lines))
        assert len(compressed.split("\n")) <= 6


class TestTaskStateSegmenter:
    """Test TaskStateSegmenter"""

    def test_register_task(self):
        """Test task registration"""
        tss = TaskStateSegmenter()

        task_id = tss.register_task({
            "title": "测试任务",
            "priority": tss.TASK_PRIORITY["HIGH"]
        })

        assert task_id == 0
        assert len(tss.task_registry) == 1
        assert tss.task_registry[0]["title"] == "测试任务"
        assert tss.task_registry[0]["status"] == tss.TASK_STATUS["PENDING"]

    def test_update_task_status(self):
        """Test task status update"""
        tss = TaskStateSegmenter()

        task_id = tss.register_task({"title": "测试任务"})
        tss.update_task_status(task_id, tss.TASK_STATUS["IN_PROGRESS"])
        tss.update_task_status(task_id, tss.TASK_STATUS["COMPLETED"])

        task = tss.get_task(task_id)
        assert task["status"] == tss.TASK_STATUS["COMPLETED"]
        assert len(tss.event_bus) > 0

    def test_detect_phase_change(self):
        """Test phase change detection"""
        tss = TaskStateSegmenter()

        result = tss.detect_phase_change(
            "我们需要实现这个功能",
            "好的，我来实现"
        )

        assert result is None

        result = tss.detect_phase_change(
            "计划很重要，先规划一下",
            "好的，让我规划一下架构设计"
        )

        assert result is not None
        assert "planning" in result

    def test_extract_tasks_from_dialog(self):
        """Test extracting tasks from dialog"""
        tss = TaskStateSegmenter()

        tasks = tss.extract_tasks_from_dialog(
            "任务: 实现登录功能",
            "好的，我来实现登录功能。下一步: 编写测试用例"
        )

        assert len(tasks) >= 1

    def test_extract_todos(self):
        """Test extracting todos"""
        tss = TaskStateSegmenter()

        todos = tss.extract_todos(
            "待做: 完成任务1",
            "- [ ] 待完成任务"
        )

        assert len(todos) >= 1

    def test_priority_queue(self):
        """Test priority queue"""
        tss = TaskStateSegmenter()

        tss.register_task({"title": "普通任务", "priority": tss.TASK_PRIORITY["MEDIUM"]})
        tss.register_task({"title": "重要任务", "priority": tss.TASK_PRIORITY["HIGH"]})
        tss.register_task({"title": "紧急任务", "priority": tss.TASK_PRIORITY["CRITICAL"]})

        tss.update_priority_queue()

        next_task = tss.get_next_task()
        assert next_task is not None

    def test_update_progress(self):
        """Test progress update"""
        tss = TaskStateSegmenter()

        tss.register_task({"title": "任务1"})
        tss.register_task({"title": "任务2"})

        progress = tss.update_progress()

        assert progress["total_tasks"] == 2
        assert progress["current_phase"] == "task_analysis"

    def test_get_state_text(self):
        """Test getting state text"""
        tss = TaskStateSegmenter()

        text = tss.get_state_text()

        assert "[当前阶段]" in text
        assert "[阶段进度]" in text

    def test_serialize_deserialize(self):
        """Test serialization and deserialization"""
        tss = TaskStateSegmenter()

        task_id = tss.register_task({"title": "测试任务"})
        tss.update_task_status(task_id, tss.TASK_STATUS["COMPLETED"])
        tss.detect_phase_change("计划很重要需要规划设计方案架构", "好的让我规划设计方案")

        data = tss.serialize()

        tss2 = TaskStateSegmenter.deserialize(data)

        assert len(tss2.task_registry) == 1
        assert len(tss2.state["phase_history"]) > 0


class TestMemoryManager:
    """Test MemoryManager"""

    def test_initialization(self):
        """Test MemoryManager initialization"""
        fake_client = FakeModelClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(fake_client, tmpdir)

            assert mm.trigger_manager is not None
            assert mm.constraint_keeper is not None
            assert mm.tool_output_compressor is not None
            assert mm.task_state_segmenter is not None

    def test_process_user_message(self):
        """Test processing user message"""
        fake_client = FakeModelClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(fake_client, tmpdir)

            mm.process_user_message("我需要实现这个功能，但不能改变API")

            assert len(mm.constraint_keeper.pinned_constraints) > 0

    def test_process_tool_result(self):
        """Test processing tool result"""
        fake_client = FakeModelClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(fake_client, tmpdir)

            result = "x" * 2000
            compressed = mm.process_tool_result("run_shell", {}, result)

            assert len(compressed) < len(result)

    def test_build_memory_text(self):
        """Test building memory text"""
        fake_client = FakeModelClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(fake_client, tmpdir)

            mm.process_user_message("实现功能，但不能改变API")

            memory_text = mm.build_memory_text()

            assert "[关键约束]" in memory_text
            assert "不能改变" in memory_text

    def test_should_compact(self):
        """Test should compact check"""
        fake_client = FakeModelClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(fake_client, tmpdir)

            history = [{"role": "user", "content": f"msg {i}"} for i in range(40)]

            should_compact, reason = mm.should_compact(history)
            assert should_compact is True

    def test_get_stats(self):
        """Test getting statistics"""
        fake_client = FakeModelClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(fake_client, tmpdir)

            mm.process_tool_result("run_shell", {}, "x" * 1000)

            stats = mm.get_stats()

            assert "compression_ratio" in stats
            assert "constraints_count" in stats
            assert stats["constraints_count"] == 0

    def test_serialize_deserialize(self):
        """Test serialization"""
        fake_client = FakeModelClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(fake_client, tmpdir)

            mm.process_user_message("测试约束")

            data = mm.serialize()

            assert "summary" in data
            assert "constraint_keeper" in data

            mm2 = MemoryManager(fake_client, tmpdir)
            mm2.deserialize(data)

            assert len(mm2.constraint_keeper.pinned_constraints) == len(mm.constraint_keeper.pinned_constraints)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

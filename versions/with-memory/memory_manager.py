"""
Mini-Coding-Agent Memory Manager
================================

Memory Manager optimization for Mini-Coding-Agent.
Implements 4 core features:
1. Rolling Summary - 滚动摘要
2. Pinned Facts / Constraints - 关键约束保留
3. Tool Output Compression - 工具输出压缩
4. Task-State Segmentation - 任务状态分段

Version: 2.1 (完整版)
"""

import re
import json
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


DEFAULT_MEMORY_MANAGER_CONFIG = {
    "trigger": {
        "enabled": True,
        "fixed_step_trigger": 30,
        "token_threshold": 8000,
        "force_compact_at": 60000,
        "preserve_count": 4,
    },
    "rolling_summary": {
        "enabled": True,
        "trigger_steps": 30,
        "min_steps_before_summary": 10,
        "overlap_steps": 5,
        "max_summary_history": 5,
        "incremental": True,
    },
    "constraint_keeper": {
        "enabled": True,
        "extract_from_user": True,
        "extract_from_assistant": False,
        "max_constraints": 20,
    },
    "tool_compression": {
        "enabled": True,
        "auto_compress": True,
        "threshold_length": 1000,
        "always_compress_tools": ["run_shell"],
        "never_compress_tools": ["read_file"],
        "max_output_length": 500,
        "test_output_max": 50,
        "error_output_max": 300,
    },
    "task_state_segmentation": {
        "enabled": True,
        "max_todos": 10,
        "max_phases": 10,
        "max_tasks": 50,
    },
    "tool_pair_protection": {
        "enabled": True,
        "check_before_compact": True,
    },
    "project_memory": {
        "enabled": True,
        "load_claude_md": True,
        "load_claw_instructions": True,
        "inherit_parent": True,
        "max_instruction_chars": 3000,
    },
    "summary_compression": {
        "max_chars": 1200,
        "max_lines": 24,
        "max_line_chars": 160,
        "priority_enabled": True,
    },
    "cache": {
        "enabled": False,
        "ttl": 300,
    },
    "stats": {
        "track_compressions": True,
        "track_tokens_saved": True,
    },
}


class TriggerManager:
    """
    智能触发管理器
    结合固定轮数 + Token 感知 + 强制压缩
    """
    def __init__(self, config=None):
        self.config = (config or {}).get("trigger", {})
        self.fixed_step_trigger = self.config.get("fixed_step_trigger", 30)
        self.token_threshold = self.config.get("token_threshold", 8000)
        self.preserve_count = self.config.get("preserve_count", 4)
        self.force_compact_at = self.config.get("force_compact_at", 60000)

    def should_compact(self, messages, estimated_tokens=None):
        """
        判断是否需要压缩

        Returns:
            (should_compact: bool, reason: str or None)
        """
        if not self.config.get("enabled", True):
            return False, None

        if len(messages) >= self.fixed_step_trigger:
            return True, "fixed_step"

        if estimated_tokens and estimated_tokens >= self.token_threshold:
            if len(messages) - self.preserve_count > self.preserve_count:
                return True, "token_threshold"

        if estimated_tokens and estimated_tokens >= self.force_compact_at:
            return True, "forced"

        return False, None

    def estimate_tokens(self, text):
        """
        估算 token 数量
        中文约 1 token ≈ 1.5-2 字符
        英文约 1 token ≈ 4 字符
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)

    def get_preserve_count(self, messages):
        """获取保留消息数"""
        total_len = sum(len(str(m.get("content", ""))) for m in messages)
        if total_len > 50000:
            return 6
        return self.preserve_count


class IncrementalRollingSummary:
    """
    增量滚动摘要
    结合 Claw Code 的增量压缩思想
    """
    SUMMARY_TEMPLATE = """## 对话摘要 [生成时间: {timestamp}]

### 关键决策
{key_decisions}

### 已完成工作
{completed_steps}

### 当前状态
{current_status}

### 遗留问题
{remaining_issues}"""

    def __init__(self, model_client, config=None):
        self.model_client = model_client
        self.config = (config or {}).get("rolling_summary", {})
        self.max_history = self.config.get("max_summary_history", 5)
        self.overlap = self.config.get("overlap_steps", 5)
        self.summary_history = []
        self.min_steps = self.config.get("min_steps_before_summary", 10)

    def should_summarize(self, history):
        """判断是否需要摘要"""
        return len(history) >= self.config.get("trigger_steps", 30)

    def generate_summary(self, history, task):
        """生成摘要（包含历史上下文）"""
        if len(history) < self.min_steps:
            return None

        historical_highlights = self.extract_highlights_from_history()
        content_to_summarize = history[:-self.overlap]

        prompt = self.build_enhanced_prompt(
            content_to_summarize,
            task,
            historical_highlights
        )

        try:
            summary = self.model_client.complete(prompt, max_new_tokens=300)
        except Exception:
            summary = self._generate_fallback_summary(history)

        self.summary_history.append({
            "summary": summary,
            "step": len(history),
            "timestamp": now()
        })

        if len(self.summary_history) > self.max_history:
            self.summary_history = self.summary_history[-self.max_history:]

        return summary

    def _generate_fallback_summary(self, history):
        """生成降级摘要"""
        lines = []
        for item in history[-10:]:
            role = item.get("role", "unknown")
            content = str(item.get("content", ""))[:100]
            lines.append(f"[{role}] {content}")
        return "\n".join(lines)

    def extract_highlights_from_history(self):
        """从历史摘要中提取关键信息"""
        highlights = []
        for entry in self.summary_history[-3:]:
            extracted = self.extract_key_points(entry["summary"])
            highlights.extend(extracted)
        return highlights[:20]

    def extract_key_points(self, summary_text):
        """从摘要中提取关键点"""
        key_points = []
        lines = summary_text.split('\n')
        in_key_section = False

        for line in lines:
            if '关键决策' in line or 'key decision' in line.lower():
                in_key_section = True
                continue
            if in_key_section:
                if line.startswith('###') or line.startswith('##'):
                    break
                if line.strip().startswith('-'):
                    key_points.append(line.strip('- ').strip())
        return key_points

    def build_enhanced_prompt(self, content, task, historical_highlights):
        """构建增强的摘要提示"""
        prompt_parts = [
            "请为以下对话历史生成简洁摘要。",
            "",
            f"原始任务: {task}",
            ""
        ]

        if historical_highlights:
            prompt_parts.extend([
                "## 历史关键信息（请保留这些信息）:",
                *[f"- {h}" for h in historical_highlights],
                ""
            ])

        prompt_parts.extend([
            "## 当前对话历史:",
            str(content),
            "",
            "请按以下格式输出:",
            "## 摘要",
            "",
            "### 关键决策",
            "- ...",
            "",
            "### 已完成工作",
            "- ...",
            "",
            "### 当前状态",
            "...",
            "",
            "### 遗留问题",
            "- ..."
        ])

        return "\n".join(prompt_parts)

    def compress_history(self, history, summary):
        """压缩历史记录"""
        return [{
            "role": "system",
            "content": f"[对话摘要]\n{summary}",
            "created_at": now()
        }] + history[-self.overlap:]


class ConstraintKeeper:
    """
    约束保留器
    自动识别并永久保留用户在对话中提出的约束条件
    """
    CONSTRAINT_KEYWORDS = {
        "zh": [
            "不能", "不要", "不可", "不允许",
            "必须", "一定要", "务必要",
            "保持", "维持", "不变",
            "禁止", "忌", "不准",
            "只使用", "仅用", "只能",
            "不要改变", "不要修改", "不要删除",
            "保持不变", "维持不变"
        ],
        "en": [
            "must not", "cannot", "should not", "do not", "don't",
            "must", "have to", "need to", "required to",
            "keep", "maintain", "preserve",
            "only use", "use only", "exclusively",
            "don't change", "don't modify", "don't delete",
            "must remain", "must keep"
        ]
    }

    def __init__(self, config=None):
        self.config = (config or {}).get("constraint_keeper", {})
        self.max_constraints = self.config.get("max_constraints", 20)
        self.pinned_constraints = []

    def extract_constraints(self, text):
        """从文本中提取约束"""
        if not self.config.get("enabled", True):
            return []

        constraints = []

        for lang, keywords in self.CONSTRAINT_KEYWORDS.items():
            for keyword in keywords:
                pattern = f".*?{keyword}[^。!?\\n]*[。!?]?"
                matches = re.findall(pattern, text, re.IGNORECASE)

                for match in matches:
                    constraint = self.normalize_constraint(match.strip())
                    if constraint and self.is_valid_constraint(constraint):
                        constraints.append(constraint)

        return self.deduplicate_and_limit(constraints)

    def normalize_constraint(self, text):
        """标准化约束文本"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'^["\'"]|["\'"]$', '', text)
        return text.strip()

    def is_valid_constraint(self, text):
        """验证是否为有效约束"""
        if len(text) < 5 or len(text) > 200:
            return False

        has_keyword = False
        for keywords in self.CONSTRAINT_KEYWORDS.values():
            if any(kw in text.lower() for kw in keywords):
                has_keyword = True
                break

        return has_keyword

    def add_constraints(self, new_constraints):
        """添加新约束到固定列表"""
        for constraint in new_constraints:
            if constraint not in self.pinned_constraints:
                self.pinned_constraints.append(constraint)

        if len(self.pinned_constraints) > self.max_constraints:
            self.pinned_constraints = self.pinned_constraints[-self.max_constraints:]

    def get_constraints_text(self):
        """获取约束文本"""
        if not self.pinned_constraints:
            return ""

        lines = ["[关键约束]", "必须遵守以下约束:"]
        for i, constraint in enumerate(self.pinned_constraints, 1):
            lines.append(f"  {i}. {constraint}")

        return "\n".join(lines)

    def deduplicate_and_limit(self, constraints):
        """去重并限制"""
        seen = set()
        result = []
        for c in constraints:
            normalized = c.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                result.append(c)
        return result[:self.max_constraints]


class ToolOutputCompressor:
    """
    工具输出压缩器
    智能识别并压缩工具输出中的噪音数据
    """
    def __init__(self, config=None):
        self.config = (config or {}).get("tool_compression", {})
        self.max_output_length = self.config.get("max_output_length", 500)
        self.test_output_max = self.config.get("test_output_max", 50)
        self.error_output_max = self.config.get("error_output_max", 300)

        self.compression_stats = {
            "total_compressions": 0,
            "total_original_length": 0,
            "total_compressed_length": 0
        }

    def compress(self, tool_name, output):
        """压缩工具输出"""
        if not self.config.get("enabled", True):
            return output

        if not self.config.get("auto_compress", True):
            return output

        original_length = len(output)

        if tool_name in self.config.get("never_compress_tools", ["read_file"]):
            return output

        if len(output) < self.config.get("threshold_length", 1000):
            return output

        if tool_name == "run_shell":
            compressed = self.compress_shell_output(output)
        elif tool_name == "search":
            compressed = self.compress_search_output(output)
        elif tool_name in ["read_file", "list_files"]:
            compressed = self.compress_file_output(output)
        else:
            compressed = output

        compressed = self.smart_truncate(compressed, self.max_output_length)
        self.update_stats(original_length, len(compressed))

        return compressed

    def compress_shell_output(self, output):
        """压缩 shell 命令输出"""
        if 'test' in output.lower() and ('passed' in output or 'failed' in output):
            return self.compress_test_output(output)

        if any(marker in output for marker in ['[INFO]', '[DEBUG]', '[ERROR]', 'ERROR:']):
            return self.compress_log_output(output)

        return self.compress_repeated_lines(output)

    def compress_test_output(self, text):
        """压缩测试输出"""
        passed_match = re.findall(r'(\d+) passed', text)
        failed_match = re.findall(r'(\d+) failed', text)
        error_match = re.findall(r'(\d+) error', text)

        passed = sum(int(m) for m in passed_match)
        failed = sum(int(m) for m in failed_match)
        errors = sum(int(m) for m in error_match)

        if passed + failed + errors > 10:
            summary = f"[测试统计] passed: {passed}, failed: {failed}, error: {errors}"

            errors_detail = re.findall(
                r'(FAILED|E|ERROR)[^"\']{0,200}',
                text,
                re.MULTILINE
            )

            if errors_detail:
                summary += f"\n\n[关键错误] ({len(errors_detail)} 条)\n"
                for i, error in enumerate(errors_detail[:3], 1):
                    summary += f"{i}. {error[:100]}...\n"
            elif failed == 0 and errors == 0:
                summary += "\n\n[所有测试通过]"

            return summary

        return text

    def compress_log_output(self, text):
        """压缩日志输出"""
        lines = text.split('\n')
        error_lines = []
        warning_lines = []
        info_lines = []

        for line in lines:
            if 'ERROR' in line or 'FAILED' in line:
                error_lines.append(line)
            elif 'WARNING' in line or 'WARN' in line:
                warning_lines.append(line)
            elif 'INFO' in line:
                info_lines.append(line)

        result = []

        if error_lines:
            result.append(f"[ERROR] {len(error_lines)} 条错误:")
            for line in error_lines[:5]:
                result.append(f"  {line[:150]}")

        if warning_lines:
            result.append(f"[WARNING] {len(warning_lines)} 条警告:")
            for line in warning_lines[:3]:
                result.append(f"  {line[:150]}")

        if info_lines:
            result.append(f"[INFO] 共 {len(info_lines)} 条信息 (已省略)")

        return '\n'.join(result) if result else "[日志输出已省略]"

    def compress_repeated_lines(self, text):
        """压缩重复行"""
        lines = text.split('\n')
        compressed = []
        prev_line = None
        count = 0

        for line in lines:
            if line == prev_line:
                count += 1
            else:
                if count > 1:
                    compressed.append(f"[上条内容重复 {count} 次]")
                elif prev_line is not None:
                    compressed.append(prev_line)
                prev_line = line
                count = 1

        if count > 1:
            compressed.append(f"[上条内容重复 {count} 次]")
        elif prev_line is not None:
            compressed.append(prev_line)

        return '\n'.join(compressed)

    def compress_search_output(self, text):
        """压缩搜索输出"""
        lines = text.split('\n')
        if len(lines) > 100:
            return f"[搜索结果] 共 {len(lines)} 行\n" + "\n".join(lines[:20]) + f"\n... 还有 {len(lines) - 20} 行"
        return text

    def compress_file_output(self, text):
        """压缩文件输出"""
        lines = text.split('\n')
        if len(lines) > 100:
            return "\n".join(lines[:50]) + f"\n... 还有 {len(lines) - 50} 行"
        return text

    def smart_truncate(self, text, max_length):
        """智能截断，保留关键信息"""
        if len(text) <= max_length:
            return text

        head_length = int(max_length * 0.7)
        tail_length = max_length - head_length - 10

        head = text[:head_length]
        tail = text[-tail_length:] if tail_length > 0 else ""

        important_keywords = ['error', 'failed', 'exception', 'traceback']
        important_parts = []

        for keyword in important_keywords:
            middle = text[head_length:-tail_length] if tail_length > 0 else text[head_length:]
            matches = re.finditer(keyword, middle, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(middle), match.end() + 50)
                important_parts.append(middle[start:end])

        result = head
        if important_parts:
            result += "\n...[包含关键信息]...\n"
            result += "\n".join(important_parts[:2])
        if tail:
            result += "\n..." + tail

        return result

    def update_stats(self, original, compressed):
        """更新压缩统计"""
        self.compression_stats["total_compressions"] += 1
        self.compression_stats["total_original_length"] += original
        self.compression_stats["total_compressed_length"] += compressed

    def get_compression_ratio(self):
        """获取压缩比"""
        if self.compression_stats["total_original_length"] == 0:
            return 1.0
        return (
            self.compression_stats["total_compressed_length"] /
            self.compression_stats["total_original_length"]
        )


class ToolPairProtector:
    """
    工具调用保护器
    确保工具调用配对不被拆分
    """
    def __init__(self, config=None):
        self.config = (config or {}).get("tool_pair_protection", {})

    def safe_compact_history(self, history, preserve_count):
        """安全压缩历史，确保工具调用配对不被拆分"""
        if not self.config.get("enabled", True):
            return history[-preserve_count:] if len(history) > preserve_count else history

        if len(history) <= preserve_count:
            return history

        to_preserve = history[-preserve_count:]

        if to_preserve[0]["role"] == "tool":
            prev_idx = len(history) - preserve_count - 1
            if prev_idx >= 0:
                prev_msg = history[prev_idx]
                if self.is_matching_tool_use(prev_msg, to_preserve[0]):
                    to_preserve = [prev_msg] + to_preserve

        return to_preserve

    def is_matching_tool_use(self, assistant_msg, tool_result_msg):
        """检查是否是匹配的 tool_use 和 tool_result"""
        if assistant_msg.get("role") != "assistant":
            return False

        content = str(assistant_msg.get("content", ""))

        has_tool_call = "<tool" in content.lower()
        result_name = tool_result_msg.get("name", "")

        return has_tool_call and result_name in content


class ProjectMemoryLoader:
    """
    项目级记忆加载器
    加载 CLAUDE.md、.claw/instructions.md 等项目指令
    """
    def __init__(self, workspace_root, config=None):
        self.workspace_root = Path(workspace_root)
        self.full_config = config or {}
        self.config = self.full_config.get("project_memory", {
            "enabled": True,
            "load_claude_md": True,
            "load_claw_instructions": True,
            "inherit_parent": True,
            "max_instruction_chars": 3000,
        })

    def load_project_instructions(self):
        """加载项目指令"""
        if not self.config.get("enabled", True):
            return {"instructions": "", "paths_checked": []}

        instructions = []
        current = self.workspace_root
        paths_checked = []

        while True:
            paths_checked.append(str(current))

            if self.config.get("load_claude_md", True):
                claude_md = current / "CLAUDE.md"
                if claude_md.exists():
                    content = self._load_instruction_file(claude_md)
                    if content:
                        instructions.append(f"# {claude_md}\n{content}")

                claude_local = current / "CLAUDE.local.md"
                if claude_local.exists():
                    content = self._load_instruction_file(claude_local)
                    if content:
                        instructions.append(f"# {claude_local} (本地)\n{content}")

            if self.config.get("load_claw_instructions", True):
                claw_instructions = current / ".claw" / "instructions.md"
                if claw_instructions.exists():
                    content = self._load_instruction_file(claw_instructions)
                    if content:
                        instructions.append(f"# {claw_instructions}\n{content}")

            parent = current.parent
            if parent == current:
                break
            if not self.config.get("inherit_parent", True):
                break
            current = parent

        return {
            "instructions": "\n\n".join(instructions),
            "paths_checked": paths_checked
        }

    def _load_instruction_file(self, path, max_chars=None):
        """加载指令文件"""
        if max_chars is None:
            max_chars = self.config.get("max_instruction_chars", 3000)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n...[已截断，共 {len(content)} 字符]"
            return content.strip()
        except Exception:
            return None


class SummaryPriorityCompressor:
    """
    优先级摘要压缩器
    按重要性分级压缩摘要内容
    """
    BUDGET = {
        "max_chars": 1200,
        "max_lines": 24,
        "max_line_chars": 160
    }

    def __init__(self, config=None):
        self.config = (config or {}).get("summary_compression", {})
        self.budget = {
            "max_chars": self.config.get("max_chars", 1200),
            "max_lines": self.config.get("max_lines", 24),
            "max_line_chars": self.config.get("max_line_chars", 160)
        }

    def compress(self, text):
        """压缩摘要"""
        lines = text.split('\n')
        result = []

        char_budget = self.budget["max_chars"]
        line_budget = self.budget["max_lines"]

        priority_0 = []
        priority_1 = []
        priority_2 = []
        priority_3 = []

        for line in lines:
            p = self.classify_priority(line)
            if p == 0:
                priority_0.append(line)
            elif p == 1:
                priority_1.append(line)
            elif p == 2:
                priority_2.append(line)
            else:
                priority_3.append(line)

        for priority_lines in [priority_0, priority_1, priority_2, priority_3]:
            for line in priority_lines:
                if len(result) >= line_budget:
                    break
                if len("\n".join(result)) + len(line) > char_budget:
                    break
                result.append(line[:self.budget["max_line_chars"]])

        if len(result) < len(lines):
            result.append(f"[... {len(lines) - len(result)} lines omitted ...]")

        return "\n".join(result)

    def classify_priority(self, line):
        """分类行优先级"""
        stripped = line.strip()

        if stripped.startswith("- ") and ("request" in stripped.lower() or "work" in stripped.lower()):
            return 0

        if stripped.startswith("- "):
            return 1

        if stripped.startswith("#") or stripped.startswith("##"):
            return 2

        return 3


class TaskStateSegmenter:
    """
    任务状态分段器
    识别和管理任务的不同阶段

    基于 Claw Code TaskRegistry 启发:
    - 任务注册表: 完整任务生命周期管理
    - 事件总线: 任务事件通知
    - 上下文分配: 按优先级管理
    """
    PHASES = [
        "task_analysis",
        "planning",
        "implementation",
        "testing",
        "refinement",
        "verification",
        "documentation",
        "completion"
    ]

    TASK_STATUS = {
        "PENDING": "pending",
        "IN_PROGRESS": "in_progress",
        "COMPLETED": "completed",
        "FAILED": "failed"
    }

    TASK_PRIORITY = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    TASK_EVENTS = {
        "CREATED": "TaskCreated",
        "ASSIGNED": "TaskAssigned",
        "COMPLETED": "TaskCompleted",
        "FAILED": "TaskFailed",
        "BLOCKED": "TaskBlocked",
        "RESUMED": "TaskResumed"
    }

    PHASE_KEYWORDS = {
        "task_analysis": ["分析", "理解", "需求", "目标", "分析需求", "理解任务"],
        "planning": ["计划", "规划", "设计方案", "架构", "设计", "方案"],
        "implementation": ["实现", "编写", "创建", "修改", "开发", "编码"],
        "testing": ["测试", "运行测试", "单元测试", "集成测试", "测试用例"],
        "refinement": ["优化", "改进", "完善", "重构", "调整", "修复"],
        "verification": ["验证", "检查", "确认", "通过", "验证通过"],
        "documentation": ["文档", "注释", "说明", "README", "更新文档"],
        "completion": ["完成", "结束", "结束任务", "任务完成"]
    }

    def __init__(self, config=None):
        self.config = (config or {}).get("task_state_segmentation", {})
        self.max_todos = self.config.get("max_todos", 10)
        self.max_phases = self.config.get("max_phases", 10)
        self.max_tasks = self.config.get("max_tasks", 50)

        self.state = {
            "current_phase": "task_analysis",
            "completed_phases": [],
            "phase_history": [],
        }

        self.task_registry = []
        self.event_bus = []
        self.todo_items = []
        self.priority_queue = {k: [] for k in self.TASK_PRIORITY.values()}

    def analyze_and_update(self, user_message, assistant_response, tool_calls):
        """
        分析对话内容，更新任务状态
        """
        changes = []

        phase_change = self.detect_phase_change(user_message, assistant_response)
        if phase_change:
            changes.append(phase_change)
            self.emit_event("phase_transition", {"from": None, "to": self.state["current_phase"]})

        tasks = self.extract_tasks_from_dialog(user_message, assistant_response)
        for task in tasks:
            task_id = self.register_task(task)
            changes.append(f"创建任务: {task['title']}")
            self.emit_event(self.TASK_EVENTS["CREATED"], {"task_id": task_id})

        todos = self.extract_todos(user_message, assistant_response)
        if todos:
            added = self.add_todos(todos)
            changes.extend([f"添加TODO: {t}" for t in added])

        task_updates = self.update_tasks_from_tool_calls(tool_calls)
        for update in task_updates:
            changes.append(update)

        completed = self.mark_completed_todos(tool_calls)
        if completed:
            changes.extend([f"完成TODO: {t}" for t in completed])

        self.update_priority_queue()
        self.update_progress()

        return changes

    def register_task(self, task_info):
        """注册新任务"""
        task_id = len(self.task_registry)
        task = {
            "id": task_id,
            "title": task_info.get("title", ""),
            "description": task_info.get("description", ""),
            "status": task_info.get("status", self.TASK_STATUS["PENDING"]),
            "priority": task_info.get("priority", self.TASK_PRIORITY["MEDIUM"]),
            "dependencies": task_info.get("dependencies", []),
            "created_at": now(),
            "updated_at": now(),
            "completed_at": None,
            "output": None,
            "error": None
        }

        self.task_registry.append(task)

        if len(self.task_registry) > self.max_tasks:
            completed = [t for t in self.task_registry if t["status"] == self.TASK_STATUS["COMPLETED"]]
            if completed:
                self.task_registry.remove(completed[0])

        return task_id

    def update_task_status(self, task_id, new_status, output=None, error=None):
        """更新任务状态"""
        task = self.get_task(task_id)
        if not task:
            return

        old_status = task["status"]
        task["status"] = new_status
        task["updated_at"] = now()

        if new_status == self.TASK_STATUS["COMPLETED"]:
            task["completed_at"] = now()
            task["output"] = output
            self.emit_event(self.TASK_EVENTS["COMPLETED"], {"task_id": task_id, "output": output})

        elif new_status == self.TASK_STATUS["FAILED"]:
            task["error"] = error
            self.emit_event(self.TASK_EVENTS["FAILED"], {"task_id": task_id, "error": error})

        self.check_dependency_unblock(task_id)

    def get_task(self, task_id):
        """获取任务"""
        for task in self.task_registry:
            if task["id"] == task_id:
                return task
        return None

    def check_dependency_unblock(self, task_id):
        """检查依赖任务是否可以解除阻塞"""
        task = self.get_task(task_id)
        if not task:
            return

        for t in self.task_registry:
            if task_id in t.get("dependencies", []):
                all_deps_completed = all(
                    self.get_task(dep_id)["status"] == self.TASK_STATUS["COMPLETED"]
                    for dep_id in t.get("dependencies", [])
                    if self.get_task(dep_id)
                )

                if all_deps_completed and t["status"] == self.TASK_STATUS["PENDING"]:
                    self.emit_event(self.TASK_EVENTS["RESUMED"], {"task_id": t["id"]})

    def emit_event(self, event_type, event_data):
        """发射任务事件"""
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": now()
        }
        self.event_bus.append(event)

        if len(self.event_bus) > 100:
            self.event_bus = self.event_bus[-50:]

    def get_events_by_type(self, event_type, limit=10):
        """获取指定类型的事件"""
        events = [e for e in self.event_bus if e["type"] == event_type]
        return events[-limit:]

    def extract_tasks_from_dialog(self, user_message, response):
        """从对话中提取任务"""
        tasks = []
        combined = f"{user_message} {response}"

        patterns = [
            (r"任务[:：]\s*(.+)", self.TASK_PRIORITY["MEDIUM"]),
            (r"[Tt]ask[:：]\s*(.+)", self.TASK_PRIORITY["MEDIUM"]),
            (r"需要完成[:：]\s*(.+)", self.TASK_PRIORITY["HIGH"]),
            (r"下一步[:：]\s*(.+)", self.TASK_PRIORITY["HIGH"]),
            (r"重要[:：]\s*(.+)", self.TASK_PRIORITY["CRITICAL"]),
            (r"优先[:：]\s*(.+)", self.TASK_PRIORITY["HIGH"]),
        ]

        for pattern, priority in patterns:
            matches = re.findall(pattern, combined)
            for match in matches:
                task_text = match.strip()
                if task_text and len(task_text) > 3:
                    tasks.append({
                        "title": task_text[:100],
                        "description": task_text,
                        "priority": priority,
                        "status": self.TASK_STATUS["PENDING"],
                        "dependencies": []
                    })

        return tasks

    def update_tasks_from_tool_calls(self, tool_calls):
        """基于工具调用更新任务状态"""
        updates = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_result = str(tool_call.get("content", ""))

            if tool_name == "run_shell":
                if "passed" in tool_result.lower() and "failed" not in tool_result.lower():
                    for task in self.task_registry:
                        if task["status"] == self.TASK_STATUS["IN_PROGRESS"]:
                            if "测试" in task["title"] or "test" in task["title"].lower():
                                self.update_task_status(task["id"], self.TASK_STATUS["COMPLETED"], output=tool_result)
                                updates.append(f"任务完成: {task['title']}")

                elif "error" in tool_result.lower() or "failed" in tool_result.lower():
                    for task in self.task_registry:
                        if task["status"] == self.TASK_STATUS["IN_PROGRESS"]:
                            if "实现" in task["title"]:
                                self.update_task_status(task["id"], self.TASK_STATUS["FAILED"], error=tool_result[:200])
                                updates.append(f"任务失败: {task['title']}")

            elif tool_name == "write_file" or tool_name == "patch_file":
                for task in self.task_registry:
                    if task["status"] == self.TASK_STATUS["IN_PROGRESS"]:
                        file_path = tool_call.get("args", {}).get("path", "")
                        if file_path in task.get("description", "") or file_path in task.get("title", ""):
                            self.update_task_status(task["id"], self.TASK_STATUS["COMPLETED"], output=f"文件已更新: {file_path}")
                            updates.append(f"任务完成: {task['title']}")

        return updates

    def update_priority_queue(self):
        """更新优先级队列"""
        self.priority_queue = {k: [] for k in self.TASK_PRIORITY.values()}

        for task in self.task_registry:
            if task["status"] in [self.TASK_STATUS["PENDING"], self.TASK_STATUS["IN_PROGRESS"]]:
                priority = task["priority"]
                self.priority_queue[priority].append(task["id"])

    def get_next_task(self):
        """获取下一个待执行任务"""
        for priority in sorted(self.priority_queue.keys()):
            if self.priority_queue[priority]:
                return self.priority_queue[priority][0]
        return None

    def detect_phase_change(self, user_message, response):
        """检测阶段转换"""
        combined_text = f"{user_message} {response}".lower()

        best_match = None
        best_score = 0

        for phase, keywords in self.PHASE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            if score > best_score:
                best_score = score
                best_match = phase

        if best_match and best_match != self.state["current_phase"] and best_score >= 2:
            old_phase = self.state["current_phase"]

            self.state["completed_phases"].append({
                "phase": old_phase,
                "timestamp": now(),
                "ended_by": best_match
            })

            if len(self.state["completed_phases"]) > self.max_phases:
                self.state["completed_phases"] = self.state["completed_phases"][-self.max_phases:]

            self.state["current_phase"] = best_match

            self.state["phase_history"].append({
                "from": old_phase,
                "to": best_match,
                "timestamp": now()
            })

            return f"阶段转换: {old_phase} -> {best_match}"

        return None

    def extract_todos(self, user_message, response):
        """从对话中提取 TODO 项"""
        todos = []

        patterns = [
            r"[Tt]odo[:：]\s*(.+)",
            r"待做[:：]\s*(.+)",
            r"需要做[:：]\s*(.+)",
            r"下一步[:：]\s*(.+)",
            r"接下来[:：]\s*(.+)",
            r"-\s*\[\s*\]\s*(.+)",
            r"\[\s*\]\s*(.+)",
        ]

        combined = f"{user_message} {response}"

        for pattern in patterns:
            matches = re.findall(pattern, combined)
            for match in matches:
                todo = match.strip()
                if todo and len(todo) > 2 and len(todo) < 200:
                    todos.append(todo)

        return todos

    def add_todos(self, new_todos):
        """添加 TODO 项"""
        added = []
        for todo in new_todos:
            if todo not in self.todo_items:
                self.todo_items.append(todo)
                added.append(todo)

        if len(self.todo_items) > self.max_todos:
            self.todo_items = self.todo_items[-self.max_todos:]

        return added

    def mark_completed_todos(self, tool_calls):
        """标记已完成的 TODO"""
        completed = []

        for todo in self.todo_items[:]:
            todo_lower = todo.lower()

            for tool_call in tool_calls:
                tool_args = str(tool_call.get("args", {})).lower()

                if any(keyword in tool_args for keyword in todo_lower.split()[:3]):
                    completed.append(todo)
                    self.todo_items.remove(todo)
                    break

        return completed

    def update_progress(self):
        """更新进度百分比"""
        total_phases = len(self.PHASES)
        current_index = self.PHASES.index(self.state["current_phase"])

        total_tasks = len(self.task_registry)
        completed_tasks = sum(
            1 for t in self.task_registry
            if t["status"] == self.TASK_STATUS["COMPLETED"]
        )

        return {
            "current_phase": self.state["current_phase"],
            "phase_progress_percent": int((current_index / total_phases) * 100),
            "completed_phases": len(self.state["completed_phases"]),
            "total_phases": total_phases,
            "task_completion_rate": int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks,
            "pending_todos": len(self.todo_items)
        }

    def get_state_text(self):
        """获取状态文本"""
        lines = []

        lines.append(f"[当前阶段] {self.state['current_phase']}")

        progress = self.update_progress()
        lines.append(f"[阶段进度] {progress['phase_progress_percent']}%")
        lines.append(f"[任务进度] {progress['task_completion_rate']}% ({progress['completed_tasks']}/{progress['total_tasks']})")

        if self.state["completed_phases"]:
            phases = [p["phase"] for p in self.state["completed_phases"][-3:]]
            lines.append(f"[已完成阶段] {' -> '.join(phases)}")

        active_tasks = [t for t in self.task_registry if t["status"] in [self.TASK_STATUS["IN_PROGRESS"], self.TASK_STATUS["PENDING"]]]
        if active_tasks:
            lines.append(f"[活跃任务] ({len(active_tasks)} 个)")
            for task in active_tasks[:3]:
                status_icon = "🔄" if task["status"] == self.TASK_STATUS["IN_PROGRESS"] else "⏳"
                lines.append(f"  {status_icon} {task['title'][:50]}")
            if len(active_tasks) > 3:
                lines.append(f"  ... 还有 {len(active_tasks) - 3} 个任务")

        if self.todo_items:
            lines.append(f"[待办] ({len(self.todo_items)} 项)")
            for i, todo in enumerate(self.todo_items[:5], 1):
                lines.append(f"  {i}. {todo[:50]}")
            if len(self.todo_items) > 5:
                lines.append(f"  ... 还有 {len(self.todo_items) - 5} 项")

        recent_events = self.event_bus[-3:]
        if recent_events:
            lines.append("[最近事件]")
            for event in recent_events:
                lines.append(f"  - {event['type']}")

        return "\n".join(lines)

    def get_task_summary(self):
        """获取任务摘要"""
        total = len(self.task_registry)
        completed = sum(1 for t in self.task_registry if t["status"] == self.TASK_STATUS["COMPLETED"])
        failed = sum(1 for t in self.task_registry if t["status"] == self.TASK_STATUS["FAILED"])

        summary_parts = [f"任务: {completed}/{total} 完成, {failed} 失败"]
        summary_parts.append(f"阶段: {self.state['current_phase']}")

        if self.todo_items:
            summary_parts.append(f"待办: {len(self.todo_items)} 项")

        return " | ".join(summary_parts)

    def serialize(self):
        """序列化状态"""
        return {
            "state": self.state,
            "task_registry": self.task_registry,
            "event_bus": self.event_bus,
            "todo_items": self.todo_items,
            "priority_queue": self.priority_queue
        }

    @classmethod
    def deserialize(cls, data):
        """反序列化状态"""
        segmenter = cls()
        segmenter.state = data.get("state", segmenter.state)
        segmenter.task_registry = data.get("task_registry", [])
        segmenter.event_bus = data.get("event_bus", [])
        segmenter.todo_items = data.get("todo_items", [])
        segmenter.priority_queue = data.get("priority_queue", {k: [] for k in cls.TASK_PRIORITY.values()})
        return segmenter


class MemoryManager:
    """
    Memory Manager 主类
    整合所有 8 个组件
    """
    def __init__(self, model_client, workspace_root, config=None):
        self.config = config or DEFAULT_MEMORY_MANAGER_CONFIG.copy()
        self.model_client = model_client
        self.workspace_root = workspace_root

        self.trigger_manager = TriggerManager(self.config)
        self.constraint_keeper = ConstraintKeeper(self.config)
        self.tool_output_compressor = ToolOutputCompressor(self.config)
        self.tool_pair_protector = ToolPairProtector(self.config)
        self.rolling_summary = IncrementalRollingSummary(model_client, self.config)
        self.task_state_segmenter = TaskStateSegmenter(self.config)
        self.project_memory_loader = ProjectMemoryLoader(workspace_root, self.config)
        self.summary_priority_compressor = SummaryPriorityCompressor(self.config)

        self.project_instructions = self.project_memory_loader.load_project_instructions()
        self.summary = ""
        self.total_tokens_saved = 0

    def process_user_message(self, user_message):
        """处理用户消息，提取约束"""
        if self.config.get("constraint_keeper", {}).get("enabled", True):
            new_constraints = self.constraint_keeper.extract_constraints(user_message)
            if new_constraints:
                self.constraint_keeper.add_constraints(new_constraints)

    def process_assistant_response(self, assistant_response):
        """处理助手响应"""
        pass

    def process_tool_result(self, tool_name, tool_args, tool_result):
        """处理工具结果，压缩输出"""
        compressed_result = self.tool_output_compressor.compress(tool_name, tool_result)
        return compressed_result

    def process_round(self, user_message, assistant_response, tool_calls):
        """处理一轮对话"""
        self.process_user_message(user_message)

        changes = []
        if self.config.get("task_state_segmentation", {}).get("enabled", True):
            changes = self.task_state_segmenter.analyze_and_update(
                user_message, assistant_response, tool_calls
            )

        return changes

    def should_compact(self, history, estimated_tokens=None):
        """判断是否需要压缩"""
        return self.trigger_manager.should_compact(history, estimated_tokens)

    def compact_history(self, history):
        """压缩历史记录"""
        preserve_count = self.trigger_manager.get_preserve_count(history)

        safe_history = self.tool_pair_protector.safe_compact_history(history, preserve_count)

        task = self._get_current_task(history)
        new_summary = self.rolling_summary.generate_summary(history, task)

        if new_summary:
            self.summary = new_summary
            compressed = self.rolling_summary.compress_history(history, new_summary)
        else:
            compressed = safe_history

        tokens_saved = sum(
            len(str(item.get("content", "")))
            for item in history[:-preserve_count]
        )
        self.total_tokens_saved += tokens_saved

        return compressed

    def _get_current_task(self, history):
        """获取当前任务描述"""
        for item in reversed(history):
            if item.get("role") == "user":
                return str(item.get("content", ""))[:300]
        return ""

    def build_memory_text(self):
        """构建增强的 memory 文本"""
        parts = []

        if self.project_instructions["instructions"]:
            parts.append("[项目指令]")
            parts.append(self.project_instructions["instructions"][:1000])
            parts.append("")

        constraints_text = self.constraint_keeper.get_constraints_text()
        if constraints_text:
            parts.append(constraints_text)
            parts.append("")

        if self.summary:
            compressed_summary = self.summary_priority_compressor.compress(self.summary)
            parts.append("[对话摘要]")
            parts.append(compressed_summary)
            parts.append("")

        if self.config.get("task_state_segmentation", {}).get("enabled", True):
            task_summary = self.task_state_segmenter.get_task_summary()
            if task_summary:
                parts.append(f"[任务状态] {task_summary}")
                parts.append("")

        return "\n".join(parts)

    def get_stats(self):
        """获取统计信息"""
        return {
            "total_tokens_saved": self.total_tokens_saved,
            "compression_ratio": self.tool_output_compressor.get_compression_ratio(),
            "constraints_count": len(self.constraint_keeper.pinned_constraints),
            "summary_history_count": len(self.rolling_summary.summary_history),
            "task_registry_count": len(self.task_state_segmenter.task_registry),
            "current_phase": self.task_state_segmenter.state["current_phase"],
        }

    def serialize(self):
        """序列化状态"""
        return {
            "config": self.config,
            "summary": self.summary,
            "total_tokens_saved": self.total_tokens_saved,
            "constraint_keeper": {
                "pinned_constraints": self.constraint_keeper.pinned_constraints,
            },
            "rolling_summary": {
                "summary_history": self.rolling_summary.summary_history,
            },
            "task_state_segmenter": self.task_state_segmenter.serialize(),
        }

    def deserialize(self, data):
        """反序列化状态"""
        self.summary = data.get("summary", "")
        self.total_tokens_saved = data.get("total_tokens_saved", 0)

        constraint_data = data.get("constraint_keeper", {})
        self.constraint_keeper.pinned_constraints = constraint_data.get("pinned_constraints", [])

        rolling_data = data.get("rolling_summary", {})
        self.rolling_summary.summary_history = rolling_data.get("summary_history", [])

        if "task_state_segmenter" in data:
            self.task_state_segmenter = TaskStateSegmenter.deserialize(data["task_state_segmenter"])

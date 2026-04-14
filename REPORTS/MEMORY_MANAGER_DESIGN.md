# Mini-Coding-Agent Memory Manager 完整设计文档

> **版本**: 2.1 (完整版 - 4个功能全部实现)
> **日期**: 2025-01-27
> **状态**: 已完成设计，待实现
> **参考设计**: Claw Code Memory System

---

## 目录

1. [项目概述](#1-项目概述)
2. [代码分析](#2-代码分析)
3. [功能选择](#3-功能选择)
4. [架构设计](#4-架构设计)
5. [组件详细设计](#5-组件详细设计)
6. [配置参数](#6-配置参数)
7. [实施计划](#7-实施计划)
8. [测试验证](#8-测试验证)
9. [风险与兼容性](#9-风险与兼容性)

---

## 1. 项目概述

### 1.1 目标

为 Mini-Coding-Agent 实现 Memory Manager 优化方案，解决长对话场景下的上下文爆炸问题，提升关键约束保留率和工具输出压缩效果。

### 1.2 核心指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| History Token 消耗 | 100% | < 60% |
| 约束保留率 | < 50% | > 90% |
| 工具输出压缩率 | 1.0 | < 0.6 |
| 摘要生成延迟 | N/A | < 2s |

### 1.3 参考项目

本设计参考了 Claw Code 的多层记忆系统，融合了以下核心思想：

- **层级分离**: 短期会话记忆与长期项目记忆分离
- **增量压缩**: 模拟人类记忆模式，早期信息通过摘要保留
- **Token 感知**: 基于消息长度的动态压缩触发
- **优先级压缩**: 保留关键信息，压缩次要内容

---

## 2. 代码分析

### 2.1 现有架构概述

Mini-Coding-Agent 的核心代码包含六大组件：

```
1) Live Repo Context -> WorkspaceContext
2) Prompt Shape And Cache Reuse -> build_prefix, memory_text, prompt
3) Structured Tools, Validation, And Permissions -> build_tools, run_tool, validate_tool
4) Context Reduction And Output Management -> clip, history_text
5) Transcripts, Memory, And Resumption -> SessionStore, record, note_tool, ask, reset
6) Delegation And Bounded Subagents -> tool_delegate
```

### 2.2 现有 Memory 机制

**Session Memory 结构**:
```python
self.session["memory"] = {
    "task": "",      # 任务描述 (截断至300字符)
    "files": [],     # 最近访问的文件列表 (最多8个)
    "notes": [],      # 笔记列表 (最多5个)
}
```

**现有局限性**:

| 限制点 | 描述 | 影响 |
|--------|------|------|
| **容量固定** | files 最多8个，notes 最多5个 | 长对话场景下关键信息可能丢失 |
| **无压缩** | notes 直接存储原始摘要 | token 消耗大 |
| **无约束保留** | 没有专门机制保留用户约束 | 约束容易被遗忘 |
| **无阶段感知** | 所有历史同等对待 | 无法识别工作阶段 |
| **无智能筛选** | 所有工具调用同等记录 | 噪音数据过多 |

### 2.3 Transcript 处理流程

**history_text() 裁剪策略**:

| 策略 | 近期记录 (最后6条) | 历史记录 |
|------|-------------------|----------|
| 工具输出 | 900 字符 | 180 字符 |
| 对话内容 | 900 字符 | 220 字符 |
| 读取去重 | 无 | 同一文件只保留最后一次读取 |
| 全局截断 | 12000 字符上限 | 12000 字符上限 |

### 2.4 关键修改位置

| 序号 | 位置 | 类/方法 | 建议修改 |
|------|------|---------|---------|
| **M1** | Line 249-255 | `MiniAgent.__init__()` | 扩展 session["memory"] 结构 |
| **M2** | Line 376-385 | `memory_text()` | 增强 memory 格式，支持分层展示 |
| **M3** | Line 390-417 | `history_text()` | 添加智能压缩逻辑 |
| **M4** | Line 437-443 | `note_tool()` | 添加约束识别和保留机制 |
| **M5** | Line 445-491 | `ask()` | 添加滚动摘要触发逻辑 |

---

## 3. 功能选择

### 3.1 全部 4 个功能 ✅

| 功能 | 优先级 | 原因 |
|------|--------|------|
| **Rolling Summary** | P0 | 解决长对话上下文爆炸问题 |
| **Pinned Facts / Constraints** | P0 | 确保用户约束不被遗忘 |
| **Tool Output Compression** | P0 | 减少噪音数据对上下文的污染 |
| **Task-State Segmentation** | P0 | 识别和管理任务阶段状态 ✅ 新增 |

### 3.2 基于 Claw Code 的增强

| 增强项 | 来源 | 优先级 |
|--------|------|--------|
| **Token 感知触发** | Claw Code | P0 |
| **增量压缩** | Claw Code | P0 |
| **工具调用配对保护** | Claw Code | P0 |
| **项目级记忆** | Claw Code | P1 |
| **优先级摘要压缩** | Claw Code | P1 |
| **指纹缓存** | Claw Code | P2 |

---

## 4. 架构设计

### 4.1 Memory 分层结构

```
Memory (增强版6层架构)
├── Layer 0: Project Memory
│   ├── CLAUDE.md (项目根级指令)
│   ├── CLAUDE.local.md (本地覆盖)
│   └── .claw/instructions.md
│
├── Layer 1: Pinned Layer (永久层)
│   ├── constraints (关键约束)
│   ├── original_task (原始任务)
│   └── important_decisions (关键决策)
│
├── Layer 2: Summary Layer (摘要层)
│   ├── current_summary (当前摘要)
│   ├── summary_history[] (历史摘要)
│   └── highlights[] (关键信息提取)
│
├── Layer 3: Task State Layer (任务状态层) ← 新增
│   ├── current_phase (当前阶段)
│   ├── completed_phases[] (已完成阶段)
│   └── todo_items[] (待办事项)
│
├── Layer 4: Working Layer (工作层)
│   ├── files (最近文件)
│   ├── notes (笔记)
│   └── recent_history (未压缩的历史)
│
└── Layer 5: Cache Layer (可选)
    └── prompt_cache (指纹缓存)
```

### 4.2 组件架构

```
MemoryManager
├── TriggerManager (智能触发)
│   ├── 固定轮数触发
│   ├── Token 阈值触发
│   └── 强制压缩触发
│
├── IncrementalRollingSummary (增量滚动摘要)
│   ├── 历史摘要管理
│   ├── 关键信息提取
│   └── 摘要生成
│
├── ConstraintKeeper (约束保留)
│   ├── 中英文关键词识别
│   ├── 约束提取与标准化
│   └── 持久化存储
│
├── ToolOutputCompressor (工具输出压缩)
│   ├── 测试输出压缩
│   ├── 日志压缩
│   ├── 重复行压缩
│   └── 智能截断
│
├── TaskStateSegmenter (任务状态分段器) ← 新增
│   ├── 阶段识别
│   ├── 阶段转换检测
│   ├── TODO 列表管理
│   └── 进度追踪
│
├── ProjectMemoryLoader (项目级记忆)
│   ├── CLAUDE.md 加载
│   └── 指令继承
│
├── SummaryPriorityCompressor (优先级压缩)
│   ├── 4级优先级分类
│   └── 预算约束压缩
│
└── ToolPairProtector (工具调用保护)
    ├── 配对检测
    └── 安全压缩
```

### 4.3 数据流架构

```
User Input
    ↓
┌─────────────────────────────────────────────────────┐
│            ConstraintKeeper.extract()               │
│         (检查是否包含约束 -> Pinned Layer)           │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│              TriggerManager.check()                 │
│         (检查是否需要摘要/压缩 -> Summary Layer)    │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│           ToolOutputCompressor.compress()           │
│         (工具输出 -> Working Layer)                 │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│           ProjectMemoryLoader.load()                │
│         (项目指令 -> Layer 0)                       │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│           IncrementalRollingSummary                 │
│         (历史摘要管理 -> Summary Layer)              │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                    Prompt Generation                 │
│     memory_text() -> 构建包含所有层级的 memory       │
└─────────────────────────────────────────────────────┘
```

---

## 5. 组件详细设计

### 5.1 TriggerManager (智能触发管理器)

**功能**: 智能判断何时触发压缩和摘要操作

```python
class TriggerManager:
    """
    智能触发管理器
    结合固定轮数 + Token 感知 + 强制压缩
    """
    def __init__(self, config=None):
        self.config = config or {}
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
        # 方式1: 固定轮数触发
        if len(messages) >= self.fixed_step_trigger:
            return True, "fixed_step"

        # 方式2: Token 阈值触发
        if estimated_tokens and estimated_tokens >= self.token_threshold:
            if len(messages) - self.preserve_count > self.preserve_count:
                return True, "token_threshold"

        # 方式3: 强制压缩
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
            return 6  # 更长会话保留更多
        return self.preserve_count
```

### 5.2 IncrementalRollingSummary (增量滚动摘要)

**功能**: 生成对话摘要，保留历史关键信息

```python
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
        self.config = config or {}
        self.max_history = self.config.get("max_summary_history", 5)
        self.overlap = self.config.get("overlap_steps", 5)
        self.summary_history = []

    def should_summarize(self, history):
        """判断是否需要摘要"""
        return len(history) >= self.config.get("trigger_steps", 30)

    def generate_summary(self, history, task):
        """生成摘要（包含历史上下文）"""
        # 1. 提取历史摘要中的关键信息
        historical_highlights = self.extract_highlights_from_history()

        # 2. 对当前消息生成摘要
        content_to_summarize = history[:-self.overlap]

        # 3. 构建增强的摘要提示
        prompt = self.build_enhanced_prompt(
            content_to_summarize,
            task,
            historical_highlights
        )

        # 4. 调用 LLM
        summary = self.model_client.complete(prompt, max_new_tokens=300)

        # 5. 保存到历史
        self.summary_history.append({
            "summary": summary,
            "step": len(history),
            "timestamp": now()
        })

        # 6. 限制历史长度
        if len(self.summary_history) > self.max_history:
            self.summary_history = self.summary_history[-self.max_history:]

        return summary

    def extract_highlights_from_history(self):
        """从历史摘要中提取关键信息"""
        highlights = []
        for entry in self.summary_history[-3:]:
            extracted = self.extract_key_points(entry["summary"])
            highlights.extend(extracted)
        return highlights[:20]

    def extract_key_points(self, summary_text):
        """从摘要中提取关键点"""
        # 提取 "关键决策"、"重要变更" 等部分
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
            content,
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
```

### 5.3 ConstraintKeeper (约束保留器)

**功能**: 自动识别并永久保留用户约束

```python
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
        self.config = config or {}
        self.max_constraints = self.config.get("max_constraints", 20)
        self.pinned_constraints = []

    def extract_constraints(self, text):
        """从文本中提取约束"""
        constraints = []

        for lang, keywords in self.CONSTRAINT_KEYWORDS.items():
            for keyword in keywords:
                pattern = f".*?{keyword}[^。!?\n]*[。!?]?"
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
```

### 5.4 ToolOutputCompressor (工具输出压缩器)

**功能**: 智能压缩工具输出中的噪音数据

```python
class ToolOutputCompressor:
    """
    工具输出压缩器
    智能识别并压缩工具输出中的噪音数据
    """
    def __init__(self, config=None):
        self.config = config or {}
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
        original_length = len(output)

        # 1. 根据工具类型选择压缩策略
        if tool_name == "run_shell":
            compressed = self.compress_shell_output(output)
        elif tool_name == "search":
            compressed = self.compress_search_output(output)
        elif tool_name in ["read_file", "list_files"]:
            compressed = self.compress_file_output(output)
        else:
            compressed = output

        # 2. 应用最大长度限制
        compressed = self.smart_truncate(compressed, self.max_output_length)

        # 3. 更新统计
        self.update_stats(original_length, len(compressed))

        return compressed

    def compress_shell_output(self, output):
        """压缩 shell 命令输出"""
        # 检测是否为测试输出
        if 'test' in output.lower() and ('passed' in output or 'failed' in output):
            return self.compress_test_output(output)

        # 检测是否为日志输出
        if any(marker in output for marker in ['[INFO]', '[DEBUG]', '[ERROR]', 'ERROR:']):
            return self.compress_log_output(output)

        # 默认压缩重复内容
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

    def smart_truncate(self, text, max_length):
        """智能截断，保留关键信息"""
        if len(text) <= max_length:
            return text

        head_length = int(max_length * 0.7)
        tail_length = max_length - head_length - 10

        head = text[:head_length]
        tail = text[-tail_length:] if tail_length > 0 else ""
        middle = text[head_length:-tail_length] if tail_length > 0 else text[head_length:]

        important_keywords = ['error', 'failed', 'exception', 'traceback']
        important_parts = []

        for keyword in important_keywords:
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
```

### 5.5 ToolPairProtector (工具调用保护器)

**功能**: 确保 tool_use 和 tool_result 配对不被拆分

```python
class ToolPairProtector:
    """
    工具调用保护器
    确保工具调用配对不被拆分
    """
    def __init__(self, config=None):
        self.config = config or {}

    def safe_compact_history(self, history, preserve_count):
        """安全压缩历史，确保工具调用配对不被拆分"""
        if len(history) <= preserve_count:
            return history

        to_preserve = history[-preserve_count:]

        # 检查是否需要回退
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

        # 检查是否有 tool 标签
        has_tool_call = "<tool" in content.lower()

        # 检查工具结果中是否有对应的工具名
        result_name = tool_result_msg.get("name", "")

        return has_tool_call and result_name in content
```

### 5.6 ProjectMemoryLoader (项目级记忆加载器)

**功能**: 加载项目级指令文件

```python
class ProjectMemoryLoader:
    """
    项目级记忆加载器
    加载 CLAUDE.md、.claw/instructions.md 等项目指令
    """
    def __init__(self, workspace_root, config=None):
        self.workspace_root = Path(workspace_root)
        self.config = config or {}

    def load_project_instructions(self):
        """加载项目指令"""
        instructions = []

        # 从根目录到当前目录，累积加载
        current = self.workspace_root
        paths_checked = []

        while True:
            paths_checked.append(str(current))

            # 查找 CLAUDE.md
            claude_md = current / "CLAUDE.md"
            if claude_md.exists():
                content = self._load_instruction_file(claude_md)
                if content:
                    instructions.append(f"# {claude_md}\n{content}")

            # 查找 .claw/instructions.md
            claw_instructions = current / ".claw" / "instructions.md"
            if claw_instructions.exists():
                content = self._load_instruction_file(claw_instructions)
                if content:
                    instructions.append(f"# {claw_instructions}\n{content}")

            # 查找 CLAUDE.local.md (不提交到 git 的本地指令)
            claude_local = current / "CLAUDE.local.md"
            if claude_local.exists():
                content = self._load_instruction_file(claude_local)
                if content:
                    instructions.append(f"# {claude_local} (本地)\n{content}")

            # 移动到父目录
            parent = current.parent
            if parent == current:  # 到达根
                break
            current = parent

        return {
            "instructions": "\n\n".join(instructions),
            "paths_checked": paths_checked
        }

    def _load_instruction_file(self, path, max_chars=3000):
        """加载指令文件"""
        try:
            content = path.read_text(encoding="utf-8")
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n...[已截断，共 {len(content)} 字符]"
            return content.strip()
        except Exception:
            return None
```

### 5.7 SummaryPriorityCompressor (优先级摘要压缩器)

**功能**: 按优先级压缩摘要内容

```python
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

    def compress(self, text):
        """压缩摘要"""
        lines = text.split('\n')
        budget = self.BUDGET.copy()
        result = []

        char_budget = budget["max_chars"]
        line_budget = budget["max_lines"]

        # 优先级分组
        priority_0 = []  # 最高：用户请求和待办
        priority_1 = []  # 用户请求
        priority_2 = []  # 标题和结构
        priority_3 = []  # 其他

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

        # 按优先级添加
        for priority_lines in [priority_0, priority_1, priority_2, priority_3]:
            for line in priority_lines:
                if len(result) >= line_budget:
                    break
                if len("\n".join(result)) + len(line) > char_budget:
                    break
                result.append(line[:budget["max_line_chars"]])

        # 如果有省略，添加提示
        if len(result) < len(lines):
            result.append(f"[... {len(lines) - len(result)} lines omitted ...]")

        return "\n".join(result)

    def classify_priority(self, line):
        """分类行优先级"""
        stripped = line.strip()

        # 优先级 0：包含 "request" 或 "work" 的列表项
        if stripped.startswith("- ") and ("request" in stripped.lower() or "work" in stripped.lower()):
            return 0

        # 优先级 1：列表项
        if stripped.startswith("- "):
            return 1

        # 优先级 2：标题
        if stripped.startswith("#") or stripped.startswith("##"):
            return 2

        # 优先级 3：其他
        return 3
```

### 5.8 TaskStateSegmenter (任务状态分段器) ← 新增

**功能**: 识别和管理任务的不同阶段，支持任务注册表、事件总线和进度追踪

**灵感来源**: 融合 Claw Code 的 TaskRegistry 设计，支持完整的任务生命周期管理

```python
class TaskStateSegmenter:
    """
    任务状态分段器
    识别和管理任务的不同阶段

    基于 Claw Code TaskRegistry 启发:
    - 任务注册表: 完整任务生命周期管理
    - 事件总线: 任务事件通知
    - 上下文分配: 按优先级管理
    """
    # 预定义阶段
    PHASES = [
        "task_analysis",     # 任务分析
        "planning",           # 规划
        "implementation",     # 实现
        "testing",           # 测试
        "refinement",        # 优化
        "verification",       # 验证
        "documentation",     # 文档
        "completion"          # 完成
    ]

    # 任务状态枚举 (基于 Claw Code)
    TASK_STATUS = {
        "PENDING": "pending",      # 待处理
        "IN_PROGRESS": "in_progress",  # 进行中
        "COMPLETED": "completed",  # 已完成
        "FAILED": "failed"         # 失败
    }

    # 任务优先级 (基于上下文分配策略)
    TASK_PRIORITY = {
        "CRITICAL": 0,   # 关键任务
        "HIGH": 1,       # 高优先级
        "MEDIUM": 2,     # 中优先级
        "LOW": 3         # 低优先级
    }

    # 任务事件类型 (基于 Claw Code 事件总线)
    TASK_EVENTS = {
        "CREATED": "TaskCreated",
        "ASSIGNED": "TaskAssigned",
        "COMPLETED": "TaskCompleted",
        "FAILED": "TaskFailed",
        "BLOCKED": "TaskBlocked",
        "RESUMED": "TaskResumed"
    }

    # 阶段转换关键词
    PHASE_KEYWORDS = {
        "task_analysis": [
            "分析", "理解", "需求", "目标", "分析需求", "理解任务"
        ],
        "planning": [
            "计划", "规划", "设计方案", "架构", "设计", "方案"
        ],
        "implementation": [
            "实现", "编写", "创建", "修改", "开发", "编码"
        ],
        "testing": [
            "测试", "运行测试", "单元测试", "集成测试", "测试用例"
        ],
        "refinement": [
            "优化", "改进", "完善", "重构", "调整", "修复"
        ],
        "verification": [
            "验证", "检查", "确认", "通过", "验证通过"
        ],
        "documentation": [
            "文档", "注释", "说明", "README", "更新文档"
        ],
        "completion": [
            "完成", "结束", "结束任务", "任务完成"
        ]
    }

    def __init__(self, config=None):
        self.config = config or {}
        self.max_todos = self.config.get("max_todos", 10)
        self.max_phases = self.config.get("max_phases", 10)
        self.max_tasks = self.config.get("max_tasks", 50)  # 任务注册表大小

        # 主状态
        self.state = {
            "current_phase": "task_analysis",
            "completed_phases": [],
            "phase_history": [],
        }

        # 任务注册表 (基于 Claw Code TaskRegistry)
        self.task_registry = []

        # 任务事件总线 (基于 Claw Code Event Bus)
        self.event_bus = []

        # TODO 项 (简化版)
        self.todo_items = []

        # 优先级队列 (基于上下文分配策略)
        self.priority_queue = {k: [] for k in self.TASK_PRIORITY.values()}

    def analyze_and_update(self, user_message, assistant_response, tool_calls):
        """
        分析对话内容，更新任务状态

        Args:
            user_message: 用户消息
            assistant_response: 助手回复
            tool_calls: 工具调用列表

        Returns:
            更新后的状态变化描述
        """
        changes = []

        # 1. 检测阶段转换
        phase_change = self.detect_phase_change(user_message, assistant_response)
        if phase_change:
            changes.append(phase_change)
            self.emit_event("phase_transition", {"from": None, "to": self.state["current_phase"]})

        # 2. 从对话中提取并注册任务
        tasks = self.extract_tasks_from_dialog(user_message, assistant_response)
        for task in tasks:
            task_id = self.register_task(task)
            changes.append(f"创建任务: {task['title']}")
            self.emit_event(self.TASK_EVENTS["CREATED"], {"task_id": task_id})

        # 3. 提取 TODO 项
        todos = self.extract_todos(user_message, assistant_response)
        if todos:
            added = self.add_todos(todos)
            changes.extend([f"添加TODO: {t}" for t in added])

        # 4. 基于工具调用更新任务状态
        task_updates = self.update_tasks_from_tool_calls(tool_calls)
        for update in task_updates:
            changes.append(update)

        # 5. 标记完成的 TODO
        completed = self.mark_completed_todos(tool_calls)
        if completed:
            changes.extend([f"完成TODO: {t}" for t in completed])

        # 6. 更新优先级队列
        self.update_priority_queue()

        # 7. 更新进度
        self.update_progress()

        return changes

    def register_task(self, task_info):
        """
        注册新任务 (基于 Claw Code TaskRegistry)

        Args:
            task_info: {
                "title": str,           # 任务标题
                "description": str,      # 任务描述
                "priority": int,         # 优先级 (0-3)
                "dependencies": list,    # 依赖任务ID列表
                "status": str           # 状态
            }

        Returns:
            task_id: 新任务的唯一标识
        """
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
            "output": None,  # 任务输出/结果
            "error": None    # 错误信息
        }

        self.task_registry.append(task)

        # 限制注册表大小
        if len(self.task_registry) > self.max_tasks:
            # 移除已完成的旧任务
            completed = [t for t in self.task_registry if t["status"] == self.TASK_STATUS["COMPLETED"]]
            if completed:
                self.task_registry.remove(completed[0])

        return task_id

    def update_task_status(self, task_id, new_status, output=None, error=None):
        """
        更新任务状态 (基于 Claw Code 事件)

        Args:
            task_id: 任务ID
            new_status: 新状态
            output: 任务输出 (可选)
            error: 错误信息 (可选)
        """
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

        # 检查依赖任务
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
                # 检查所有依赖是否完成
                all_deps_completed = all(
                    self.get_task(dep_id)["status"] == self.TASK_STATUS["COMPLETED"]
                    for dep_id in t.get("dependencies", [])
                    if self.get_task(dep_id)
                )

                if all_deps_completed and t["status"] == self.TASK_STATUS["PENDING"]:
                    # 解除阻塞，变为可执行
                    self.emit_event(self.TASK_EVENTS["RESUMED"], {"task_id": t["id"]})

    def emit_event(self, event_type, event_data):
        """
        发射任务事件 (基于 Claw Code Event Bus)

        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": now()
        }
        self.event_bus.append(event)

        # 限制事件总线大小
        if len(self.event_bus) > 100:
            self.event_bus = self.event_bus[-50:]

    def get_events_by_type(self, event_type, limit=10):
        """获取指定类型的事件"""
        events = [e for e in self.event_bus if e["type"] == event_type]
        return events[-limit:]

    def extract_tasks_from_dialog(self, user_message, response):
        """
        从对话中提取任务

        基于 Claw Code 的任务识别模式
        """
        tasks = []
        combined = f"{user_message} {response}"

        # 任务提取模式
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
        """
        基于工具调用更新任务状态

        基于 Claw Code 的工具输出解析
        """
        updates = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_result = str(tool_call.get("content", ""))

            # 测试成功 -> 标记相关测试任务完成
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
                            if "实现" in task["title"] or "实现" in task["title"]:
                                self.update_task_status(task["id"], self.TASK_STATUS["FAILED"], error=tool_result[:200])
                                updates.append(f"任务失败: {task['title']}")

            # 文件写入成功 -> 标记相关实现任务完成
            elif tool_name == "write_file" or tool_name == "patch_file":
                for task in self.task_registry:
                    if task["status"] == self.TASK_STATUS["IN_PROGRESS"]:
                        file_path = tool_call.get("args", {}).get("path", "")
                        if file_path in task.get("description", "") or file_path in task.get("title", ""):
                            self.update_task_status(task["id"], self.TASK_STATUS["COMPLETED"], output=f"文件已更新: {file_path}")
                            updates.append(f"任务完成: {task['title']}")

        return updates

    def update_priority_queue(self):
        """
        更新优先级队列 (基于 Claw Code 上下文分配策略)

        高优先级任务优先处理
        """
        self.priority_queue = {k: [] for k in self.TASK_PRIORITY.values()}

        for task in self.task_registry:
            if task["status"] in [self.TASK_STATUS["PENDING"], self.TASK_STATUS["IN_PROGRESS"]]:
                priority = task["priority"]
                self.priority_queue[priority].append(task["id"])

    def get_next_task(self):
        """
        获取下一个待执行任务 (基于优先级)

        Returns:
            task_id or None
        """
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
            r"-\s*\[ \]\s*(.+)",
            r"\[ \]\s*(.+)",
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

        # 计算任务完成率
        total_tasks = len(self.task_registry)
        completed_tasks = sum(
            1 for t in self.task_registry
            if t["status"] == self.TASK_STATUS["COMPLETED"]
        )

        progress = {
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

        return progress

    def get_state_text(self):
        """获取状态文本"""
        lines = []

        # 当前阶段
        lines.append(f"[当前阶段] {self.state['current_phase']}")

        # 进度
        progress = self.update_progress()
        lines.append(f"[阶段进度] {progress['phase_progress_percent']}%")
        lines.append(f"[任务进度] {progress['task_completion_rate']}% ({progress['completed_tasks']}/{progress['total_tasks']})")

        # 已完成阶段
        if self.state["completed_phases"]:
            phases = [p["phase"] for p in self.state["completed_phases"][-3:]]
            lines.append(f"[已完成阶段] {' -> '.join(phases)}")

        # 活跃任务
        active_tasks = [t for t in self.task_registry if t["status"] in [self.TASK_STATUS["IN_PROGRESS"], self.TASK_STATUS["PENDING"]]]
        if active_tasks:
            lines.append(f"[活跃任务] ({len(active_tasks)} 个)")
            for task in active_tasks[:3]:
                status_icon = "🔄" if task["status"] == self.TASK_STATUS["IN_PROGRESS"] else "⏳"
                lines.append(f"  {status_icon} {task['title'][:50]}")
            if len(active_tasks) > 3:
                lines.append(f"  ... 还有 {len(active_tasks) - 3} 个任务")

        # 待办事项
        if self.todo_items:
            lines.append(f"[待办] ({len(self.todo_items)} 项)")
            for i, todo in enumerate(self.todo_items[:5], 1):
                lines.append(f"  {i}. {todo[:50]}")
            if len(self.todo_items) > 5:
                lines.append(f"  ... 还有 {len(self.todo_items) - 5} 项")

        # 最近事件
        recent_events = self.event_bus[-3:]
        if recent_events:
            lines.append("[最近事件]")
            for event in recent_events:
                lines.append(f"  - {event['type']}")

        return "\n".join(lines)

    def get_task_summary(self):
        """获取任务摘要 (用于记忆)"""
        summary_parts = []

        # 任务统计
        total = len(self.task_registry)
        completed = sum(1 for t in self.task_registry if t["status"] == self.TASK_STATUS["COMPLETED"])
        failed = sum(1 for t in self.task_registry if t["status"] == self.TASK_STATUS["FAILED"])

        summary_parts.append(f"任务: {completed}/{total} 完成, {failed} 失败")

        # 当前阶段
        summary_parts.append(f"阶段: {self.state['current_phase']}")

        # 待办
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
```

---

## 6. 配置参数

### 6.1 完整配置

```python
DEFAULT_MEMORY_MANAGER_CONFIG = {
    # ==================== 触发机制 ====================
    "trigger": {
        "enabled": True,
        "fixed_step_trigger": 30,        # 固定轮数触发
        "token_threshold": 8000,          # Token 阈值触发
        "force_compact_at": 60000,        # 强制压缩阈值
        "preserve_count": 4,              # 保留消息数
    },

    # ==================== 滚动摘要 ====================
    "rolling_summary": {
        "enabled": True,
        "trigger_steps": 30,              # 触发摘要的对话回合数
        "min_steps_before_summary": 10,   # 最少累积多少回合后才允许摘要
        "overlap_steps": 5,               # 摘要时保留最近N轮不压缩
        "max_summary_history": 5,         # 最多保留5个历史摘要
        "incremental": True,              # 增量压缩
    },

    # ==================== 约束保留 ====================
    "constraint_keeper": {
        "enabled": True,
        "extract_from_user": True,
        "extract_from_assistant": False,
        "max_constraints": 20,
        "keywords_zh": [
            "不能", "不要", "不可", "不允许",
            "必须", "一定要", "务必要",
            "保持", "维持", "不变",
            "禁止", "忌", "不准",
            "只使用", "仅用", "只能",
            "不要改变", "不要修改", "不要删除",
            "保持不变", "维持不变"
        ],
        "keywords_en": [
            "must not", "cannot", "should not", "do not", "don't",
            "must", "have to", "need to", "required to",
            "keep", "maintain", "preserve",
            "only use", "use only", "exclusively",
            "don't change", "don't modify", "don't delete",
            "must remain", "must keep"
        ]
    },

    # ==================== 工具输出压缩 ====================
    "tool_compression": {
        "enabled": True,
        "auto_compress": True,
        "threshold_length": 1000,
        "always_compress_tools": ["run_shell"],
        "never_compress_tools": ["read_file"],
        "max_output_length": 500,
        "test_output_max": 50,
        "error_output_max": 300
    },

    # ==================== 任务状态分段 ==================== ← 新增
    "task_state_segmentation": {
        "enabled": True,
        "max_todos": 10,               # 最多保留的 TODO 项
        "max_phases": 10,              # 最多保留的阶段历史
        "phase_keywords": {             # 阶段识别关键词
            "task_analysis": ["分析", "理解", "需求", "目标"],
            "planning": ["计划", "规划", "设计方案", "架构"],
            "implementation": ["实现", "编写", "创建", "修改"],
            "testing": ["测试", "运行测试", "单元测试"],
            "refinement": ["优化", "改进", "完善", "重构"],
            "verification": ["验证", "检查", "确认", "通过"],
            "documentation": ["文档", "注释", "说明"],
            "completion": ["完成", "结束", "任务完成"]
        }
    },

    # ==================== 工具调用保护 ====================
    "tool_pair_protection": {
        "enabled": True,
        "check_before_compact": True,
    },

    # ==================== 项目级记忆 ====================
    "project_memory": {
        "enabled": True,
        "load_claude_md": True,
        "load_claw_instructions": True,
        "inherit_parent": True,
        "max_instruction_chars": 3000,
    },

    # ==================== 摘要压缩 ====================
    "summary_compression": {
        "max_chars": 1200,
        "max_lines": 24,
        "max_line_chars": 160,
        "priority_enabled": True,
    },

    # ==================== 缓存 ====================
    "cache": {
        "enabled": False,
        "ttl": 300,
    },

    # ==================== 统计 ====================
    "stats": {
        "track_compressions": True,
        "track_tokens_saved": True,
    }
}
```

---

## 7. 实施计划

### 7.1 Phase 3: 代码实现

#### 3.1 创建 memory_manager.py

| 任务 | 优先级 | 工作量 |
|------|--------|--------|
| TriggerManager 类 | P0 | 1小时 |
| IncrementalRollingSummary 类 | P0 | 2小时 |
| ConstraintKeeper 类 | P0 | 1小时 |
| ToolOutputCompressor 类 | P0 | 2小时 |
| ToolPairProtector 类 | P0 | 30分钟 |
| ProjectMemoryLoader 类 | P1 | 1小时 |
| SummaryPriorityCompressor 类 | P1 | 1小时 |

#### 3.2 修改 mini_coding_agent.py

| 任务 | 优先级 | 工作量 |
|------|--------|--------|
| 集成 MemoryManager | P0 | 1小时 |
| 修改 memory_text() | P0 | 30分钟 |
| 修改 ask() | P0 | 2小时 |
| 添加向后兼容代码 | P0 | 1小时 |

### 7.2 时间估算

| 阶段 | 预计时间 |
|------|----------|
| Phase 3 代码实现 | 6-8 小时 |
| Phase 4 文档编写 | 2-3 小时 |
| Phase 5 测试验证 | 3-4 小时 |
| Phase 6 整理提交 | 1-2 小时 |
| **总计** | **12-17 小时** |

---

## 8. 测试验证

### 8.1 单元测试

| 测试编号 | 测试项 | 验证点 |
|---------|--------|--------|
| UT-001 | TriggerManager | 固定轮数触发 |
| UT-002 | TriggerManager | Token 阈值触发 |
| UT-003 | TriggerManager | 强制压缩触发 |
| UT-004 | IncrementalRollingSummary | 增量摘要生成 |
| UT-005 | IncrementalRollingSummary | 历史摘要合并 |
| UT-006 | ConstraintKeeper | 约束识别 |
| UT-007 | ConstraintKeeper | 去重和限制 |
| UT-008 | ToolOutputCompressor | 测试输出压缩 |
| UT-009 | ToolOutputCompressor | 日志压缩 |
| UT-010 | ToolPairProtector | 配对保护 |
| UT-011 | ProjectMemoryLoader | 指令加载 |
| UT-012 | SummaryPriorityCompressor | 优先级压缩 |

### 8.2 集成测试

| 测试编号 | 测试场景 | 验证点 |
|---------|---------|--------|
| IT-001 | 约束提取 | 5轮对话后约束仍保留 |
| IT-002 | 滚动摘要 | 30轮对话后生成摘要 |
| IT-003 | 工具压缩 | run_shell 输出被压缩 |
| IT-004 | 会话恢复 | 重启后 memory 正确恢复 |
| IT-005 | 向后兼容 | 旧 session 正确迁移 |
| IT-006 | Token 感知 | 长消息提前触发压缩 |

### 8.3 性能测试

| 测试项 | 指标 | 目标值 |
|--------|------|--------|
| Memory Manager 初始化 | 耗时 | < 50ms |
| 单次工具压缩 | 耗时 | < 10ms |
| 摘要生成 | 耗时 | < 2s |
| Memory 文本生成 | Token 数 | < 500 |

---

## 9. 风险与兼容性

### 9.1 技术风险

| 风险 | 等级 | 缓解策略 |
|------|------|---------|
| LLM 摘要质量不稳定 | 中 | 提供示例模板，引导 LLM 生成结构化摘要 |
| 约束误识别 | 中 | 使用保守的关键词列表，允许用户手动标记 |
| 压缩丢失关键信息 | 高 | 保留所有错误信息，仅压缩重复/噪音 |

### 9.2 兼容性设计

#### Session 格式迁移

```python
def migrate_session(old_session):
    """迁移旧版本的 session 到新版本"""
    new_session = copy.deepcopy(old_session)

    if "memory" in new_session:
        old_memory = new_session["memory"]

        # 添加新字段
        new_session["memory"]["summary"] = old_memory.get("summary", "")
        new_session["memory"]["constraints"] = old_memory.get("constraints", [])
        new_session["memory"]["summary_history"] = []
        new_session["memory"]["compression_stats"] = {
            "summary_trigger_steps": 0,
            "last_summary_step": 0
        }

    return new_session
```

#### 版本检测

```python
def detect_session_version(session):
    """检测 session 版本"""
    memory = session.get("memory", {})

    if "constraints" in memory:
        return "2.0"
    elif "files" in memory:
        return "1.0"
    else:
        return "unknown"
```

### 9.3 向后兼容性保证

- 新配置有默认值
- 旧 session 可正常加载
- 可选择性地启用/禁用改进
- 渐进式迁移策略

---

## 附录

### A. 代码统计

| 指标 | 数值 |
|------|------|
| 设计文档行数 | ~2500 行 |
| 组件数量 | 8 个类 |
| 配置参数 | 50+ 个 |
| 接口方法 | 30+ 个 |
| 核心功能 | 4 个 (全部实现) |

### B. 参考资料

- Claw Code Memory System Design
- Mini-Coding-Agent 源代码分析
- LLM Context Management Best Practices

---

**文档版本**: 2.1 (完整版 - 4个功能全部实现)
**状态**: 已完成设计
**下一步**: Phase 3 代码实现
**创建时间**: 2025-01-27

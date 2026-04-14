# Memory Manager 测试框架

> 严格按照笔试要求实现的测试框架，用于评估 Memory Manager 的优化效果。

## 目录

1. [概述](#概述)
2. [目录结构](#目录结构)
3. [任务工作区](#任务工作区)
4. [运行测试](#运行测试)
5. [评测指标](#评测指标)
6. [结果对比](#结果对比)

---

## 概述

本测试框架按照笔试要求设计，包含三个核心任务：

| 任务 | 名称 | 考察重点 | 关键指标 |
|------|------|----------|----------|
| **Task 1** | Decision Retention | 关键约束和决策保留 | 约束保留率 > 90% |
| **Task 2** | Noisy Tool Output | 工具输出压缩 | 压缩率 < 0.6 |
| **Task 3** | Long Workflow | 任务状态分段 | 阶段识别准确率 > 80% |

---

## 目录结构

```
versions/tasks/
├── README.md                           # 本文档
├── run_task.py                         # 任务运行脚本
├── eval_memory.py                       # 评测脚本
│
├── task_01_decision_retention.json      # Task 1 配置
├── task_02_noisy_tool_output.json       # Task 2 配置
├── task_03_long_workflow.json           # Task 3 配置
│
├── task_workspaces/                     # 任务工作区
│   ├── repo_todo_app/                  # Task 1 工作区
│   │   ├── todo/
│   │   │   ├── __init__.py             # 核心代码
│   │   │   └── cli.py                  # CLI 接口（不可修改）
│   │   └── tests/
│   │       └── test_filtering.py        # 测试用例
│   │
│   ├── repo_log_parser/                 # Task 2 工作区
│   │   ├── parser/
│   │   │   └── __init__.py             # 核心代码
│   │   └── tests/
│   │       └── test_parser_regression.py # 测试用例
│   │
│   └── repo_config_loader/              # Task 3 工作区
│       ├── config/
│       │   └── __init__.py             # 核心代码
│       └── tests/
│           └── test_loader_precedence.py  # 测试用例
│
└── results/                            # 结果目录（运行后生成）
    ├── baseline/                        # Baseline 版本结果
    │   ├── task_01_decision_retention_results.json
    │   ├── task_02_noisy_tool_output_results.json
    │   └── task_03_long_workflow_results.json
    │
    └── with-memory/                     # Memory 版本结果
        ├── task_01_decision_retention_results.json
        ├── task_02_noisy_tool_output_results.json
        └── task_03_long_workflow_results.json
```

---

## 任务工作区

### Task 1: Decision Retention

**考察**: 关键约束和决策保留能力

**工作区**: `repo_todo_app`

**任务描述**: 修改 todo 过滤行为并保持向后兼容性

**约束要求**:
- 必须保持公共 CLI 不变
- 不能重命名任何现有导出函数

**配置检查**:
```json
{
  "must_modify_files": ["todo/__init__.py", "tests/test_filtering.py"],
  "must_not_modify_files": ["todo/cli.py"],
  "final_must_contain": [
    "keep the public CLI unchanged",
    "do not rename any existing exported function"
  ],
  "test_command": "pytest -q"
}
```

---

### Task 2: Noisy Tool Output

**考察**: 工具输出压缩能力

**工作区**: `repo_log_parser`

**任务描述**: 修复解析器测试中的 bug（日志包含大量噪音）

**配置检查**:
```json
{
  "must_modify_files": ["parser/__init__.py", "tests/test_parser_regression.py"],
  "final_must_contain": ["null handling", "JSON parsing"],
  "test_command": "pytest -q",
  "expect_metrics": {
    "compressed_tool_output_ratio_lt": 0.6
  }
}
```

**噪声日志特征**:
- 50+ 条 WARNING 信息
- 100+ 条 INFO 信息
- 只有 3 条关键 ERROR 信息

---

### Task 3: Long Workflow

**考察**: 任务状态分段管理能力

**工作区**: `repo_config_loader`

**任务描述**: 实现配置加载器的 fallback 优先级机制

**Fallback 顺序**: `env var > local config > default config`

**配置检查**:
```json
{
  "must_modify_files": ["config/__init__.py", "tests/test_loader_precedence.py"],
  "final_must_contain": ["env var > local config > default config"],
  "test_command": "pytest -q",
  "expect_metrics": {
    "phase_awareness_accuracy_gt": 0.8,
    "final_summary_accuracy_gt": 0.8
  }
}
```

---

## 运行测试

### 前置要求

```bash
# 确保在正确的 conda 环境中
conda activate minicodeagent

# 安装项目依赖
cd versions/baseline  # 或 versions/with-memory
pip install -e .
```

### 运行单个任务

```bash
# 运行 Task 1 (Baseline 版本)
python versions/tasks/run_task.py --task task_01_decision_retention --version baseline

# 运行 Task 1 (Memory 版本)
python versions/tasks/run_task.py --task task_01_decision_retention --version with-memory

# 指定模型
python versions/tasks/run_task.py --task task_01 --version with-memory --model qwen3.5:2b

# 详细输出
python versions/tasks/run_task.py --task task_01 -v
```

### 运行所有任务

```bash
# 运行所有任务 (Baseline 版本)
python versions/tasks/run_task.py --all --version baseline --output results/baseline

# 运行所有任务 (Memory 版本)
python versions/tasks/run_task.py --all --version with-memory --output results/with-memory
```

### 评测任务

```bash
# 评测单个任务
python versions/tasks/eval_memory.py --task task_01_decision_retention.json --version with-memory

# 评测所有任务
python versions/tasks/eval_memory.py --tasks . --version with-memory --output results/with-memory

# 对比 Baseline 和 Memory 版本
python versions/tasks/eval_memory.py --tasks . --compare --output results/
```

---

## 评测指标

### Task 1: Decision Retention

| 指标 | Baseline | Target | 说明 |
|------|----------|--------|------|
| **约束保留率** | < 50% | > 90% | 最终总结中包含关键约束的比例 |
| **上下文压缩率** | 1.0 | < 0.6 | 最终/初始上下文长度比 |
| **CLI 兼容性** | ✅ | ✅ | 必须保持不变 |

### Task 2: Noisy Tool Output

| 指标 | Baseline | Target | 说明 |
|------|----------|--------|------|
| **压缩率** | 1.0 | < 0.6 | 处理后/原始工具输出比 |
| **测试通过** | ❌ | ✅ | pytest -q 必须通过 |
| **关键信息保留** | ✅ | ✅ | 必须保留 ERROR 信息 |

### Task 3: Long Workflow

| 指标 | Baseline | Target | 说明 |
|------|----------|--------|------|
| **阶段识别准确率** | < 50% | > 80% | Agent 对当前阶段的识别准确率 |
| **最终总结准确率** | < 50% | > 80% | 最终总结中文件变更描述准确率 |
| **测试通过** | ❌ | ✅ | pytest -q 必须通过 |

---

## 结果对比

### 对比脚本

```bash
# 对比两个版本的评测结果
python versions/tasks/eval_memory.py --tasks . --compare --output results/
```

### 对比输出示例

```
============================================================
IMPROVEMENTS
============================================================

task_01_decision_retention:
  constraint_retention_rate: 0.30 -> 0.92 (+0.62)
  context_compression_ratio: 1.00 -> 0.58 (-0.42)

task_02_noisy_tool_output:
  compressed_tool_output_ratio: 1.00 -> 0.45 (-0.55)

task_03_long_workflow:
  phase_awareness_accuracy: 0.40 -> 0.88 (+0.48)
  final_summary_accuracy: 0.30 -> 0.92 (+0.62)

============================================================
DEGRADATIONS
============================================================

task_02_noisy_tool_output:
  (none detected)
```

---

## 任务配置文件格式

每个任务配置 JSON 文件包含以下字段：

```json
{
  "id": "task_01_decision_retention",
  "name": "Decision Retention",
  "description": "任务描述",
  "workspace": "task_workspaces/repo_todo_app",
  "system_goal": "系统目标",
  "turns": [
    "第一轮用户输入",
    "第二轮用户输入"
  ],
  "checks": {
    "must_modify_files": ["必须修改的文件"],
    "must_not_modify_files": ["不应修改的文件"],
    "final_must_contain": ["最终总结必须包含的内容"],
    "test_command": "pytest -q",
    "expect_metrics": {
      "metric_name_gt": 0.9,
      "metric_name_lt": 0.6
    }
  },
  "baseline_metrics": {
    "metric1": 0.3,
    "metric2": 0.5
  },
  "target_metrics": {
    "metric1": 0.9,
    "metric2": 0.4
  }
}
```

---

## 故障排查

### 常见问题

**Q: ModuleNotFoundError: No module named 'mini_coding_agent'**

```bash
# 确保在正确的目录中
cd versions/with-memory  # 或 versions/baseline
pip install -e .
```

**Q: 任务运行卡住**

```bash
# 使用超时设置
timeout 300 python versions/tasks/run_task.py --task task_01 -v
```

**Q: 测试命令失败**

```bash
# 手动运行测试检查
cd task_workspaces/repo_todo_app
pytest -v
```

---

## 扩展任务

### 添加新任务

1. 创建工作区目录: `task_workspaces/repo_new_feature/`
2. 添加源代码和测试用例
3. 创建任务配置: `task_new_feature.json`
4. 更新本 README

### 自定义评测指标

在任务配置的 `expect_metrics` 中添加：

```json
{
  "expect_metrics": {
    "my_custom_metric_gt": 0.8,
    "my_custom_metric_lt": 0.5
  }
}
```

---

## 参考资料

- [笔试介绍文档](../../笔试介绍.md)
- [Memory Manager 设计文档](../../REPORTS/MEMORY_MANAGER_DESIGN.md)
- [TODO 列表](../../todo_list.md)

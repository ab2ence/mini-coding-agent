# Mini Coding Agent

本项目基于 [rasbt/mini-coding-agent](https://github.com/rasbt/mini-coding-agent) 进行二次开发，并实现了**Memory-Aware**增强版本。

有关原始项目的详细信息和详细教程，请访问 [Components of a Coding Agent](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)。

---

## 📋 目录

- [项目简介](#项目简介)
- [环境准备](#环境准备)
  - [Conda环境配置](#conda环境配置)
  - [API Key配置](#api-key配置)
  - [依赖安装](#依赖安装)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [Memory Manager 技术文档](#memory-manager-技术文档) ⭐
- [测试与评估](#测试与评估) ⭐
- [项目结构](#项目结构)
- [资源链接](#资源链接)

---

## 项目简介

Mini-Coding-Agent 是一个轻量级本地代码助手，具有以下核心功能：

- 🔍 **工作区快照收集** - 自动收集项目结构和上下文
- 📝 **稳定Prompt管理** - 优化的提示词设计
- 🛠️ **结构化工具集** - 文件读写、命令执行等
- ✅ **风险操作审批** - 危险的系统操作需要确认
- 💾 **会话持久化** - 支持中断恢复
- 🤖 **模型后端** - 基于 DeepSeek API，提供强大的代码生成能力
- 🧠 **Memory Manager** - 智能上下文压缩和约束保留（with-memory版本）⭐

---

## Memory Manager 技术文档 ⭐

### 设计概述

Memory Manager 是本项目的核心增强功能，实现了4项内存优化能力：

| 能力 | 说明 | 位置 |
|------|------|------|
| **Rolling Summary** | 滚动摘要 - 压缩早期历史为结构化摘要 | IncrementalRollingSummary |
| **Pinned Facts** | 关键约束永久保留 - 避免重要约束被遗忘 | ConstraintKeeper |
| **Tool Output Compression** | 工具输出智能压缩 - 去除噪声保留关键信息 | ToolOutputCompressor |
| **Task-State Segmentation** | 任务状态分段 - 管理多阶段工作流 | TaskStateSegmenter |

### 核心架构

Memory Manager 采用**分层记忆结构**：

```
Memory Layers:
├── Layer 0: Project Memory (项目级指令，如 CLAUDE.md)
├── Layer 1: Pinned Layer (永久层 - 关键约束、原始任务)
├── Layer 2: Summary Layer (摘要层 - 滚动摘要)
├── Layer 3: Task State Layer (任务状态层 - 阶段、待办) ⭐
└── Layer 4: Working Layer (工作层 - 最近对话)
```

### 关键技术特性

#### 1. 智能触发机制 (TriggerManager)
- **轮数触发**: 每 N 轮自动压缩
- **Token 触发**: 上下文长度超过阈值时触发
- **强制触发**: 关键事件发生时立即压缩

#### 2. 约束保护 (ConstraintKeeper)
- **关键词识别**: 中英文约束关键词库
- **自动提取**: 从对话中识别"必须/禁止"类语句
- **永久保留**: 约束存入 Pinned Layer，永不压缩

#### 3. 工具输出压缩 (ToolOutputCompressor)
- **分类压缩**: shell输出、测试结果、日志分别处理
- **智能截断**: 保留首尾关键信息，去除重复行
- **错误高亮**: ERROR/WARNING 行单独保留

#### 4. 任务状态管理 (TaskStateSegmenter) ⭐
- **任务注册**: 自动从对话提取待办任务
- **状态追踪**: Pending → InProgress → Completed 状态机
- **依赖检查**: 任务依赖满足时自动触发
- **阶段识别**: 检测工作流阶段变化（分析→实现→测试→修复）

### 设计权衡

**主要权衡点**:
- ✅ **压缩率 vs 信息完整性**: 保守策略，优先保留关键信息
- ✅ **自动化 vs 可控性**: 自动触发但提供手动 `/memory` 查看
- ✅ **通用性 vs 任务特化**: 通用规则为主，辅以启发式策略

**局限性**:
- ⚠️ 依赖 LLM 生成摘要的质量
- ⚠️ 约束提取基于关键词，可能漏掉隐式约束
- ⚠️ 任务状态识别依赖模型能力

### 详细技术文档

完整的技术设计、实现细节、性能指标和失败分析，请参阅：

- 📄 **[完整设计文档](REPORTS/MEMORY_MANAGER_DESIGN.md)** - 架构设计、组件详解 (~1500行)
- 📊 **[测试结果报告](REPORTS/结果.md)** - 评测数据、对比分析、失败案例 (~750行)
- 📋 **[错误案例统计](REPORTS/错误案例统计.md)** - Step Limit 问题深度诊断

---

## 测试与评估 ⭐

### 测试任务

本项目包含3个真实测试任务，用于评估 Memory Manager 效果：

| 任务 | 考察重点 | 状态 |
|------|----------|------|
| **Task 1**: Decision Retention | 关键约束保留能力 | ✅ 测试完成 |
| **Task 2**: Noisy Tool Output | 工具输出压缩能力 | ✅ 测试完成 |
| **Task 3**: Long Workflow | 长工作流状态管理 | ✅ **Memory 版本通过** |

### 运行测试

```powershell
# 运行单个任务（Baseline 版本）
python versions/tasks/run_task.py --task task_01 --version baseline

# 运行单个任务（Memory 版本）
python versions/tasks/run_task.py --task task_01 --version with-memory

# 运行所有任务
python versions/tasks/run_task.py --all --version with-memory --output results/

# 评测对比
python versions/tasks/eval_memory.py --tasks . --compare --output results/
```

### 核心指标

| 指标 | Baseline | With-Memory | 改进 |
|------|----------|-------------|------|
| **上下文压缩率** | 605.53x | 68.88x | ⬇️ **88.6% 降低** |
| **每轮增长** | 29,322 字符 | 3,757 字符 | ⬇️ **87.2% 降低** |
| **Task 3 完成率** | 0% | **100%** | ✅ **完全通过** |

详见: [REPORTS/结果.md](REPORTS/结果.md)

---

## 项目结构

### Conda环境配置

#### 1. 创建 conda 环境

如果还没有 conda 环境，创建新环境：

```powershell
conda create -n minicodeagent python=3.10
conda activate minicodeagent
```

#### 2. 验证 Python 版本

```powershell
python --version
```

确保输出为 Python 3.10.x

---

### API Key配置

#### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件：

```powershell
# 复制 .env-example 为 .env
copy .env-example .env
```

#### 2. 配置 API Key

编辑 `.env` 文件，填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

获取 API Key: [https://platform.deepseek.com/](https://platform.deepseek.com/)

---

### 依赖安装

安装所需的 Python 包：

```powershell
pip install openai python-dotenv
```

或者使用项目配置：

```powershell
pip install -e .
```

---

## 项目结构

```
mini-coding-agent/
├── versions/
│   ├── baseline/                          # Baseline 版本（无 Memory）
│   │   └── mini_coding_agent_original.py  # 原始 agent 实现
│   └── with-memory/                       # With-Memory 版本
│       ├── mini_coding_agent.py           # 集成 Memory Manager 的 agent
│       ├── memory_manager.py              # ⭐ Memory Manager 核心 (~1700 行)
│       ├── README.md                      # ⭐ 详细技术文档 (29KB)
│       └── test_memory_manager.py         # 45 个单元测试
├── versions/tasks/                        # 测试框架（按笔试要求实现）
│   ├── run_task.py                        # 任务运行脚本
│   ├── eval_memory.py                     # 评测脚本
│   ├── task_01_decision_retention.json    # Task 1: 决策保留
│   ├── task_02_noisy_tool_output.json     # Task 2: 噪声工具输出
│   ├── task_03_long_workflow.json         # Task 3: 长工作流
│   ├── task_workspaces/                   # 3个真实任务工作区
│   │   ├── repo_todo_app/                 # Task 1: Todo 应用
│   │   ├── repo_log_parser/               # Task 2: 日志解析器
│   │   └── repo_config_loader/            # Task 3: 配置加载器
│   └── results/                           # 测试结果
│       ├── baseline/                      # Baseline 结果
│       └── with-memory/                   # Memory 结果
├── REPORTS/                               # 📊 报告目录
│   ├── MEMORY_MANAGER_DESIGN.md           # 完整设计文档 (~1500行)
│   ├── 错误案例统计.md                    # Step Limit 问题深度分析
│   └── 结果.md                            # 测试结果报告 (本次提交) ⭐
├── pyproject.toml                         # 项目配置
├── .env-example                           # API Key 模板
└── README.md                              # 本文件
```

---

## 快速开始

### 启动 Mini Coding Agent

```powershell
# 激活 conda 环境
conda activate minicodeagent

# 进入项目目录
cd f:\programs\minicodingagent\mini-coding-agent

# 启动 Agent（使用 DeepSeek API）
python versions/baseline/mini_coding_agent_original.py

# 或启动带 Memory Manager 的版本
python versions/with-memory/mini_coding_agent.py
```

### 使用参数

**查看所有选项：**
```powershell
python versions/baseline/mini_coding_agent_original.py --help
```

**使用不同模型：**
```powershell
python versions/baseline/mini_coding_agent_original.py --model deepseek-chat
```

**自动审批模式（谨慎使用）：**
```powershell
python versions/baseline/mini_coding_agent_original.py --approval auto
```

**限制最大步数：**
```powershell
python versions/baseline/mini_coding_agent_original.py --max-steps 10
```

**恢复之前的会话：**
```powershell
python versions/baseline/mini_coding_agent_original.py --resume latest
```

---

## 使用指南

### 交互命令

在 Agent 运行期间，可使用以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/memory` | 显示当前会话的蒸馏记忆（仅with-memory版本） |
| `/session` | 显示保存的会话文件路径 |
| `/reset` | 清除当前会话历史和记忆 |
| `/exit` 或 `/quit` | 退出 Agent |

### 示例任务

启动 Agent 后，可以尝试以下任务：

1. **查看项目结构**
   ```
   帮我查看当前目录的所有文件
   ```

2. **创建新文件**
   ```
   帮我创建一个 hello.py 文件，包含一个打印"Hello World"的函数
   ```

3. **解释代码**
   ```
   解释一下 mini_coding_agent.py 的主要功能
   ```

4. **调试问题**
   ```
   我的代码出现了 ImportError 错误，请帮我看看
   ```

---

## 版本对比

### Baseline 版本
- 位置：`versions/baseline/mini_coding_agent_original.py`
- 功能：基础代码助手，无记忆管理
- 适用场景：简单任务，短对话

### With-Memory 版本
- 位置：`versions/with-memory/mini_coding_agent.py`
- 功能：
  - ✅ 滚动摘要 (Rolling Summary)
  - ✅ 关键约束保留 (Pinned Facts / Constraints)
  - ✅ 工具输出压缩 (Tool Output Compression)
  - ✅ 任务状态分段 (Task-State Segmentation)
- 适用场景：长对话、复杂任务、多轮协作

---

**限制最大步数：**
```powershell
python versions/baseline/mini_coding_agent_original.py --max-steps 10
```

**恢复之前的会话：**
```powershell
python versions/baseline/mini_coding_agent_original.py --resume latest
```

---

## 版本对比

### Baseline 版本
- 位置：`versions/baseline/mini_coding_agent_original.py`
- 功能：基础代码助手，无记忆管理
- 适用场景：简单任务，短对话

### With-Memory 版本
- 位置：`versions/with-memory/mini_coding_agent.py`
- 功能：
  - ✅ 滚动摘要 (Rolling Summary)
  - ✅ 关键约束保留 (Pinned Facts / Constraints)
  - ✅ 工具输出压缩 (Tool Output Compression)
  - ✅ 任务状态分段 (Task-State Segmentation)
- 适用场景：长对话、复杂任务、多轮协作

---

## 测试与评估

### 测试任务说明

本项目使用3个真实任务评估 Memory Manager 效果，详细配置见 `versions/tasks/` 目录：

**Task 1: Decision Retention** (`task_01_decision_retention.json`)
- 考察：关键约束保留能力
- 期望：约束保留率 > 90%

**Task 2: Noisy Tool Output** (`task_02_noisy_tool_output.json`)
- 考察：工具输出压缩能力
- 期望：压缩率 < 0.6

**Task 3: Long Workflow** (`task_03_long_workflow.json`)
- 考察：长工作流状态管理
- 期望：正确识别阶段并完成测试

### 运行完整测试套件

```powershell
# 1. 激活环境
conda activate minicodeagent

# 2. 进入测试目录
cd versions/tasks

# 3. 运行 Baseline 测试（记录原始性能）
python run_task.py --all --version baseline --output results/baseline

# 4. 运行 Memory 版本测试
python run_task.py --all --version with-memory --output results/with-memory

# 5. 生成对比评测报告
python eval_memory.py --tasks . --compare --output results/

# 6. 查看结果
# Baseline: results/baseline/eval_summary_baseline.json
# Memory:   results/with-memory/eval_summary_with-memory.json
# 对比:     results/comparison.json
```

### 单任务测试

```powershell
# 运行单个任务
python run_task.py --task task_01 --version with-memory --output results/

# 评测单个任务
python eval_memory.py --task task_01_decision_retention.json --version with-memory
```

### 测试结果

最新测试结果（2026-04-14）：

| 任务 | Baseline 完成率 | With-Memory 完成率 | 主要改进 |
|------|----------------|-------------------|----------|
| Task 1 | 0% | 0% | 约束保留率指标异常 |
| Task 2 | 0% | 0% | 测试有1个已知失败 |
| Task 3 | 0% | **100%** | ✅ 完全通过 |
| **平均** | **0%** | **33.3%** | ⬆️ |

**上下文压缩效果**（Memory vs Baseline）:
- Task 1: 压缩率 347x → 67x (**80.7% 降低**)
- Task 2: 压缩率 433x → 55x (**87.2% 降低**)
- Task 3: 压缩率 1037x → 84x (**91.9% 降低**)

详细分析见: [REPORTS/结果.md](REPORTS/结果.md)

---

## 提交物清单（笔试要求）

根据 [笔试介绍.md](%E7%AC%94%E8%AF%95%E4%BB%8B%E7%BB%8D.md) 的交付物要求，本项目提供：

### 1. 可运行代码 ✅

| 文件 | 说明 | 行数 |
|------|------|------|
| `versions/with-memory/memory_manager.py` | Memory Manager 核心实现 | ~1700 |
| `versions/with-memory/mini_coding_agent.py` | 集成 Memory Manager 的 Agent | ~1100 |
| `versions/baseline/mini_coding_agent_original.py` | Baseline 原始版本 | ~900 |
| `versions/tasks/run_task.py` | 测试运行脚本 | ~500 |
| `versions/tasks/eval_memory.py` | 评测脚本 | ~540 |

**验证命令**:
```bash
python versions/tasks/eval_memory.py --tasks . --compare --output results/
```

### 2. README ✅

- 📘 `README.md` (本文件) - 项目总览 + 快速开始
- 📗 `versions/with-memory/README.md` - Memory Manager 详细技术文档 (29KB)
- 📙 `REPORTS/MEMORY_MANAGER_DESIGN.md` - 完整设计文档 (60KB)

README 包含笔试要求的所有内容：
- ✅ Memory 设计说明
- ✅ 设计理由
- ✅ 触发压缩/摘要时机
- ✅ 关键约束保护机制
- ✅ Noisy tool outputs 处理方式
- ✅ 主要 trade-off
- ✅ 方案局限性

### 3. 结果报告 ✅

- 📊 `REPORTS/结果.md` - **本次提交的核心报告** (26KB, 745行)
  - ✅ 压缩前后上下文长度对比表
  - ✅ Task 3 成功案例（100% 通过）
  - ✅ Task 1/2 失败/退化案例分析
  - ✅ 关键权衡点说明（压缩率 vs 信息完整性）
  - ✅ Before/After 指标对比
  - ✅ 失败原因与改进建议

### 4. 过程记录 ✅

- 📋 `REPORTS/错误案例统计.md` - Step Limit 问题深度诊断 (24KB)
- 📋 `todo_list.md` - 完整开发历程与里程碑
- 📁 `versions/tasks/results/` - 所有测试日志与结果文件

---

## 核心设计文档

Memory Manager 的设计文档分为3个层次：

| 文档 | 内容 | 适合读者 |
|------|------|----------|
| [**README.md**](README.md) (本文件) | 项目总览、快速开始、测试方法 | 所有用户 |
| [**versions/with-memory/README.md**](versions/with-memory/README.md) | 技术实现细节、API 使用、配置选项 | 开发者、贡献者 |
| [**REPORTS/MEMORY_MANAGER_DESIGN.md**](REPORTS/MEMORY_MANAGER_DESIGN.md) | 完整架构设计、组件详解、设计决策 | 架构师、面试官 |
| [**REPORTS/结果.md**](REPORTS/结果.md) | 测试结果、性能对比、失败分析 | 评估者、产品经理 |

---

## 资源链接

- 🌐 [DeepSeek 官方平台](https://platform.deepseek.com/)
- 📚 [DeepSeek API 文档](https://platform.deepseek.com/docs)
- 🎓 [Coding Agent 教程](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)
- 🐙 [GitHub 源码](https://github.com/rasbt/mini-coding-agent)

---

## 📊 测试结果摘要

### 执行时间线

```
2026-04-14 测试执行记录:
17:07  - Task 01 (Memory) 开始
17:10  - Task 02 (Memory) 开始，发现 Step Limit 问题
17:33  - 发现 GBK 编码错误，修复 run_task.py
17:35  - 发现 nested results 路径错误，移动文件
17:37  - 发现 subprocess 导入错误，修复 eval_memory.py
17:38  - 完成全部评测，生成对比报告
```

### 关键问题记录

**已修复问题**:
1. ✅ **GBK 编码错误** - UnicodeEncodeError 导致结果无法写入
2. ✅ **路径错误** - results 保存到错误的嵌套目录
3. ✅ **Subprocess 导入失败** - ModuleNotFoundError 无法运行测试

**待处理问题**:
- ⚠️ **Step Limit 机制缺陷** - 工具调用循环快速耗尽 max_steps（详见 [错误案例统计.md](REPORTS/错误案例统计.md)）

### 性能指标速览

| 指标 | Baseline | With-Memory | 改进 |
|------|----------|-------------|------|
| 上下文压缩率 | 605.53x | **68.88x** | ⬇️ 88.6% |
| 每轮增长 | 29,322 字符 | **3,757 字符** | ⬇️ 87.2% |
| Task 3 完成 | 0% | **100%** | ✅ |
| 约束保留率 | 50% | 0%* | ⚠️ 异常 |

*注: Task 1 With-Memory 的约束保留率指标异常（0%），但日志显示第6轮成功回忆了约束，可能是指标计算逻辑有 bug。

完整分析见: [REPORTS/结果.md](REPORTS/结果.md)

---

## 🎯 提交前最终检查

根据 [笔试介绍.md](%E7%AC%94%E8%AF%95%E4%BB%8B%E7%BB%8D.md) 的提交清单：

- ✅ **可运行代码** - Memory Manager 1700+ 行，已集成，已测试
- ✅ **README** - 本文件 + `versions/with-memory/README.md` 完整技术文档
- ✅ **结果报告** - `REPORTS/结果.md` 包含所有必需内容
  - ✅ 压缩前后对比
  - ✅ 至少1个成功案例 (Task 3)
  - ✅ 至少1个失败案例 (Task 1/2)
  - ✅ 关键权衡分析
- ✅ **过程记录** - `REPORTS/错误案例统计.md` + `todo_list.md`
- ✅ **运行说明** - 本文件"快速开始"章节

---

## 📝 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-04-14 | v1.0 | 初始版本 - Memory Manager 完整实现与测试 |
| 2026-04-14 | v1.1 | 补充结果报告、修复编码错误、完成对比评测 |

---

*祝你使用愉快！ 🚀*

- 🌐 [DeepSeek 官方平台](https://platform.deepseek.com/)
- 📚 [DeepSeek API 文档](https://platform.deepseek.com/docs)
- 🎓 [Coding Agent 教程](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)
- 🐙 [GitHub 源码](https://github.com/rasbt/mini-coding-agent)

---

*祝你使用愉快！ 🚀*

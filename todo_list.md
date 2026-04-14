# Memory-Aware Coding Agent - 任务拆解清单

## 📋 项目概览

**目标**: 为 Mini-Coding-Agent 实现 Memory Manager 优化方案  
**要求**: 实现4项能力中的至少3项  
**截止时间**: 24小时内完成

### ✅ 当前环境状态
- **Conda环境**: minicodeagent + Python 3.10
- **AI模型**: qwen3.5:2b
- **Ollama版本**: 0.20.6
- **GPU**: RTX 5060 (8GB显存)

---

## 🎯 核心功能需求（4选3）✅

- [x] **Rolling Summary** - 滚动摘要
- [x] **Pinned Facts / Constraints** - 关键约束保留
- [x] **Tool Output Compression** - 工具输出压缩
- [ ] **Task-State Segmentation** - 任务状态分段（❌ 不实现）

---

## � 对比测试框架（笔试明确要求）

### 评价指标体系（根据笔试介绍.md）

根据十三、评估标准 - 验证意识：
> 较强的信号包括：
> - **有明确的 before / after 指标**
> - 能在提供的 tasks 上完成运行
> - 能分析失败案例
> - 指标与结论一致

#### 核心评价指标
| 指标 | 说明 | 目标值 |
|------|------|--------|
| **上下文压缩率** | 压缩后 token 数 / 原始 token 数 | 越低越好 |
| **Tool Output 压缩率** | Task 2 要求: compressed_tool_output_ratio < 0.6 | < 0.6 |
| **任务完成率** | 3个任务是否全部完成 | 100% |
| **关键约束保留率** | Task 1 考察：约束是否被保留 | 100% |
| **Task State 准确性** | Task 3 考察：阶段状态是否清晰 | 高 |

#### 提供的测试任务（来自tasks/目录）
| 任务 | 考察重点 | 关键指标 |
|------|----------|----------|
| **Task 1: Decision Retention** | 关键约束和决策保留 | final_must_contain 匹配率 |
| **Task 2: Noisy Tool Output** | 工具输出压缩 | compressed_tool_output_ratio < 0.6 |
| **Task 3: Long Workflow** | 任务状态分段 | 阶段识别准确率、最终总结质量 |

### 对比实验设计

**实验组 vs 对照组：**
```
对照组 (Baseline):  原始 mini-coding-agent（无 memory 优化）
实验组 (With Memory): 添加 Memory Manager 后的版本
```

**对比维度：**
- [ ] 上下文长度变化（before/after）
- [ ] Token 消耗对比
- [ ] 任务完成质量对比
- [ ] 关键约束保留对比
- [ ] 运行时间对比

### 代码分支管理（重要！）

**要求**: 必须保留原始代码，不与 memory 版本混在一起

| 版本 | 文件位置 | 说明 |
|------|----------|------|
| **原始版本** | `mini_coding_agent_original.py` | 未添加任何 memory 优化 |
| **Memory 版本** | `mini_coding_agent.py` | 集成 Memory Manager |

**注意**: 
- 原始版本放在 `versions/baseline/` 目录
- Memory 版本放在项目根目录或 `versions/with-memory/` 目录
- 两者对比时使用相同的测试用例和 seed

---

## � 提交物清单

### 1. 可运行代码 ✅
- [ ] Memory Manager 实现 (`memory_manager.py`)
- [ ] 与现有 agent 集成
- [ ] 支持多轮 coding tasks
- [ ] 输出 memory 相关指标
- [ ] **原始版本代码（baseline）保留**

### 2. README 📝
- [ ] Memory 设计说明
- [ ] 设计理由
- [ ] 触发压缩/摘要的时机
- [ ] 关键约束保护机制
- [ ] noisy tool outputs 处理方式
- [ ] 主要 trade-off
- [ ] 方案局限性

### 3. 结果报告 📊（关键！）
- [ ] **压缩前后上下文长度对比**
- [ ] **至少一个成功案例**
- [ ] **至少一个失败/退化案例**
- [ ] 关键权衡点说明
- [ ] **Before/After 指标对比表**

### 4. 过程记录 📚
- [ ] prompt 日志
- [ ] tool/terminal 日志
- [ ] 或开发过程说明

---

## 📅 详细任务拆解

### Phase 1: 项目准备与环境验证 ⏱️

#### 1.1 环境配置
- [x] 验证 conda 环境 (minicodeagent + Python 3.10)
- [x] 验证 Ollama 服务运行状态
- [x] 验证 qwen3.5:2b 模型可用
- [x] 测试 mini-coding-agent 基本功能

#### 1.2 开发工具增强
- [x] 创建 interview-recorder skill (自动记录对话)
- [x] 创建 todo-updater skill (自动更新任务状态)

#### 1.3 代码分支管理（关键！）
- [x] 创建 `versions/baseline/` 目录
- [x] 复制原始 `mini_coding_agent.py` → `versions/baseline/mini_coding_agent_original.py`
- [x] 验证原始版本可独立运行
- [x] 创建 `versions/with-memory/` 目录
- [x] 确保原始代码不被覆盖

#### 1.4 代码分析 ✅
- [x] 阅读 `mini_coding_agent.py` 核心代码
- [x] 理解现有 memory 机制
- [x] 理解 session 持久化逻辑
- [x] 分析 transcript 处理流程
- [x] 定位需要修改的关键位置
- [x] 生成代码分析报告

**阶段产出**: [REPORTS/1.4_code_analysis_report.md](file:///f:/programs/minicodingagent/mini-coding-agent/REPORTS/1.4_code_analysis_report.md)

#### 1.5 任务理解 ✅
- [x] 分析 Task 1: Decision Retention
- [x] 分析 Task 2: Noisy Tool Output
- [x] 分析 Task 3: Long Workflow
- [x] 理解评测脚本逻辑

**阶段产出**: 任务分析已完成

---

### Phase 2: Memory Manager 设计 🎨

#### 2.1 架构设计 ✅
- [x] 确定采用的功能（4选3）
  - ✅ Rolling Summary (滚动摘要)
  - ✅ Pinned Facts / Constraints (关键约束保留)
  - ✅ Tool Output Compression (工具输出压缩)
  - ❌ Task-State Segmentation (不实现)
- [x] 设计 memory 分层结构
- [x] 设计组件接口
- [x] 设计压缩/摘要触发机制
- [x] 详细设计每个模块

**Memory 分层设计**:
```python
Memory:
├── Layer 1: Pinned Layer (永久层)
│   ├── constraints (关键约束)
│   └── original_task (原始任务)
├── Layer 2: Summary Layer (摘要层)
│   ├── current_summary (当前摘要)
│   └── previous_summaries (历史摘要列表)
├── Layer 3: Working Layer (工作层)
│   ├── files (最近文件)
│   ├── notes (笔记)
│   └── recent_history (未压缩的历史)
└── Layer 4: Raw Layer (原始层)
    └── full_history (完整历史，可选)
```

#### 2.2 核心组件设计 ✅
- [x] Rolling Summary 模块设计
- [x] Pinned Facts 提取与保护机制
- [x] Tool Output 压缩策略
- [x] Task-State 管理机制 (仅设计，不实现)

**阶段产出**: [REPORTS/1.5_memory_manager_design_report.md](file:///f:/programs/minicodingagent/mini-coding-agent/REPORTS/1.5_memory_manager_design_report.md)

---

### Phase 3: 代码实现 💻

#### 3.1 基础框架
- [ ] 创建 `memory_manager.py`
- [ ] 定义 Memory 结构类
- [ ] 实现基础接口（add, get, compress等）
- [ ] 定义配置选项

#### 3.2 功能实现

**如果实现 Rolling Summary:**
- [ ] 实现历史消息队列
- [ ] 实现摘要生成逻辑
- [ ] 实现滚动窗口管理
- [ ] 实现摘要触发机制
- [ ] 集成 LLM 摘要调用

**如果实现 Pinned Facts:**
- [ ] 实现约束关键词识别
- [ ] 实现决策提取逻辑
- [ ] 实现受保护的 memory bucket
- [ ] 实现持久化机制
- [ ] 实现查询接口

**如果实现 Tool Output Compression:**
- [ ] 实现输出长度检测
- [ ] 实现压缩/摘要策略
- [ ] 实现去重逻辑
- [ ] 实现结构化保留
- [ ] 实现关键信息提取（error signature等）

**如果实现 Task-State Segmentation:**
- [ ] 实现任务状态追踪
- [ ] 实现 TODO 列表管理
- [ ] 实现阶段识别
- [ ] 实现进度更新机制
- [ ] 实现状态持久化

#### 3.3 Agent 集成
- [ ] 修改 `mini_coding_agent.py` 集成 Memory Manager
- [ ] 修改 prompt 组装逻辑
- [ ] 实现 memory 更新逻辑
- [ ] 实现指标收集

**阶段产出**: 完整可运行的 Memory Manager 代码

---

### Phase 4: 文档编写 📝

#### 4.1 README 编写
- [ ] 编写 Memory 设计概述
- [ ] 说明为什么这样设计
- [ ] 说明触发压缩/摘要的时机
- [ ] 说明关键约束保护机制
- [ ] 说明 noisy tool outputs 处理
- [ ] 说明主要 trade-off
- [ ] 说明局限性
- [ ] 包含使用说明和配置选项

#### 4.2 结果报告编写
- [ ] 收集压缩前后上下文长度对比
- [ ] 整理成功案例
- [ ] 整理失败/退化案例
- [ ] 分析关键权衡点
- [ ] 说明局限性和下一步改进方向

#### 4.3 过程记录
- [ ] 整理 prompt 日志
- [ ] 整理 tool/terminal 日志
- [ ] 或编写开发过程说明

**阶段产出**: 完整的项目文档

---

### Phase 5: 验证与测试 🧪

#### 5.0 测试套件管理 📋（集中进度追踪）

##### 测试套件结构

```
versions/
├── baseline/                      # Baseline 版本测试（无优化）
│   └── tests/
│       ├── task_01_decision_retention/
│       │   ├── test_task1.py              # 测试脚本
│       │   ├── test_results.json          # 测试结果
│       │   └── README.md
│       ├── task_02_noisy_tool_output/
│       │   ├── test_task2.py              # 测试脚本
│       │   ├── test_results.json          # 测试结果
│       │   └── README.md
│       └── task_03_long_workflow/
│           ├── test_task3.py              # 测试脚本
│           ├── test_results.json          # 测试结果
│           └── README.md
│
├── with-memory/                  # With-Memory 版本测试（优化后）
│   └── tests/
│       ├── task_01_decision_retention/
│       │   ├── test_task1_with_memory.py  # 测试脚本
│       │   ├── test_results_with_memory.json  # 测试结果
│       │   └── README.md
│       ├── task_02_noisy_tool_output/
│       │   ├── test_task2_with_memory.py  # 测试脚本
│       │   ├── test_results_with_memory.json  # 测试结果
│       │   └── README.md
│       └── task_03_long_workflow/
│           ├── test_task3_with_memory.py  # 测试脚本
│           ├── test_results_with_memory.json  # 测试结果
│           └── README.md
│
├── tests/                       # 测试套件总览
│   └── README.md
│
└── run_all_tests.py            # 统一测试运行脚本
```

##### 5.0.1 Task 1: Decision Retention 测试任务

**考察**: 关键约束和决策保留能力

| 版本 | 测试文件 | 结果文件 | 状态 |
|------|---------|---------|------|
| **Baseline** | `test_task1.py` | `test_results.json` | ☐ 待运行 |
| **With-Memory** | `test_task1_with_memory.py` | `test_results_with_memory.json` | ☐ 待运行 |

**Baseline 预期指标**:
- 约束保留率: < 50%
- 上下文增长: 快

**With-Memory 预期指标**:
- 约束保留率: > 90%
- 上下文增长: 受控

**运行命令**:
```bash
# Baseline
python versions/baseline/tests/task_01_decision_retention/test_task1.py

# With-Memory
python versions/with-memory/tests/task_01_decision_retention/test_task1_with_memory.py
```

##### 5.0.2 Task 2: Noisy Tool Output 测试任务

**考察**: 工具输出压缩能力

| 版本 | 测试文件 | 结果文件 | 状态 |
|------|---------|---------|------|
| **Baseline** | `test_task2.py` | `test_results.json` | ☐ 待运行 |
| **With-Memory** | `test_task2_with_memory.py` | `test_results_with_memory.json` | ☐ 待运行 |

**Baseline 预期指标**:
- 压缩率: 1.0（无压缩）
- 上下文增长: 快

**With-Memory 预期指标**:
- 压缩率: < 0.6 ⭐
- 上下文增长: 受控

**运行命令**:
```bash
# Baseline
python versions/baseline/tests/task_02_noisy_tool_output/test_task2.py

# With-Memory
python versions/with-memory/tests/task_02_noisy_tool_output/test_task2_with_memory.py
```

##### 5.0.3 Task 3: Long Workflow 测试任务

**考察**: 任务状态分段管理能力

| 版本 | 测试文件 | 结果文件 | 状态 |
|------|---------|---------|------|
| **Baseline** | `test_task3.py` | `test_results.json` | ☐ 待运行 |
| **With-Memory** | `test_task3_with_memory.py` | `test_results_with_memory.json` | ☐ 待运行 |

**Baseline 预期指标**:
- 阶段识别准确率: < 50%
- 最终总结准确率: < 50%

**With-Memory 预期指标**:
- 阶段识别准确率: > 80%
- 最终总结准确率: > 80%

**运行命令**:
```bash
# Baseline
python versions/baseline/tests/task_03_long_workflow/test_task3.py

# With-Memory
python versions/with-memory/tests/task_03_long_workflow/test_task3_with_memory.py
```

##### 5.0.4 测试结果汇总

| 测试任务 | Baseline 状态 | With-Memory 状态 | 对比分析 |
|---------|--------------|-----------------|---------|
| **Task 1: Decision Retention** | ☐ | ☐ | ☐ |
| **Task 2: Noisy Tool Output** | ☐ | ☐ | ☐ |
| **Task 3: Long Workflow** | ☐ | ☐ | ☐ |

**统一运行命令**:
```bash
cd versions
python run_all_tests.py
```

**汇总结果文件**: `versions/test_summary.json`

#### 5.1 功能测试
- [ ] 测试 Memory Manager 基本功能
- [ ] 测试与 agent 集成
- [ ] 验证各功能正常工作

#### 5.2 Baseline 测试（原始版本）
- [ ] 在 baseline 版本上运行 Task 1
- [ ] 在 baseline 版本上运行 Task 2
- [ ] 在 baseline 版本上运行 Task 3
- [ ] 记录 baseline 的上下文长度、token 消耗、任务完成率
- [ ] 记录 baseline 的关键约束保留情况

#### 5.3 Memory 版本测试
- [ ] 在 memory 版本上运行 Task 1
- [ ] 在 memory 版本上运行 Task 2
- [ ] 在 memory 版本上运行 Task 3
- [ ] 记录 memory 版本的上下文长度、token 消耗、任务完成率
- [ ] 记录 memory 版本的关键约束保留情况

#### 5.4 Before/After 对比分析（关键！）
- [ ] **对比 Task 1**: 关键约束保留率对比
- [ ] **对比 Task 2**: Tool Output 压缩率对比（目标 < 0.6）
- [ ] **对比 Task 3**: 任务状态清晰度对比
- [ ] **对比指标**:
  - 上下文长度变化（before/after）
  - Token 消耗对比
  - 任务完成质量对比
  - 运行时间对比
- [ ] 整理成功案例
- [ ] 分析失败/退化案例
- [ ] 生成对比报告（压缩前后对比表）

**阶段产出**: Before/After 对比报告、性能指标对比表

---

### Phase 6: 最终整理与提交 📤

#### 6.1 代码整理
- [ ] 代码重构与优化
- [ ] 添加必要的注释
- [ ] 确保代码可读性
- [ ] 检查边界情况

#### 6.2 文档整理
- [ ] 完善 README
- [ ] 完善结果报告
- [ ] 整理过程记录
- [ ] 添加运行说明

#### 6.3 提交前检查
- [ ] ☐ 可运行代码已提交
- [ ] ☐ 原始版本代码已保留（versions/baseline/）
- [ ] ☐ README 已完成
- [ ] ☐ 结果报告已包含
  - [ ] ☐ Before/After 指标对比表
  - [ ] ☐ 成功案例
  - [ ] ☐ 失败/退化案例
- [ ] ☐ 过程记录已包含
- [ ] ☐ 运行说明已提供
- [ ] ☐ 代码可读性检查通过
- [ ] ☐ Baseline 测试完成
- [ ] ☐ Memory 版本测试完成
- [ ] ☐ 对比分析完成

**阶段产出**: 完整可提交的代码包

---

## 🎯 交付物清单

| 交付物 | 状态 | 位置 |
|--------|------|------|
| **原始版本代码** | ✅ | `versions/baseline/mini_coding_agent_original.py` |
| **代码分析报告** | ✅ | `REPORTS/1.4_code_analysis_report.md` |
| **Memory Manager 设计报告** | ✅ | `REPORTS/1.5_memory_manager_design_report.md` |
| **Phase 1-2 阶段总结** | ✅ | `REPORTS/phase1_2_summary_report.md` |
| **Memory 版本代码** | ☐ | `mini_coding_agent.py` + `memory_manager.py` |
| **Before/After 对比报告** | ☐ | `REPORT.md` 或 `RESULTS.md` |
| README | ☐ | 项目根目录 |
| 过程记录 | ☐ | `vibe_coding_interview_record.md` |
| 运行说明 | ☐ | README 或 `RUN.md` |

---

## 📊 优先级排序

### P0 - 核心必须
1. ✅ 环境配置完成
2. ☐ Memory Manager 核心实现
3. ☐ Agent 集成
4. ☐ 基本功能测试
5. ☐ README 编写

### P1 - 重要
1. ☐ Task 1 测试通过
2. ☐ Task 2 测试通过
3. ☐ Task 3 测试通过
4. ☐ 结果报告编写
5. ☐ 过程记录整理

### P2 - 优化
1. ☐ 代码优化
2. ☐ 文档完善
3. ☐ 性能调优

---

## 📝 关键里程碑

- [x] **M1**: 环境配置完成
- [x] **M1.5**: 代码分支管理完成（保留原始版本）
- [x] **M2**: Memory Manager 设计完成
- [ ] **M3**: 核心代码实现完成
- [ ] **M4**: 与 agent 集成完成
- [ ] **M5**: Baseline 测试完成（原始版本运行3个任务）
- [ ] **M5.5**: Memory 版本测试完成
- [ ] **M6**: Before/After 对比分析完成
- [ ] **M7**: 所有任务测试完成
- [ ] **M8**: 文档编写完成
- [ ] **M9**: 最终提交

---

## 🔜 下一步

**根据你的需求，我已经添加了以下内容：**

### ✅ 已完成更新
1. **对比测试框架** - 添加了评价指标体系和3个测试任务
2. **代码分支管理** - 添加了保留原始版本的要求
3. **Before/After 对比** - 添加了对比分析和报告要求
4. **里程碑更新** - 添加了 M1.5, M5, M5.5, M6 等新里程碑

### 🎯 当前最紧急的任务

**请选择下一步：**

1. 📦 **创建代码分支** - 创建 `versions/baseline/` 并保留原始代码（最重要！）
2. 🏗️ **Memory 架构设计** - 讨论 memory 分层结构和组件设计
3. 📝 **任务代码分析** - 深入分析现有 agent 代码
4. 🎯 **功能选择** - 确定实现哪3个功能
5. 🚀 **快速开始** - 直接开始实现

**建议**: 先完成代码分支管理（任务1），这是后续所有对比测试的基础！
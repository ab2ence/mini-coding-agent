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

## 🎯 核心功能需求（4选3）

- [ ] **Rolling Summary** - 滚动摘要
- [ ] **Pinned Facts / Constraints** - 关键约束保留
- [ ] **Tool Output Compression** - 工具输出压缩
- [ ] **Task-State Segmentation** - 任务状态分段

---

## 📦 提交物清单

### 1. 可运行代码 ✅
- [ ] Memory Manager 实现 (`memory_manager.py`)
- [ ] 与现有 agent 集成
- [ ] 支持多轮 coding tasks
- [ ] 输出 memory 相关指标

### 2. README 📝
- [ ] Memory 设计说明
- [ ] 设计理由
- [ ] 触发压缩/摘要的时机
- [ ] 关键约束保护机制
- [ ] noisy tool outputs 处理方式
- [ ] 主要 trade-off
- [ ] 方案局限性

### 3. 结果报告 📊
- [ ] 压缩前后上下文长度对比
- [ ] 至少一个成功案例
- [ ] 至少一个失败/退化案例
- [ ] 关键权衡点说明

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
- [ ] 测试 mini-coding-agent 基本功能

#### 1.2 代码分析
- [ ] 阅读 `mini_coding_agent.py` 核心代码
- [ ] 理解现有 memory 机制
- [ ] 理解 session 持久化逻辑
- [ ] 分析 transcript 处理流程
- [ ] 定位需要修改的关键位置

#### 1.3 任务理解
- [ ] 分析 Task 1: Decision Retention
- [ ] 分析 Task 2: Noisy Tool Output
- [ ] 分析 Task 3: Long Workflow
- [ ] 理解评测脚本逻辑

**阶段产出**: 环境验证报告、代码分析笔记

---

### Phase 2: Memory Manager 设计 🎨

#### 2.1 架构设计
- [ ] 确定采用的功能（4选3）
- [ ] 设计 memory 分层结构
- [ ] 设计组件接口
- [ ] 设计压缩/摘要触发机制
- [ ] **讨论**: 详细设计每个模块

**Memory 分层设计**（待讨论）:
```python
# 示例结构
Memory:
├── recent_conversations    # 最近N轮原始对话
├── rolling_summary          # 滚动摘要
├── pinned_facts            # 关键约束/决策
├── task_state              # 当前任务状态/TODO
└── tool_evidence           # 关键工具证据
```

#### 2.2 核心组件设计
- [ ] **讨论**: Rolling Summary 模块设计
- [ ] **讨论**: Pinned Facts 提取与保护机制
- [ ] **讨论**: Tool Output 压缩策略
- [ ] **讨论**: Task-State 管理机制

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

#### 5.1 功能测试
- [ ] 测试 Memory Manager 基本功能
- [ ] 测试与 agent 集成
- [ ] 验证各功能正常工作

#### 5.2 任务测试
- [ ] 运行 Task 1: Decision Retention
- [ ] 运行 Task 2: Noisy Tool Output
- [ ] 运行 Task 3: Long Workflow
- [ ] 收集评测指标

#### 5.3 性能验证
- [ ] 测量上下文长度变化
- [ ] 测量 token 消耗
- [ ] 验证压缩效果
- [ ] 分析任务完成质量

**阶段产出**: 测试结果、性能指标

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
- [ ] ☐ README 已完成
- [ ] ☐ 结果报告已包含
- [ ] ☐ 过程记录已包含
- [ ] ☐ 运行说明已提供
- [ ] ☐ 代码可读性检查通过
- [ ] ☐ 功能测试通过

**阶段产出**: 完整可提交的代码包

---

## 🎯 交付物清单

| 交付物 | 状态 | 位置 |
|--------|------|------|
| 可运行代码 | ☐ | 待确定 |
| README | ☐ | 待确定 |
| 结果报告 | ☐ | 待确定 |
| 过程记录 | ☐ | 待确定 |
| 运行说明 | ☐ | 待确定 |

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
- [ ] **M2**: Memory Manager 设计完成
- [ ] **M3**: 核心代码实现完成
- [ ] **M4**: 与 agent 集成完成
- [ ] **M5**: 基本功能测试通过
- [ ] **M6**: 所有任务测试完成
- [ ] **M7**: 文档编写完成
- [ ] **M8**: 最终提交

---

## 🔜 下一步

**请告诉我你想先讨论哪个部分：**

1. 🏗️ **Memory 架构设计** - 讨论 memory 分层结构和组件设计
2. 📝 **任务代码分析** - 深入分析现有 agent 代码
3. 🎯 **功能选择** - 确定实现哪3个功能
4. 🚀 **快速开始** - 直接开始实现

或者你有其他优先级，请告诉我！
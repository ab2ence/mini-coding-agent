# Task 1: Decision Retention 测试 (With-Memory)

## 任务描述

**目标**: 测试关键约束和决策保留能力（Memory 优化版本）

## 测试文件

- `test_task1_with_memory.py`: 使用 Memory Manager 的测试脚本
- `README.md`: 本文件

## 与 Baseline 的区别

### Baseline 版本
- 无优化，关键约束可能被遗忘

### With-Memory 版本
- 使用 Pinned Facts 机制显式提取和保护约束
- 使用 Rolling Summary 管理对话历史
- 关键约束始终可访问

## 运行方法

```bash
# 激活 conda 环境
conda activate minicodeagent

# 运行测试
cd versions/with-memory/tests/task_01_decision_retention
python test_task1_with_memory.py
```

## 预期改进

- 约束保留率: > 90%
- 上下文长度: 得到控制

## 检查点

- [ ] 测试脚本可运行
- [ ] 约束保留率提升
- [ ] 上下文长度得到控制
- [ ] 与 Baseline 对比分析完成

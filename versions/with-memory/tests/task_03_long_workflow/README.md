# Task 3: Long Workflow 测试 (With-Memory)

## 任务描述

**目标**: 测试任务状态分段管理能力（Memory 优化版本）

## 测试文件

- `test_task3_with_memory.py`: 使用 Memory Manager 的测试脚本
- `README.md`: 本文件

## 与 Baseline 的区别

### Baseline 版本
- 无显式任务状态管理
- 阶段识别准确率低

### With-Memory 版本
- 使用 Task-State Segmentation 机制
- 显式记录任务阶段和进度
- 保留已完成工作的追踪

## 运行方法

```bash
# 激活 conda 环境
conda activate minicodeagent

# 运行测试
cd versions/with-memory/tests/task_03_long_workflow
python test_task3_with_memory.py
```

## 预期改进

- 阶段识别准确率: > 80%
- 最终总结准确率: > 80%

## 检查点

- [ ] 测试脚本可运行
- [ ] 阶段识别准确率提升
- [ ] 最终总结准确率提升
- [ ] 与 Baseline 对比分析完成

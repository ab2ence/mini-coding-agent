# Task 2: Noisy Tool Output 测试 (With-Memory)

## 任务描述

**目标**: 测试工具输出压缩能力（Memory 优化版本）

## 测试文件

- `test_task2_with_memory.py`: 使用 Memory Manager 的测试脚本
- `README.md`: 本文件

## 与 Baseline 的区别

### Baseline 版本
- 无压缩，压缩率为 1.0

### With-Memory 版本
- 使用 Tool Output Compression 机制
- 提取关键信息（error signature）
- 去重和分层保留

## 运行方法

```bash
# 激活 conda 环境
conda activate minicodeagent

# 运行测试
cd versions/with-memory/tests/task_02_noisy_tool_output
python test_task2_with_memory.py
```

## 预期改进

- Tool Output 压缩率: < 0.6（Task 2 要求）
- 上下文长度: 显著降低

## 检查点

- [ ] 测试脚本可运行
- [ ] 压缩率 < 0.6
- [ ] 上下文长度显著降低
- [ ] 与 Baseline 对比分析完成

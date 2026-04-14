# Task 2: Noisy Tool Output 测试

## 任务描述

**目标**: 测试工具输出压缩能力

**考察点**:
1. Tool output 是否分层保留
2. 是否会提取 error signature / key lines
3. 是否会避免重复注入同一类长日志

## 测试文件

- `test_task2.py`: 自动化测试脚本
- `README.md`: 本文件

## 运行方法

```bash
# 激活 conda 环境
conda activate minicodeagent

# 运行测试
cd versions/baseline/tests/task_02_noisy_tool_output
python test_task2.py
```

## 测试场景

1. 运行产生大量输出的测试
2. 执行包含长日志的搜索操作
3. 分析 traceback 中的关键信息
4. 测量压缩率

## 预期结果

### Baseline 版本（无优化）

**预期行为**:
- 所有工具输出原样保留
- 上下文快速膨胀
- 重复信息多次出现

**预期指标**:
- Tool Output 压缩率: 1.0（无压缩）
- 上下文长度: 快速增加

### With-Memory 版本（优化后）

**预期行为**:
- 工具输出被压缩和分层
- 关键信息（error signature）被提取
- 重复信息被去重

**预期指标**:
- Tool Output 压缩率: < 0.6（Task 2 要求）
- 上下文长度: 得到控制

## 检查点

- [ ] 测试脚本可运行
- [ ] 收集 Tool Output 压缩率
- [ ] 收集上下文长度变化
- [ ] 分析关键信息提取效果

## 状态

- [ ] 测试脚本已创建
- [ ] 基本功能测试通过
- [ ] 性能指标已收集
- [ ] 对比分析已完成

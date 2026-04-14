# Baseline 版本 - 未优化的原始代码

## 目录说明

本目录包含 **mini-coding-agent 的原始版本**，即在添加任何 Memory 优化之前的代码。

## 文件说明

- `mini_coding_agent_original.py`: 原始的 mini-coding-agent 代码，未添加任何 memory 优化
- `README.md`: 本文件

## 版本信息

- **创建时间**: 2026-04-14
- **代码状态**: 原始版本，无 memory 优化
- **代码大小**: 40,269 字节

## 用途

这个版本用于 **对比测试**，确保我们能够：

1. **验证原始行为**: 确认未优化的代码在测试任务上的表现
2. **Before/After 对比**: 与添加 Memory Manager 后的版本进行对比
3. **性能基准**: 建立性能基准，衡量 Memory 优化的效果

## 测试任务

原始版本将用于运行以下测试任务：

1. **Task 1: Decision Retention** - 关键约束保留
2. **Task 2: Noisy Tool Output** - 工具输出压缩
3. **Task 3: Long Workflow** - 任务状态分段

## 运行方法

```bash
# 激活 conda 环境
conda activate minicodeagent

# 运行原始版本
cd versions/baseline
python mini_coding_agent_original.py

# 或者直接运行测试脚本
cd ../..
python test_baseline.py
```

## 对比矩阵

| 版本 | 位置 | 说明 |
|------|------|------|
| **Baseline** | `versions/baseline/mini_coding_agent_original.py` | 原始版本，无优化 |
| **With Memory** | `mini_coding_agent.py` 或 `versions/with-memory/` | 添加 Memory Manager 后的版本 |

## 注意事项

- ⚠️ **不要修改本目录中的文件** - 保持原始代码的完整性
- ✅ 可以自由运行和测试
- ✅ 用于对比分析和性能基准建立

## 验证状态

- [x] 文件已保存
- [ ] 基本功能测试通过
- [ ] 所有测试任务完成
- [ ] 性能指标已收集

# With-Memory 版本 - 添加 Memory Manager 优化后的代码

## 目录说明

本目录用于存放 **添加 Memory Manager 优化后** 的 mini-coding-agent 代码。

## 文件说明

- `README.md`: 本文件

## 用途

这个版本用于存放：

1. **Memory Manager 实现**: `memory_manager.py`
2. **优化后的 Agent**: 修改后的 `mini_coding_agent.py`
3. **集成代码**: 将 Memory Manager 集成到现有 agent 的代码

## 预计实现的功能

根据笔试要求，至少实现以下 4 项中的 3 项：

- [ ] **Rolling Summary** - 滚动摘要
- [ ] **Pinned Facts / Constraints** - 关键约束保留
- [ ] **Tool Output Compression** - 工具输出压缩
- [ ] **Task-State Segmentation** - 任务状态分段

## 版本信息

- **创建时间**: 2026-04-14
- **代码状态**: 待实现
- **目标**: 在 baseline 基础上添加 Memory 优化

## 与 Baseline 的对比

| 版本 | 位置 | 说明 | 状态 |
|------|------|------|------|
| **Baseline** | `versions/baseline/mini_coding_agent_original.py` | 原始版本，无优化 | ✅ 已完成 |
| **With Memory** | `versions/with-memory/` | 添加 Memory 优化 | ⏳ 待实现 |

## 性能对比指标

添加 Memory Manager 后，预期在以下方面有所改善：

1. **上下文压缩率**: 降低 token 消耗
2. **Tool Output 压缩率**: 目标 < 0.6（Task 2 要求）
3. **关键约束保留率**: 提升（Task 1 要求）
4. **任务状态清晰度**: 提升（Task 3 要求）

## 注意事项

- ✅ 可以自由修改本目录中的文件
- ✅ 用于开发 Memory Manager 功能
- ⚠️ 记得定期与 baseline 版本对比
- ⚠️ 确保代码可读性和可维护性

## 下一步

1. 实现 Memory Manager (`memory_manager.py`)
2. 集成到 `mini_coding_agent.py`
3. 运行对比测试
4. 收集性能指标
5. 编写结果报告

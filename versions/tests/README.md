# 测试套件总览

## 目录结构

```
versions/
├── baseline/                      # Baseline 版本测试
│   └── tests/
│       ├── task_01_decision_retention/
│       │   ├── test_task1.py
│       │   ├── test_results.json
│       │   └── README.md
│       ├── task_02_noisy_tool_output/
│       │   ├── test_task2.py
│       │   ├── test_results.json
│       │   └── README.md
│       └── task_03_long_workflow/
│           ├── test_task3.py
│           ├── test_results.json
│           └── README.md
│
├── with-memory/                  # With-Memory 版本测试
│   └── tests/
│       ├── task_01_decision_retention/
│       │   ├── test_task1_with_memory.py
│       │   ├── test_results_with_memory.json
│       │   └── README.md
│       ├── task_02_noisy_tool_output/
│       │   ├── test_task2_with_memory.py
│       │   ├── test_results_with_memory.json
│       │   └── README.md
│       └── task_03_long_workflow/
│           ├── test_task3_with_memory.py
│           ├── test_results_with_memory.json
│           └── README.md
│
└── run_all_tests.py              # 统一测试运行脚本
```

## 测试任务

### Task 1: Decision Retention
- **考察**: 关键约束和决策保留能力
- **Baseline 预期**: 约束保留率低
- **With-Memory 预期**: 约束保留率高

### Task 2: Noisy Tool Output
- **考察**: 工具输出压缩能力
- **Baseline 预期**: 压缩率 1.0（无压缩）
- **With-Memory 预期**: 压缩率 < 0.6

### Task 3: Long Workflow
- **考察**: 任务状态分段管理能力
- **Baseline 预期**: 阶段识别准确率低
- **With-Memory 预期**: 阶段识别准确率高

## 运行方法

### 运行单个测试

```bash
# Baseline 版本
cd versions/baseline/tests/task_01_decision_retention
python test_task1.py

# With-Memory 版本
cd versions/with-memory/tests/task_01_decision_retention
python test_task1_with_memory.py
```

### 运行所有测试

```bash
cd versions
python run_all_tests.py
```

### 查看测试结果

```bash
# 查看单个测试结果
cat versions/baseline/tests/task_01_decision_retention/test_results.json

# 查看测试汇总
cat versions/test_summary.json
```

## 评价指标

### Task 1: Decision Retention
| 指标 | Baseline | With-Memory | 目标 |
|------|----------|-------------|------|
| 约束保留率 | < 50% | > 90% | 高 |
| 上下文增长 | 快 | 受控 | 受控 |

### Task 2: Noisy Tool Output
| 指标 | Baseline | With-Memory | 目标 |
|------|----------|-------------|------|
| 压缩率 | 1.0 | < 0.6 | < 0.6 |

### Task 3: Long Workflow
| 指标 | Baseline | With-Memory | 目标 |
|------|----------|-------------|------|
| 阶段识别准确率 | < 50% | > 80% | 高 |
| 最终总结准确率 | < 50% | > 80% | 高 |

## 下一步

1. 运行所有测试
2. 收集性能指标
3. 生成 Before/After 对比报告
4. 分析改进效果

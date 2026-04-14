# Claw Code 记忆与上下文管理机制设计文档

> 本文档基于 Claw Code 开源项目的源码分析，总结其在 AI 编程助手场景下的多层记忆系统设计、上下文压缩技术和缓存策略。这些设计思路可应用于多智能体系统的上下文管理和记忆机制优化。

---

## 一、设计理念

### 1.1 核心原则

Claw Code 的记忆系统遵循以下核心原则：

1. **层级分离**：短期会话记忆与长期项目记忆分离，避免相互干扰
2. **成本意识**：通过压缩和缓存双重机制降低 API 调用成本
3. **渐进式遗忘**：模拟人类记忆模式，早期信息通过摘要保留
4. **工作区隔离**：多项目并行时确保记忆不会混淆
5. **可追溯性**：所有压缩和缓存操作都有日志，便于审计

### 1.2 记忆分类

```
┌─────────────────────────────────────────────────────────┐
│                    长期项目记忆                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ 层级指令文件 │  │ 项目配置    │  │ Git 上下文       │ │
│  │ (CLAUDE.md) │  │ (.claw.json)│  │ (状态+diff)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                        ▼                                │
│                    短期会话记忆                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ 消息历史    │  │ Prompt历史  │  │ 会话元数据      │ │
│  │ (Messages)  │  │ (Prompts)   │  │ (Metadata)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                        ▼                                │
│                    优化缓存层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ Prompt缓存  │  │ 上下文压缩  │  │ Token估算       │ │
│  │ (API响应)  │  │ (摘要生成)  │  │ (成本控制)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 二、多层记忆系统架构

### 2.1 会话级记忆 (Session Memory)

#### 设计思路

会话记忆是最活跃的记忆层，存储当前交互的所有消息。每个会话是独立的上下文单元。

#### 核心数据结构

```markdown
Session {
  session_id: String,           // 唯一标识符
  created_at: Timestamp,       // 创建时间
  updated_at: Timestamp,       // 最后更新时间
  messages: Vec<Message>,      // 对话消息列表
  compaction: Option<Summary>,  // 压缩摘要（如果有）
  fork: Option<ForkInfo>,      // 分支信息（用于并行会话）
  workspace_root: Path,        // 绑定的工作区
  model: String,               // 使用的模型
}
```

#### 关键特性

1. **持久化格式**：使用 JSON Lines 格式，支持增量写入
2. **文件轮转**：超过 256KB 自动创建新文件，保留最近 3 个历史文件
3. **工作区指纹**：基于工作区路径生成哈希，避免多项目记忆混淆

#### 存储结构

```
<project>/.claw/sessions/<workspace_hash>/
├── <session_id>.jsonl        # 主会话文件
├── <session_id>-1.jsonl     # 历史轮转文件
├── <session_id>-2.jsonl     # 更早的历史
└── <session_id>-3.jsonl     # 最早的历史
```

### 2.2 项目级记忆 (Project Memory)

#### 设计思路

项目级记忆存储不随会话变化的长期知识，通过文件系统层级实现继承。

#### 指令文件发现规则

```markdown
发现顺序（从根目录到当前目录）：

1. <root>/CLAUDE.md           # 项目根级指令
2. <root>/CLAUDE.local.md     # 本地覆盖（不提交到 git）
3. <root>/.claw/CLAUDE.md     # 配置目录指令
4. <root>/.claw/instructions.md

5. <parent>/CLAUDE.md         # 父目录指令（累积）
6. <parent>/CLAUDE.local.md

7. <current>/CLAUDE.md        # 当前目录指令
8. <current>/CLAUDE.local.md
```

#### 继承机制

子目录的指令会**追加**到父目录指令之后，形成累积效果。这允许：
- 项目根定义通用规则
- 子目录定义特定模块的规则
- 本地文件（CLAUDE.local.md）用于个人偏好，不提交到版本控制

#### 指令文件内容类型

```markdown
1. 技术栈指导：使用的语言、框架、代码风格
2. 项目规范：命名约定、目录结构、模块划分
3. 工作流程：开发流程、测试要求、提交规范
4. 约束条件：禁止的操作、必须遵守的规则
5. 上下文知识：业务逻辑、设计决策、历史原因
```

### 2.3 环境上下文 (Environment Context)

#### Git 上下文

自动捕获并注入：
- **分支状态**：当前分支、未合并的远程分支
- **暂存变更**：已 `git add` 的文件
- **未暂存变更**：工作目录中的修改
- **关键文件**：`CHANGELOG.md`、`CONTRIBUTING.md` 等

#### 动态上下文

```markdown
- 当前日期和时间
- 工作目录路径
- 操作系统和版本
- 可用的工具链（编译器、解释器等）
- 环境变量（选择性地暴露）
```

---

## 三、上下文压缩技术

### 3.1 设计目标

当会话长度接近模型的上下文窗口限制时，需要将早期消息转换为摘要形式，保留核心信息的同时释放上下文空间。

### 3.2 压缩触发条件

```markdown
触发条件（需同时满足）：
1. 可压缩消息数 > 保留消息数
2. 可压缩消息的 Token 数 >= 压缩阈值（默认 10,000）
```

**默认配置**：
- 保留最近消息数：4 条
- 压缩阈值：10,000 tokens
- 自动压缩阈值：100,000 tokens（环境变量控制）

### 3.3 摘要生成算法

#### 步骤 1：消息聚类

将消息按角色分类统计：
```markdown
- 用户消息数
- 助手消息数
- 工具调用消息数
```

#### 步骤 2：工具提取

从消息中提取所有工具调用信息：
```markdown
- 工具名称列表（去重）
- 工具调用次数统计
- 工具调用结果摘要
```

#### 步骤 3：关键信息提取

```markdown
1. 用户请求摘要（最近 3 条）
   - 提取每个用户消息的核心意图
   - 截断到 160 字符

2. 待办工作推断
   - 从助手回复中推断未完成的任务
   - 从工具调用中识别目标状态

3. 关键文件追踪
   - 提取被修改/读取的文件路径
   - 识别项目中的重要文件

4. 当前工作识别
   - 最近一次操作的意图
   - 正在处理的问题
```

#### 步骤 4：时间线生成

```markdown
按时间顺序生成消息摘要：
- role: 消息角色
- content: 消息内容的压缩表示

工具调用的特殊格式：
- tool_use: tool_name(input)
- tool_result: tool_name: [success/error]output
```

### 3.4 安全边界处理

#### 问题

压缩边界可能恰好落在 `tool_use` 和 `tool_result` 之间，导致工具调用对被拆分。

#### 解决方案

```markdown
1. 检测拆分：如果保留的第一条消息是 tool_result
2. 回退检查：查看前一条消息是否为对应的 tool_use
3. 安全包含：如果配对被拆分，则同时保留两条消息
```

这解决了某些 API（如 OpenAI 兼容接口）的 **"tool message must follow assistant with tool_calls"** 错误。

### 3.5 增量压缩

#### 问题

长会话可能需要多次压缩，如何保留历史压缩的上下文？

#### 解决方案

```markdown
合并压缩摘要：
1. 提取之前压缩的高亮内容（关键决策、重要变更）
2. 提取新压缩的高亮内容
3. 合并时间线（仅保留最新段）
4. 格式：

<summary>
- Previously compacted context:
  - [历史关键信息 1]
  - [历史关键信息 2]

- Newly compacted context:
  - [新压缩的关键信息 1]
  - [新压缩的关键信息 2]

- Key timeline:
  - [最新消息的时间线]
</summary>
```

### 3.6 压缩后的会话结构

```markdown
压缩后的 Session.messages 结构：

[0] System Message (压缩摘要)
    - 压缩前言
    - 历史摘要
    - 最近消息保留提示
    - 继续指令

[1...N] 保留的消息（最近 N 条）
```

---

## 四、Prompt 缓存技术

### 4.1 设计目标

对于相同的请求（相同的 system prompt + tools + messages），缓存 API 响应以避免重复调用，降低成本。

### 4.2 缓存架构

```
┌─────────────────────────────────────────────┐
│            Prompt 缓存层                    │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │        请求指纹 (Fingerprint)        │   │
│  │  - model_hash                       │   │
│  │  - system_hash                      │   │
│  │  - tools_hash                       │   │
│  │  - messages_hash                    │   │
│  └─────────────────────────────────────┘   │
│                    │                       │
│                    ▼                       │
│  ┌─────────────────────────────────────┐   │
│  │         缓存存储 (Cache Store)       │   │
│  │  - 响应内容                          │   │
│  │  - 缓存时间戳                        │   │
│  │  - Token 使用统计                    │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 4.3 指纹系统

#### 哈希算法选择

使用 **FNV-1a** 哈希算法：
- 确定性：相同输入产生相同哈希
- 快速：适合实时计算
- 跨平台：结果稳定，不受运行环境影响

#### 指纹组成

```markdown
TrackedPromptState {
  model_hash:          // 模型名称的哈希
  system_hash:         // 系统提示的哈希
  tools_hash:          // 工具定义的哈希
  messages_hash:       // 消息载荷的哈希
  cache_read_input_tokens:  // 缓存读取的 token 数
  observed_at:         // 时间戳
  fingerprint_version: // 版本号（用于强制失效）
}
```

### 4.4 缓存失效检测

#### 检测类型

```markdown
1. 版本升级
   - fingerprint_version 变化
   - 通常由系统升级触发
   - 预期行为，无需告警

2. 内容变更
   - model/system/tools/messages 哈希任一变化
   - 原因记录：model changed / system prompt changed 等

3. TTL 过期
   - 默认 5 分钟无活动
   - 记录经过的时间

4. Token 下降
   - 缓存读取 token 数下降超过阈值（默认 2,000）
   - 可能表示模型端缓存失效
```

#### 异常检测

```markdown
如果指纹未变但 token 下降：
- 标记为 unexpected: true
- 记录告警
- 可能需要人工检查
```

### 4.5 缓存配置

```markdown
PromptCacheConfig {
  session_id:              // 会话标识
  completion_ttl:  30秒   // 完成结果缓存时间
  prompt_ttl:     5分钟   // 提示状态缓存时间
  cache_break_min_drop: 2000  // Token 下降阈值
}
```

### 4.6 统计追踪

```markdown
缓存统计指标：
- tracked_requests:      // 追踪的请求总数
- cache_hits:           // 缓存命中次数
- cache_misses:         // 缓存未命中次数
- cache_writes:         // 缓存写入次数
- expected_invalidations: // 预期的缓存失效
- unexpected_cache_breaks: // 异常的缓存失效
- total_cache_creation_input_tokens:  // 创建缓存的 token 总数
- total_cache_read_input_tokens:     // 读取缓存的 token 总数
```

---

## 五、摘要压缩技术

### 5.1 设计目标

在需要显示或传输摘要时（如日志、报告），对文本进行压缩，保留核心信息。

### 5.2 压缩预算

```markdown
SummaryCompressionBudget {
  max_chars: 1,200,      // 最大字符数
  max_lines: 24,         // 最大行数
  max_line_chars: 160,   // 单行最大字符数
}
```

### 5.3 压缩算法

#### 步骤 1：规范化

```markdown
1. 去除首尾空白
2. 截断超长行（>160 字符）
3. 折叠行内多余空白
```

#### 步骤 2：去重

```markdown
使用有序集合（BTreeSet）移除重复行：
- 精确去重：完全相同的行
- 规范化后去重：去除空白后相同的行
```

#### 步骤 3：优先级选择

```markdown
行优先级分级（0-3，数字越小优先级越高）：

优先级 0（最高）：
  - 以 "- " 开头且包含 "request" 或 "work" 的列表项
  - 用户请求和待办工作

优先级 1：
  - 其他以 "- " 开头的列表项
  - 详细信息

优先级 2：
  - 以 "#" 或 "##" 开头的标题
  - 结构标记

优先级 3（最低）：
  - 其他内容
  - 辅助信息
```

#### 步骤 4：预算约束

```markdown
选择算法：
1. 按优先级从低到高遍历
2. 检查添加后是否超出预算（行数/字符数）
3. 未超出则加入选择集
4. 超出则跳过，尝试更低优先级的行
```

#### 步骤 5：省略提示

```markdown
如果跳过了部分行，添加省略提示：
"[... N lines omitted ...]"
```

### 5.4 压缩结果

```markdown
SummaryCompressionResult {
  summary: String,                    // 压缩后的文本
  original_chars: usize,             // 原始字符数
  compressed_chars: usize,            // 压缩后字符数
  original_lines: usize,              // 原始行数
  compressed_lines: usize,            // 压缩后行数
  removed_duplicate_lines: usize,     // 移除的重复行数
  omitted_lines: usize,               // 省略的行数
  truncated: bool,                    // 是否被截断
}
```

---

## 六、多智能体系统设计建议

### 6.1 层级记忆架构

#### Agent 级别记忆

每个 Agent 应维护自己的会话记忆：

```markdown
Agent Session {
  agent_id: String,
  session_id: String,
  messages: Vec<Message>,
  summary: Option<CompressedSummary>,  // 压缩摘要
  created_at: Timestamp,
  last_active: Timestamp,
}
```

#### Team 级别记忆

多智能体团队应有共享的项目记忆：

```markdown
Team Project Memory {
  project_id: String,
  shared_instructions: Vec<InstructionFile>,
  team_charter: String,              // 团队职责定义
  shared_context: SharedContext,       // 共享的上下文
  tool_registry: ToolRegistry,         // 团队可用的工具
}
```

#### 全局记忆（可选）

跨项目的全局知识库：

```markdown
Global Memory {
  organization_id: String,
  global_rules: Vec<Rule>,           // 全局约束
  common_patterns: Vec<Pattern>,      // 通用模式
  learnings: Vec<LearnedKnowledge>,   // 学习的知识
}
```

### 6.2 记忆同步策略

#### 同步类型

```markdown
1. 拉取同步（Pull）
   - Agent 启动时拉取团队共享记忆
   - 定期检查更新

2. 推送同步（Push）
   - 重要决策后推送到团队共享记忆
   - 使用事件驱动

3. 广播同步（Broadcast）
   - 团队规则变更时广播
   - 使用发布-订阅模式
```

#### 冲突解决

```markdown
冲突类型及解决策略：

1. 指令冲突
   - 更高层级的指令优先（全局 > 团队 > 项目 > Agent）
   - 同层级：最后写入优先

2. 状态冲突
   - 使用向量时钟（Vector Clock）跟踪版本
   - 合并冲突：保留所有版本的变更
   - 覆盖冲突：使用最新时间戳

3. 工具注册冲突
   - 团队管理员授权
   - 工具名称冲突时拒绝注册
```

### 6.3 分布式压缩策略

#### 压缩触发点

```markdown
1. 单 Agent 级别
   - 本会话达到阈值时触发
   - 生成 Agent 级别的摘要

2. Team 级别
   - 汇总所有 Agent 的摘要
   - 生成团队级别的摘要

3. 全局级别（可选）
   - 跨团队共享的知识压缩
   - 提取跨项目的模式
```

#### 摘要传播

```markdown
压缩后的摘要传播流程：

1. Agent A 生成摘要
2. 发布到 Team 共享空间
3. 其他 Agent 可选择性地获取摘要
4. Team 定期汇总 Agent 摘要
5. 全局层面定期提取团队摘要
```

### 6.4 分布式缓存策略

#### 缓存层级

```markdown
Level 1: Agent 本地缓存
  - 最近的 API 响应
  - 本地计算的指纹
  - 内存级，速度最快

Level 2: Team 共享缓存
  - 团队常用请求的响应
  - 共享的工具定义缓存
  - 网络级，有一定延迟

Level 3: 全局缓存（可选）
  - 组织级通用请求
  - 跨团队的共享知识
  - 最慢但最共享
```

#### 缓存一致性

```markdown
一致性保证策略：

1. 最终一致性
   - 缓存更新异步传播
   - 适用于非关键数据

2. 版本向量
   - 使用向量时钟跟踪缓存版本
   - 客户端可检测并处理冲突

3. TTL + 版本号
   - 每个缓存项有 TTL
   - 版本号变化时强制刷新
```

### 6.5 上下文边界管理

#### Agent 上下文限制

```markdown
每个 Agent 应有上下文预算：

AgentContextBudget {
  max_tokens: 100_000,           // 最大 token 数
  reserve_tokens: 10_000,        // 保留空间（用于紧急操作）
  warning_threshold: 80_000,      // 警告阈值
  critical_threshold: 95_000,     // 临界阈值
}
```

#### 上下文分配策略

```markdown
消息优先级（分配上下文空间）：

高优先级：
  1. 当前任务相关消息
  2. 团队指令
  3. 工具定义

中优先级：
  4. 相关文件的摘要
  5. 最近的操作历史

低优先级（可压缩）：
  6. 早期对话历史
  7. 不相关的上下文
```

### 6.6 团队协调记忆

#### 共享工作区

```markdown
Team Workspace {
  workspace_id: String,
  workspace_root: Path,
  shared_files: Vec<FilePath>,
  locks: Mutex<Map<Path, Owner>>,  // 文件锁
  events: EventLog,                  // 事件日志
}
```

#### 任务注册表

```markdown
TaskRegistry {
  tasks: Map<TaskId, TaskRecord>,

  TaskRecord {
    id: TaskId,
    creator: AgentId,
    status: Pending|InProgress|Completed|Failed,
    created_at: Timestamp,
    assigned_to: Option<AgentId>,
    dependencies: Vec<TaskId>,
    output: Option<String>,
  }
}
```

#### 团队事件总线

```markdown
事件类型：

1. 任务事件
   - TaskCreated
   - TaskAssigned
   - TaskCompleted
   - TaskFailed

2. 文件事件
   - FileCreated
   - FileModified
   - FileDeleted

3. 通信事件
   - MessageSent
   - ContextShared

4. 状态事件
   - AgentJoined
   - AgentLeft
   - Heartbeat
```

### 6.7 安全性考虑

#### 记忆隔离

```markdown
1. 项目隔离
   - 不同项目的记忆物理隔离
   - 使用加密存储

2. Agent 权限
   - 基于角色的访问控制（RBAC）
   - 最小权限原则

3. 敏感信息处理
   - API 密钥不存储在记忆中
   - 使用环境变量或密钥管理服务
```

#### 审计追踪

```markdown
记忆操作日志：

LogEntry {
  timestamp: Timestamp,
  agent_id: String,
  operation: Read|Write|Delete|Compress,
  target: MemoryPath,
  details: String,
  result: Success|Failure,
}
```

---

## 七、实现要点总结

### 7.1 核心设计模式

```markdown
1. 分层设计
   - 分离关注点：会话、项目、全局
   - 每层独立演化

2. 延迟计算
   - Token 估算使用近似算法（length/4）
   - 避免实时精确计算

3. 版本控制
   - 所有可缓存项都有版本号
   - 版本升级时自动失效

4. 统计驱动
   - 所有操作都有统计指标
   - 用于优化决策

5. 安全优先
   - 工具调用配对检查
   - 文件边界验证
```

### 7.2 关键权衡

```markdown
1. 压缩率 vs 信息保留
   - 高压缩率可能丢失重要上下文
   - 需要可配置的预算

2. 缓存命中率 vs 缓存新鲜度
   - 高命中率降低 API 调用成本
   - 但可能使用过期数据

3. 记忆持久性 vs 存储成本
   - 保留更多历史便于回溯
   - 但增加存储和检索成本

4. 同步实时性 vs 系统负载
   - 实时同步确保一致性
   - 但增加网络和计算开销
```

### 7.3 可配置参数

```markdown
建议的可配置参数（按场景调整）：

开发环境：
  - 压缩阈值：5,000 tokens
  - 保留消息：6 条
  - 缓存 TTL：60 秒

生产环境：
  - 压缩阈值：10,000 tokens
  - 保留消息：4 条
  - 缓存 TTL：30 秒

调试模式：
  - 压缩阈值：禁用（保留所有消息）
  - 保留消息：无限制
  - 缓存 TTL：0（禁用缓存）
```

---

## 八、参考架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        多智能体记忆系统                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Agent A    │  │  Agent B    │  │  Agent C    │             │
│  │  ┌───────┐  │  │  ┌───────┐  │  │  ┌───────┐  │             │
│  │  │Session│  │  │  │Session│  │  │  │Session│  │             │
│  │  └───────┘  │  │  └───────┘  │  │  └───────┘  │             │
│  │  ┌───────┐  │  │  ┌───────┐  │  │  ┌───────┐  │             │
│  │  │ L1    │  │  │  │ L1    │  │  │  │ L1    │  │             │
│  │  │Cache  │  │  │  │Cache  │  │  │  │Cache  │  │             │
│  │  └───────┘  │  │  └───────┘  │  │  └───────┘  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│              ┌───────────────────────┐                         │
│              │    Team Memory        │                         │
│              │  ┌─────────────────┐  │                         │
│              │  │ Shared Context │  │                         │
│              │  └─────────────────┘  │                         │
│              │  ┌─────────────────┐  │                         │
│              │  │  Task Registry │  │                         │
│              │  └─────────────────┘  │                         │
│              │  ┌─────────────────┐  │                         │
│              │  │    L2 Cache     │  │                         │
│              │  └─────────────────┘  │                         │
│              │  ┌─────────────────┐  │                         │
│              │  │  Event Bus     │  │                         │
│              │  └─────────────────┘  │                         │
│              └──────────┬───────────┘                         │
│                         │                                       │
│                         ▼                                       │
│              ┌───────────────────────┐                         │
│              │   Compression Engine  │                         │
│              │  ┌─────────────────┐  │                         │
│              │  │ Summary Generator│  │                         │
│              │  └─────────────────┘  │                         │
│              │  ┌─────────────────┐  │                         │
│              │  │ Token Estimator │  │                         │
│              │  └─────────────────┘  │                         │
│              └───────────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 九、总结

Claw Code 的记忆系统通过以下核心机制实现了高效的上下文管理：

1. **多层分离**：会话记忆、项目记忆、全局记忆各司其职
2. **智能压缩**：基于消息角色的优先级摘要生成
3. **指纹缓存**：FNV-1a 哈希 + TTL 的双层缓存失效检测
4. **增量更新**：多次压缩时保留历史上下文
5. **安全优先**：工具调用配对保护、文件边界验证

这些设计思路可以直接应用于多智能体系统的记忆和上下文管理，特别是在需要处理长对话、多 Agent 协作的场景下。

---

*文档版本：1.0*
*生成时间：2026-04-10*
*基于源码：ultraworkers/claw-code*

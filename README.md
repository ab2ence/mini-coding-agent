# Mini Coding Agent

本项目基于 [rasbt/mini-coding-agent](https://github.com/rasbt/mini-coding-agent) 进行二次开发。

有关原始项目的详细信息和详细教程，请访问 [Components of a Coding Agent](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)。

---

## 📋 目录

- [项目简介](#项目简介)
- [环境准备](#环境准备)
  - [Conda环境配置](#conda环境配置)
  - [API Key配置](#api-key配置)
  - [依赖安装](#依赖安装)
- [快速开始](#快速开始)
- [使用指南](#使用指南)

---

## 项目简介

Mini-Coding-Agent 是一个轻量级本地代码助手，具有以下核心功能：

- 🔍 **工作区快照收集** - 自动收集项目结构和上下文
- 📝 **稳定Prompt管理** - 优化的提示词设计
- 🛠️ **结构化工具集** - 文件读写、命令执行等
- ✅ **风险操作审批** - 危险的系统操作需要确认
- 💾 **会话持久化** - 支持中断恢复
- 🤖 **模型后端** - 基于 DeepSeek API，提供强大的代码生成能力
- 🧠 **Memory Manager** - 智能上下文压缩和约束保留（with-memory版本）

---

## 环境准备

### Conda环境配置

#### 1. 创建 conda 环境

如果还没有 conda 环境，创建新环境：

```powershell
conda create -n minicodeagent python=3.10
conda activate minicodeagent
```

#### 2. 验证 Python 版本

```powershell
python --version
```

确保输出为 Python 3.10.x

---

### API Key配置

#### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件：

```powershell
# 复制 .env-example 为 .env
copy .env-example .env
```

#### 2. 配置 API Key

编辑 `.env` 文件，填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

获取 API Key: [https://platform.deepseek.com/](https://platform.deepseek.com/)

---

### 依赖安装

安装所需的 Python 包：

```powershell
pip install openai python-dotenv
```

或者使用项目配置：

```powershell
pip install -e .
```

---

## 快速开始

### 启动 Mini Coding Agent

```powershell
# 激活 conda 环境
conda activate minicodeagent

# 进入项目目录
cd f:\programs\minicodingagent\mini-coding-agent

# 启动 Agent（使用 DeepSeek API）
python versions/baseline/mini_coding_agent_original.py

# 或启动带 Memory Manager 的版本
python versions/with-memory/mini_coding_agent.py
```

### 使用参数

**查看所有选项：**
```powershell
python versions/baseline/mini_coding_agent_original.py --help
```

**使用不同模型：**
```powershell
python versions/baseline/mini_coding_agent_original.py --model deepseek-chat
```

**自动审批模式（谨慎使用）：**
```powershell
python versions/baseline/mini_coding_agent_original.py --approval auto
```

**限制最大步数：**
```powershell
python versions/baseline/mini_coding_agent_original.py --max-steps 10
```

**恢复之前的会话：**
```powershell
python versions/baseline/mini_coding_agent_original.py --resume latest
```

---

## 使用指南

### 交互命令

在 Agent 运行期间，可使用以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/memory` | 显示当前会话的蒸馏记忆（仅with-memory版本） |
| `/session` | 显示保存的会话文件路径 |
| `/reset` | 清除当前会话历史和记忆 |
| `/exit` 或 `/quit` | 退出 Agent |

### 示例任务

启动 Agent 后，可以尝试以下任务：

1. **查看项目结构**
   ```
   帮我查看当前目录的所有文件
   ```

2. **创建新文件**
   ```
   帮我创建一个 hello.py 文件，包含一个打印"Hello World"的函数
   ```

3. **解释代码**
   ```
   解释一下 mini_coding_agent.py 的主要功能
   ```

4. **调试问题**
   ```
   我的代码出现了 ImportError 错误，请帮我看看
   ```

---

## 版本对比

### Baseline 版本
- 位置：`versions/baseline/mini_coding_agent_original.py`
- 功能：基础代码助手，无记忆管理
- 适用场景：简单任务，短对话

### With-Memory 版本
- 位置：`versions/with-memory/mini_coding_agent.py`
- 功能：
  - ✅ 滚动摘要 (Rolling Summary)
  - ✅ 关键约束保留 (Pinned Facts / Constraints)
  - ✅ 工具输出压缩 (Tool Output Compression)
  - ✅ 任务状态分段 (Task-State Segmentation)
- 适用场景：长对话、复杂任务、多轮协作

---

## 资源链接

- 🌐 [DeepSeek 官方平台](https://platform.deepseek.com/)
- 📚 [DeepSeek API 文档](https://platform.deepseek.com/docs)
- 🎓 [Coding Agent 教程](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)
- 🐙 [GitHub 源码](https://github.com/rasbt/mini-coding-agent)

---

*祝你使用愉快！ 🚀*

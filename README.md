# Mini Coding Agent

本项目基于 [rasbt/mini-coding-agent](https://github.com/rasbt/mini-coding-agent) 进行二次开发。

有关原始项目的详细信息和详细教程，请访问 [Components of a Coding Agent](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)。

---

## 📋 目录

- [项目简介](#项目简介)
- [环境准备](#环境准备)
  - [Ollama安装](#ollama安装)
  - [Conda环境配置](#conda环境配置)
  - [AI模型拉取](#ai模型拉取)
  - [环境验证](#环境验证)
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
- 🤖 **模型后端** - 基于 Ollama，支持多种本地模型

---

## 环境准备

### Ollama安装

#### 1. 下载 Ollama

访问 Ollama 官方网站下载 Windows 安装包：

🔗 **[https://ollama.com/download](https://ollama.com/download)**

#### 2. 安装 Ollama

1. 双击下载的 `OllamaSetup.exe`
2. 按照安装向导完成安装
3. 安装程序会自动将 Ollama 添加到系统 PATH

#### 3. 验证安装

打开终端（PowerShell 或 CMD），运行：

```powershell
ollama --version
```

如果看到版本号（如 `0.20.6`），则安装成功。

#### 4. 启动 Ollama 服务

Ollama 安装后会自动在后台运行。如果需要手动启动：

```powershell
ollama serve
```

服务默认运行在 `http://127.0.0.1:11434`

**验证服务状态：**

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/version
```

成功响应示例：
```json
{"version":"0.20.6"}
```

---

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

#### 3. 项目依赖

本项目**仅使用 Python 标准库**，无需额外安装依赖。但你可以安装测试框架（可选）：

```powershell
# 可选：安装测试框架
pip install pytest
```

---

### AI模型拉取

运行以下命令拉取模型：

```powershell
ollama pull qwen3.5:2b
```

---

### 环境验证

#### 1. 验证 Ollama 服务

```powershell
ollama list
```

确保你的模型出现在列表中。

#### 2. 测试模型响应

```powershell
ollama run qwen3.5:2b "你好"
```

如果模型正常回复，则环境配置成功。

#### 3. 验证 Python 环境

```powershell
conda activate minicodeagent
python --version
python -c "import urllib.request; print('✅ 标准库导入成功')"
```

---

#### 4. 验证 ollama 模型是否可用

```powershell
python test_ollama.py
```

---

## 快速开始

### 启动 Mini Coding Agent

```powershell
# 激活 conda 环境
conda activate minicodeagent

# 进入项目目录
cd f:\programs\minicodingagent\mini-coding-agent

# 启动 Agent（默认使用 qwen3.5:2b）
python mini_coding_agent.py
```

### 使用参数

**查看所有选项：**
```powershell
python mini_coding_agent.py --help
```

**使用不同模型：**
```powershell
python mini_coding_agent.py --model qwen3.5:2b
```

**自动审批模式（谨慎使用）：**
```powershell
python mini_coding_agent.py --approval auto
```

**限制最大步数：**
```powershell
python mini_coding_agent.py --max-steps 10
```

**恢复之前的会话：**
```powershell
python mini_coding_agent.py --resume latest
```

---

## 使用指南

### 交互命令

在 Agent 运行期间，可使用以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/memory` | 显示当前会话的蒸馏记忆 |
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

## 资源链接

- 📚 [Ollama 官方文档](https://ollama.ai/docs)
- 📖 [Qwen 模型库](https://ollama.com/library/qwen3.5)
- 🎓 [Coding Agent 教程](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)
- 🐙 [GitHub 源码](https://github.com/rasbt/mini-coding-agent)

---

*祝你使用愉快！ 🚀*

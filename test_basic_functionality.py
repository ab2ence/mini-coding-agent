"""
基本功能测试脚本
测试 mini-coding-agent 的核心功能
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mini_coding_agent import (
    FakeModelClient,
    MiniAgent,
    SessionStore,
    WorkspaceContext,
    build_welcome,
)


def test_workspace_context():
    """测试工作区上下文构建"""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)

        # 创建测试文件
        (tmp_path / "README.md").write_text("# Test Project\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")

        # 构建工作区上下文
        workspace = WorkspaceContext.build(tmp_path)

        print("[PASS] WorkspaceContext 构建成功")
        print(f"   - CWD: {workspace.cwd}")
        print(f"   - 项目文档: {workspace.project_docs}")
        return workspace


def test_session_store():
    """测试会话存储"""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)

        # 创建会话存储
        store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")

        print("[PASS] SessionStore 创建成功")
        print(f"   - 会话根目录: {store.root}")
        return store


def test_fake_model_client():
    """测试模拟模型客户端"""
    outputs = [
        '<tool>{"name":"read_file","args":{"path":"test.txt","start":1,"end":2}}</tool>',
        "<final>File read successfully.</final>",
    ]

    client = FakeModelClient(outputs)

    print("[PASS] FakeModelClient 创建成功")
    print(f"   - 预定义输出数量: {len(outputs)}")
    return client


def test_agent_initialization():
    """测试 Agent 初始化"""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)

        # 创建测试环境
        (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")

        # 构建组件
        workspace = WorkspaceContext.build(tmp_path)
        store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
        model_client = FakeModelClient(["<final>Hello!</final>"])

        # 创建 Agent
        agent = MiniAgent(
            model_client=model_client,
            workspace=workspace,
            session_store=store,
            approval_policy="auto",
        )

        print("[PASS] MiniAgent 初始化成功")
        print(f"   - 模型客户端: {type(agent.model_client).__name__}")
        print(f"   - 工作区: {agent.workspace.cwd}")
        print(f"   - 会话存储: {agent.session_store is not None}")
        return agent


def test_agent_ask():
    """测试 Agent 交互功能"""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)

        # 创建测试文件
        (tmp_path / "hello.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

        # 构建 Agent
        workspace = WorkspaceContext.build(tmp_path)
        store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
        model_client = FakeModelClient([
            '<tool>{"name":"read_file","args":{"path":"hello.txt","start":1,"end":2}}</tool>',
            "<final>File content: alpha, beta</final>",
        ])

        agent = MiniAgent(
            model_client=model_client,
            workspace=workspace,
            session_store=store,
            approval_policy="auto",
        )

        # 测试 ask 方法
        answer = agent.ask("Read hello.txt")

        print("[PASS] Agent.ask() 执行成功")
        print(f"   - 响应: {answer}")
        print(f"   - 历史记录数: {len(agent.session['history'])}")

        return agent


def test_welcome_message():
    """测试欢迎消息构建（跳过，需要交互式参数）"""
    # build_welcome 需要 agent, model, host 参数，需要在交互环境中使用
    # 这里简单测试函数存在性
    print("[PASS] build_welcome() 函数存在")
    print("   - 需要在交互式环境中测试")
    return True


def main():
    """运行所有基本功能测试"""
    print("=" * 60)
    print("Mini-Coding-Agent 基本功能测试")
    print("=" * 60)
    print()

    try:
        print("1. 测试 WorkspaceContext...")
        test_workspace_context()
        print()

        print("2. 测试 SessionStore...")
        test_session_store()
        print()

        print("3. 测试 FakeModelClient...")
        test_fake_model_client()
        print()

        print("4. 测试 MiniAgent 初始化...")
        test_agent_initialization()
        print()

        print("5. 测试 Agent 交互...")
        test_agent_ask()
        print()

        print("6. 测试欢迎消息...")
        test_welcome_message()
        print()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"[FAIL] 测试失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

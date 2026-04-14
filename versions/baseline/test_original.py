"""
Baseline 版本基本功能测试
验证原始版本（未优化）是否可以独立运行
"""
import sys
import tempfile
from pathlib import Path
import importlib.util

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 直接导入原始模块（从项目根目录）
from mini_coding_agent import (
    FakeModelClient,
    MiniAgent,
    SessionStore,
    WorkspaceContext,
)

# 验证我们导入的是原始版本
print(f"[INFO] 导入模块路径: {FakeModelClient.__module__}")


def test_original_workspace_context():
    """测试原始版本的 WorkspaceContext"""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        (tmp_path / "README.md").write_text("# Test Project\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")

        workspace = WorkspaceContext.build(tmp_path)
        print("[PASS] Baseline: WorkspaceContext 构建成功")
        return workspace


def test_original_session_store():
    """测试原始版本的 SessionStore"""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
        print("[PASS] Baseline: SessionStore 创建成功")
        return store


def test_original_agent():
    """测试原始版本的 Agent"""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        (tmp_path / "hello.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

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

        answer = agent.ask("Read hello.txt")
        print(f"[PASS] Baseline: Agent.ask() 执行成功 - 响应: {answer}")
        return agent


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Baseline 版本（原始代码）功能测试")
    print("=" * 60)
    print()

    try:
        print("1. 测试 WorkspaceContext...")
        test_original_workspace_context()
        print()

        print("2. 测试 SessionStore...")
        test_original_session_store()
        print()

        print("3. 测试 Agent 交互...")
        test_original_agent()
        print()

        print("=" * 60)
        print("BASELINE TESTS PASSED!")
        print("原始版本代码可以独立运行")
        print("=" * 60)
        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"[FAIL] Baseline 测试失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

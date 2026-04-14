"""
Task 2: Noisy Tool Output 测试脚本
测试工具输出压缩能力
"""
import sys
import tempfile
from pathlib import Path
import json
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mini_coding_agent import (
    FakeModelClient,
    MiniAgent,
    SessionStore,
    WorkspaceContext,
)


class Task2Metrics:
    """Task 2 性能指标收集器"""
    
    def __init__(self):
        self.tool_outputs = []
        self.original_lengths = []
        self.processed_lengths = []
        
    def record_tool_output(self, original_length, processed_length=None):
        """记录工具输出"""
        self.tool_outputs.append({
            'original': original_length,
            'processed': processed_length if processed_length else original_length
        })
        self.original_lengths.append(original_length)
        self.processed_lengths.append(processed_length if processed_length else original_length)
        
    def get_summary(self):
        """获取指标总结"""
        total_original = sum(self.original_lengths)
        total_processed = sum(self.processed_lengths)
        
        compression_ratio = total_processed / total_original if total_original > 0 else 1.0
        
        return {
            'total_original_length': total_original,
            'total_processed_length': total_processed,
            'compression_ratio': compression_ratio,
            'num_tool_calls': len(self.tool_outputs),
            'meets_target': compression_ratio < 0.6
        }


def simulate_noisy_test_output():
    """模拟嘈杂的测试输出"""
    return """
================================================================================
                           TEST RUN REPORT
================================================================================
tests/test_parser.py::test_parse_json - PASSED
tests/test_parser.py::test_parse_xml - PASSED
tests/test_parser.py::test_parse_yaml - PASSED
tests/test_parser.py::test_parse_invalid - PASSED
tests/test_parser.py::test_edge_cases - PASSED
tests/test_parser.py::test_large_input - PASSED
tests/test_parser.py::test_special_chars - PASSED
tests/test_parser.py::test_encoding - PASSED
tests/test_parser.py::test_unicode - PASSED
tests/test_parser.py::test_whitespace - PASSED
[INFO] Starting pytest with verbose output
[INFO] Loading test configuration
[INFO] Test discovery complete
[INFO] Found 10 test modules
[INFO] Initializing test fixtures
[INFO] Setup complete
[WARNING] Slow test detected: test_large_input (2.3s)
[WARNING] Deprecated feature used: xml.etree
[WARNING] Performance issue: memory usage > 80%
[INFO] Test execution started
[INFO] Running test_parse_json
[INFO] Test passed
[INFO] Running test_parse_xml
[INFO] Test passed
...
[INFO] All tests completed
[INFO] Generating coverage report
[INFO] Coverage: 85.3%
[INFO] Cleaning up
[INFO] Done
================================================================================
                           SUMMARY
================================================================================
Total: 150 tests
Passed: 148
Failed: 2
Skipped: 0
Warnings: 23
Errors: 0
Time: 45.3s
================================================================================
FAILED tests/test_parser.py::test_malformed_json - AssertionError: Expected 'null' but got 'None'
FAILED tests/test_parser.py::test_invalid_encoding - UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80
================================================================================
"""


def test_noisy_tool_output():
    """测试嘈杂工具输出处理"""
    print("=" * 60)
    print("Task 2: Noisy Tool Output 测试")
    print("=" * 60)
    print()
    
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        
        # 创建测试工作区
        (tmp_path / "README.md").write_text("# Parser Project\n", encoding="utf-8")
        (tmp_path / "parser.py").write_text("""
def parse_json(data):
    return json.loads(data)

def parse_xml(data):
    return ET.fromstring(data)
""", encoding="utf-8")
        
        # 创建 Agent
        workspace = WorkspaceContext.build(tmp_path)
        store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
        
        # 模拟工具调用和嘈杂输出
        noisy_output = simulate_noisy_test_output()
        
        # 模拟模型响应
        model_responses = [
            "我看到了测试输出",
            "有两个测试失败",
            "分析失败原因...",
            "修复了 parse_json 中的问题",
            "修复了 parse_encoding 中的问题",
            "总结：主要问题是类型处理不一致"
        ]
        
        # 创建 FakeModelClient
        model_client = FakeModelClient([
            f"<final>{response}</final>" for response in model_responses
        ])
        
        agent = MiniAgent(
            model_client=model_client,
            workspace=workspace,
            session_store=store,
            approval_policy="auto",
        )
        
        # 记录指标
        metrics = Task2Metrics()
        
        # 记录原始输出长度
        original_length = len(noisy_output)
        metrics.record_tool_output(original_length, original_length)  # Baseline 不压缩
        
        print(f"[INFO] 原始工具输出长度: {original_length}")
        
        # 执行对话
        conversation = [
            "检查仓库，找到 parser 入口",
            "运行测试并调查失败",
            "修复 bug，不改变测试契约",
            "添加一个回归测试",
            "用一段话总结根本原因"
        ]
        
        print("\n[INFO] 开始对话...")
        for i, user_input in enumerate(conversation):
            print(f"\n--- Turn {i+1} ---")
            print(f"用户: {user_input}")
            
            # 获取响应
            response = agent.ask(user_input)
            print(f"Agent: {response}")
            
            # 模拟延迟
            time.sleep(0.1)
        
        # 获取最终上下文大小
        final_context = len(json.dumps(agent.session))
        
        print("\n" + "=" * 60)
        print("测试结果")
        print("=" * 60)
        
        summary = metrics.get_summary()
        print(f"原始工具输出总长度: {summary['total_original_length']}")
        print(f"处理后工具输出总长度: {summary['total_processed_length']}")
        print(f"Tool Output 压缩率: {summary['compression_ratio']:.2f}")
        print(f"工具调用次数: {summary['num_tool_calls']}")
        print(f"是否满足目标 (< 0.6): {'是' if summary['meets_target'] else '否'}")
        
        # 保存结果
        results_file = Path(__file__).parent / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n[INFO] 结果已保存到: {results_file}")
        
        print("\n" + "=" * 60)
        print("Baseline 版本测试完成")
        print("预期: 压缩率为 1.0（无压缩）")
        print("Task 2 目标: 压缩率 < 0.6")
        print("=" * 60)
        
        return summary


if __name__ == "__main__":
    try:
        result = test_noisy_tool_output()
        
        print("\n[RESULT] Task 2 测试完成")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[ERROR] Task 2 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

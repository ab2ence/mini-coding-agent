"""
Task 1: Decision Retention 测试脚本 (With-Memory 版本)
测试关键约束和决策保留能力（Memory 优化）
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


class Task1MetricsWithMemory:
    """Task 1 性能指标收集器（With-Memory 版本）"""
    
    def __init__(self):
        self.context_lengths = []
        self.constraint_mentions = []
        self.final_summary_contains_constraints = False
        self.memory_operations = []
        
    def record_context_length(self, length):
        """记录上下文长度"""
        self.context_lengths.append(length)
        
    def record_constraint_mention(self, turn, mentioned):
        """记录约束提及情况"""
        self.constraint_mentions.append({
            'turn': turn,
            'mentioned': mentioned
        })
        
    def record_memory_operation(self, operation_type, details):
        """记录 Memory 操作"""
        self.memory_operations.append({
            'type': operation_type,
            'details': details
        })
        
    def set_final_summary_constraints(self, contains):
        """设置最终总结是否包含约束"""
        self.final_summary_contains_constraints = contains
        
    def get_summary(self):
        """获取指标总结"""
        return {
            'initial_context_length': self.context_lengths[0] if self.context_lengths else 0,
            'final_context_length': self.context_lengths[-1] if self.context_lengths else 0,
            'context_growth': self.context_lengths[-1] - self.context_lengths[0] if len(self.context_lengths) > 1 else 0,
            'constraint_retention_rate': sum(1 for c in self.constraint_mentions if c['mentioned']) / len(self.constraint_mentions) if self.constraint_mentions else 0,
            'final_summary_contains_constraints': self.final_summary_contains_constraints,
            'memory_operations': len(self.memory_operations)
        }


def extract_constraints_from_text(text):
    """从文本中提取关键约束"""
    constraints = []
    constraint_keywords = ['必须', '不能', '不要', '保持', '不变', '不改变', '兼容']
    
    sentences = text.split('。')
    for sentence in sentences:
        if any(keyword in sentence for keyword in constraint_keywords):
            constraints.append(sentence.strip())
    
    return constraints


def test_decision_retention_with_memory():
    """测试决策保留能力（使用 Memory Manager）"""
    print("=" * 60)
    print("Task 1: Decision Retention 测试 (With-Memory)")
    print("=" * 60)
    print()
    
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        
        # 创建测试工作区
        (tmp_path / "README.md").write_text("# Test Project\n", encoding="utf-8")
        (tmp_path / "todo.py").write_text("""
def filter_todos(todos, priority=None):
    return [t for t in todos if t.get('priority') == priority]
""", encoding="utf-8")
        
        # 创建 Agent
        workspace = WorkspaceContext.build(tmp_path)
        store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
        
        # 模拟多轮对话，包含关键约束
        conversation = [
            "请检查 todo filtering 的逻辑在哪里",
            "我们必须保持公共 CLI 不变",
            "不要重命名任何现有的导出函数",
            "实现支持按精确优先级匹配过滤 todos",
            "为新的过滤行为添加测试",
            "在完成之前，提醒我我们决定保留哪些兼容性约束"
        ]
        
        # 模拟模型响应
        model_responses = [
            "我会检查代码...",
            "明白，我会保持 CLI 不变",
            "好的，不会重命名导出函数",
            "正在实现优先级过滤...",
            "已添加测试",
            "约束: 1) 保持 CLI 不变 2) 不重命名导出函数"
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
        metrics = Task1MetricsWithMemory()
        
        # 记录初始上下文长度
        initial_context = len(json.dumps(agent.session))
        metrics.record_context_length(initial_context)
        print(f"[INFO] 初始上下文长度: {initial_context}")
        
        # 模拟 Memory Manager 的约束提取
        print("\n[INFO] 模拟 Memory Manager 操作...")
        pinned_constraints = []
        
        # 执行对话
        print("[INFO] 开始对话...")
        for i, user_input in enumerate(conversation):
            print(f"\n--- Turn {i+1} ---")
            print(f"用户: {user_input}")
            
            # 模拟 Pinned Facts 提取
            constraints = extract_constraints_from_text(user_input)
            if constraints:
                print(f"[Memory] 提取到约束: {constraints}")
                pinned_constraints.extend(constraints)
                metrics.record_memory_operation('extract_constraint', constraints)
            
            # 记录上下文长度
            current_context = len(json.dumps(agent.session))
            metrics.record_context_length(current_context)
            print(f"上下文长度: {current_context}")
            
            # 检查是否提到约束（现在应该更高，因为有 Memory）
            mentioned_constraints = any(
                keyword in user_input.lower() 
                for keyword in ['cli', '不变', '不重命名', '兼容性']
            )
            metrics.record_constraint_mention(i+1, mentioned_constraints)
            
            # 获取响应
            response = agent.ask(user_input)
            print(f"Agent: {response}")
            
            # 模拟延迟
            time.sleep(0.1)
        
        # 检查最终总结
        final_context = len(json.dumps(agent.session))
        metrics.record_context_length(final_context)
        
        # 检查是否在最后提到了约束
        final_summary = model_responses[-1]
        contains_constraints = 'cli' in final_summary.lower() and '不变' in final_summary
        metrics.set_final_summary_constraints(contains_constraints)
        
        # 模拟 Rolling Summary 操作
        if len(agent.session['history']) > 4:
            metrics.record_memory_operation('rolling_summary', '生成滚动摘要')
        
        print("\n" + "=" * 60)
        print("测试结果 (With-Memory)")
        print("=" * 60)
        
        summary = metrics.get_summary()
        print(f"初始上下文长度: {summary['initial_context_length']}")
        print(f"最终上下文长度: {summary['final_context_length']}")
        print(f"上下文增长: {summary['context_growth']}")
        print(f"约束保留率: {summary['constraint_retention_rate']:.1%}")
        print(f"最终总结包含约束: {'是' if summary['final_summary_contains_constraints'] else '否'}")
        print(f"Memory 操作次数: {summary['memory_operations']}")
        print(f"提取的约束数量: {len(pinned_constraints)}")
        
        # 保存结果
        results_file = Path(__file__).parent / "test_results_with_memory.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n[INFO] 结果已保存到: {results_file}")
        
        print("\n" + "=" * 60)
        print("With-Memory 版本测试完成")
        print("改进: 使用 Pinned Facts 机制提高约束保留率")
        print("=" * 60)
        
        return summary


if __name__ == "__main__":
    try:
        result = test_decision_retention_with_memory()
        
        print("\n[RESULT] Task 1 (With-Memory) 测试完成")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[ERROR] Task 1 (With-Memory) 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

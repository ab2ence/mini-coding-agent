"""
统一测试运行脚本
运行所有测试任务（Baseline 和 With-Memory 版本）
"""
import sys
import subprocess
from pathlib import Path
import json
import time


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def run_test(test_path, description):
    """运行单个测试"""
    print(f"[RUNNING] {description}")
    print(f"[PATH] {test_path}")
    
    try:
        result = subprocess.run(
            ["python", str(test_path)],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(f"[PASS] {description} - 测试通过\n")
            return True
        else:
            print(f"[FAIL] {description} - 测试失败")
            print(f"错误输出:\n{result.stderr}\n")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {description} - 测试超时\n")
        return False
    except Exception as e:
        print(f"[ERROR] {description} - {e}\n")
        return False


def load_results(results_file):
    """加载测试结果"""
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def main():
    """主函数"""
    print_header("Mini-Coding-Agent 完整测试套件")
    
    print("测试目标:")
    print("1. 验证 Baseline 版本（无优化）")
    print("2. 验证 With-Memory 版本（优化后）")
    print("3. 生成 Before/After 对比报告\n")
    
    # 收集结果
    results = {
        'baseline': {},
        'with_memory': {}
    }
    
    # Baseline 测试
    print_header("Phase 1: Baseline 版本测试（无优化）")
    
    baseline_tests = [
        ("versions/baseline/tests/task_01_decision_retention/test_task1.py", 
         "Task 1: Decision Retention (Baseline)"),
        ("versions/baseline/tests/task_02_noisy_tool_output/test_task2.py", 
         "Task 2: Noisy Tool Output (Baseline)"),
        ("versions/baseline/tests/task_03_long_workflow/test_task3.py", 
         "Task 3: Long Workflow (Baseline)")
    ]
    
    baseline_results = []
    for test_path, description in baseline_tests:
        full_path = Path(__file__).parent / test_path
        success = run_test(full_path, description)
        baseline_results.append({
            'test': description,
            'passed': success,
            'results_file': full_path.parent / "test_results.json"
        })
        time.sleep(0.5)  # 避免太快
    
    results['baseline'] = baseline_results
    
    # With-Memory 测试
    print_header("Phase 2: With-Memory 版本测试（优化后）")
    
    with_memory_tests = [
        ("versions/with-memory/tests/task_01_decision_retention/test_task1_with_memory.py", 
         "Task 1: Decision Retention (With-Memory)"),
        ("versions/with-memory/tests/task_02_noisy_tool_output/test_task2_with_memory.py", 
         "Task 2: Noisy Tool Output (With-Memory)"),
        ("versions/with-memory/tests/task_03_long_workflow/test_task3_with_memory.py", 
         "Task 3: Long Workflow (With-Memory)")
    ]
    
    with_memory_results = []
    for test_path, description in with_memory_tests:
        full_path = Path(__file__).parent / test_path
        success = run_test(full_path, description)
        with_memory_results.append({
            'test': description,
            'passed': success,
            'results_file': full_path.parent / "test_results_with_memory.json"
        })
        time.sleep(0.5)  # 避免太快
    
    results['with_memory'] = with_memory_results
    
    # 生成对比报告
    print_header("Phase 3: Before/After 对比分析")
    
    print("\n测试结果汇总:\n")
    print("-" * 80)
    print(f"{'测试任务':<40} {'Baseline':<15} {'With-Memory':<15}")
    print("-" * 80)
    
    for i in range(3):
        baseline_pass = baseline_results[i]['passed']
        memory_pass = with_memory_results[i]['passed']
        
        baseline_status = "PASS" if baseline_pass else "FAIL"
        memory_status = "PASS" if memory_pass else "FAIL"
        
        test_name = f"Task {i+1}"
        print(f"{test_name:<40} {baseline_status:<15} {memory_status:<15}")
    
    print("-" * 80)
    
    # 保存汇总结果
    summary_file = Path(__file__).parent / "test_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INFO] 测试汇总已保存到: {summary_file}")
    
    # 打印说明
    print_header("下一步操作")
    print("1. 查看各个测试目录下的 test_results.json 文件")
    print("2. 查看 test_summary.json 获取完整汇总")
    print("3. 运行 REPORTS/generate_comparison_report.py 生成对比报告")
    print("4. 在 README.md 中记录测试结果")
    
    print("\n" + "=" * 80)
    print("测试套件完成!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n[INFO] 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试套件失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

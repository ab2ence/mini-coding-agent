#!/usr/bin/env python3
"""
Memory Manager Evaluation Script

按照笔试要求实现的任务评测脚本，用于评估 Memory Manager 的优化效果。

用法:
    python eval_memory.py --tasks tasks/
    python eval_memory.py --task tasks/task_01_decision_retention.json
    python eval_memory.py --version with-memory
    python eval_memory.py --baseline
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TaskEvaluator:
    """任务评测器 - 按照笔试要求评估 Memory Manager"""

    def __init__(self, task_config: Dict, version: str = "with-memory"):
        self.task_config = task_config
        self.task_id = task_config["id"]
        self.workspace = task_config["workspace"]
        self.checks = task_config.get("checks", {})
        self.version = version
        self.results = {
            "task_id": self.task_id,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "metrics": {},
            "passed": False,
            "details": []
        }

    def evaluate_file_modifications(self, workspace_path: Path) -> Dict[str, Any]:
        """检查文件修改情况"""
        result = {
            "must_modify_checked": False,
            "must_not_modify_checked": False,
            "passed": True,
            "details": []
        }

        # 检查必须修改的文件
        must_modify = self.checks.get("must_modify_files", [])
        if must_modify:
            result["must_modify_checked"] = True
            for file_path in must_modify:
                full_path = workspace_path / file_path
                if full_path.exists():
                    result["details"].append(f"✓ Modified: {file_path}")
                else:
                    result["details"].append(f"✗ Missing: {file_path}")
                    result["passed"] = False

        # 检查不应修改的文件
        must_not_modify = self.checks.get("must_not_modify_files", [])
        if must_not_modify:
            result["must_not_modify_checked"] = True
            for file_path in must_not_modify:
                full_path = workspace_path / file_path
                if not full_path.exists():
                    result["details"].append(f"✓ Not modified: {file_path}")
                else:
                    result["details"].append(f"✗ Should not modify: {file_path}")
                    result["passed"] = False

        return result

    def evaluate_final_contain(self, final_summary: str) -> Dict[str, Any]:
        """检查最终总结是否包含必要内容"""
        result = {
            "checked": False,
            "passed": True,
            "details": [],
            "matched": []
        }

        must_contain = self.checks.get("final_must_contain", [])
        if not must_contain:
            return result

        result["checked"] = True
        final_lower = final_summary.lower()

        for item in must_contain:
            item_lower = item.lower()
            if item_lower in final_lower:
                result["matched"].append(item)
                result["details"].append(f"✓ Contains: {item}")
            else:
                result["details"].append(f"✗ Missing: {item}")
                result["passed"] = False

        return result

    def evaluate_test_command(self, workspace_path: Path) -> Dict[str, Any]:
        """执行测试命令并评估结果"""
        import subprocess

        result = {
            "command": self.checks.get("test_command", "pytest -q"),
            "executed": False,
            "passed": False,
            "output": "",
            "error": ""
        }

        cmd = self.checks.get("test_command", "pytest -q")
        if not cmd:
            return result

        result["command"] = cmd

        try:
            result["executed"] = True
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            result["output"] = proc.stdout
            result["error"] = proc.stderr
            result["passed"] = proc.returncode == 0

        except subprocess.TimeoutExpired:
            result["error"] = "Test command timed out"
        except Exception as e:
            result["error"] = str(e)

        return result

    def evaluate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """评估性能指标"""
        result = {
            "checked": False,
            "passed": True,
            "metrics": {},
            "details": []
        }

        expect_metrics = self.checks.get("expect_metrics", {})
        if not expect_metrics:
            return result

        result["checked"] = True

        for metric_name, expected in expect_metrics.items():
            actual = metrics.get(metric_name)

            if actual is None:
                result["details"].append(f"? {metric_name}: No data")
                continue

            passed = False

            # 根据指标类型判断
            if metric_name.endswith("_gt"):
                base_name = metric_name[:-3]
                actual_val = metrics.get(base_name)
                if actual_val is not None:
                    passed = actual_val > expected
                    result["details"].append(
                        f"{'✓' if passed else '✗'} {base_name}: {actual_val:.2f} > {expected:.2f}"
                    )

            elif metric_name.endswith("_lt"):
                base_name = metric_name[:-3]
                actual_val = metrics.get(base_name)
                if actual_val is not None:
                    passed = actual_val < expected
                    result["details"].append(
                        f"{'✓' if passed else '✗'} {base_name}: {actual_val:.2f} < {expected:.2f}"
                    )

            else:
                passed = actual == expected
                result["details"].append(
                    f"{'✓' if passed else '✗'} {metric_name}: {actual} == {expected}"
                )

            if not passed:
                result["passed"] = False

            result["metrics"][metric_name] = {
                "actual": actual,
                "expected": expected,
                "passed": passed
            }

        return result

    def run_evaluation(
        self,
        workspace_path: Path,
        final_summary: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行完整评测"""
        print(f"\n{'='*60}")
        print(f"Evaluating Task: {self.task_id} ({self.version})")
        print(f"{'='*60}")

        # 1. 评估文件修改
        print("\n[1] Checking file modifications...")
        file_result = self.evaluate_file_modifications(workspace_path)
        self.results["checks"]["file_modifications"] = file_result
        for detail in file_result.get("details", []):
            print(f"    {detail}")

        # 2. 评估最终总结内容
        print("\n[2] Checking final summary content...")
        summary_result = self.evaluate_final_contain(final_summary)
        self.results["checks"]["final_content"] = summary_result
        for detail in summary_result.get("details", []):
            print(f"    {detail}")

        # 3. 执行测试命令
        print(f"\n[3] Running test command: {self.checks.get('test_command', 'N/A')}")
        test_result = self.evaluate_test_command(workspace_path)
        self.results["checks"]["test_command"] = test_result
        if test_result["executed"]:
            print(f"    Exit code: {test_result['passed']}")
            if test_result["output"]:
                print(f"    Output: {test_result['output'][:200]}...")
        else:
            print(f"    Error: {test_result['error']}")

        # 4. 评估性能指标
        print("\n[4] Evaluating metrics...")
        metrics_result = self.evaluate_metrics(metrics)
        self.results["checks"]["metrics"] = metrics_result
        for detail in metrics_result.get("details", []):
            print(f"    {detail}")

        # 5. 汇总结果
        all_passed = (
            file_result["passed"] and
            summary_result["passed"] and
            (not test_result["executed"] or test_result["passed"]) and
            (not metrics_result["checked"] or metrics_result["passed"])
        )

        self.results["passed"] = all_passed
        self.results["metrics"] = metrics

        # 打印最终结果
        print(f"\n{'='*60}")
        print(f"Result: {'PASSED ✓' if all_passed else 'FAILED ✗'}")
        print(f"{'='*60}")

        return self.results


def run_single_task(
    task_config: Dict,
    version: str = "with-memory",
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """运行单个任务评测"""
    evaluator = TaskEvaluator(task_config, version)

    # 确定工作区路径
    tasks_dir = Path(__file__).parent
    workspace_path = tasks_dir / task_config["workspace"]

    if not workspace_path.exists():
        print(f"Error: Workspace not found: {workspace_path}")
        return {"error": f"Workspace not found: {workspace_path}"}

    # 获取最终总结（从 metrics 或日志文件）
    final_summary = ""
    metrics_file = output_dir / f"{task_config['id']}_{version}_summary.txt" if output_dir else None

    if metrics_file and metrics_file.exists():
        final_summary = metrics_file.read_text()
    else:
        # 尝试从结果目录读取
        result_dir = Path(__file__).parent / "results" / version
        summary_file = result_dir / f"{task_config['id']}_final_summary.txt"
        if summary_file.exists():
            final_summary = summary_file.read_text()

    # 加载指标数据
    metrics = {}
    if output_dir:
        metrics_file = output_dir / f"{task_config['id']}_{version}_metrics.json"
        if metrics_file.exists():
            metrics = json.loads(metrics_file.read_text())

    return evaluator.run_evaluation(workspace_path, final_summary, metrics)


def run_all_tasks(
    tasks_dir: Path,
    version: str = "with-memory",
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """运行所有任务评测"""
    results = {
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "total_tasks": 0,
        "passed_tasks": 0,
        "failed_tasks": 0,
        "task_results": []
    }

    # 查找所有任务配置文件
    task_files = list(tasks_dir.glob("task_*.json"))

    print(f"\nFound {len(task_files)} task configurations")

    for task_file in sorted(task_files):
        print(f"\n{'#'*60}")
        print(f"Processing: {task_file.name}")
        print(f"{'#'*60}")

        task_config = json.loads(task_file.read_text())
        result = run_single_task(task_config, version, output_dir)

        results["total_tasks"] += 1
        if result.get("passed"):
            results["passed_tasks"] += 1
        else:
            results["failed_tasks"] += 1

        results["task_results"].append(result)

        # 保存单个任务结果
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            result_file = output_dir / f"{task_config['id']}_{version}_eval.json"
            result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    # 打印汇总结果
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Version: {version}")
    print(f"Total tasks: {results['total_tasks']}")
    print(f"Passed: {results['passed_tasks']}")
    print(f"Failed: {results['failed_tasks']}")
    print(f"Pass rate: {results['passed_tasks']/results['total_tasks']*100:.1f}%")

    # 保存汇总结果
    if output_dir:
        summary_file = output_dir / f"eval_summary_{version}.json"
        summary_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\nResults saved to: {summary_file}")

    return results


def compare_versions(
    baseline_results: Dict,
    memory_results: Dict
) -> Dict[str, Any]:
    """对比 Baseline 和 Memory 版本的评测结果"""
    comparison = {
        "baseline_metrics": {},
        "memory_metrics": {},
        "improvements": {},
        "degradations": {}
    }

    # 提取关键指标
    for task_result in baseline_results.get("task_results", []):
        task_id = task_result["task_id"]
        metrics = task_result.get("metrics", {})
        comparison["baseline_metrics"][task_id] = metrics

    for task_result in memory_results.get("task_results", []):
        task_id = task_result["task_id"]
        metrics = task_result.get("metrics", {})
        comparison["memory_metrics"][task_id] = metrics

    # 计算改进/退化
    for task_id in comparison["baseline_metrics"]:
        if task_id in comparison["memory_metrics"]:
            baseline = comparison["baseline_metrics"][task_id]
            memory = comparison["memory_metrics"][task_id]

            improvements = {}
            degradations = {}

            for key in set(baseline.keys()) | set(memory.keys()):
                b_val = baseline.get(key)
                m_val = memory.get(key)

                if b_val is not None and m_val is not None:
                    # 假设指标是越小越好（如压缩率）
                    if key in ["compression_ratio", "context_growth_rate"]:
                        if m_val < b_val:
                            improvements[key] = {"baseline": b_val, "memory": m_val}
                        elif m_val > b_val:
                            degradations[key] = {"baseline": b_val, "memory": m_val}
                    else:
                        # 假设指标是越大越好（如准确率）
                        if m_val > b_val:
                            improvements[key] = {"baseline": b_val, "memory": m_val}
                        elif m_val < b_val:
                            degradations[key] = {"baseline": b_val, "memory": m_val}

            comparison["improvements"][task_id] = improvements
            comparison["degradations"][task_id] = degradations

    return comparison


def main():
    parser = argparse.ArgumentParser(
        description="Memory Manager Evaluation Script - 按照笔试要求评测"
    )

    parser.add_argument(
        "--tasks",
        type=str,
        default="tasks/",
        help="Tasks directory containing task_*.json files"
    )

    parser.add_argument(
        "--task",
        type=str,
        help="Single task file to evaluate"
    )

    parser.add_argument(
        "--version",
        type=str,
        choices=["baseline", "with-memory"],
        default="with-memory",
        help="Version to evaluate"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for results"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare baseline and memory versions"
    )

    args = parser.parse_args()

    # 确定路径
    script_dir = Path(__file__).parent
    tasks_dir = script_dir / args.tasks if not args.task else None

    if args.task:
        # 单任务模式
        task_file = Path(args.task)
        if not task_file.is_absolute():
            task_file = script_dir / task_file

        task_config = json.loads(task_file.read_text())
        output_dir = Path(args.output) if args.output else None

        result = run_single_task(task_config, args.version, output_dir)

        print("\n" + json.dumps(result, indent=2, ensure_ascii=False))

        return 0 if result.get("passed") else 1

    else:
        # 多任务模式
        output_dir = Path(args.output) if args.output else script_dir / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.compare:
            # 对比模式
            baseline_dir = output_dir / "baseline"
            memory_dir = output_dir / "with-memory"

            print("Running baseline evaluation...")
            baseline_results = run_all_tasks(tasks_dir, "baseline", baseline_dir)

            print("\nRunning memory evaluation...")
            memory_results = run_all_tasks(tasks_dir, "with-memory", memory_dir)

            print("\nComparing versions...")
            comparison = compare_versions(baseline_results, memory_results)

            comparison_file = output_dir / "comparison.json"
            comparison_file.write_text(json.dumps(comparison, indent=2, ensure_ascii=False))

            print(f"\nComparison saved to: {comparison_file}")

            # 打印改进摘要
            print("\n" + "="*60)
            print("IMPROVEMENTS")
            print("="*60)
            for task_id, improvements in comparison["improvements"].items():
                if improvements:
                    print(f"\n{task_id}:")
                    for metric, values in improvements.items():
                        delta = values["memory"] - values["baseline"]
                        print(f"  {metric}: {values['baseline']:.2f} -> {values['memory']:.2f} ({delta:+.2f})")

            print("\n" + "="*60)
            print("DEGRADATIONS")
            print("="*60)
            for task_id, degradations in comparison["degradations"].items():
                if degradations:
                    print(f"\n{task_id}:")
                    for metric, values in degradations.items():
                        delta = values["memory"] - values["baseline"]
                        print(f"  {metric}: {values['baseline']:.2f} -> {values['memory']:.2f} ({delta:+.2f})")

        else:
            # 单版本模式
            results = run_all_tasks(tasks_dir, args.version, output_dir)
            return 0 if results["failed_tasks"] == 0 else 1

        return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Baseline 版本完整性验证脚本
验证保存的原始版本文件与当前版本的一致性
"""
import hashlib
from pathlib import Path


def get_file_hash(filepath):
    """计算文件的 MD5 哈希值"""
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def verify_baseline():
    """验证 baseline 版本"""
    project_root = Path(__file__).parent.parent.parent
    baseline_file = project_root / "versions" / "baseline" / "mini_coding_agent_original.py"
    current_file = project_root / "mini_coding_agent.py"

    print("=" * 60)
    print("Baseline 版本完整性验证")
    print("=" * 60)
    print()

    # 检查文件是否存在
    print(f"1. 检查 baseline 文件是否存在...")
    if baseline_file.exists():
        print(f"   [PASS] 文件存在: {baseline_file}")
        print(f"   文件大小: {baseline_file.stat().st_size:,} 字节")
    else:
        print(f"   [FAIL] 文件不存在: {baseline_file}")
        return False

    print()

    # 检查当前文件是否存在
    print(f"2. 检查当前文件是否存在...")
    if current_file.exists():
        print(f"   [PASS] 文件存在: {current_file}")
        print(f"   文件大小: {current_file.stat().st_size:,} 字节")
    else:
        print(f"   [FAIL] 文件不存在: {current_file}")
        return False

    print()

    # 比较文件哈希值
    print(f"3. 比较文件哈希值...")
    baseline_hash = get_file_hash(baseline_file)
    current_hash = get_file_hash(current_file)

    print(f"   Baseline 文件哈希: {baseline_hash}")
    print(f"   Current 文件哈希: {current_hash}")

    if baseline_hash == current_hash:
        print(f"   [WARN] 两个文件内容完全相同")
        print(f"   说明: 当前版本尚未添加 Memory 优化")
    else:
        print(f"   [PASS] 两个文件内容不同")
        print(f"   说明: 当前版本已添加 Memory 优化")

    print()

    # 检查 baseline 文件是否包含预期内容
    print(f"4. 检查 baseline 文件内容...")
    with open(baseline_file, 'r', encoding='utf-8') as f:
        content = f.read(10000)  # 读取更多内容

    if 'class MiniAgent' in content:
        print(f"   [PASS] 包含 MiniAgent 类定义")
    else:
        print(f"   [FAIL] 缺少 MiniAgent 类定义")
        return False

    if 'SessionStore' in content:
        print(f"   [PASS] 包含 SessionStore 类")
    else:
        print(f"   [FAIL] 缺少 SessionStore 类")
        return False

    print()

    print("=" * 60)
    print("验证结果:")
    print("  [PASS] Baseline 版本文件完整且可访问")
    print("  [INFO] 可用于对比测试的原始版本已就绪")
    print("=" * 60)
    return True


if __name__ == "__main__":
    import sys
    success = verify_baseline()
    sys.exit(0 if success else 1)

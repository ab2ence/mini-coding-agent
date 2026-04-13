"""
Ollama API 使用教程脚本
学习如何通过 Python 调用 Ollama 服务访问本地 AI 模型

使用方法：
    python test_ollama.py
"""

import urllib.request
import urllib.error
import json
import time


OLLAMA_HOST = "http://127.0.0.1:11434"
#MODEL_NAME = "qwen3.5:4b"
MODEL_NAME = "qwen3.5:2b"

def check_ollama_status():
    """检查 Ollama 服务是否正在运行"""
    print("=" * 60)
    print("1. 检查 Ollama 服务状态")
    print("=" * 60)
    
    try:
        url = f"{OLLAMA_HOST}/api/version"
        with urllib.request.urlopen(url, timeout=5) as response:
            version = json.loads(response.read().decode())
            print(f"✅ Ollama 服务正在运行！")
            print(f"   版本: {version.get('version', 'unknown')}")
            return True
    except urllib.error.URLError:
        print("❌ Ollama 服务未运行")
        print("   请运行命令: ollama serve")
        return False


def list_models():
    """列出所有已安装的模型"""
    print("\n" + "=" * 60)
    print("2. 列出已安装的模型")
    print("=" * 60)
    
    try:
        url = f"{OLLAMA_HOST}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            models = data.get('models', [])
            
            if not models:
                print("📭 没有安装任何模型")
                return []
            
            print(f"已安装 {len(models)} 个模型：\n")
            for model in models:
                name = model.get('name', 'unknown')
                size = model.get('size', 0)
                size_gb = size / (1024**3)
                modified = model.get('modified_at', 'unknown')
                print(f"  📦 {name}")
                print(f"     大小: {size_gb:.2f} GB")
                print(f"     更新时间: {modified[:19] if len(modified) > 19 else modified}")
                print()
            
            return models
    except urllib.error.URLError as e:
        print(f"❌ 无法获取模型列表: {e}")
        return []


def chat_with_model(prompt, system_prompt=None):
    """使用聊天接口与模型对话（推荐方式）"""
    print("\n" + "=" * 60)
    print("3. 使用聊天接口")
    print("=" * 60)
    print(f"📝 发送消息: {prompt}\n")
    
    messages = []
    
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    
    try:
        url = f"{OLLAMA_HOST}/api/chat"
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode())
            elapsed = time.time() - start_time
            
            response_message = result.get('message', {})
            content = response_message.get('content', '')
            
            print(f"🤖 模型回复 ({elapsed:.2f}秒):")
            print("-" * 60)
            print(content)
            print("-" * 60)
            
            return content
            
    except urllib.error.URLError as e:
        print(f"❌ 请求失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return None


def generate_with_model(prompt, system_prompt=None):
    """使用生成接口（简单补全）"""
    print("\n" + "=" * 60)
    print("4. 使用生成接口（补全模式）")
    print("=" * 60)
    print(f"📝 发送提示: {prompt}\n")
    
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 500,
        }
    }
    
    try:
        url = f"{OLLAMA_HOST}/api/generate"
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode())
            elapsed = time.time() - start_time
            
            response_text = result.get('response', '')
            
            print(f"🤖 模型回复 ({elapsed:.2f}秒):")
            print("-" * 60)
            print(response_text)
            print("-" * 60)
            
            return response_text
            
    except urllib.error.URLError as e:
        print(f"❌ 请求失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return None


def show_model_info():
    """显示模型详细信息"""
    print("\n" + "=" * 60)
    print("5. 显示模型信息")
    print("=" * 60)
    
    try:
        url = f"{OLLAMA_HOST}/api/show"
        payload = {
            "name": MODEL_NAME
        }
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            info = json.loads(response.read().decode())
            
            print(f"📋 模型: {MODEL_NAME}")
            print(f"\n参数信息:")
            for key, value in info.items():
                if key not in ['modelfile', 'parameters']:
                    print(f"  {key}: {value}")
            
            if 'parameters' in info:
                print(f"\n模型参数:")
                print(f"  {info['parameters']}")
                
    except urllib.error.URLError as e:
        print(f"❌ 无法获取模型信息: {e}")


def interactive_chat():
    """交互式聊天"""
    print("\n" + "=" * 60)
    print("🌟 交互式聊天模式")
    print("=" * 60)
    print("输入 'quit' 或 'exit' 退出聊天\n")
    
    messages = []
    
    system_prompt = input("设置系统提示（直接回车跳过）: ").strip()
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False
            }
            
            url = f"{OLLAMA_HOST}/api/chat"
            data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=300) as response:
                result = json.loads(response.read().decode())
                assistant_message = result.get('message', {}).get('content', '')
                
                messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                print(f"\n🤖 AI: {assistant_message}\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")


def main():
    """主函数"""
    print("\n" + "🎯" * 20)
    print("Ollama API 使用教程")
    print("🎯" * 20)
    print(f"\n目标模型: {MODEL_NAME}")
    print(f"服务地址: {OLLAMA_HOST}\n")
    
    if not check_ollama_status():
        print("\n请先启动 Ollama 服务:")
        print("1. 打开新终端")
        print("2. 运行: ollama serve")
        print("3. 然后重新运行此脚本")
        return
    
    list_models()
    
    print("\n是否运行测试对话？")
    print("1. 是，使用聊天接口（推荐）")
    print("2. 是，使用生成接口")
    print("3. 是，显示模型信息")
    print("4. 是，开启交互式聊天")
    print("5. 否，仅查看信息")
    
    choice = input("\n请选择 (1-5): ").strip()
    
    if choice == '1':
        test_prompts = [
            "你好！请简单介绍一下你自己。",
            "Python中如何快速排序？请给出代码示例。",
            "解释一下什么是递归函数。"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}/{len(test_prompts)}")
            chat_with_model(prompt)
            time.sleep(1)
            
    elif choice == '2':
        test_prompts = [
            "写一个Python的快速排序函数",
            "用一句话解释什么是机器学习"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}/{len(test_prompts)}")
            generate_with_model(prompt)
            time.sleep(1)
            
    elif choice == '3':
        show_model_info()
        
    elif choice == '4':
        interactive_chat()
        
    else:
        print("\n✅ 教程结束！")
        print("\n💡 下一步：")
        print("   1. 启动 Mini-Coding-Agent:")
        print("      python mini_coding_agent.py")
        print("   2. 或者继续探索 Ollama API")
        print("   3. 查看官方文档: https://ollama.ai")


if __name__ == "__main__":
    main()

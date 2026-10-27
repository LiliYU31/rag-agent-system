import os
import dashscope

print("API Key 前 8 位:", os.getenv("DASHSCOPE_API_KEY", "")[:8])
print("dashscope 版本:", dashscope.__version__)

# 依次测试模型
for model_name in ["qwen3-max", "qwen-max", "qwen-plus", "qwen-turbo"]:
    print(f"\n测试 {model_name}...")
    try:
        response = dashscope.Generation.call(
            model=model_name,
            prompt="你好",
        )
        print("status_code:", response.status_code)
        print("message:", response.message)
        if response.status_code == 200:
            print("✅ 回复:", response.output.text[:50])
    except Exception as e:
        print(f"❌ 异常: {e}")

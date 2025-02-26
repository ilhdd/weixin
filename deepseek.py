from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API 的配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat"  # 替换为实际的 DeepSeek API URL
DEEPSEEK_API_KEY = "your-deepseek-api-key"  # 替换为你的 DeepSeek API Key

# 用于存储用户对话上下文（可根据实际需求替换为数据库）
user_contexts = {}

@app.route('/deepseek', methods=['POST'])
def deepseek():
    # 获取用户输入和用户 ID（用于维护上下文）
    data = request.json
    user_input = data.get('user_input')
    user_id = data.get('user_id')  # 假设前端传递用户 ID

    if not user_input:
        return jsonify({"error": "user_input is required"}), 400

    # 获取用户上下文（如果存在）
    context = user_contexts.get(user_id, [])

    # 构造 DeepSeek API 请求数据
    messages = context + [{"role": "user", "content": user_input}]

    try:
        # 调用 DeepSeek API
        response = requests.post(
            DEEPSEEK_API_URL,
            json={
                "model": "deepseek-reasoner",  # 指定使用 deepseek-chat 模型
                "messages": messages,
                "api_key": DEEPSEEK_API_KEY
            },
            headers={"Content-Type": "application/json"},
            timeout=10  # 设置超时时间
        )
        response.raise_for_status()  # 检查是否有错误
        result = response.json()

        # 更新用户上下文
        if user_id:
            user_contexts[user_id] = messages + [{"role": "assistant", "content": result["choices"][0]["message"]["content"]}]

        # 返回结果
        return jsonify({
            "response": result["choices"][0]["message"]["content"],
            "context": user_contexts.get(user_id, [])  # 返回当前上下文（可选）
        })
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        return jsonify({"error": "DeepSeek API 调用失败，请稍后重试"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

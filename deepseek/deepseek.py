from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# DeepSeek API 的配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat"  # 替换为实际的 DeepSeek API URL
DEEPSEEK_API_KEY = "your-deepseek-api-key"  # 替换为你的 DeepSeek API Key

@app.route('/deepseek', methods=['POST'])
def deepseek():
    # 获取用户输入
    user_input = request.json.get('user_input')
    if not user_input:
        return jsonify({"error": "user_input is required"}), 400

    # 调用 DeepSeek API
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            json={
                "prompt": user_input,
                "api_key": DEEPSEEK_API_KEY
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()  # 检查是否有错误
        result = response.json()
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
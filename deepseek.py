from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API 的配置
DEEPSEEK_API_URL = "https://api.deepseek.com"  # 替换为实际的 DeepSeek API URL
DEEPSEEK_API_KEY = "sk-137f9f346e6646528f019b73d034b0b4"  # 替换为你的 DeepSeek API Key

# 用于存储用户对话上下文（可根据实际需求替换为数据库）
user_contexts = {}

def generate_recommendation_prompt(age_groups, time, city, budget, transportation, departure, destination):
    """
    根据用户输入生成推荐提示，优先级如下：
    1. 年龄段
    2. 旅行的时间地点
    3. 预算
    4. 交通方式
    5. 出发位置和目的地
    """
    return (
        f"用户计划从 {departure} 前往 {destination} 旅游，时间为 {time}，预算为 {budget}。"
        f"年龄段分布：青年（{age_groups['young']}人），中年（{age_groups['middle']}人），老年（{age_groups['old']}人）。"
        f"请按照以下优先级推荐最佳旅游路线（包含景点名称、文字介绍、推荐参观时间点）、交通方式和大致预算："
        f"1. 优先考虑年龄段，推荐适合青年、中年、老年的景点和活动。"
        f"2. 根据旅行时间和地点推荐合适的景点。"
        f"3. 在预算范围内推荐景点和活动。"
        f"4. 根据交通方式推荐合适的路线。"
        f"5. 考虑出发位置和目的地的距离和交通便利性。"
    )

@app.route('/deepseek', methods=['POST'])
def deepseek():
    # 获取用户输入和用户 ID（用于维护上下文）
    data = request.json
    age_groups = {
        "young": data.get("young", 0),  # 青年人数
        "middle": data.get("middle", 0),  # 中年人数
        "old": data.get("old", 0)  # 老年人数
    }
    time = data.get("time")  # 旅行时间
    city = data.get("city")  # 旅行地点
    budget = data.get("budget")  # 预算
    transportation = data.get("transportation")  # 交通方式
    departure = data.get("departure")  # 出发位置
    destination = data.get("destination")  # 想要去的位置
    user_id = data.get("user_id")  # 用户 ID
    user_feedback = data.get("feedback")  # 用户反馈（可选）

    # 验证输入
    if not all([time, city, budget, transportation, departure, destination]):
        return jsonify({"error": "time, city, budget, transportation, departure, and destination are required"}), 400

    # 获取用户上下文（如果存在）
    context = user_contexts.get(user_id, [])

    # 如果是第一次请求，生成推荐提示
    if not user_feedback:
        prompt = generate_recommendation_prompt(age_groups, time, city, budget, transportation, departure, destination)
        context.append({"role": "user", "content": prompt})
    else:
        # 如果有用户反馈，添加到上下文
        context.append({"role": "user", "content": user_feedback})

    try:
        # 调用 DeepSeek API
        response = requests.post(
            DEEPSEEK_API_URL,
            json={
                "model": "deepseek-reasoner",  # 指定使用 deepseek-reasoner 模型
                "messages": context,
                "api_key": DEEPSEEK_API_KEY
            },
            headers={"Content-Type": "application/json"},
            timeout=10  # 设置超时时间
        )
        response.raise_for_status()  # 检查是否有错误
        result = response.json()

        # 更新用户上下文
        assistant_response = result["choices"][0]["message"]["content"]
        context.append({"role": "assistant", "content": assistant_response})
        user_contexts[user_id] = context

        # 返回结果
        return jsonify({
            "response": assistant_response,
            "context": context  # 返回当前上下文（可选）
        })
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        return jsonify({"error": "DeepSeek API 调用失败，请稍后重试"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API 的配置
DEEPSEEK_API_URL = " https://api.deepseek.com"  # 替换为实际的 DeepSeek API URL
DEEPSEEK_API_KEY = " sk-137f9f346e6646528f019b73d034b0b4"  # 替换为你的 DeepSeek API Key

# 用于存储用户对话上下文（可根据实际需求替换为数据库）
user_contexts = {}

def generate_recommendation_prompt(age_groups, time, city, budget, transportation, departure, destination):
    """
    根据用户输入生成推荐提示，使用木桶效应进行推荐。
    缺失的数据用 ? 表示。
    """
    return (
        f"用户计划从 {departure} 前往 {destination} 旅游，时间为 {time}，预算为 {budget}。"
        f"年龄段分布：青年（{age_groups['young']}人），中年（{age_groups['middle']}人），老年（{age_groups['old']}人）。"
        f"交通方式为 {transportation}。请按照以下优先级推荐："
        f"1. 最佳旅游路线（包含景点名称、文字介绍、推荐参观时间点）。"
        f"2. 交通方式。"
        f"3. 推荐预算。"
        f"4. 当地美食推荐。"
        f"注意：使用木桶效应进行推荐，确保满足最低优先级的需求。"
    )

@app.route('/deepseek', methods=['POST'])
def deepseek():
    # 获取用户输入和用户 ID（用于维护上下文）
    data = request.json
    age_groups = {
        "young": data.get("young", "?"),  # 青年人数，缺失时用 ? 表示
        "middle": data.get("middle", "?"),  # 中年人数，缺失时用 ? 表示
        "old": data.get("old", "?")  # 老年人数，缺失时用 ? 表示
    }
    time = data.get("time", "?")  # 旅行时间，缺失时用 ? 表示
    city = data.get("city", "?")  # 旅行地点，缺失时用 ? 表示
    budget = data.get("budget", "?")  # 预算，缺失时用 ? 表示
    transportation = data.get("transportation", "?")  # 交通方式，缺失时用 ? 表示
    departure = data.get("departure", "?")  # 出发位置，缺失时用 ? 表示
    destination = data.get("destination", "?")  # 想要去的位置，缺失时用 ? 表示
    user_id = data.get("user_id")  # 用户 ID
    user_feedback = data.get("feedback", "")  # 用户反馈（可选）

    # 验证用户 ID
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

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

        # 解析输出格式
        output = {
            "最佳旅游路线": assistant_response,  # 假设 DeepSeek 返回的格式符合要求
            "交通方式": transportation if transportation != "?" else "待补充",
            "推荐预算": budget if budget != "?" else "待补充",
            "当地美食推荐": "待补充"  # 可以根据需要从 DeepSeek 返回的内容中提取
        }

        # 返回结果
        return jsonify(output)
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        return jsonify({"error": "DeepSeek API 调用失败，请稍后重试"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


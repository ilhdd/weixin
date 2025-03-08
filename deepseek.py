from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API 的配置
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"  # 替换为实际的 DeepSeek API URL
DEEPSEEK_API_KEY = "sk-c47f6f0e0dc74381960322fa682a1529"  # 替换为你的 DeepSeek API Key

# 缓存：存储每个用户的最近一轮对话输出
user_cache = {}

def generate_recommendation_prompt(age_groups, time, city, budget, transportation, departure, destination, user_feedback):
    """
    根据用户输入生成推荐提示，使用木桶效应进行推荐。
    缺失的数据用 ? 表示。
    """
    base_prompt = (
        f"用户计划从 {departure} 前往 {destination} 旅游，时间为 {time}，预算为 {budget}。"
        f"年龄段分布：青年（{age_groups['young']}人），中年（{age_groups['middle']}人），老年（{age_groups['old']}人）。"
        f"交通方式为 {transportation}。请按照以下优先级推荐："
        f"1. 最佳旅游路线（包含景点名称、文字介绍、推荐参观时间点）。"
        f"2. 交通方式。"
        f"3. 推荐预算。"
        f"4. 当地美食推荐。"
        f"注意：使用木桶效应进行推荐，确保满足最低优先级的需求。"
    )
    
    if user_feedback:
        return f"{base_prompt}\n用户反馈：{user_feedback}"
    else:
        return base_prompt

@app.route('/deepseek', methods=['POST'])
def deepseek():
    # 获取用户输入
    data = request.json

    # 首先尝试获取 user_id
    user_id = data.get("user_id")  # 用户 ID
    
    # 验证用户 ID 是否存在
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # 继续解析其他参数
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
    user_feedback = data.get("feedback", "")  # 用户反馈（可选）

    # 检查 age_groups 中是否有任何值为 "0"
    if any(age == "0" for age in age_groups.values()):
        logger.info(f"用户 {user_id} 的 age_groups 中有值为 '0'，停止请求并清理缓存。")
        if user_id in user_cache:
            del user_cache[user_id]
        return jsonify({"error": "age_groups 中有值为 '0'，请求被拒绝"}), 400

    # 生成推荐提示
    prompt = generate_recommendation_prompt(age_groups, time, city, budget, transportation, departure, destination, user_feedback)

    try:
        # 打印发送给 DeepSeek API 的请求体
        logger.info(f"Sending request to DeepSeek API with payload: {prompt}")
        
        response = requests.post(
            DEEPSEEK_API_URL,
            json={
                "model": "deepseek-reasoner",
                "messages": [{"role": "user", "content": prompt}]
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            },
            timeout=10
        )
        
        # 打印响应的状态码
        logger.info(f"Received response from DeepSeek API with status code: {response.status_code}")

        # 打印响应的内容
        logger.info(f"Response content: {response.text}")

        response.raise_for_status()
        result = response.json()

        # 解析输出格式
        assistant_response = result["choices"][0]["message"]["content"]
        output = {
            "最佳旅游路线": assistant_response,  # 假设 DeepSeek 返回的格式符合要求
            "交通方式": transportation if transportation != "?" else "待补充",
            "推荐预算": budget if budget != "?" else "待补充",
            "当地美食推荐": "待补充"  # 可以根据需要从 DeepSeek 返回的内容中提取
        }

        # 更新缓存
        user_cache[user_id] = output
        logger.info(f"用户 {user_id} 的对话结果已更新到缓存。")

        # 返回结果
        return jsonify(output)
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 调用失败, 具体错误: {e}, 请求体: {prompt}")
        return jsonify({"error": f"DeepSeek API 调用失败，请稍后重试 ({str(e)})"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify
import requests
import logging
import json

app = Flask(__name__)

# 配置日志
log_file_path = 'app.log'  # 日志文件路径
logging.basicConfig(
    level=logging.INFO,
    filename=log_file_path,  # 将日志记录到文件
    filemode='a',  # 追加模式
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# DeepSeek API 的配置
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"  # 替换为实际的 DeepSeek API URL
DEEPSEEK_API_KEY = "sk-c47f6f0e0dc74381960322fa682a1529"  # 替换为你的 DeepSeek API Key

# 缓存：存储每个用户的最近一轮对话输出
user_cache = {}

def generate_recommendation_prompt(planId, agelevel, young, middle, old, startdate, enddate, budget, transportation, departure, destination, preference):
    """
    根据用户输入生成推荐提示。
    """
    base_prompt = (
        f"用户计划从 {departure} 前往 {destination} 旅游，时间为 {startdate} 至 {enddate}，预算为 {budget}元。\n"
        f"年龄段为 {agelevel}，青年人数为 {young}人，中年人数为 {middle}人，老年人数为 {old}人。\n"
        f"交通方式为 {transportation}。\n"
        f"用户的理想建议是：{preference}\n"
        f"请按照以下优先级推荐：\n"
        f"1. 最佳旅游路线（包含景点名称、文字介绍、推荐参观时间点）。\n"
        f"2. 交通方式。\n"
        f"3. 推荐预算。\n"
        f"4. 当地美食推荐。\n"
        f"注意：使用木桶效应进行推荐，确保满足最低优先级的需求。\n"
        f"请按照以下格式返回结果：\n"
        f"```json\n"
        f'{{'
          f'"title": "旅行标题",'
          f'"itinerary": ['
          f'{{'
            f'"date": "日期",'
            f'"schedule": ['
              f'{{'
                f'"startTime": "开始时间",'
                f'"endTime": "结束时间",'
                f'"subtitle": "活动标题",'
                f'"budget": 预算,'
                f'"transportation": "交通方式",'
                f'"accommodation": "住宿信息",'
                f'"foodRecommendations": "餐饮推荐",'
                f'"attractionIntroduction": "景点介绍",'
                f'"notes": "备注"'
              f'}}'
            f']'
          f'}}'
        f'],'
        f'"costSummary": {{'
          f'"highSpeedRail": 高铁费用,'
          f'"accommodation": 住宿费用,'
          f'"meals": 餐饮费用,'
          f'"attractionTransportation": 景点交通费用,'
          f'"other": 其他费用,'
          f'"total": 总费用'
        f'}},'
        f'"notes": ['
          f'"注意事项1",'
          f'"注意事项2"'
        f']'
      f'}}\n'
        f"```"
    )
    
    return base_prompt

@app.route('/deepseek', methods=['POST'])
def deepseek():
    # 获取用户输入
    data = request.json

    # 获取 planId
    planId = data.get("planId")  # 用户 ID
    
    # 验证 planId 是否存在
    if not planId:
        return jsonify({"error": "planId is required"}), 400

    operation = data.get("operation")
    if not operation:
        return jsonify({"error": "operation is required"}), 400

    if operation == "confirm":
        # 确认操作，删除缓存中的数据并结束操作
        if planId in user_cache:
            del user_cache[planId]
            logger.info(f"计划 {planId} 的对话结果已从缓存中删除。")
        return jsonify({"message": "操作已确认，对话结束。"})

    feedback = data.get("feedback", "")  # 用户反馈

    if operation == "init":
        # 初始化操作，创建新的对话
        agelevel = data.get("agelevel", "?")  # 年龄段
        young = data.get("young", "?")  # 青年人数
        middle = data.get("middle", "?")  # 中年人数
        old = data.get("old", "?")  # 老年人数
        startdate = data.get("startdate", "?")  # 旅行开始日期
        enddate = data.get("enddate", "?")  # 旅行结束日期
        budget = data.get("budget", "?")  # 预算
        transportation = data.get("transportation", "?")  # 交通方式
        departure = data.get("departure", "?")  # 出发位置
        destination = data.get("destination", "?")  # 目的地
        preference = data.get("preference", "")  # 用户偏好

        prompt = generate_recommendation_prompt(planId, agelevel, young, middle, old, startdate, enddate, budget, transportation, departure, destination, preference)

        # 存储初始数据到缓存
        user_cache[planId] = {
            "agelevel": agelevel,
            "young": young,
            "middle": middle,
            "old": old,
            "startdate": startdate,
            "enddate": enddate,
            "budget": budget,
            "transportation": transportation,
            "departure": departure,
            "destination": destination,
            "preference": preference,
            "最佳旅游路线": ""
        }
    elif operation in ["continue", "reload"]:
        # 继续或重新加载操作，从缓存中读取数据并添加用户反馈
        if planId not in user_cache:
            return jsonify({"error": "planId not found in cache, please initialize first"}), 400
        cached_data = user_cache[planId]
        prompt = f"{cached_data['最佳旅游路线']} {feedback}"
    else:
        return jsonify({"error": "Invalid operation"}), 400

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
            timeout=60
        )
        
        # 打印响应的状态码
        logger.info(f"Received response from DeepSeek API with status code: {response.status_code}")

        # 打印响应的内容
        logger.info(f"Response content: {response.text}")

        response.raise_for_status()
        result = response.json()

        # 解析输出格式
        assistant_response = result["choices"][0]["message"]["content"]
        try:
            output = json.loads(assistant_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return jsonify({"error": "Failed to parse JSON response from DeepSeek API"}), 500

        # 更新缓存
        user_cache[planId]['最佳旅游路线'] = assistant_response
        logger.info(f"计划 {planId} 的对话结果已更新到缓存。")

        # 返回结果
        return jsonify(output)
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 调用失败, 具体错误: {e}, 请求体: {prompt}")
        return jsonify({"error": f"DeepSeek API 调用失败，请稍后重试 ({str(e)})"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

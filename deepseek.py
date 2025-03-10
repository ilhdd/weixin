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
           f'"planId": "planId",'
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

@app.route('/deepseek_test', methods=['POST'])
def deepseek_test():
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
        
        # 模拟 DeepSeek API 的响应
        assistant_response = """
        {
        "planId":"12345"
  "title": "北京至上海历史文化美食之旅",
  "itinerary": [
    {
      "date": "2023-10-01",
      "schedule": [
        {
          "startTime": "08:00",
          "endTime": "12:00",
          "subtitle": "北京南站至上海虹桥站",
          "budget": 553,
          "transportation": "高铁",
          "accommodation": "无",
          "foodRecommendations": "高铁餐",
          "attractionIntroduction": "乘坐高铁从北京南站前往上海虹桥站，车程约4小时。",
          "notes": "建议提前预订高铁票，确保座位。"
        },
        {
          "startTime": "12:30",
          "endTime": "14:00",
          "subtitle": "午餐",
          "budget": 100,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "上海小笼包",
          "attractionIntroduction": "在上海虹桥站附近品尝正宗上海小笼包。",
          "notes": "推荐尝试蟹粉小笼包。"
        },
        {
          "startTime": "14:30",
          "endTime": "17:30",
          "subtitle": "上海博物馆",
          "budget": 0,
          "transportation": "地铁",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "参观上海博物馆，了解中国历史文化。",
          "notes": "博物馆免费开放，建议提前预约。"
        },
        {
          "startTime": "18:00",
          "endTime": "19:30",
          "subtitle": "晚餐",
          "budget": 150,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "本帮菜",
          "attractionIntroduction": "品尝上海本帮菜，如红烧肉、油爆虾等。",
          "notes": "推荐餐厅：老正兴菜馆。"
        },
        {
          "startTime": "20:00",
          "endTime": "22:00",
          "subtitle": "外滩夜景",
          "budget": 0,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "漫步外滩，欣赏黄浦江两岸的夜景。",
          "notes": "建议带上相机，记录美丽瞬间。"
        }
      ]
    },
    {
      "date": "2023-10-02",
      "schedule": [
        {
          "startTime": "09:00",
          "endTime": "12:00",
          "subtitle": "豫园",
          "budget": 40,
          "transportation": "地铁",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "游览豫园，感受江南园林的精致与古典。",
          "notes": "豫园门票40元，建议提前购买。"
        },
        {
          "startTime": "12:30",
          "endTime": "14:00",
          "subtitle": "午餐",
          "budget": 100,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "南翔小笼包",
          "attractionIntroduction": "在豫园附近品尝南翔小笼包。",
          "notes": "推荐尝试蟹粉小笼包。"
        },
        {
          "startTime": "14:30",
          "endTime": "17:30",
          "subtitle": "田子坊",
          "budget": 0,
          "transportation": "地铁",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "漫步田子坊，感受上海的艺术氛围。",
          "notes": "田子坊免费开放，建议带上相机。"
        },
        {
          "startTime": "18:00",
          "endTime": "19:30",
          "subtitle": "晚餐",
          "budget": 150,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "上海本帮菜",
          "attractionIntroduction": "品尝上海本帮菜，如红烧肉、油爆虾等。",
          "notes": "推荐餐厅：老正兴菜馆。"
        },
        {
          "startTime": "20:00",
          "endTime": "22:00",
          "subtitle": "南京路步行街",
          "budget": 0,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "漫步南京路步行街，感受上海的繁华与时尚。",
          "notes": "建议带上相机，记录美丽瞬间。"
        }
      ]
    },
    {
      "date": "2023-10-03",
      "schedule": [
        {
          "startTime": "09:00",
          "endTime": "12:00",
          "subtitle": "上海科技馆",
          "budget": 60,
          "transportation": "地铁",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "参观上海科技馆，了解科技与自然的奥秘。",
          "notes": "科技馆门票60元，建议提前购买。"
        },
        {
          "startTime": "12:30",
          "endTime": "14:00",
          "subtitle": "午餐",
          "budget": 100,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "上海本帮菜",
          "attractionIntroduction": "品尝上海本帮菜，如红烧肉、油爆虾等。",
          "notes": "推荐餐厅：老正兴菜馆。"
        },
        {
          "startTime": "14:30",
          "endTime": "17:30",
          "subtitle": "上海杜莎夫人蜡像馆",
          "budget": 190,
          "transportation": "地铁",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "参观上海杜莎夫人蜡像馆，与名人蜡像合影。",
          "notes": "蜡像馆门票190元，建议提前购买。"
        },
        {
          "startTime": "18:00",
          "endTime": "19:30",
          "subtitle": "晚餐",
          "budget": 150,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "上海本帮菜",
          "attractionIntroduction": "品尝上海本帮菜，如红烧肉、油爆虾等。",
          "notes": "推荐餐厅：老正兴菜馆。"
        },
        {
          "startTime": "20:00",
          "endTime": "22:00",
          "subtitle": "上海环球金融中心观光厅",
          "budget": 180,
          "transportation": "地铁",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "登上上海环球金融中心观光厅，俯瞰上海夜景。",
          "notes": "观光厅门票180元，建议提前购买。"
        }
      ]
    },
    {
      "date": "2023-10-04",
      "schedule": [
        {
          "startTime": "09:00",
          "endTime": "12:00",
          "subtitle": "上海迪士尼乐园",
          "budget": 575,
          "transportation": "地铁",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "游玩上海迪士尼乐园，体验童话世界的乐趣。",
          "notes": "迪士尼乐园门票575元，建议提前购买。"
        },
        {
          "startTime": "12:30",
          "endTime": "14:00",
          "subtitle": "午餐",
          "budget": 100,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "迪士尼乐园内餐饮",
          "attractionIntroduction": "在迪士尼乐园内享用午餐。",
          "notes": "推荐尝试米奇形状的披萨。"
        },
        {
          "startTime": "14:30",
          "endTime": "17:30",
          "subtitle": "继续游玩迪士尼乐园",
          "budget": 0,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "继续游玩迪士尼乐园，体验更多游乐设施。",
          "notes": "建议提前规划游玩路线。"
        },
        {
          "startTime": "18:00",
          "endTime": "19:30",
          "subtitle": "晚餐",
          "budget": 150,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "迪士尼乐园内餐饮",
          "attractionIntroduction": "在迪士尼乐园内享用晚餐。",
          "notes": "推荐尝试米奇形状的披萨。"
        },
        {
          "startTime": "20:00",
          "endTime": "22:00",
          "subtitle": "迪士尼乐园烟花秀",
          "budget": 0,
          "transportation": "步行",
          "accommodation": "无",
          "foodRecommendations": "无",
          "attractionIntroduction": "观看迪士尼乐园烟花秀，结束美好的一天。",
          "notes": "建议提前占好位置。"
        }
      ]
    },
    {
      "date": "2023-10-05",
      "schedule": [
        {
          "startTime": "09:00",
          "endTime": "12:00",
          "subtitle": "上海虹桥站至北京南站",
          "budget": 553,
          "transportation": "高铁",
          "accommodation": "无",
          "foodRecommendations": "高铁餐",
          "attractionIntroduction": "乘坐高铁从上海虹桥站返回北京南站，车程约4小时。",
          "notes": "建议提前预订高铁票，确保座位。"
        }
      ]
    }
  ],
  "costSummary": {
    "highSpeedRail": 2212,
    "accommodation": 0,
    "meals": 1500,
    "attractionTransportation": 200,
    "other": 1088,
    "total": 5000
  },
  "notes": [
    "建议提前预订高铁票和景点门票，确保行程顺利。",
    "注意保管好个人财物，特别是在人多的景点。"
  ]
}
        """
        
        # 打印响应的内容
        logger.info(f"Response content: {assistant_response}")

        # 解析输出格式
        try:
            output = json.loads(assistant_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return jsonify({"error": "Failed to parse JSON response from DeepSeek API"}), 500

        # 在输出中添加 planId
        output["planId"] = planId

        # 更新缓存
        user_cache[planId]['最佳旅游路线'] = assistant_response
        logger.info(f"计划 {planId} 的对话结果已更新到缓存。")

        # 返回结果
        return jsonify(output)
    except Exception as e:
        logger.error(f"模拟 DeepSeek API 调用失败, 具体错误: {e}, 请求体: {prompt}")
        return jsonify({"error": f"模拟 DeepSeek API 调用失败，请稍后重试 ({str(e)})"}), 500

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
    elif operation == "confirm":
        # 确认操作，返回缓存中的数据并清除缓存
        if planId not in user_cache:
            return jsonify({"error": "planId not found in cache, no data to confirm"}), 400

        # 获取缓存中的数据
        cached_data = user_cache[planId]
        assistant_response = cached_data.get("最佳旅游路线", "")

        # 解析输出格式
        try:
            output = json.loads(assistant_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return jsonify({"error": "Failed to parse JSON response from cache"}), 500

        # 在输出中添加 planId
        output["planId"] = planId

        # 删除缓存中的数据
        del user_cache[planId]
        logger.info(f"计划 {planId} 的对话结果已从缓存中删除。")

        # 返回结果
        return jsonify(output)
    else:
        return jsonify({"error": "Invalid operation"}), 400

    try:
        # 打印发送给 DeepSeek API 的请求体
        logger.info(f"Sending request to DeepSeek API with payload: {prompt}")
        
        response = requests.post(
            DEEPSEEK_API_URL,
            json={
                "model": "deepseek-chat",
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
        assistant_response = assistant_response.replace("```json", "").replace("```", "")
        logger.info(f"Response content: ================{assistant_response}")
        try:
            output = json.loads(assistant_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return jsonify({"error": "Failed to parse JSON response from DeepSeek API"}), 500

        # 在输出中添加 planId
        output["planId"] = planId

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

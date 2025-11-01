from flask import Flask, request, jsonify  # Flask 框架用于构建后端 API
from flask_cors import CORS  # 允许跨域请求，便于前端调用
import requests  # 用于发送 HTTP 请求
import xml.etree.ElementTree as ET  # 解析 MedlinePlus 返回的 XML 数据
import urllib.parse  # 用于 URL 编码
from datetime import timedelta, time as dt_time  # 避免覆盖
import threading  # 用于后台线程定时清理缓存
import time  # 时间相关操作
from datetime import datetime  # 日期时间处理

app = Flask(__name__)  # 创建 Flask 应用实例

# 把你从 Vercel 拿到的前端地址填在这里
FRONTEND_URL = "https://intelligent-symptom-inquiry-and-dec.vercel.app" 

# 允许 Vercel 和你本地开发时访问
CORS(app, origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:8080"])

# 或者，如果你想简单点，但只允许你的 API 路径被跨域：
# CORS(app, resources={r"/api/*": {"origins": [FRONTEND_URL, "http://localhost:5173"]}})

"""
简单内存缓存，结构如下：
cache = {
    'type:1|param:xxx': { ...结果... },
    'type:2|param:[xxx,yyy]': { ...结果... }
}
cache_date 用于记录缓存日期，每天凌晨清理一次。
"""
cache = {}
cache_date = datetime.now().date()

def clear_cache_daily():
    """
    后台线程：每天凌晨 0:00 清理缓存，保证缓存只保留一天的数据。
    """
    global cache, cache_date
    while True:
        now = datetime.now()
        current_date = now.date()
        # 如果日期变化，清理缓存
        if current_date != cache_date:
            cache = {}
            cache_date = current_date
            print(f'缓存已清理于 {now}')
        # 计算到明天00:00的秒数
        tomorrow = now + timedelta(days=1)
        next_midnight = datetime.combine(tomorrow.date(), dt_time.min)
        sleep_seconds = (next_midnight - now).total_seconds()
        time.sleep(sleep_seconds)  # 直接睡到第二天00:00

# 启动后台线程，自动清理缓存
threading.Thread(target=clear_cache_daily, daemon=True).start()

@app.route('/api/search', methods=['POST'])
def search_medlineplus():
    """
    主接口：根据 searchType 处理不同的查询方式，并返回统一格式结果。
    searchType=1: symptom 为一句话字符串
    searchType=2: symptom 为症状词数组
    支持缓存，命中则直接返回。
    """
    try:
        data = request.get_json()  # 获取前端传来的 JSON 数据
        print('前端上送数据:', data)  # 调试输出
        search_type = str(data.get('searchType'))  # 查询类型
        # 生成缓存 key，保证不同参数唯一
        cache_key = f"type:{search_type}|param:{str(data.get('symptom'))}"
        if cache_key in cache:
            print('命中缓存')
            return jsonify(cache[cache_key])  # 命中缓存直接返回
        if search_type == '1':
            # searchType=1，symptom 为一句话
            query = str(data.get('symptom', '')).strip()
            if not query:
                return jsonify({"error": "symptom must be a non-empty string when searchType=1"}), 400
            url = f"https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term={query}"
            try:
                response = requests.get(url, timeout=10)  # 请求 MedlinePlus API
                if response.status_code != 200:
                    return jsonify({"error": "MedlinePlus API 请求失败"}), 500
                root = ET.fromstring(response.text)  # 解析 XML
                all_results = []
                # 解析 XML，提取 title、FullSummary、url
                for doc in root.findall(".//document"):
                    title = doc.find(".//content[@name='title']")
                    full_summary = doc.find(".//content[@name='FullSummary']")
                    doc_url = doc.get('url')
                    all_results.append({
                        "title": title.text if title is not None else '',
                        "FullSummary": full_summary.text if full_summary is not None else '',
                        "url": doc_url if doc_url is not None else ''
                    })
                response = {
                    "success": True,
                    "searchType": 1,
                    "results": all_results
                }
                cache[cache_key] = response  # 缓存结果
                return jsonify(response)
            except Exception as e:
                return jsonify({"error": f"MedlinePlus API error: {str(e)}"}), 500
        if search_type == '2':
            # searchType=2，symptom 为数组
            symptom_list = data.get('symptom')
            if not isinstance(symptom_list, list) or not symptom_list:
                return jsonify({"error": "symptom must be a non-empty array when searchType=2"}), 400
            all_results = []
            for word in symptom_list:
                external_api_url = ''  # 保证异常处理时有值
                if not word or not str(word).strip():
                    continue  # 跳过空词
                keyword = str(word).strip()
                print('处理单词:', keyword)  # 调试输出
                # 对关键词加引号并 URL 编码
                encoded_keyword = urllib.parse.quote(f'"{keyword}"')
                print('编码后:', encoded_keyword)
                external_api_url = f"https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term={encoded_keyword}"
                print('处理url:', external_api_url)  # 调试输出
                try:
                    external_response = requests.get(external_api_url, timeout=10)
                    external_response.raise_for_status()
                    xml_response = external_response.text
                    root = ET.fromstring(xml_response)
                    # 解析 XML，提取 title、FullSummary、url
                    for doc in root.findall('.//document'):
                        title = doc.find(".//content[@name='title']")
                        full_summary = doc.find(".//content[@name='FullSummary']")
                        doc_url = doc.get('url')
                        all_results.append({
                            'title': title.text if title is not None else '',
                            'FullSummary': full_summary.text if full_summary is not None else '',
                            'url': doc_url if doc_url is not None else ''
                        })
                except Exception as e:
                    # 单个词查询失败也返回错误信息
                    all_results.append({
                        'title': '',
                        'FullSummary': f'Error: {str(e)}',
                        'url': ''
                    })
            response = {
                "success": True,
                "searchType": 2,
                "results": all_results
            }
            cache[cache_key] = response  # 缓存结果
            return jsonify(response)
        # 兜底分支（理论上不会走到）
        try:
            external_response = requests.get(external_api_url, timeout=10)
            external_response.raise_for_status()
            xml_response = external_response.text
            result_list = []
            root = ET.fromstring(xml_response)
            for doc in root.findall('.//document'):
                title = doc.find(".//content[@name='title']")
                full_summary = doc.find(".//content[@name='FullSummary']")
                result_list.append({
                    'title': title.text if title is not None else '',
                    'summary': full_summary.text if full_summary is not None else ''
                })
            response = {
                "success": True,
                "symptom": keyword,
                "encoded_keyword": encoded_keyword,
                "external_api_url": external_api_url,
                "results": result_list
            }
        except requests.exceptions.RequestException as e:
            return jsonify({
                "success": False,
                "error": f"Failed to call external API: {str(e)}"
            }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Failed to parse XML: {str(e)}"
            }), 500
        return jsonify(response)
    except Exception as e:
        # 全局异常捕获，返回错误信息
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/medlineplus', methods=['POST'])
def medlineplus():
    """
    测试接口：模拟 MedlinePlus XML API 响应，解析 XML 并返回 title 和 FullSummary。
    实际使用时应替换 xml_response 为真实 API 响应。
    """
    data = request.get_json()
    keyword = data.get('keyword', '')
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400

    # 模拟 MedlinePlus XML API 响应
    xml_response = '''<nlmSearchResult>...your XML content...</nlmSearchResult>'''
    # 实际使用时请用 requests.get() 获取真实内容

    # 解析 XML，提取 title 和 FullSummary
    result_list = []
    try:
        root = ET.fromstring(xml_response)
        for doc in root.findall('.//document'):
            title = doc.find(".//content[@name='title']").text if doc.find(".//content[@name='title']") is not None else ''
            full_summary = doc.find(".//content[@name='FullSummary']").text if doc.find(".//content[@name='FullSummary']") is not None else ''
            result_list.append({
                'title': title,
                'summary': full_summary
            })
    except Exception as e:
        return jsonify({'error': 'XML parse error', 'detail': str(e)}), 500

    return jsonify({'results': result_list})

if __name__ == '__main__':
    # 启动 Flask 服务，debug 模式方便开发调试
    app.run(debug=True)
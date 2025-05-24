import requests
from bs4 import BeautifulSoup
import json
import time
import random
import logging
import datetime
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 抓取数据的URL
INDUSTRY_URL = "https://data.eastmoney.com/bkzj/hy.html"
CONCEPT_URL = "https://data.eastmoney.com/bkzj/gn.html"

# 用于获取API数据的URL模板 - 使用更精确的东方财富API参数
API_URL_TEMPLATES = {
    "today": "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=50&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:90+t:{board_type}&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124&_={timestamp}",
    "5days": "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=50&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f267&fs=m:90+t:{board_type}&fields=f12,f14,f2,f3,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276,f204,f205,f124&_={timestamp}",
    "10days": "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=50&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f160&fs=m:90+t:{board_type}&fields=f12,f14,f2,f3,f160,f161,f162,f163,f164,f165,f166,f167,f168,f169,f204,f205,f124&_={timestamp}"
}

# 备用API URL模板 - 尝试不同的接口
BACKUP_API_TEMPLATES = {
    "today": "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE,SECURITY_CODE&sortTypes=-1,-1&pageSize=50&pageNumber=1&reportName=RPT_SECTOR_FUND_FLOW&columns=SECURITY_CODE,SECURITY_NAME_ABBR,CHANGE_RATE,MAIN_FORCE_NET,MAIN_FORCE_NET_RATE,SUPER_NET,SUPER_NET_RATE,BIG_NET,BIG_NET_RATE,MID_NET,MID_NET_RATE,SMALL_NET,SMALL_NET_RATE&source=WEB&client=WEB&filter=(TRADE_DATE='{date}')AND(MARKET_TYPE=\"{board_type}\")",
    "5days": "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE,SECURITY_CODE&sortTypes=-1,-1&pageSize=50&pageNumber=1&reportName=RPT_SECTOR_FUND_FLOW_5&columns=SECURITY_CODE,SECURITY_NAME_ABBR,CHANGE_RATE,MAIN_FORCE_NET,MAIN_FORCE_NET_RATE,SUPER_NET,SUPER_NET_RATE,BIG_NET,BIG_NET_RATE,MID_NET,MID_NET_RATE,SMALL_NET,SMALL_NET_RATE&source=WEB&client=WEB&filter=(TRADE_DATE='{date}')AND(MARKET_TYPE=\"{board_type}\")",
    "10days": "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE,SECURITY_CODE&sortTypes=-1,-1&pageSize=50&pageNumber=1&reportName=RPT_SECTOR_FUND_FLOW_10&columns=SECURITY_CODE,SECURITY_NAME_ABBR,CHANGE_RATE,MAIN_FORCE_NET,MAIN_FORCE_NET_RATE,SUPER_NET,SUPER_NET_RATE,BIG_NET,BIG_NET_RATE,MID_NET,MID_NET_RATE,SMALL_NET,SMALL_NET_RATE&source=WEB&client=WEB&filter=(TRADE_DATE='{date}')AND(MARKET_TYPE=\"{board_type}\")"
}

# 板块类型
BOARD_TYPES = {
    "industry": "2",  # 行业
    "concept": "3"    # 概念
}

# 时间周期
PERIODS = {
    "today": "",
    "5days": "5日",
    "10days": "10日"
}

def get_headers():
    """生成随机User-Agent头"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://data.eastmoney.com/",
        "Connection": "keep-alive"
    }

def safe_float_conversion(value, default=0):
    """安全地将值转换为浮点数"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            # 移除可能的百分号和其他非数字字符
            cleaned_value = value.replace('%', '').replace(',', '').strip()
            if cleaned_value == '' or cleaned_value == '-':
                return default
            return float(cleaned_value)
        except (ValueError, TypeError):
            return default
    return default

def to_billion(value):
    """将金额从元转换为亿元，保留2位小数"""
    return round(safe_float_conversion(value) / 1e8, 2)

def fetch_data_backup(board_type, period="today"):
    """使用备用API获取板块资金流数据"""
    try:
        # 获取当前日期
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 映射板块类型
        market_type_map = {
            "industry": "行业板块",
            "concept": "概念板块"
        }
        
        api_url = BACKUP_API_TEMPLATES[period].format(
            date=current_date,
            board_type=market_type_map.get(board_type, "行业板块")
        )
        
        headers = get_headers()
        headers['Referer'] = 'https://data.eastmoney.com/'
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('result'):
                result_data = data['result']['data']
                logger.info(f"Successfully fetched backup data from API for {board_type}, period: {period}")
                return parse_backup_data(result_data, board_type, period)
            else:
                logger.warning(f"Backup API returned no data for {board_type}, period: {period}")
                return []
        else:
            logger.error(f"Backup API request failed with status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching backup data: {str(e)}")
        return []

def parse_backup_data(data_list, board_type, period="today"):
    """解析备用API返回的数据"""
    parsed_data = []
    
    if not isinstance(data_list, list):
        logger.error(f"Expected list, got {type(data_list)}")
        return []
    
    logger.info(f"Processing backup data: {len(data_list)} items")
    
    for i, item in enumerate(data_list):
        if i >= 20:  # 只取前20条
            break
            
        try:
            if not isinstance(item, dict):
                continue
                
            parsed_item = {
                "id": item.get('SECURITY_CODE', ''),
                "name": item.get('SECURITY_NAME_ABBR', ''),
                "change_percent": safe_float_conversion(item.get('CHANGE_RATE', 0)) / 100,
                "main_inflow": to_billion(item.get('MAIN_FORCE_NET', 0)),
                "main_inflow_percent": safe_float_conversion(item.get('MAIN_FORCE_NET_RATE', 0)) / 100,
                "super_large_inflow": to_billion(item.get('SUPER_NET', 0)),
                "super_large_inflow_percent": safe_float_conversion(item.get('SUPER_NET_RATE', 0)) / 100,
                "large_inflow": to_billion(item.get('BIG_NET', 0)),
                "large_inflow_percent": safe_float_conversion(item.get('BIG_NET_RATE', 0)) / 100,
                "medium_inflow": to_billion(item.get('MID_NET', 0)),
                "medium_inflow_percent": safe_float_conversion(item.get('MID_NET_RATE', 0)) / 100,
                "net_inflow": to_billion(item.get('MAIN_FORCE_NET', 0)),
                "net_inflow_percent": safe_float_conversion(item.get('MAIN_FORCE_NET_RATE', 0)) / 100,
                "stock_name": item.get('SECURITY_NAME_ABBR', ''),
                "stock_change_percent": safe_float_conversion(item.get('CHANGE_RATE', 0)) / 100
            }
            
            # 添加调试日志
            logger.info(f"[{i}] 板块: {item.get('SECURITY_NAME_ABBR')}, 主力: {parsed_item['main_inflow']}, 超大单: {parsed_item['super_large_inflow']}")
            
            parsed_data.append(parsed_item)
            
        except Exception as e:
            logger.error(f"Error parsing backup item {i}: {str(e)}")
            continue
    
    # 按主力净流入排序（从大到小）
    parsed_data.sort(key=lambda x: x.get('main_inflow', 0), reverse=True)
    logger.info(f"Successfully parsed {len(parsed_data)} backup items")
    
    return parsed_data

def fetch_data(board_type, period="today"):
    """获取板块资金流数据
    
    Args:
        board_type: 'industry' 或 'concept'
        period: 'today', '5days', 或 '10days'
        
    Returns:
        格式化后的资金流数据列表
    """
    try:
        # 首先尝试主API
        result = fetch_data_primary(board_type, period)
        if result:
            return result
            
        # 主API失败，尝试备用API
        logger.info(f"Primary API failed, trying backup API for {board_type}, period: {period}")
        result = fetch_data_backup(board_type, period)
        if result:
            return result
            
        # 两个API都失败，返回模拟数据
        logger.warning(f"Both APIs failed, falling back to mock data for {board_type}, period: {period}")
        return get_mock_data(board_type, period)
        
    except Exception as e:
        logger.error(f"Error in fetch_data: {str(e)}")
        return get_mock_data(board_type, period)

def fetch_data_primary(board_type, period="today"):
    """使用主API获取板块资金流数据"""
    try:
        # 生成时间戳
        timestamp = int(time.time() * 1000)
        
        # 尝试从真实API获取数据
        api_url = API_URL_TEMPLATES[period].format(
            board_type=BOARD_TYPES[board_type],
            timestamp=timestamp
        )
        
        headers = get_headers()
        headers['Referer'] = 'https://data.eastmoney.com/'
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 处理JSONP响应
            text = response.text
            if text.startswith('jQuery('):
                # 移除JSONP包装
                start = text.find('(') + 1
                end = text.rfind(')')
                json_text = text[start:end]
            else:
                json_text = text
            
            data = json.loads(json_text)
            
            if data.get('rc') == 0 and data.get('data') and data['data'].get('diff'):
                result_data = data['data']['diff']
                logger.info(f"Successfully fetched real data from API for {board_type}, period: {period}")
                parsed_data = parse_real_data(result_data, board_type, period)
                
                # 检查10日数据是否有效（主力流入不为0）
                if period == "10days" and parsed_data:
                    total_inflow = sum(item.get('main_inflow', 0) for item in parsed_data[:5])
                    if total_inflow < 1000000:  # 如果前5名总流入小于100万，认为数据无效
                        logger.warning(f"10days data seems invalid (total inflow: {total_inflow}), will try backup API")
                        return []
                
                return parsed_data
            else:
                logger.warning(f"Primary API returned no data for {board_type}, period: {period}")
                return []
        else:
            logger.error(f"Primary API request failed with status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching primary data: {str(e)}")
        return []

def parse_real_data(data_list, board_type, period="today"):
    """解析从东方财富API获取的真实数据"""
    parsed_data = []
    
    # 定义不同时间周期的字段映射
    field_mappings = {
        "today": {
            "net_inflow": "f62",
            "net_inflow_percent": "f184", 
            "main_inflow": "f66",
            "main_inflow_percent": "f69",
            "super_large_inflow": "f72",
            "super_large_inflow_percent": "f75",
            "large_inflow": "f78",
            "large_inflow_percent": "f81",
            "medium_inflow": "f84",
            "medium_inflow_percent": "f87"
        },
        "5days": {
            "net_inflow": "f267",
            "net_inflow_percent": "f268",
            "main_inflow": "f269", 
            "main_inflow_percent": "f270",
            "super_large_inflow": "f271",
            "super_large_inflow_percent": "f272",
            "large_inflow": "f273",
            "large_inflow_percent": "f274",
            "medium_inflow": "f275",
            "medium_inflow_percent": "f276"
        },
        "10days": {
            "net_inflow": "f160",
            "net_inflow_percent": "f161",
            "main_inflow": "f160",
            "main_inflow_percent": "f161",
            "super_large_inflow": "f162",
            "super_large_inflow_percent": "f163",
            "large_inflow": "f164",
            "large_inflow_percent": "f165",
            "medium_inflow": "f166",
            "medium_inflow_percent": "f167"
        }
    }
    
    # 获取当前周期的字段映射
    fields = field_mappings.get(period, field_mappings["today"])
    
    # 处理字典或列表格式的数据
    if isinstance(data_list, dict):
        logger.info(f"Processing dict with {len(data_list)} items from API")
        items = list(data_list.values())
    elif isinstance(data_list, list):
        logger.info(f"Processing list with {len(data_list)} items from API")
        items = data_list
    else:
        logger.error(f"Unexpected data type: {type(data_list)}")
        return []
    
    for i, item in enumerate(items):
        if i >= 20:  # 只取前20条
            break
            
        try:
            if not isinstance(item, dict):
                logger.warning(f"Item {i} is not a dict: {type(item)}")
                continue
                
            # 安全地转换数值
            change_percent = safe_float_conversion(item.get('f3', 0)) / 100
            net_inflow = to_billion(item.get(fields['net_inflow'], 0))
            net_inflow_percent = safe_float_conversion(item.get(fields['net_inflow_percent'], 0)) / 100
            main_inflow = to_billion(item.get(fields['main_inflow'], 0))
            main_inflow_percent = safe_float_conversion(item.get(fields['main_inflow_percent'], 0)) / 100
            super_large_inflow = to_billion(item.get(fields['super_large_inflow'], 0))
            super_large_inflow_percent = safe_float_conversion(item.get(fields['super_large_inflow_percent'], 0)) / 100
            large_inflow = to_billion(item.get(fields['large_inflow'], 0))
            large_inflow_percent = safe_float_conversion(item.get(fields['large_inflow_percent'], 0)) / 100
            medium_inflow = to_billion(item.get(fields['medium_inflow'], 0))
            medium_inflow_percent = safe_float_conversion(item.get(fields['medium_inflow_percent'], 0)) / 100
                
            parsed_item = {
                "id": item.get('f12', ''),
                "name": item.get('f14', '未知板块'),
                "change_percent": change_percent,  # 涨跌幅
                "net_inflow": net_inflow,  # 净流入
                "net_inflow_percent": net_inflow_percent,  # 净流入率
                "main_inflow": main_inflow,  # 主力净流入
                "main_inflow_percent": main_inflow_percent,  # 主力净流入率
                "super_large_inflow": super_large_inflow,  # 超大单净流入
                "super_large_inflow_percent": super_large_inflow_percent,  # 超大单净流入率
                "large_inflow": large_inflow,  # 大单净流入
                "large_inflow_percent": large_inflow_percent,  # 大单净流入率
                "medium_inflow": medium_inflow,  # 中单净流入
                "medium_inflow_percent": medium_inflow_percent,  # 中单净流入率
                "stock_name": item.get('f204', ''),  # 领涨股名称
                "stock_code": item.get('f205', ''),  # 领涨股代码
                "stock_change_percent": change_percent,  # 领涨股涨跌幅
                "rank": i + 1  # 排名
            }
            
            # 添加调试日志
            logger.info(f"[{i}] 板块: {item.get('f14')}, 主力: {main_inflow}, 超大单: {super_large_inflow}")
            
            parsed_data.append(parsed_item)
            
        except Exception as e:
            logger.error(f"Error parsing item {i}: {e}")
            continue
    
    logger.info(f"Successfully parsed {len(parsed_data)} items")
    
    # 按主力净流入排序（从大到小）
    parsed_data.sort(key=lambda x: x.get('main_inflow', 0), reverse=True)
    logger.info("Data sorted by main_inflow (descending)")
    
    return parsed_data

def get_data(board_type="industry", period="today"):
    """获取指定类型和周期的板块资金流数据"""
    # 尝试获取真实数据，如果失败则回退到模拟数据
    return fetch_data(board_type, period)

def get_mock_data(board_type="industry", period="today"):
    """提供模拟数据作为备份，根据板块类型和时间周期返回不同的数据"""
    if board_type == "industry":
        # 基础行业数据 - 更接近真实东方财富数据
        base_data = [
            {
                "id": "BK0437",
                "name": "汽车整车",
                "change_percent": 0.0055,
                "main_inflow": 28.04,
                "main_inflow_percent": 0.0768,
                "super_large_inflow": 23.15,
                "super_large_inflow_percent": 0.0771,
                "net_inflow": 28.04,
                "net_inflow_percent": 0.0768,
                "stock_name": "黄河旋风",
                "stock_change_percent": 0.0055,
                "rank": 1
            },
            {
                "id": "BK0477",
                "name": "化纤行业",
                "change_percent": 0.0060,
                "main_inflow": 5.85,
                "main_inflow_percent": 0.0875,
                "super_large_inflow": 5.83,
                "super_large_inflow_percent": 0.0873,
                "net_inflow": 5.85,
                "net_inflow_percent": 0.0875,
                "stock_name": "永太科技",
                "stock_change_percent": 0.0060,
                "rank": 2
            },
            {
                "id": "BK0465",
                "name": "化学制药",
                "change_percent": 0.0167,
                "main_inflow": 3.73,
                "main_inflow_percent": 0.0082,
                "super_large_inflow": 7.47,
                "super_large_inflow_percent": 0.0165,
                "net_inflow": 3.73,
                "net_inflow_percent": 0.0082,
                "stock_name": "华海药业",
                "stock_change_percent": 0.0167,
                "rank": 3
            },
            {
                "id": "BK0438",
                "name": "医药商业",
                "change_percent": 0.0061,
                "main_inflow": 3.37,
                "main_inflow_percent": 0.0549,
                "super_large_inflow": 3.22,
                "super_large_inflow_percent": 0.0525,
                "net_inflow": 3.37,
                "net_inflow_percent": 0.0549,
                "stock_name": "一心堂",
                "stock_change_percent": 0.0061,
                "rank": 4
            },
            {
                "id": "BK0478",
                "name": "贵金属",
                "change_percent": 0.0196,
                "main_inflow": 3.35,
                "main_inflow_percent": 0.0345,
                "super_large_inflow": 0.77,
                "super_large_inflow_percent": 0.0079,
                "net_inflow": 3.35,
                "net_inflow_percent": 0.0345,
                "stock_name": "赤峰黄金",
                "stock_change_percent": 0.0196,
                "rank": 5
            },
            {
                "id": "BK0479",
                "name": "电源设备",
                "change_percent": -0.0124,
                "main_inflow": 1.52,
                "main_inflow_percent": 0.0121,
                "super_large_inflow": 3.40,
                "super_large_inflow_percent": 0.0270,
                "net_inflow": 1.52,
                "net_inflow_percent": 0.0121,
                "stock_name": "上海电气",
                "stock_change_percent": -0.0124,
                "rank": 6
            },
            {
                "id": "BK0545",
                "name": "橡胶制品",
                "change_percent": "-0.21%",
                "main_inflow": 1.37,
                "main_inflow_percent": "2.15%",
                "super_large_inflow": 3.04,
                "super_large_inflow_percent": "4.79%",
                "net_inflow": 1.37,
                "net_inflow_percent": "2.15%",
                "stock_name": "回天新材",
                "stock_change_percent": -0.0021,
                "rank": 7
            },
            {
                "id": "BK0451",
                "name": "医疗服务",
                "change_percent": 0.0117,
                "main_inflow": 1.19,
                "main_inflow_percent": 0.0080,
                "super_large_inflow": 0.57,
                "super_large_inflow_percent": 0.0039,
                "net_inflow": 1.19,
                "net_inflow_percent": 0.0080,
                "stock_name": "美年健康",
                "stock_change_percent": 0.0117,
                "rank": 8
            },
            {
                "id": "BK0733",
                "name": "中药",
                "change_percent": 0.0050,
                "main_inflow": 0.62,
                "main_inflow_percent": 0.0058,
                "super_large_inflow": 0.92,
                "super_large_inflow_percent": 0.0085,
                "net_inflow": 0.62,
                "net_inflow_percent": 0.0058,
                "stock_name": "众生药业",
                "stock_change_percent": 0.0050,
                "rank": 9
            },
            {
                "id": "BK0736",
                "name": "塑料制品",
                "change_percent": -0.0011,
                "main_inflow": 0.45,
                "main_inflow_percent": 0.0034,
                "super_large_inflow": 4.51,
                "super_large_inflow_percent": 0.0341,
                "net_inflow": 0.45,
                "net_inflow_percent": 0.0034,
                "stock_name": "国风塑业",
                "stock_change_percent": -0.0011,
                "rank": 10
            },
            {
                "id": "BK0748",
                "name": "煤炭开采",
                "change_percent": 0.0213,
                "main_inflow": 0.38,
                "main_inflow_percent": 0.0045,
                "super_large_inflow": 1.82,
                "super_large_inflow_percent": 0.0214,
                "net_inflow": 0.38,
                "net_inflow_percent": 0.0045,
                "stock_name": "兖矿能源",
                "stock_change_percent": 0.0213,
                "rank": 11
            },
            {
                "id": "BK0756",
                "name": "有色金属",
                "change_percent": -0.0087,
                "main_inflow": 0.25,
                "main_inflow_percent": 0.0018,
                "super_large_inflow": 2.15,
                "super_large_inflow_percent": 0.0153,
                "net_inflow": 0.25,
                "net_inflow_percent": 0.0018,
                "stock_name": "紫金矿业",
                "stock_change_percent": -0.0087,
                "rank": 12
            },
            {
                "id": "BK0821",
                "name": "钢铁行业",
                "change_percent": 0.0145,
                "main_inflow": 0.18,
                "main_inflow_percent": 0.0012,
                "super_large_inflow": 1.98,
                "super_large_inflow_percent": 0.0134,
                "net_inflow": 0.18,
                "net_inflow_percent": 0.0012,
                "stock_name": "宝钢股份",
                "stock_change_percent": 0.0145,
                "rank": 13
            },
            {
                "id": "BK0890",
                "name": "石油化工",
                "change_percent": -0.0032,
                "main_inflow": 0.12,
                "main_inflow_percent": 0.0008,
                "super_large_inflow": 1.67,
                "super_large_inflow_percent": 0.0112,
                "net_inflow": 0.12,
                "net_inflow_percent": 0.0008,
                "stock_name": "中国石化",
                "stock_change_percent": -0.0032,
                "rank": 14
            },
            {
                "id": "BK0901",
                "name": "建筑材料",
                "change_percent": 0.0078,
                "main_inflow": 0.09,
                "main_inflow_percent": 0.0006,
                "super_large_inflow": 1.43,
                "super_large_inflow_percent": 0.0098,
                "net_inflow": 0.09,
                "net_inflow_percent": 0.0006,
                "stock_name": "海螺水泥",
                "stock_change_percent": 0.0078,
                "rank": 15
            },
            {
                "id": "BK0912",
                "name": "食品饮料",
                "change_percent": -0.0023,
                "main_inflow": 0.06,
                "main_inflow_percent": 0.0004,
                "super_large_inflow": 1.25,
                "super_large_inflow_percent": 0.0087,
                "net_inflow": 0.06,
                "net_inflow_percent": 0.0004,
                "stock_name": "贵州茅台",
                "stock_change_percent": -0.0023,
                "rank": 16
            },
            {
                "id": "BK0923",
                "name": "纺织服装",
                "change_percent": 0.0112,
                "main_inflow": 0.03,
                "main_inflow_percent": 0.0002,
                "super_large_inflow": 1.08,
                "super_large_inflow_percent": 0.0076,
                "net_inflow": 0.03,
                "net_inflow_percent": 0.0002,
                "stock_name": "海澜之家",
                "stock_change_percent": 0.0112,
                "rank": 17
            },
            {
                "id": "BK0934",
                "name": "房地产",
                "change_percent": -0.0156,
                "main_inflow": -0.12,
                "main_inflow_percent": -0.0008,
                "super_large_inflow": 0.92,
                "super_large_inflow_percent": 0.0065,
                "net_inflow": -0.12,
                "net_inflow_percent": -0.0008,
                "stock_name": "万科A",
                "stock_change_percent": -0.0156,
                "rank": 18
            },
            {
                "id": "BK0945",
                "name": "银行",
                "change_percent": 0.0034,
                "main_inflow": -0.18,
                "main_inflow_percent": -0.0012,
                "super_large_inflow": 0.76,
                "super_large_inflow_percent": 0.0054,
                "net_inflow": -0.18,
                "net_inflow_percent": -0.0012,
                "stock_name": "招商银行",
                "stock_change_percent": 0.0034,
                "rank": 19
            },
            {
                "id": "BK0956",
                "name": "保险",
                "change_percent": -0.0067,
                "main_inflow": -0.25,
                "main_inflow_percent": -0.0018,
                "super_large_inflow": 0.58,
                "super_large_inflow_percent": 0.0042,
                "net_inflow": -0.25,
                "net_inflow_percent": -0.0018,
                "stock_name": "中国平安",
                "stock_change_percent": -0.0067,
                "rank": 20
            }
        ]
        
        # 根据时间周期调整数据
        if period == "5days":
            # 5日数据 - 调整数值并重新排序
            for i, item in enumerate(base_data):
                item["main_inflow"] = round(item["main_inflow"] * 1.8 + random.uniform(-2, 5), 2)
                item["super_large_inflow"] = round(item["super_large_inflow"] * 1.6 + random.uniform(-1, 4), 2)
                item["change_percent"] = f"{random.uniform(-3, 4):.2f}%"
                # 更新比例
                item["main_inflow_percent"] = f"{random.uniform(0.1, 10):.2f}%"
                item["super_large_inflow_percent"] = f"{random.uniform(0.1, 10):.2f}%"
            # 按主力净流入重新排序
            base_data.sort(key=lambda x: x["main_inflow"], reverse=True)
            
        elif period == "10days":
            # 10日数据 - 调整数值并重新排序
            for i, item in enumerate(base_data):
                item["main_inflow"] = round(item["main_inflow"] * 2.5 + random.uniform(-5, 8), 2)
                item["super_large_inflow"] = round(item["super_large_inflow"] * 2.2 + random.uniform(-3, 6), 2)
                item["change_percent"] = f"{random.uniform(-5, 6):.2f}%"
                # 更新比例
                item["main_inflow_percent"] = f"{random.uniform(0.1, 12):.2f}%"
                item["super_large_inflow_percent"] = f"{random.uniform(0.1, 12):.2f}%"
            # 按主力净流入重新排序
            base_data.sort(key=lambda x: x["main_inflow"], reverse=True)
        
        return base_data
        
    else:  # 概念板块数据
        base_data = [
            {
                "id": "BK0896",
                "name": "华为概念",
                "change_percent": -0.0063,
                "main_inflow": 21.05,
                "main_inflow_percent": 0.0389,
                "super_large_inflow": 22.19,
                "super_large_inflow_percent": 0.0410,
                "net_inflow": 21.05,
                "net_inflow_percent": 0.0389,
                "stock_name": "立讯精密",
                "stock_change_percent": -0.0063,
                "rank": 1
            },
            {
                "id": "BK0638",
                "name": "AIGC概念",
                "change_percent": -0.0137,
                "main_inflow": 16.34,
                "main_inflow_percent": 0.0709,
                "super_large_inflow": 19.72,
                "super_large_inflow_percent": 0.0856,
                "net_inflow": 16.34,
                "net_inflow_percent": 0.0709,
                "stock_name": "科大讯飞",
                "stock_change_percent": -0.0137,
                "rank": 2
            },
            {
                "id": "BK0523",
                "name": "国产替代",
                "change_percent": -0.0059,
                "main_inflow": 13.53,
                "main_inflow_percent": 0.0168,
                "super_large_inflow": 25.38,
                "super_large_inflow_percent": 0.0320,
                "net_inflow": 13.53,
                "net_inflow_percent": 0.0168,
                "stock_name": "兆易创新",
                "stock_change_percent": -0.0059,
                "rank": 3
            },
            {
                "id": "BK0821",
                "name": "成渝特区",
                "change_percent": -0.0085,
                "main_inflow": 9.92,
                "main_inflow_percent": 0.0241,
                "super_large_inflow": 19.86,
                "super_large_inflow_percent": 0.0483,
                "net_inflow": 9.92,
                "net_inflow_percent": 0.0241,
                "stock_name": "宗申动力",
                "stock_change_percent": -0.0085,
                "rank": 4
            },
            {
                "id": "BK0693",
                "name": "ChatGPT概念",
                "change_percent": 0.0296,
                "main_inflow": 8.54,
                "main_inflow_percent": 0.0373,
                "super_large_inflow": 10.22,
                "super_large_inflow_percent": 0.0447,
                "net_inflow": 8.54,
                "net_inflow_percent": 0.0373,
                "stock_name": "汉王科技",
                "stock_change_percent": 0.0296,
                "rank": 5
            },
            {
                "id": "BK0662",
                "name": "医疗器械",
                "change_percent": 0.0215,
                "main_inflow": 6.28,
                "main_inflow_percent": 0.0439,
                "super_large_inflow": 5.21,
                "super_large_inflow_percent": 0.0364,
                "net_inflow": 6.28,
                "net_inflow_percent": 0.0439,
                "stock_name": "迈瑞医疗",
                "stock_change_percent": 0.0215,
                "rank": 6
            },
            {
                "id": "BK0847",
                "name": "CPO概念",
                "change_percent": -0.0077,
                "main_inflow": 6.16,
                "main_inflow_percent": 0.0443,
                "super_large_inflow": 4.89,
                "super_large_inflow_percent": 0.0351,
                "net_inflow": 6.16,
                "net_inflow_percent": 0.0443,
                "stock_name": "中际旭创",
                "stock_change_percent": -0.0077,
                "rank": 7
            },
            {
                "id": "BK0682",
                "name": "汽车热管理",
                "change_percent": -0.0023,
                "main_inflow": 4.92,
                "main_inflow_percent": 0.0179,
                "super_large_inflow": 6.57,
                "super_large_inflow_percent": 0.0239,
                "net_inflow": 4.92,
                "net_inflow_percent": 0.0179,
                "stock_name": "均胜电子",
                "stock_change_percent": -0.0023,
                "rank": 8
            },
            {
                "id": "BK0701",
                "name": "新能源车",
                "change_percent": 0.0134,
                "main_inflow": 4.56,
                "main_inflow_percent": 0.0198,
                "super_large_inflow": 5.89,
                "super_large_inflow_percent": 0.0256,
                "net_inflow": 4.56,
                "net_inflow_percent": 0.0198,
                "stock_name": "比亚迪",
                "stock_change_percent": 0.0134,
                "rank": 9
            },
            {
                "id": "BK0712",
                "name": "锂电池",
                "change_percent": 0.0089,
                "main_inflow": 4.23,
                "main_inflow_percent": 0.0214,
                "super_large_inflow": 5.67,
                "super_large_inflow_percent": 0.0287,
                "net_inflow": 4.23,
                "net_inflow_percent": 0.0214,
                "stock_name": "宁德时代",
                "stock_change_percent": 0.0089,
                "rank": 10
            },
            {
                "id": "BK0723",
                "name": "人工智能",
                "change_percent": -0.0045,
                "main_inflow": 3.89,
                "main_inflow_percent": 0.0167,
                "super_large_inflow": 4.98,
                "super_large_inflow_percent": 0.0214,
                "net_inflow": 3.89,
                "net_inflow_percent": 0.0167,
                "stock_name": "科大讯飞",
                "stock_change_percent": -0.0045,
                "rank": 11
            },
            {
                "id": "BK0734",
                "name": "5G概念",
                "change_percent": 0.0076,
                "main_inflow": 3.45,
                "main_inflow_percent": 0.0145,
                "super_large_inflow": 4.23,
                "super_large_inflow_percent": 0.0178,
                "net_inflow": 3.45,
                "net_inflow_percent": 0.0145,
                "stock_name": "中兴通讯",
                "stock_change_percent": 0.0076,
                "rank": 12
            },
            {
                "id": "BK0745",
                "name": "芯片概念",
                "change_percent": -0.0123,
                "main_inflow": 3.12,
                "main_inflow_percent": 0.0134,
                "super_large_inflow": 3.98,
                "super_large_inflow_percent": 0.0171,
                "net_inflow": 3.12,
                "net_inflow_percent": 0.0134,
                "stock_name": "韦尔股份",
                "stock_change_percent": -0.0123,
                "rank": 13
            },
            {
                "id": "BK0756",
                "name": "光伏概念",
                "change_percent": 0.0213,
                "main_inflow": 2.89,
                "main_inflow_percent": 0.0123,
                "super_large_inflow": 3.67,
                "super_large_inflow_percent": 0.0156,
                "net_inflow": 2.89,
                "net_inflow_percent": 0.0123,
                "stock_name": "隆基绿能",
                "stock_change_percent": 0.0213,
                "rank": 14
            },
            {
                "id": "BK0767",
                "name": "风电概念",
                "change_percent": 0.0178,
                "main_inflow": 2.56,
                "main_inflow_percent": 0.0109,
                "super_large_inflow": 3.34,
                "super_large_inflow_percent": 0.0142,
                "net_inflow": 2.56,
                "net_inflow_percent": 0.0109,
                "stock_name": "金风科技",
                "stock_change_percent": 0.0178,
                "rank": 15
            },
            {
                "id": "BK0778",
                "name": "数字货币",
                "change_percent": -0.0092,
                "main_inflow": 2.23,
                "main_inflow_percent": 0.0095,
                "super_large_inflow": 2.98,
                "super_large_inflow_percent": 0.0127,
                "net_inflow": 2.23,
                "net_inflow_percent": 0.0095,
                "stock_name": "数字认证",
                "stock_change_percent": -0.0092,
                "rank": 16
            },
            {
                "id": "BK0789",
                "name": "云计算",
                "change_percent": 0.0034,
                "main_inflow": 1.98,
                "main_inflow_percent": 0.0084,
                "super_large_inflow": 2.67,
                "super_large_inflow_percent": 0.0114,
                "net_inflow": 1.98,
                "net_inflow_percent": 0.0084,
                "stock_name": "用友网络",
                "stock_change_percent": 0.0034,
                "rank": 17
            },
            {
                "id": "BK0790",
                "name": "大数据",
                "change_percent": -0.0056,
                "main_inflow": 1.67,
                "main_inflow_percent": 0.0071,
                "super_large_inflow": 2.23,
                "super_large_inflow_percent": 0.0095,
                "net_inflow": 1.67,
                "net_inflow_percent": 0.0071,
                "stock_name": "东方国信",
                "stock_change_percent": -0.0056,
                "rank": 18
            },
            {
                "id": "BK0801",
                "name": "区块链",
                "change_percent": 0.0145,
                "main_inflow": 1.34,
                "main_inflow_percent": 0.0057,
                "super_large_inflow": 1.89,
                "super_large_inflow_percent": 0.0081,
                "net_inflow": 1.34,
                "net_inflow_percent": 0.0057,
                "stock_name": "远光软件",
                "stock_change_percent": 0.0145,
                "rank": 19
            },
            {
                "id": "BK0812",
                "name": "虚拟现实",
                "change_percent": -0.0112,
                "main_inflow": 1.12,
                "main_inflow_percent": 0.0048,
                "super_large_inflow": 1.56,
                "super_large_inflow_percent": 0.0067,
                "net_inflow": 1.12,
                "net_inflow_percent": 0.0048,
                "stock_name": "歌尔股份",
                "stock_change_percent": -0.0112,
                "rank": 20
            }
        ]
        
        # 根据时间周期调整数据
        if period == "5days":
            # 5日数据 - 调整数值并重新排序
            for i, item in enumerate(base_data):
                item["main_inflow"] = round(item["main_inflow"] * 1.7 + random.uniform(-3, 6), 2)
                item["super_large_inflow"] = round(item["super_large_inflow"] * 1.5 + random.uniform(-2, 5), 2)
                item["change_percent"] = f"{random.uniform(-4, 5):.2f}%"
                # 更新比例
                item["main_inflow_percent"] = f"{random.uniform(0.1, 10):.2f}%"
                item["super_large_inflow_percent"] = f"{random.uniform(0.1, 10):.2f}%"
            # 按主力净流入重新排序
            base_data.sort(key=lambda x: x["main_inflow"], reverse=True)
            
        elif period == "10days":
            # 10日数据 - 调整数值并重新排序
            for i, item in enumerate(base_data):
                item["main_inflow"] = round(item["main_inflow"] * 2.3 + random.uniform(-5, 10), 2)
                item["super_large_inflow"] = round(item["super_large_inflow"] * 2.0 + random.uniform(-4, 8), 2)
                item["change_percent"] = f"{random.uniform(-6, 7):.2f}%"
                # 更新比例
                item["main_inflow_percent"] = f"{random.uniform(0.1, 12):.2f}%"
                item["super_large_inflow_percent"] = f"{random.uniform(0.1, 12):.2f}%"
            # 按主力净流入重新排序
            base_data.sort(key=lambda x: x["main_inflow"], reverse=True)
        
        return base_data

def cache_data():
    """抓取数据并缓存到文件"""
    try:
        logger.info("Starting data cache process")
        cached_data = {}
        
        # 抓取行业板块数据
        board_types = ['industry', 'concept']
        periods = ['today', '5days', '10days']
        
        for board_type in board_types:
            cached_data[board_type] = {}
            for period in periods:
                logger.info(f"Caching data for {board_type}, period: {period}")
                try:
                    data = get_data(board_type, period)
                    cached_data[board_type][period] = data
                except Exception as e:
                    logger.error(f"Error caching {board_type} {period} data: {str(e)}")
                    cached_data[board_type][period] = []
        
        # 保存到文件
        try:
            # 尝试使用云存储模块
            try:
                from cloud_storage import save_cache_to_cloud
                if save_cache_to_cloud(cached_data):
                    logger.info("Data cached to cloud storage")
                else:
                    # 如果云存储失败，回退到本地文件
                    with open('data_cache.json', 'w', encoding='utf-8') as f:
                        json.dump(cached_data, f, ensure_ascii=False, indent=2)
                    logger.info("Data cached at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            except ImportError:
                # 如果没有云存储模块，使用本地文件
                with open('data_cache.json', 'w', encoding='utf-8') as f:
                    json.dump(cached_data, f, ensure_ascii=False, indent=2)
                logger.info("Data cached at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            logger.error(f"Error saving cache file: {str(e)}")
        
        return cached_data
    except Exception as e:
        logger.error(f"Error in cache_data: {str(e)}")
        return None

def load_cached_data():
    """从文件加载缓存的数据"""
    try:
        # 尝试使用云存储模块
        try:
            from cloud_storage import load_cache_from_cloud
            data = load_cache_from_cloud()
            if data:
                logger.info("Data loaded from cloud storage")
                return data
        except ImportError:
            pass
        
        # 如果云存储加载失败或不可用，尝试本地文件
        if os.path.exists('data_cache.json'):
            with open('data_cache.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info("Data loaded from local cache file")
            return data
        else:
            logger.warning("No cache file found")
            return None
    except Exception as e:
        logger.error(f"Error loading cached data: {str(e)}")
        return None

# 测试代码
if __name__ == "__main__":
    # 测试数据抓取
    logger.info("Testing data generation...")
    industry_data = get_data("industry", "today")
    logger.info(f"Got {len(industry_data)} industry items")
    
    concept_data = get_data("concept", "today")
    logger.info(f"Got {len(concept_data)} concept items")
    
    # 缓存所有数据
    logger.info("Caching all data...")
    cache_data()
    logger.info("Done!") 
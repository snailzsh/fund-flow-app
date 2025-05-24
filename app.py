from flask import Flask, render_template, jsonify, request, send_file
import os
import datetime
import json
import logging
import threading
import time
import pandas as pd
from io import BytesIO

# 导入数据抓取模块
from scraper import get_data, cache_data, load_cached_data

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局变量保存缓存数据和最后更新时间
cached_data = None
last_update = None

def update_cache():
    """后台任务：定期更新数据缓存"""
    global cached_data, last_update
    
    while True:
        try:
            logger.info("Updating data cache...")
            cached_data = cache_data()
            last_update = datetime.datetime.now()
            logger.info(f"Cache updated at {last_update}")
            
            # 市场交易时间内（9:30-15:00）每15分钟更新一次，非交易时间每2小时更新一次
            now = datetime.datetime.now()
            is_trading_hours = (
                9 <= now.hour <= 15 and 
                not (now.hour == 9 and now.minute < 30) and
                not (now.hour == 15 and now.minute > 0)
            )
            
            sleep_time = 15 * 60 if is_trading_hours else 2 * 60 * 60
            time.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"Error updating cache: {str(e)}")
            time.sleep(5 * 60)  # 发生错误后等待5分钟重试

# 启动后台线程更新数据
def start_background_tasks():
    """启动后台任务"""
    # 首次加载尝试从文件加载缓存
    global cached_data, last_update
    cached_data = load_cached_data()
    
    if cached_data:
        last_update = datetime.datetime.now()
        logger.info("Loaded data from cache file")
    else:
        # 如果没有缓存文件，立即抓取新数据
        logger.info("No cache file found, fetching new data...")
        cached_data = cache_data()
        last_update = datetime.datetime.now()
    
    # 启动后台更新线程
    thread = threading.Thread(target=update_cache, daemon=True)
    thread.start()
    logger.info("Background update task started")

# 获取数据的函数，优先使用缓存
def get_cached_data(board_type, period):
    """获取缓存的数据，如果缓存不可用则直接抓取"""
    global cached_data
    
    try:
        if cached_data and board_type in cached_data and period in cached_data[board_type]:
            logger.info(f"Returning cached data for {board_type} {period}")
            raw_data = cached_data[board_type][period]
            
            # 转换字段名以保持与前端的兼容性
            converted_data = []
            for item in raw_data:
                converted_item = item.copy()
                
                # 将新字段名转换为前端期望的老字段名
                field_mapping = {
                    'main_inflow': 'main_net_inflow',
                    'main_inflow_percent': 'main_net_ratio', 
                    'super_large_inflow': 'super_net_inflow',
                    'super_large_inflow_percent': 'super_net_ratio',
                    'stock_name': 'top_stock'
                }
                
                for new_field, old_field in field_mapping.items():
                    if new_field in converted_item:
                        converted_item[old_field] = converted_item[new_field]
                        # 保留原字段以确保兼容性
                        
                # 格式化百分比字段为字符串（如果前端期望字符串格式）
                percent_fields = ['change_percent', 'main_net_ratio', 'super_net_ratio']
                for field in percent_fields:
                    if field in converted_item and isinstance(converted_item[field], (int, float)):
                        converted_item[field] = f"{converted_item[field] * 100:.2f}%"
                
                converted_data.append(converted_item)
            
            return converted_data
    except Exception as e:
        logger.error(f"Error accessing cached data: {str(e)}")
    
    # 如果缓存不可用，直接抓取
    logger.info(f"Cache miss for {board_type} {period}, fetching directly...")
    return get_data(board_type, period)

@app.route('/')
def index():
    """主页"""
    global last_update
    update_time = last_update.strftime("%Y-%m-%d %H:%M:%S") if last_update else "未更新"
    logger.info(f"Rendering index page with update time: {update_time}")
    return render_template('index.html', current_time=update_time)

@app.route('/api/industry_data')
def get_industry_data():
    """获取行业板块资金流数据"""
    period = request.args.get('period', 'today')  # today, 5days, 10days
    logger.info(f"API request for industry data, period: {period}")
    
    try:
        data = get_cached_data('industry', period)
        logger.info(f"Returning {len(data)} industry data items")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching industry data: {str(e)}", exc_info=True)
        return jsonify([]), 500

@app.route('/api/concept_data')
def get_concept_data():
    """获取概念板块资金流数据"""
    period = request.args.get('period', 'today')  # today, 5days, 10days
    logger.info(f"API request for concept data, period: {period}")
    
    try:
        data = get_cached_data('concept', period)
        logger.info(f"Returning {len(data)} concept data items")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching concept data: {str(e)}", exc_info=True)
        return jsonify([]), 500

@app.route('/api/last_update')
def get_last_update():
    """获取最后更新时间"""
    global last_update
    logger.info("API request for last update time")
    
    update_time = last_update.strftime("%Y-%m-%d %H:%M:%S") if last_update else "未更新"
    return jsonify({
        'last_update': update_time
    })

@app.route('/export/excel')
def export_excel():
    """导出Excel数据"""
    board_type = request.args.get('type', 'industry')
    period = request.args.get('period', 'today')
    logger.info(f"Export Excel request for {board_type}, period: {period}")
    
    try:
        data = get_cached_data(board_type, period)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 使用BytesIO在内存中创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='资金流数据')
        
        output.seek(0)
        
        # 设置文件名
        board_type_name = "行业板块" if board_type == "industry" else "概念板块"
        period_name = "今日" if period == "today" else ("5日" if period == "5days" else "10日")
        filename = f"{board_type_name}资金流_{period_name}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        
        logger.info(f"Exporting Excel file: {filename}")
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting Excel: {str(e)}", exc_info=True)
        return "导出失败", 500

@app.route('/export/csv')
def export_csv():
    """导出CSV数据"""
    board_type = request.args.get('type', 'industry')
    period = request.args.get('period', 'today')
    logger.info(f"Export CSV request for {board_type}, period: {period}")
    
    try:
        data = get_cached_data(board_type, period)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 使用BytesIO在内存中创建CSV文件
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')  # 使用带BOM的UTF-8编码确保Excel可以正确打开中文
        
        output.seek(0)
        
        # 设置文件名
        board_type_name = "行业板块" if board_type == "industry" else "概念板块"
        period_name = "今日" if period == "today" else ("5日" if period == "5days" else "10日")
        filename = f"{board_type_name}资金流_{period_name}_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
        
        logger.info(f"Exporting CSV file: {filename}")
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}", exc_info=True)
        return "导出失败", 500

# 添加一个测试API路由，用于确认后端正常工作
@app.route('/api/test')
def test_api():
    """测试API端点"""
    logger.info("Test API endpoint called")
    return jsonify({"status": "ok", "message": "API is working"})

if __name__ == '__main__':
    # 启动后台任务
    start_background_tasks()
    
    # 启动Flask应用
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)

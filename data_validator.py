#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具 - 用于对比我们的数据与东方财富网站数据
"""

import json
import requests
from datetime import datetime

def load_our_data():
    """加载我们缓存的数据"""
    try:
        with open('data_cache.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载缓存数据失败: {e}")
        return None

def format_money(amount):
    """格式化金额显示"""
    if abs(amount) >= 100000000:
        return f"{amount/100000000:.2f}亿"
    elif abs(amount) >= 10000:
        return f"{amount/10000:.2f}万"
    else:
        return f"{amount:.2f}元"

def format_percent(percent):
    """格式化百分比显示"""
    return f"{percent*100:.2f}%"

def display_data_comparison():
    """显示数据对比"""
    data = load_our_data()
    if not data:
        return
    
    print("=" * 80)
    print("📊 数据验证工具 - 板块资金流向数据对比")
    print("=" * 80)
    
    # 显示更新时间
    timestamp = data.get('timestamp', '未知')
    print(f"数据更新时间: {timestamp}")
    print()
    
    # 显示今日行业板块前10名
    print("🏭 今日行业板块资金流向 TOP 10:")
    print("-" * 80)
    print(f"{'排名':<4} {'板块名称':<12} {'主力流入':<12} {'涨跌幅':<8} {'领涨股':<10}")
    print("-" * 80)
    
    for i, item in enumerate(data['industry']['today'][:10]):
        rank = i + 1
        name = item['name']
        main_inflow = format_money(item['main_inflow'])
        change_percent = format_percent(item['change_percent'])
        stock_name = item.get('stock_name', '未知')
        
        print(f"{rank:<4} {name:<12} {main_inflow:<12} {change_percent:<8} {stock_name:<10}")
    
    print()
    
    # 显示5日行业板块前5名
    print("📈 5日行业板块资金流向 TOP 5:")
    print("-" * 80)
    print(f"{'排名':<4} {'板块名称':<12} {'主力流入':<12} {'涨跌幅':<8}")
    print("-" * 80)
    
    for i, item in enumerate(data['industry']['5days'][:5]):
        rank = i + 1
        name = item['name']
        main_inflow = format_money(item['main_inflow'])
        change_percent = format_percent(item['change_percent'])
        
        print(f"{rank:<4} {name:<12} {main_inflow:<12} {change_percent:<8}")
    
    print()
    
    # 显示10日行业板块前5名
    print("📊 10日行业板块资金流向 TOP 5:")
    print("-" * 80)
    print(f"{'排名':<4} {'板块名称':<12} {'主力流入':<12} {'涨跌幅':<8}")
    print("-" * 80)
    
    for i, item in enumerate(data['industry']['10days'][:5]):
        rank = i + 1
        name = item['name']
        main_inflow = format_money(item['main_inflow'])
        change_percent = format_percent(item['change_percent'])
        
        print(f"{rank:<4} {name:<12} {main_inflow:<12} {change_percent:<8}")
    
    print()
    print("=" * 80)
    print("💡 使用说明:")
    print("1. 请将上述数据与东方财富网站 (data.eastmoney.com) 的数据进行对比")
    print("2. 如果发现数据差异，可能的原因:")
    print("   - 数据更新时间不同")
    print("   - API接口参数差异")
    print("   - 排序规则不同")
    print("3. 如需更精确的数据，请告知具体的差异情况")
    print("=" * 80)

def test_api_endpoints():
    """测试不同的API端点"""
    print("🔍 测试不同API端点...")
    
    # 测试主API
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=10&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:90+t:2&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124&_=1640995200000"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ 主API连接成功")
        else:
            print(f"❌ 主API连接失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 主API测试失败: {e}")
    
    # 测试备用API
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        url = f"https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE,SECURITY_CODE&sortTypes=-1,-1&pageSize=10&pageNumber=1&reportName=RPT_SECTOR_FUND_FLOW&columns=SECURITY_CODE,SECURITY_NAME_ABBR,CHANGE_RATE,MAIN_FORCE_NET,MAIN_FORCE_NET_RATE&source=WEB&client=WEB&filter=(TRADE_DATE='{current_date}')AND(MARKET_TYPE=\"行业板块\")"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ 备用API连接成功")
        else:
            print(f"❌ 备用API连接失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 备用API测试失败: {e}")

if __name__ == "__main__":
    print("启动数据验证工具...")
    display_data_comparison()
    print()
    test_api_endpoints() 
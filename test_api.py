import requests
import json

try:
    # 测试行业板块数据
    response = requests.get('http://localhost:8080/api/industry_data')
    if response.status_code == 200:
        data = response.json()
        print("=== 行业板块数据测试 ===")
        print("第一个板块的所有字段:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
        print()
        
        # 检查数据值，判断是否来自缓存
        first_item = data[0]
        print(f"板块名称: {first_item.get('name', '未知')}")
        
        # 检查主力净流入的值
        main_inflow_value = first_item.get('main_net_inflow', 0)
        print(f"主力净流入: {main_inflow_value}亿元")
        
        # 如果值是28.04左右，说明使用了正确的缓存数据
        if 25 <= main_inflow_value <= 30:
            print("✅ 数据来源正确：使用了转换后的亿元单位数据")
        else:
            print("❌ 数据可能有问题：数值不在预期范围内")
            
        # 检查前3个板块的数据
        print("\n前3个板块的主力净流入:")
        for i, item in enumerate(data[:3]):
            main_value = item.get('main_net_inflow', 0)
            print(f"{i+1}. {item['name']}: {main_value}亿元")
                
    else:
        print(f"API请求失败，状态码: {response.status_code}")
        
except Exception as e:
    print(f"测试失败: {e}") 
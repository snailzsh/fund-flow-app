from scraper import get_data
import json

print("=== 直接调用 get_data() 函数测试 ===")

# 测试行业板块数据
data = get_data("industry", "today")
print(f"返回数据条数: {len(data)}")
print("第一个板块的所有字段:")
print(json.dumps(data[0], indent=2, ensure_ascii=False))

print("\n前3个板块的主力净流入:")
for i, item in enumerate(data[:3]):
    # 检查不同的字段名
    main_inflow = item.get('main_inflow', 'N/A')
    main_net_inflow = item.get('main_net_inflow', 'N/A')
    print(f"{i+1}. {item['name']}: main_inflow={main_inflow}, main_net_inflow={main_net_inflow}") 
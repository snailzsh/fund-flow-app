# 东方财富板块资金流数据应用

这是一个实时获取和展示东方财富网板块资金流数据的Web应用。

## 功能特点

- 实时获取东方财富网行业板块和概念板块资金流数据
- 支持今日/5日/10日资金流数据展示
- 自动数据更新（交易时段15分钟更新一次，非交易时段2小时更新一次）
- 数据支持Excel/CSV导出
- 数据单位统一为"亿元"，与东方财富网官方显示一致
- 具备数据搜索与排序功能

## 部署说明

### 本地部署

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

### Render云平台部署

1. 在Render上创建新的Web Service
2. 连接到GitHub仓库
3. 设置构建命令：`pip install -r requirements.txt`
4. 设置启动命令：`gunicorn app:app`
5. 点击"Create Web Service"

## API接口说明

- `/api/industry_data?period=today` - 获取行业板块资金流数据
- `/api/concept_data?period=today` - 获取概念板块资金流数据
- `/api/last_update` - 获取数据最后更新时间
- `/api/test` - API可用性测试端点

`period`参数可选值：`today`、`5days`、`10days`

## 数据导出

- `/export/excel?type=industry&period=today` - 导出Excel格式数据
- `/export/csv?type=industry&period=today` - 导出CSV格式数据

`type`参数可选值：`industry`、`concept`

## 项目结构

```
fund_flow_app/
├── static/             # 静态资源文件夹
│   ├── css/            # 样式表
│   └── js/             # JavaScript脚本
├── templates/          # HTML模板
│   └── index.html      # 主页面模板
├── app.py              # 主应用程序入口
├── scraper.py          # 数据抓取模块
├── data_validator.py   # 数据验证工具
├── requirements.txt    # 项目依赖
├── Procfile            # Render部署配置
├── render.yaml         # Render部署配置
└── data_cache.json     # 数据缓存文件
```

## 数据来源

数据来源于东方财富网，本应用仅供学习参考使用。

## 许可证

MIT 
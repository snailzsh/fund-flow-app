# 部署指南 - 东方财富板块资金流数据应用

本文档提供了在不同环境下部署应用的详细说明。

## 目录

1. [Render云平台部署](#render云平台部署)
2. [本地开发环境](#本地开发环境)
3. [使用Waitress的Windows部署](#使用waitress的windows部署)
4. [其他部署选项](#其他部署选项)
5. [环境变量配置](#环境变量配置)

## Render云平台部署

### 前提条件

- 一个GitHub账户
- 一个Render账户 (https://render.com)

### 步骤

1. **将代码推送到GitHub仓库**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/fund-flow-app.git
   git push -u origin main
   ```

2. **在Render上创建新的Web Service**

   - 登录Render账户
   - 点击"New +"按钮，选择"Web Service"
   - 选择"Connect a repository"，连接到GitHub
   - 选择你的fund-flow-app仓库

3. **配置Web Service**

   - 名称: `fund-flow-app` (或你喜欢的任何名称)
   - 运行时环境: `Python`
   - 构建命令: `pip install -r requirements.txt`
   - 启动命令: `gunicorn app:app`
   - 实例类型: 选择合适的计划（Free计划足够测试）
   - 区域: 选择离你的用户最近的区域
   - 环境变量: 设置`PYTHON_VERSION=3.9.0` 和 `FLASK_ENV=production`

4. **创建Web Service**

   点击"Create Web Service"按钮，Render将开始构建和部署应用。

5. **访问应用**

   部署完成后，Render会提供一个类似`https://fund-flow-app.onrender.com`的URL。

## 本地开发环境

1. **克隆代码**

   ```bash
   git clone https://github.com/yourusername/fund-flow-app.git
   cd fund-flow-app
   ```

2. **创建虚拟环境**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

4. **运行应用**

   ```bash
   python app.py
   ```

5. **访问应用**

   在浏览器中打开 http://localhost:8080

## 使用Waitress的Windows部署

1. **安装Waitress**

   ```bash
   pip install waitress
   ```

2. **运行应用**

   ```bash
   python run_waitress.py
   ```

3. **访问应用**

   在浏览器中打开 http://localhost:8080

## 其他部署选项

### Docker部署

1. **构建Docker镜像**

   ```bash
   docker build -t fund-flow-app .
   ```

2. **运行Docker容器**

   ```bash
   docker run -p 8080:8080 fund-flow-app
   ```

3. **访问应用**

   在浏览器中打开 http://localhost:8080

### Heroku部署

请参考Heroku的官方文档进行部署。应用已经包含了所需的`Procfile`。

## 环境变量配置

应用支持以下环境变量配置：

- `PORT`: 应用监听的端口号（默认：8080）
- `FLASK_ENV`: Flask环境（'development'或'production'）
- `PYTHON_VERSION`: Python版本（推荐：3.9.0或更高）
- `RENDER_CACHE_DIR`: Render平台上的缓存目录（由平台自动设置） 
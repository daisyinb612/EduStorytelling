# EduStorytelling Backend

## 项目设置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 环境配置
复制 `env.example` 文件为 `.env` 并修改配置：
```bash
cp env.example .env
```

编辑 `.env` 文件，设置你的配置值。

**重要：`.env` 文件包含敏感信息，请确保它已被添加到 `.gitignore` 中，不要提交到版本控制系统。**

### 3. 运行项目
```bash
python launch.py
```

## 环境变量说明

- `SQLALCHEMY_DATABASE_URI`: 数据库连接字符串
- `JWT_SECRET_KEY`: JWT 密钥
- `ALLOWED_ORIGINS`: 允许的 CORS 源
- `FLASK_HOST`: Flask 服务器主机
- `FLASK_PORT`: Flask 服务器端口
- `FLASK_DEBUG`: 是否开启调试模式
- `DB_RESET`: 是否重置数据库（生产环境请设置为 0）

## 注意事项

- 确保已安装 Python 3.7+
- 生产环境请务必配置 `ALLOWED_ORIGINS` 和 `JWT_SECRET_KEY`
- 数据库文件会自动创建在项目根目录

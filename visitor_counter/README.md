# 访客计数服务

基于FastAPI的独立访客计数服务，使用JSON文件存储数据，提供RESTful API接口。

## 功能特性

- 🚀 基于FastAPI的高性能Web框架
- 📊 访客计数统计功能
- 🔒 线程安全的数据操作
- 📝 详细的日志记录
- 🌐 CORS跨域支持
- 📚 自动生成的API文档
- 💾 JSON文件数据持久化

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行服务

```bash
python main.py
```

服务将在 `http://localhost:8081` 启动

### 3. 访问API文档

- Swagger UI: http://localhost:8081/docs
- ReDoc: http://localhost:8081/redoc

## API接口

### 基础接口

- `GET /` - 服务信息
- `GET /api/visitor/health` - 健康检查

### 访客计数接口

- `GET /api/visitor` - 获取当前访客计数
- `POST /api/visitor` - 增加访客计数
- `GET /api/visitor/stats` - 获取详细统计信息
- `POST /api/visitor/reset` - 重置访客计数（管理员功能）

## 使用示例

### 获取访客计数

```bash
curl http://localhost:8081/api/visitor
```

响应：
```json
{
  "count": 42
}
```

### 增加访客计数

```bash
curl -X POST http://localhost:8081/api/visitor
```

响应：
```json
{
  "count": 43
}
```

### 获取统计信息

```bash
curl http://localhost:8081/api/visitor/stats
```

响应：
```json
{
  "count": 43,
  "last_updated": "2024-01-01T12:00:00.000000",
  "data_file": "visitor_count.json",
  "status": "active"
}
```

## 数据存储

访客计数数据存储在 `visitor_count.json` 文件中：

```json
{
  "count": 43
}
```

## 配置

可以通过修改 `main.py` 中的配置来调整服务设置：

- 端口号：默认8081
- 主机地址：默认0.0.0.0
- 数据文件路径：默认visitor_count.json

## 日志

服务会记录以下信息：
- 访客计数的加载和保存
- API请求和响应
- 错误信息

## 注意事项

- 确保有足够的文件写入权限
- 建议定期备份 `visitor_count.json` 文件
- 生产环境建议使用进程管理器（如systemd、supervisor等）

"""
数据库扩展初始化文件
====================

本文件用于初始化和管理 Flask 扩展实例：
- db: SQLAlchemy 数据库实例
- jwt: JWT 认证实例
- migrate: 数据库迁移实例

这些实例在应用工厂函数中被初始化，使用延迟初始化模式
（即在 create_app() 中调用 init_app()），这样可以支持
多个应用实例（如测试应用）。
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 创建扩展实例（此时未绑定到应用）
db = SQLAlchemy()
"""SQLAlchemy 数据库实例

用于：
- 定义数据模型（继承 db.Model）
- 执行数据库查询和操作
- 管理数据库事务
"""

migrate = Migrate()
"""数据库迁移实例

用于：
- 生成数据库迁移脚本
- 同步模型与数据库结构
"""

jwt = JWTManager()
"""JWT 认证扩展实例

用于：
- 生成和验证 JWT 令牌
- 保护需要认证的路由
- 获取当前用户信息
"""

# 在应用工厂中调用的初始化函数
def init_extensions(app):
    """
    初始化所有扩展
    :param app: Flask 应用实例
    """
    # 绑定数据库到应用
    db.init_app(app)

    # 绑定迁移工具到应用
    migrate.init_app(app, db)

    # 绑定 JWT 到应用
    jwt.init_app(app)

    # 开发联调：允许前端跨域访问 API
    CORS(app, resources={r'/api/*': {'origins': '*'}})

"""
配置文件 - 用于管理 Flask 应用的各种配置
========================================

本文件定义了不同的配置类，用于在不同环境下运行应用：
- DevelopmentConfig: 开发环境配置（调试模式开启）
- ProductionConfig: 生产环境配置（调试模式关闭，安全性更高）
- TestingConfig: 测试环境配置

使用方式：
    from config import config_by_name
    app = create_app('development')
"""

import os
from datetime import timedelta


class BaseConfig:
    """
    基础配置类
    包含所有环境共用的配置项
    """
    # Flask 核心配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'classpulse-secret-key-2024-change-in-production'
    """Flask 应用的密钥，用于 session 和 cookie 加密

    在生产环境中，应该通过环境变量 SECRET_KEY 设置一个随机的强密钥
    """

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # SQLALCHEMY 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:123456@localhost:3306/classpulse'
    """
    数据库连接字符串

    格式：mysql+pymysql://用户名:密码@主机:端口/数据库名

    示例：
    - 本地数据库: mysql+pymysql://root:123456@localhost:3306/classpulse
    - 远程数据库: mysql+pymysql://user:pass@192.168.1.100:3306/classpulse

    环境变量方式：
    DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/classpulse
    """

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    """
    是否追踪数据库修改状态

    设置为 False 可以关闭 SQLAlchemy 的修改通知机制，
    减少不必要的性能开销
    """

    SQLALCHEMY_ECHO = False
    """
    是否显示 SQL 语句执行日志

    开发环境中可以设置为 True，方便调试和查看生成的 SQL
    """


class DevelopmentConfig(BaseConfig):
    """
    开发环境配置
    用于本地开发调试
    """
    DEBUG = True
    """开启调试模式，错误时显示详细信息"""

    SQLALCHEMY_ECHO = True
    """显示 SQL 语句，方便调试"""


class ProductionConfig(BaseConfig):
    """
    生产环境配置
    用于线上部署，安全性更高
    """
    DEBUG = False
    """关闭调试模式，防止敏感信息泄露"""

    SQLALCHEMY_ECHO = False
    """关闭 SQL 日志"""

    # 安全相关配置
    SECRET_KEY = os.environ.get('SECRET_KEY')
    """生产环境必须通过环境变量设置强密钥"""

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    """JWT 密钥，必须通过环境变量设置"""

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    """生产环境缩短 JWT 有效期到 1 小时"""

    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    """刷新令牌有效期 30 天"""


class TestingConfig(BaseConfig):
    """
    测试环境配置
    用于单元测试和集成测试
    """
    TESTING = True
    """测试模式标志"""

    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'mysql+pymysql://root:123456@localhost:3306/classpulse_test'
    """测试数据库连接字符串"""

    WTF_CSRF_ENABLED = False
    """测试时禁用 CSRF 保护"""


# 配置字典 - 用于根据名称获取配置类
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# 默认配置名称
default_config = 'development'

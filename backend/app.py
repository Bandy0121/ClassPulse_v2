"""
Flask 应用工厂模块
==================

本文件包含应用工厂函数 create_app()，用于创建和配置 Flask 应用实例。

应用工厂模式的优势：
1. 可以创建多个应用实例（如用于测试）
2. 每个实例可以使用不同的配置
3. 避免循环导入问题
4. 更好的模块化和可测试性

使用方式：
    # 创建开发环境应用
    app = create_app('development')

    # 创建生产环境应用
    app = create_app('production')

    # 运行应用
    if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0', port=5000)
"""

from flask import Flask, jsonify, request
from config import config_by_name, default_config
from extensions import db, migrate, jwt, init_extensions


def create_app(config_name=None):
    """
    应用工厂函数 - 创建并配置 Flask 应用实例

    参数：
        config_name: 配置名称，可选值：
            - 'development': 开发环境
            - 'production': 生产环境
            - 'testing': 测试环境
            如果不提供，使用默认配置

    返回：
        Flask 应用实例
    """
    # 初始化 Flask 应用
    app = Flask(__name__)

    # 获取配置名称（优先使用参数，否则使用默认配置）
    config_name = config_name or default_config

    # 从配置类加载配置
    app.config.from_object(config_by_name[config_name])

    # 初始化所有扩展（数据库、JWT、迁移等）
    init_extensions(app)

    # 注册蓝图（API 路由模块）
    register_blueprints(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 注册请求处理钩子
    register_request_hooks(app)

    return app


def register_blueprints(app):
    """
    注册所有 API 蓝图

    蓝图的作用：
    - 将不同的功能模块化（如认证、教师、学生等）
    - 每个蓝图有独立的路由前缀
    - 保持主应用文件简洁

    已注册的蓝图：
    - auth_bp: 认证相关接口 (前缀: /api/auth)
    - teacher_bp: 教师端接口 (前缀: /api/teacher)
    - student_bp: 学生端接口 (前缀: /api/student)
    - stats_bp: 统计数据接口 (前缀: /api/stats)
    """
    from blueprints.auth import auth_bp
    from blueprints.teacher import teacher_bp
    from blueprints.student import student_bp
    from blueprints.stats import stats_bp

    # 注册认证蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # 注册教师端蓝图
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')

    # 注册学生端蓝图
    app.register_blueprint(student_bp, url_prefix='/api/student')

    # 注册统计蓝图
    app.register_blueprint(stats_bp, url_prefix='/api/stats')


def register_error_handlers(app):
    """
    注册全局错误处理器

    处理的错误类型：
    - 404: 资源未找到
    - 401: 未授权（JWT 认证失败）
    - 403: 禁止访问
    - 500: 服务器内部错误
    - SQLALCHEMY_DATABASE_ERROR: 数据库相关错误
    """

    @app.errorhandler(404)
    def not_found(error):
        """处理 404 错误"""
        return jsonify({
            'code': 404,
            'message': '资源未找到',
            'data': None
        }), 404

    @app.errorhandler(401)
    def unauthorized(error):
        """处理 401 未授权错误"""
        return jsonify({
            'code': 401,
            'message': '未授权，请先登录',
            'data': None
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """处理 403 禁止访问错误"""
        return jsonify({
            'code': 403,
            'message': '禁止访问',
            'data': None
        }), 403

    @app.errorhandler(500)
    def internal_error(error):
        """处理 500 服务器内部错误"""
        return jsonify({
            'code': 500,
            'message': '服务器内部错误，请稍后重试',
            'data': None
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """捕获所有未处理的异常"""
        # 如果是 Flask 的 HTTP 异常，重新抛出
        if hasattr(error, 'code'):
            raise error

        # 记录错误日志（生产环境应使用专业的日志系统）
        app.logger.error(f'未处理的异常: {str(error)}', exc_info=True)

        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500


def register_request_hooks(app):
    """
    注册请求处理钩子

    可用的钩子：
    - @app.before_request: 每个请求前执行
    - @app.after_request: 每个请求后执行（有响应时）
    - @app.teardown_request: 请求结束后执行（无论是否有异常）
    """

    @app.before_request
    def before_request():
        """
        请求前处理

        可以在这里：
        - 记录请求日志
        - 检查请求参数
        - 处理跨域预检请求
        """
        app.logger.debug(f'Request: {request.method} {request.path}')

    @app.after_request
    def after_request(response):
        """
        请求后处理

        可以在这里：
        - 添加响应头（CORS 相关）
        - 记录响应时间
        - 统一响应格式
        """
        # 添加常用响应头
        response.headers['Content-Type'] = 'application/json'
        return response

    @app.teardown_request
    def teardown_request(exception):
        """
        请求结束后处理

        可以在这里：
        - 关闭数据库连接
        - 清理资源
        - 记录异常信息
        """
        if exception:
            app.logger.error(f'Request error: {str(exception)}')


# 只有直接运行本文件时才启动应用
if __name__ == '__main__':
    # 创建开发环境应用
    app = create_app('development')

    # 启动应用
    # debug=True: 开启调试模式，代码修改后自动重启
    # host='0.0.0.0': 允许外部访问（在容器中必须设置）
    # port=5000: 监听端口
    app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Flask, jsonify, request
from config import config_by_name, default_config
from extensions import db, jwt, init_extensions


def create_app(config_name=None):
    app = Flask(__name__)
    config_name = config_name or default_config
    app.config.from_object(config_by_name[config_name])
    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_request_hooks(app)
    return app


def register_blueprints(app):
    from blueprints.auth import auth_bp
    from blueprints.teacher import teacher_bp
    from blueprints.student import student_bp
    from blueprints.stats import stats_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')


def register_error_handlers(app):

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': '资源未找到',
            'data': None
        }), 404

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'code': 401,
            'message': '未授权，请先登录',
            'data': None
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'code': 403,
            'message': '禁止访问',
            'data': None
        }), 403

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'code': 500,
            'message': '服务器内部错误，请稍后重试',
            'data': None
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        if hasattr(error, 'code'):
            raise error

        app.logger.error(f'未处理的异常: {str(error)}', exc_info=True)

        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500


def register_request_hooks(app):

    @app.before_request
    def before_request():
        app.logger.debug(f'Request: {request.method} {request.path}')

    @app.after_request
    def after_request(response):
        response.headers['Content-Type'] = 'application/json'
        return response

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            app.logger.error(f'Request error: {str(exception)}')


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)

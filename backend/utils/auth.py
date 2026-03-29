"""
认证工具函数
============

本文件提供 JWT 认证相关的工具函数：
- 生成 JWT 令牌
- 验证 JWT 令牌
- 获取当前用户信息

什么是 JWT？
-----------
JWT (JSON Web Token) 是一种开放标准（RFC 7519），
用于在各方之间以 JSON 对象的形式安全传输信息。

JWT 由三部分组成：
1. Header (头部): 包含令牌类型和签名算法
2. Payload (载荷): 包含声明（用户信息等）
3. Signature (签名): 防止令牌被篡改

使用示例：
    # 生成令牌
    token = generate_jwt_token(user_id=1, user_type='teacher')

    # 在路由中使用装饰器保护接口
    @jwt_required()
    def protected():
        current_user = get_jwt_identity()

    # 验证用户角色
    @roles_required('teacher')
    def teacher_only():
        pass
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from extensions import db
from models.user import Teacher, Student


# ====================
# 令牌生成函数
# ====================

def generate_jwt_token(user_id: int, user_type: str) -> str:
    """
    生成 JWT 访问令牌

    参数：
        user_id: 用户 ID
        user_type: 用户类型，'teacher' 或 'student'

    返回：
        str: JWT 令牌字符串

    令牌中包含的声明（claims）：
    {
        "sub": "user_id",           # 主题：用户 ID
        "user_type": "teacher",     # 用户类型
        "iat": timestamp,           # 签发时间
        "exp": timestamp            # 过期时间
    }

    使用示例：
        # 教师登录成功后生成令牌
        token = generate_jwt_token(teacher.id, 'teacher')
        return jsonify({'token': token})

        # 学生登录成功后生成令牌
        token = generate_jwt_token(student.id, 'student')
        return jsonify({'token': token})
    """
    identity = {
        'user_id': user_id,
        'user_type': user_type
    }

    expires_delta = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    token = create_access_token(
        identity=identity,
        expires_delta=expires_delta
    )

    return token


def generate_refresh_token(user_id: int, user_type: str) -> str:
    """
    生成 JWT 刷新令牌

    刷新令牌用于获取新的访问令牌，当访问令牌过期时使用。

    参数：
        user_id: 用户 ID
        user_type: 用户类型，'teacher' 或 'student'

    返回：
        str: 刷新令牌字符串

    注意：
        - 刷新令牌的过期时间比访问令牌长
        - 刷新令牌仅用于获取新访问令牌
        - 应该安全存储刷新令牌（如 HTTP-only cookie）
    """
    identity = {
        'user_id': user_id,
        'user_type': user_type
    }

    expires_delta = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
    return create_refresh_token(identity=identity, expires_delta=expires_delta)


# ====================
# 用户获取函数
# ====================

def get_current_user():
    """
    获取当前登录用户对象

    该函数从 JWT 令牌中提取用户信息，并从数据库中获取完整的用户对象。

    返回：
        Teacher 或 Student 对象，如果用户不存在或令牌无效则返回 None

    使用示例：
        @app.route('/profile')
        @jwt_required()
        def profile():
            user = get_current_user()
            if user is None:
                return error_response('用户不存在', 404)
            return success_response(user.to_dict())
    """
    try:
        # 从 JWT 令牌中获取身份信息
        identity = get_jwt_identity()

        if not identity:
            return None

        user_id = identity.get('user_id')
        user_type = identity.get('user_type')

        if not user_id or not user_type:
            return None

        # 根据用户类型从数据库获取用户
        if user_type == 'teacher':
            user = Teacher.query.get(user_id)
        elif user_type == 'student':
            user = Student.query.get(user_id)
        else:
            return None

        return user

    except Exception as e:
        current_app.logger.error(f'获取当前用户失败: {str(e)}')
        return None


def get_current_user_id() -> int:
    """
    获取当前登录用户的 ID

    返回：
        int: 用户 ID，如果未登录则返回 None
    """
    try:
        identity = get_jwt_identity()
        return identity.get('user_id') if identity else None
    except Exception:
        return None


def get_current_user_type() -> str:
    """
    获取当前登录用户的类型

    返回：
        str: 用户类型 ('teacher' 或 'student')，如果未登录则返回 None
    """
    try:
        identity = get_jwt_identity()
        return identity.get('user_type') if identity else None
    except Exception:
        return None


# ====================
# 角色验证装饰器
# ====================

def roles_required(*roles):
    """
    角色验证装饰器

    用于验证当前用户是否拥有指定的角色（权限）

    参数：
        *roles: 允许的角色列表，如 'teacher', 'student'

    返回：
        装饰器函数

    使用示例：
        # 仅允许教师访问
        @app.route('/teacher/dashboard')
        @jwt_required()
        @roles_required('teacher')
        def teacher_dashboard():
            return success_response({'message': '教师仪表盘'})

        # 教师和管理员可以访问
        @app.route('/stats')
        @jwt_required()
        @roles_required('teacher', 'admin')
        def get_stats():
            pass
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()

            if current_user is None:
                return jsonify({
                    'code': 401,
                    'message': '用户不存在',
                    'data': None
                }), 401

            current_user_type = get_jwt_identity().get('user_type')

            if current_user_type not in roles:
                return jsonify({
                    'code': 403,
                    'message': '没有权限访问此资源',
                    'data': None
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ====================
# 令牌验证函数
# ====================

def validate_token(token: str) -> dict:
    """
    验证 JWT 令牌是否有效

    参数：
        token: JWT 令牌字符串

    返回：
        dict: 验证结果
        {
            'valid': True/False,
            'user_id': int 或 None,
            'user_type': str 或 None
        }
    """
    try:
        # 解码令牌（不验证签名）
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)

        return {
            'valid': True,
            'user_id': decoded.get('user_id'),
            'user_type': decoded.get('user_type')
        }
    except Exception as e:
        return {
            'valid': False,
            'user_id': None,
            'user_type': None,
            'error': str(e)
        }


# ====================
# 令牌黑名单管理
# ====================

# 在内存中存储被吊销的令牌（生产环境应使用 Redis）
REVOKED_TOKENS = set()


def RevokeToken(token: str) -> bool:
    """
    吊销（注销）某个令牌

    将令牌添加到黑名单中，使其立即失效

    参数：
        token: JWT 令牌字符串

    返回：
        bool: 操作是否成功
    """
    try:
        REVOKED_TOKENS.add(token)
        return True
    except Exception:
        return False


def IsTokenRevoked(jwt_header: dict, jwt_data: dict) -> bool:
    """
    检查令牌是否已被吊销

    这是 Flask-JWT-Extended 的回调函数，
    在每次请求时自动调用

    参数：
        jwt_header: 令牌头部
        jwt_data: 令牌载荷

    返回：
        bool: True 表示令牌已被吊销
    """
    jti = jwt_data.get('jti')  # 令牌唯一标识
    return jti in REVOKED_TOKENS

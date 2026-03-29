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


# 令牌生成函数

def generate_jwt_token(user_id: int, user_type: str) -> str:
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
    identity = {
        'user_id': user_id,
        'user_type': user_type
    }

    expires_delta = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
    return create_refresh_token(identity=identity, expires_delta=expires_delta)


# 用户获取函数

def get_current_user():
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
    try:
        identity = get_jwt_identity()
        return identity.get('user_id') if identity else None
    except Exception:
        return None


def get_current_user_type() -> str:
    try:
        identity = get_jwt_identity()
        return identity.get('user_type') if identity else None
    except Exception:
        return None


# 角色验证装饰器

def roles_required(*roles):
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


# 令牌验证函数

def validate_token(token: str) -> dict:
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


# 令牌黑名单管理

# 在内存中存储被吊销的令牌（生产环境应使用 Redis）
REVOKED_TOKENS = set()


def RevokeToken(token: str) -> bool:
    try:
        REVOKED_TOKENS.add(token)
        return True
    except Exception:
        return False


def IsTokenRevoked(jwt_header: dict, jwt_data: dict) -> bool:
    jti = jwt_data.get('jti')  # 令牌唯一标识
    return jti in REVOKED_TOKENS

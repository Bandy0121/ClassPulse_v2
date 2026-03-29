"""
认证蓝图 - 处理用户登录、注册、JWT 令牌等认证相关操作
=======================================================

本蓝图提供以下接口：
- 教师注册 /login /register
- 学生注册 /login /register
- 刷新令牌 /refresh
- 获取当前用户信息 /me
- 退出登录 /logout

使用方式：
    from blueprints.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

API 前缀：/api/auth
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

# 导入扩展和模型
from extensions import db
from models.user import Teacher, Student

# 导入工具函数
from utils.auth import generate_jwt_token, generate_refresh_token, get_current_user
from utils.response import success_response, error_response, validation_error_response

# 创建蓝图（url 前缀仅在 app.register_blueprint 中指定）
auth_bp = Blueprint('auth', __name__)


# ==================== 辅助函数 ====================

def validate_email(email: str) -> bool:
    """
    验证邮箱格式是否正确

    参数：
        email: 待验证的邮箱地址

    返回：
        bool: 邮箱格式是否有效

    支持的邮箱格式：
    - simple@example.com
    - very.common@disposable.email
    - simple@subdomain.example.com
    """
    # 简单的邮箱正则表达式
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple:
    """
    验证密码强度

    密码要求：
    - 长度至少 6 个字符
    - 包含字母和数字（可选增强）

    参数：
        password: 待验证的密码

    返回：
        tuple: (is_valid, message)
        - is_valid: bool, 密码是否有效
        - message: str, 验证消息
    """
    if len(password) < 6:
        return False, "密码长度至少为 6 个字符"

    # 可选：检查是否包含字母和数字
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_letter and has_digit):
        # 这里暂时不做强制要求，只作为警告
        pass

    return True, "密码有效"


# ==================== 教师认证接口 ====================

@auth_bp.route('/teacher/register', methods=['POST'])
def teacher_register():
    """
    教师注册接口

    请求方式：POST
    请求路径：/api/auth/teacher/register

    请求体（JSON）：
    {
        "username": "teacher123",       // 用户名（必填）
        "password": "password123",      // 密码（必填）
        "email": "teacher@example.com", // 邮箱（必填）
        "real_name": "张老师"           // 真实姓名（必填）
    }

    响应格式：
    {
        "code": 201,
        "message": "注册成功",
        "data": {
            "id": 1,
            "username": "teacher123",
            "email": "teacher@example.com",
            "real_name": "张老师"
        }
    }

    错误响应：
    - 400: 用户名或邮箱已存在
    - 422: 参数验证失败
    - 500: 服务器内部错误
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        # 检查必要字段
        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

        # 2. 提取和验证字段
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip().lower()
        real_name = data.get('real_name', '').strip()

        # 字段验证
        errors = {}

        if not username:
            errors['username'] = '用户名不能为空'
        elif len(username) < 3:
            errors['username'] = '用户名长度至少为 3 个字符'
        elif len(username) > 50:
            errors['username'] = '用户名长度不能超过 50 个字符'

        if not password:
            errors['password'] = '密码不能为空'
        else:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors['password'] = msg

        if not email:
            errors['email'] = '邮箱不能为空'
        elif not validate_email(email):
            errors['email'] = '邮箱格式不正确'

        if not real_name:
            errors['real_name'] = '真实姓名不能为空'

        # 如果有验证错误，返回 422
        if errors:
            return validation_error_response(errors)

        # 3. 检查用户是否已存在
        existing_teacher = Teacher.query.filter(
            (Teacher.username == username) | (Teacher.email == email)
        ).first()

        if existing_teacher:
            if existing_teacher.username == username:
                return error_response('用户名已存在', 400, http_status=400)
            else:
                return error_response('邮箱已被注册', 400, http_status=400)

        # 4. 创建新教师用户
        # 生成密码哈希（重要：永远不要存储明文密码）
        password_hash = generate_password_hash(password)

        teacher = Teacher(
            username=username,
            password_hash=password_hash,
            email=email,
            real_name=real_name
        )

        # 5. 保存到数据库
        db.session.add(teacher)
        db.session.commit()

        # 6. 返回成功响应
        return success_response(
            data=teacher.to_dict(),
            message='注册成功',
            code=201
        )

    except Exception as e:
        # 数据库操作失败时回滚
        db.session.rollback()
        # 记录错误日志（生产环境应使用专业的日志系统）
        current_app.logger.error(f'教师注册失败: {str(e)}')

        return error_response(
            message='注册失败，请稍后重试',
            code=500,
            http_status=500
        )


@auth_bp.route('/teacher/login', methods=['POST'])
def teacher_login():
    """
    教师登录接口

    请求方式：POST
    请求路径：/api/auth/teacher/login

    请求体（JSON）：
    {
        "username": "teacher123",  // 用户名（必填）
        "password": "password123"  // 密码（必填）
    }

    响应格式：
    {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": "eyJhbGciOiJIUzI1NiIs...",  // JWT 访问令牌
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",  // JWT 刷新令牌
            "user": {
                "id": 1,
                "username": "teacher123",
                "email": "teacher@example.com",
                "real_name": "张老师"
            }
        }
    }

    错误响应：
    - 401: 用户名或密码错误
    - 422: 参数验证失败
    - 500: 服务器内部错误
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

        # 2. 提取字段
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # 3. 参数验证
        errors = {}
        if not username:
            errors['username'] = '用户名不能为空'
        if not password:
            errors['password'] = '密码不能为空'

        if errors:
            return validation_error_response(errors)

        # 4. 查找用户
        teacher = Teacher.query.filter_by(username=username).first()

        # 5. 验证密码
        # 注意：使用 check_password_hash 验证哈希密码
        # 永远不要直接比较密码字符串
        if not teacher or not teacher.check_password(password):
            return error_response(
                message='用户名或密码错误',
                code=401,
                http_status=401
            )

        # 6. 生成 JWT 令牌
        token = generate_jwt_token(teacher.id, 'teacher')
        refresh_token = generate_refresh_token(teacher.id, 'teacher')

        # 7. 返回成功响应
        return success_response({
            'token': token,
            'refresh_token': refresh_token,
            'user': teacher.to_dict()
        }, '登录成功')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'教师登录失败: {str(e)}')

        return error_response(
            message='登录失败，请稍后重试',
            code=500,
            http_status=500
        )


@auth_bp.route('/teacher/me', methods=['GET'])
def teacher_get_profile():
    """
    获取当前教师信息接口

    请求方式：GET
    请求路径：/api/auth/teacher/me

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "username": "teacher123",
            "email": "teacher@example.com",
            "real_name": "张老师"
        }
    }

    错误响应：
    - 401: 未授权（Token 无效或过期）
    - 404: 用户不存在
    - 500: 服务器内部错误
    """
    try:
        # 1. 获取当前用户（通过 JWT 令牌）
        # get_current_user() 函数会自动从 Token 中提取用户信息
        teacher = get_current_user()

        # 2. 检查用户是否存在
        if not teacher:
            return error_response(
                message='用户不存在',
                code=404,
                http_status=404
            )

        # 3. 返回用户信息
        return success_response(teacher.to_dict())

    except Exception as e:
        current_app.logger.error(f'获取教师信息失败: {str(e)}')

        return error_response(
            message='获取信息失败',
            code=500,
            http_status=500
        )


# ==================== 学生认证接口 ====================

@auth_bp.route('/student/register', methods=['POST'])
def student_register():
    """
    学生注册接口

    请求方式：POST
    请求路径：/api/auth/student/register

    请求体（JSON）：
    {
        "username": "student123",       // 用户名（必填）
        "password": "password123",      // 密码（必填）
        "email": "student@example.com", // 邮箱（必填）
        "real_name": "张三"             // 真实姓名（必填）
        "student_id": "2023001234"     // 学号（必填）
    }

    响应格式：
    {
        "code": 201,
        "message": "注册成功",
        "data": {
            "id": 1,
            "username": "student123",
            "email": "student@example.com",
            "real_name": "张三",
            "student_id": "2023001234"
        }
    }

    错误响应：
    - 400: 用户名、邮箱或学号已存在
    - 422: 参数验证失败
    - 500: 服务器内部错误
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

        # 2. 提取和验证字段
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip().lower()
        real_name = data.get('real_name', '').strip()
        student_id = data.get('student_id', '').strip()

        # 字段验证
        errors = {}

        if not username:
            errors['username'] = '用户名不能为空'
        elif len(username) < 3:
            errors['username'] = '用户名长度至少为 3 个字符'
        elif len(username) > 50:
            errors['username'] = '用户名长度不能超过 50 个字符'

        if not password:
            errors['password'] = '密码不能为空'
        else:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors['password'] = msg

        if not email:
            errors['email'] = '邮箱不能为空'
        elif not validate_email(email):
            errors['email'] = '邮箱格式不正确'

        if not real_name:
            errors['real_name'] = '真实姓名不能为空'

        if not student_id:
            errors['student_id'] = '学号不能为空'

        if errors:
            return validation_error_response(errors)

        # 3. 检查用户是否已存在
        existing_student = Student.query.filter(
            (Student.username == username) |
            (Student.email == email) |
            (Student.student_id == student_id)
        ).first()

        if existing_student:
            if existing_student.username == username:
                return error_response('用户名已存在', 400, http_status=400)
            elif existing_student.email == email:
                return error_response('邮箱已被注册', 400, http_status=400)
            else:
                return error_response('学号已被注册', 400, http_status=400)

        # 4. 创建新学生用户
        password_hash = generate_password_hash(password)

        student = Student(
            username=username,
            password_hash=password_hash,
            email=email,
            real_name=real_name,
            student_id=student_id
        )

        # 5. 保存到数据库
        db.session.add(student)
        db.session.commit()

        # 6. 返回成功响应
        return success_response(
            data=student.to_dict(),
            message='注册成功',
            code=201
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'学生注册失败: {str(e)}')

        return error_response(
            message='注册失败，请稍后重试',
            code=500,
            http_status=500
        )


@auth_bp.route('/student/login', methods=['POST'])
def student_login():
    """
    学生登录接口

    请求方式：POST
    请求路径：/api/auth/student/login

    请求体（JSON）：
    {
        "username": "student123",  // 用户名（必填）
        "password": "password123"  // 密码（必填）
    }

    响应格式：
    {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "user": {
                "id": 1,
                "username": "student123",
                "email": "student@example.com",
                "real_name": "张三",
                "student_id": "2023001234"
            }
        }
    }

    错误响应：
    - 401: 用户名或密码错误
    - 422: 参数验证失败
    - 500: 服务器内部错误
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

        # 2. 提取字段
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # 3. 参数验证
        errors = {}
        if not username:
            errors['username'] = '用户名不能为空'
        if not password:
            errors['password'] = '密码不能为空'

        if errors:
            return validation_error_response(errors)

        # 4. 查找用户
        student = Student.query.filter_by(username=username).first()

        # 5. 验证密码
        if not student or not student.check_password(password):
            return error_response(
                message='用户名或密码错误',
                code=401,
                http_status=401
            )

        # 6. 生成 JWT 令牌
        token = generate_jwt_token(student.id, 'student')
        refresh_token = generate_refresh_token(student.id, 'student')

        # 7. 返回成功响应
        return success_response({
            'token': token,
            'refresh_token': refresh_token,
            'user': student.to_dict()
        }, '登录成功')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'学生登录失败: {str(e)}')

        return error_response(
            message='登录失败，请稍后重试',
            code=500,
            http_status=500
        )


@auth_bp.route('/student/me', methods=['GET'])
def student_get_profile():
    """
    获取当前学生信息接口

    请求方式：GET
    请求路径：/api/auth/student/me

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "username": "student123",
            "email": "student@example.com",
            "real_name": "张三",
            "student_id": "2023001234"
        }
    }

    错误响应：
    - 401: 未授权
    - 404: 用户不存在
    - 500: 服务器内部错误
    """
    try:
        # 1. 获取当前用户
        student = get_current_user()

        if not student:
            return error_response(
                message='用户不存在',
                code=404,
                http_status=404
            )

        # 2. 返回用户信息
        return success_response(student.to_dict())

    except Exception as e:
        current_app.logger.error(f'获取学生信息失败: {str(e)}')

        return error_response(
            message='获取信息失败',
            code=500,
            http_status=500
        )


# ==================== 通用接口 ====================

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    刷新 JWT 令牌接口

    当访问令牌过期时，可以使用刷新令牌获取新的访问令牌。

    请求方式：POST
    请求路径：/api/auth/refresh

    请求头：
    Authorization: Bearer <Refresh Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "token": "eyJhbGciOiJIUzI1NiIs..."  // 新的访问令牌
        }
    }

    错误响应：
    - 401: 刷新令牌无效或过期
    - 500: 服务器内部错误
    """
    from flask_jwt_extended import jwt_required, get_jwt_identity

    try:
        # 1. 验证刷新令牌
        # jwt_required() 装饰器会自动验证令牌
        @jwt_required()
        def get_new_token():
            identity = get_jwt_identity()
            user_id = identity.get('user_id')
            user_type = identity.get('user_type')

            if not user_id or not user_type:
                return error_response(
                    message='令牌无效',
                    code=401,
                    http_status=401
                )

            # 2. 生成新的访问令牌
            new_token = generate_jwt_token(user_id, user_type)

            return success_response(
                {'token': new_token},
                '令牌已刷新'
            )

        return get_new_token()

    except Exception as e:
        current_app.logger.error(f'刷新令牌失败: {str(e)}')

        return error_response(
            message='刷新令牌失败',
            code=500,
            http_status=500
        )


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    退出登录接口

    注销当前用户的登录状态（将令牌加入黑名单）。

    请求方式：POST
    请求路径：/api/auth/logout

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "退出登录成功",
        "data": null
    }

    错误响应：
    - 401: 未授权
    - 500: 服务器内部错误
    """
    from flask_jwt_extended import jwt_required, get_jwt
    from utils.auth import RevokeToken

    try:
        # 1. 验证令牌
        @jwt_required()
        def do_logout():
            # 2. 获取令牌的 JTI（唯一标识）
            jti = get_jwt()['jti']

            # 3. 将令牌加入黑名单
            RevokeToken(jti)

            return success_response(None, '退出登录成功')

        return do_logout()

    except Exception as e:
        current_app.logger.error(f'退出登录失败: {str(e)}')

        return error_response(
            message='退出登录失败',
            code=500,
            http_status=500
        )

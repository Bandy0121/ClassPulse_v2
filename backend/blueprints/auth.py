from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

from extensions import db
from models.user import Teacher, Student

from utils.auth import generate_jwt_token, generate_refresh_token, get_current_user
from utils.response import success_response, error_response, validation_error_response

auth_bp = Blueprint('auth', __name__)



def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple:
    if len(password) < 6:
        return False, "密码长度至少为 6 个字符"

    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_letter and has_digit):
        pass

    return True, "密码有效"



@auth_bp.route('/teacher/register', methods=['POST'])
def teacher_register():
    try:
        data = request.get_json()

        # 检查必要字段
        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

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

        existing_teacher = Teacher.query.filter(
            (Teacher.username == username) | (Teacher.email == email)
        ).first()

        if existing_teacher:
            if existing_teacher.username == username:
                return error_response('用户名已存在', 400, http_status=400)
            else:
                return error_response('邮箱已被注册', 400, http_status=400)

        # 生成密码哈希（重要：永远不要存储明文密码）
        password_hash = generate_password_hash(password)

        teacher = Teacher(
            username=username,
            password_hash=password_hash,
            email=email,
            real_name=real_name
        )

        db.session.add(teacher)
        db.session.commit()

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
    try:
        data = request.get_json()

        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

        username = data.get('username', '').strip()
        password = data.get('password', '')

        errors = {}
        if not username:
            errors['username'] = '用户名不能为空'
        if not password:
            errors['password'] = '密码不能为空'

        if errors:
            return validation_error_response(errors)

        teacher = Teacher.query.filter_by(username=username).first()

        # 注意：使用 check_password_hash 验证哈希密码
        # 永远不要直接比较密码字符串
        if not teacher or not teacher.check_password(password):
            return error_response(
                message='用户名或密码错误',
                code=401,
                http_status=401
            )

        token = generate_jwt_token(teacher.id, 'teacher')
        refresh_token = generate_refresh_token(teacher.id, 'teacher')

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
    try:
        # get_current_user() 函数会自动从 Token 中提取用户信息
        teacher = get_current_user()

        if not teacher:
            return error_response(
                message='用户不存在',
                code=404,
                http_status=404
            )

        return success_response(teacher.to_dict())

    except Exception as e:
        current_app.logger.error(f'获取教师信息失败: {str(e)}')

        return error_response(
            message='获取信息失败',
            code=500,
            http_status=500
        )



@auth_bp.route('/student/register', methods=['POST'])
def student_register():
    try:
        data = request.get_json()

        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

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

        password_hash = generate_password_hash(password)

        student = Student(
            username=username,
            password_hash=password_hash,
            email=email,
            real_name=real_name,
            student_id=student_id
        )

        db.session.add(student)
        db.session.commit()

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
    try:
        data = request.get_json()

        if not data:
            return error_response("请求体不能为空", 400, http_status=400)

        username = data.get('username', '').strip()
        password = data.get('password', '')

        errors = {}
        if not username:
            errors['username'] = '用户名不能为空'
        if not password:
            errors['password'] = '密码不能为空'

        if errors:
            return validation_error_response(errors)

        student = Student.query.filter_by(username=username).first()

        if not student or not student.check_password(password):
            return error_response(
                message='用户名或密码错误',
                code=401,
                http_status=401
            )

        token = generate_jwt_token(student.id, 'student')
        refresh_token = generate_refresh_token(student.id, 'student')

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
    try:
        student = get_current_user()

        if not student:
            return error_response(
                message='用户不存在',
                code=404,
                http_status=404
            )

        return success_response(student.to_dict())

    except Exception as e:
        current_app.logger.error(f'获取学生信息失败: {str(e)}')

        return error_response(
            message='获取信息失败',
            code=500,
            http_status=500
        )



@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    from flask_jwt_extended import jwt_required, get_jwt_identity

    try:
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
    from flask_jwt_extended import jwt_required, get_jwt
    from utils.auth import RevokeToken

    try:
        @jwt_required()
        def do_logout():
            jti = get_jwt()['jti']

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

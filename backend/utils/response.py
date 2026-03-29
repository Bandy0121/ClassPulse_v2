"""
统一响应格式工具函数
====================

本文件提供统一的 API 响应格式函数，确保前后端交互的一致性。

统一响应格式的好处：
1. 前端可以使用统一的方式处理响应
2. 便于错误处理和调试
3. 提高代码可维护性

统一响应格式示例：
{
    "code": 200,           # 状态码：200 表示成功，其他表示错误
    "message": "success",  # 消息：描述操作结果
    "data": {}            # 数据：返回的具体数据内容
}
"""

from flask import jsonify
from typing import Any, Optional, Dict


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> tuple:
    """
    成功响应格式

    参数：
        data: 返回的数据内容，可以是字典、列表或 None
        message: 响应消息，默认为"操作成功"
        code: HTTP 状态码，默认为 200

    返回：
        tuple: (json_response, http_status_code)
        例如：(jsonify({...}), 200)

    使用示例：
        # 返回成功消息，无数据
        return success_response()

        # 返回数据
        return success_response(data={"user_id": 1})

        # 自定义消息
        return success_response(message="登录成功", data={"token": "xxx"})
    """
    return jsonify({
        'code': code,
        'message': message,
        'data': data
    }), code


def error_response(
    message: str = "请求失败",
    code: int = 400,
    data: Optional[Any] = None,
    http_status: int = 400
) -> tuple:
    """
    错误响应格式

    参数：
        message: 错误消息
        code: 业务错误码（自定义，非 HTTP 状态码）
        data: 错误详情数据（可选）
        http_status: HTTP 状态码，默认为 400

    返回：
        tuple: (json_response, http_status_code)

    使用示例：
        # 参数错误
        return error_response(message="用户名不能为空", code=1001, http_status=400)

        # 未授权
        return error_response(message="请先登录", code=1002, http_status=401)

        # 服务器错误
        return error_response(message="服务器内部错误", code=500, http_status=500)
    """
    return jsonify({
        'code': code,
        'message': message,
        'data': data
    }), http_status


def paginated_response(
    data: list,
    total: int,
    page: int = 1,
    per_page: int = 10,
    message: str = "操作成功"
) -> tuple:
    """
    分页响应格式

    用于返回分页数据，包含总页数、当前页等信息

    参数：
        data: 当前页的数据列表
        total: 总记录数
        page: 当前页码（从 1 开始）
        per_page: 每页记录数
        message: 响应消息

    返回：
        tuple: (json_response, 200)

    返回格式示例：
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "items": [...],      # 当前页数据
            "total": 100,        # 总记录数
            "page": 1,           # 当前页
            "per_page": 10,      # 每页数量
            "total_pages": 10    # 总页数
        }
    }
    """
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    return jsonify({
        'code': 200,
        'message': message,
        'data': {
            'items': data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }
    }), 200


def validation_error_response(errors: Dict[str, str]) -> tuple:
    """
    验证错误响应格式

    用于返回字段验证错误，通常用于 POST/PUT 请求

    参数：
        errors: 错误字典，键为字段名，值为错误消息
        例如：{"username": "用户名不能为空", "email": "邮箱格式不正确"}

    返回：
        tuple: (json_response, 422)

    返回格式示例：
    {
        "code": 422,
        "message": "参数验证失败",
        "data": {
            "errors": {
                "username": "用户名不能为空",
                "email": "邮箱格式不正确"
            }
        }
    }
    """
    return jsonify({
        'code': 422,
        'message': '参数验证失败',
        'data': {
            'errors': errors
        }
    }), 422

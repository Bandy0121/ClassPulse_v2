from flask import jsonify
from typing import Any, Optional, Dict


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> tuple:
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
    return jsonify({
        'code': 422,
        'message': '参数验证失败',
        'data': {
            'errors': errors
        }
    }), 422

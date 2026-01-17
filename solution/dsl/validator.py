from typing import List, Optional
from pydantic import BaseModel

class DslValidationError(BaseModel):
    code: str
    message: str
    position: Optional[int] = None
    near: Optional[str] = None

class DslValidateResponse(BaseModel):
    is_valid: bool
    normalized_expression: Optional[str] = None
    errors: List[DslValidationError]

def count_ast_nodes(node) -> int:
    """подсчитывает количество узлов в AST дереве"""
    if isinstance(node, dict):
        count = 1
        for value in node.values():
            count += count_ast_nodes(value)
        return count
    elif isinstance(node, list):
        count = 0
        for item in node:
            count += count_ast_nodes(item)
        return count
    else:
        return 1


def apply_fraud_rules(transaction_data: dict) -> dict:
    return {
        "is_fraud": False,
        "score": 0.0,
        "rules_triggered": []
    }


def validate_dsl_expression(dsl_expression: str) -> DslValidateResponse:
    """
    проверяет выражения dsl в соответствии с реализацией уровня 1 
    поддерживает: amount, операторы > >= < <= = !=, числа
    """
    import re
    
    # читка ненужных пробелов чтоб изб проблемз
    expr = ' '.join(dsl_expression.split())
    operators = ['>=', '<=', '!=', '=', '>', '<']
    for op in operators:
        expr = expr.replace(op, f' {op} ')
    
    # дополнительная нормализация
    expr = ' '.join(expr.split())
    allowed_fields = ['amount']
    allowed_operators = ['>', '>=', '<', '<=', '=', '!=']
    tokens = expr.split()
    
    if len(tokens) == 3:
        field, operator, value = tokens
        if field not in allowed_fields:
            error = DslValidationError(
                code="DSL_INVALID_FIELD",
                message=f"Field '{field}' is not supported in current tier",
                position=0,
                near=field
            )
            return DslValidateResponse(
                is_valid=False,
                normalized_expression=None,
                errors=[error]
            )
        
        if operator not in allowed_operators:
            error = DslValidationError(
                code="DSL_INVALID_OPERATOR",
                message=f"Operator '{operator}' is not supported",
                position=len(field) + 1,
                near=operator
            )
            return DslValidateResponse(
                is_valid=False,
                normalized_expression=None,
                errors=[error]
            )
        
        try:
            float(value)
        except ValueError:
            error = DslValidationError(
                code="DSL_PARSE_ERROR",
                message=f"Expected number after '{operator}', got '{value}'",
                position=len(field) + len(operator) + 2,
                near=value
            )
            return DslValidateResponse(
                is_valid=False,
                normalized_expression=None,
                errors=[error]
            )
        
        # допустимое выражение для уровня 1 настройки
        return DslValidateResponse(
            is_valid=True,
            normalized_expression=expr,
            errors=[]
        )
    
    # возвращать unsupported для чего-либо более сложного
    error = DslValidationError(
        code="DSL_UNSUPPORTED_TIER",
        message="Complex expressions are not supported in current tier implementation",
        position=0,
        near=dsl_expression[:20]  # показ начала выражения
    )
    
    return DslValidateResponse(
        is_valid=False,
        normalized_expression=None,
        errors=[error]
    )
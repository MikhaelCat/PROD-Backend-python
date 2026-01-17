import re
from typing import Dict, Any, Optional
from decimal import Decimal


def evaluate_dsl_expression(dsl_expression: str, context: Dict[str, Any]) -> tuple[bool, str]:
    """
    Вычисляет выражение DSL в соответствии с контекстом.
    
    Аргументы:
        dsl_expression: Вычисляемое выражение DSL
        контекст: контекст, содержащий транзакцию, пользователя и другие данные
        
    Возвращается:
        Кортеж (результат, описание), где результат равен True, если правило соответствует
    """
    # делит лишних пробелов
    expr = ' '.join(dsl_expression.split())
    
    parts = expr.split()
    if len(parts) == 3:
        field, operator, value_str = parts
        actual_value = _get_field_value(context, field)
        
        # преобразование value_str в соответствующий тип
        try:
            expected_value = _parse_value(value_str)
        except ValueError as e:
            return False, f"Error parsing value '{value_str}': {str(e)}"
        
        # сравнение значений
        result = _compare_values(actual_value, operator, expected_value)
        
        # создание понятного для человека описания
        if result:
            description = f"{field} ({actual_value}) {operator} {expected_value}, rule matched"
        else:
            description = f"{field} ({actual_value}) does not satisfy {operator} {expected_value}, rule did not match"
        
        return result, description
    return False, f"Unsupported expression format: {dsl_expression}"


def _get_field_value(context: Dict[str, Any], field: str) -> Any:
    """извлечение данных """
    # обработка вложенные поля, такие как user.age, user.region
    if '.' in field:
        parts = field.split('.')
        current = context
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
    else:
        # смотрим на транзакцию, пользователя и метаданные
        for source in [context.get('transaction', {}), context.get('user', {}), context.get('metadata', {})]:
            if isinstance(source, dict) and field in source:
                return source[field]
        return None


def _parse_value(value_str: str) -> Any:
    """Преобразует строку в соответствующий ей тип."""
    if value_str.startswith("'") and value_str.endswith("'"):
        return value_str[1:-1]  # Remove 
    
    # обработка числовых значений
    try:
        if '.' in value_str:
            return float(value_str)
        else:
            return int(value_str)
    except ValueError:
        return value_str


def _compare_values(left: Any, operator: str, right: Any) -> bool:
    """Сравнивает два значения оператора"""
    if left is None:
        return False  # если значение поля равно null, сравнение всегда завершается неудачей
    
    # обрабатывать сравнения строк
    if isinstance(left, str) and operator not in ['=', '!=']:
        return False  #строки можно сравнивать только с = и !=
    
    # выполните сравнение на основе оператора
    if operator == '=':
        return left == right
    elif operator == '!=':
        return left != right
    elif operator == '>':
        return left > right
    elif operator == '>=':
        return left >= right
    elif operator == '<':
        return left < right
    elif operator == '<=':
        return left <= right
    else:
        return False  
# warnings_script.py

import os  # Предупреждение: неиспользуемый импорт


def add_numbers(a, b):
    """Складывает два числа."""
    result = a + b
    unused_variable = (
        "Этот код может вызывать вопросы"  # Предупреждение: неиспользуемая переменная
    )

    # Не самый лучший способ проверки типа
    if type(b) is int:
        print("Второе число - целое.")

    return result


# Пример использования
sum_result = add_numbers(5, 3)
print(f"Результат сложения: {sum_result}")

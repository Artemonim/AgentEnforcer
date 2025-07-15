# correct_script.py


def calculate_rectangle_area(width: float, height: float) -> float:
    """Вычисляет площадь прямоугольника."""
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        raise TypeError("Ширина и высота должны быть числами.")
    if width < 0 or height < 0:
        raise ValueError("Ширина и высота не могут быть отрицательными.")
    return width * height


# Пример использования
rect_width = 10
rect_height = 5
area = calculate_rectangle_area(rect_width, rect_height)

print(
    f"Площадь прямоугольника с шириной {rect_width} и высотой {rect_height} равна {area}."
)

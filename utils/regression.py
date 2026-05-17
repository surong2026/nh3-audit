from typing import List, Tuple
from math import sqrt


def linear_regression(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """最小二乘线性回归，返回 (截距a, 斜率b, 相关系数r)"""
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)
    sum_y2 = sum(yi * yi for yi in y)

    denominator_b = n * sum_x2 - sum_x * sum_x
    if denominator_b == 0:
        return 0.0, 0.0, 0.0

    b = (n * sum_xy - sum_x * sum_y) / denominator_b
    a = (sum_y - b * sum_x) / n

    denominator_r = sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
    if denominator_r == 0:
        r = 0.0
    else:
        r = (n * sum_xy - sum_x * sum_y) / denominator_r

    return a, b, r


def predict_absorbance(mass: float, a: float, b: float) -> float:
    """根据回归方程预测给定质量的吸光度"""
    return a + b * mass


def calc_concentration(absorbance: float, blank: float, a: float, b: float,
                       volume: float, dilution: float = 1.0) -> float:
    """公式 ρN = (As - Ab - a) / (b × V) × f"""
    if b <= 0:
        return 0.0
    return (absorbance - blank - a) / (b * volume) * dilution

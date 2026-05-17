from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from config import CALIBRATION_POINTS, MIN_CORRELATION_R, CALIBRATION_TOTAL_VOLUME
from utils.regression import linear_regression


class CalibrationPointsRule(BaseAuditRule):
    """B1: 校准点数量与浓度"""
    code = "B1"
    category = "校准曲线"

    def audit(self, record: AnalysisRecord) -> list:
        points = record.calibration_curve.points
        items = []

        expected_n = len(CALIBRATION_POINTS)
        if len(points) != expected_n:
            items.append(self._fail(name="校准点数量",
                                    actual=f"{len(points)}个",
                                    limit=f"{expected_n}个", hj_ref="7.1",
                                    detail=f"校准曲线应有{expected_n}个点",
                                    suggestion="应按照方法要求配制完整的标准系列"))
            return items

        for i, (point, expected_mass) in enumerate(zip(points, CALIBRATION_POINTS)):
            tol = 0.01 if expected_mass == 0 else expected_mass * 0.01
            if abs(point.nh3_mass - expected_mass) > tol:
                items.append(self._fail(name=f"校准点{i+1}含量",
                                        actual=f"{point.nh3_mass} μg",
                                        limit=f"{expected_mass} μg", hj_ref="7.1",
                                        detail=f"第{i+1}个校准点NH3-N含量不符",
                                        suggestion=f"应加入{expected_mass/(point.working_conc or 10.0):.2f}mL使用液"))

        if not points[-1].absorbance or points[-1].absorbance <= 0:
            items.append(self._fail(name="校准点吸光度", actual="未填写",
                                    limit="需填写各点吸光度", hj_ref="7.1",
                                    detail="未填写校准点吸光度数据"))

        if not items:
            items.append(self._pass(name="校准点数量与含量",
                                    actual=f"{len(points)}点, 0-100 μg",
                                    limit=f"{expected_n}点, 0-100 μg", hj_ref="7.1"))
        return items


class CorrelationCoefficientRule(BaseAuditRule):
    """B2: 相关系数 r ≥ 0.999，同时校核回归方程"""
    code = "B2"
    category = "校准曲线"

    def audit(self, record: AnalysisRecord) -> list:
        points = record.calibration_curve.points
        if len(points) < 2:
            return [self._fail(name="相关系数", actual="校准点数不足",
                              limit=f"r ≥ {MIN_CORRELATION_R}", hj_ref="7.1",
                              detail="无法计算相关系数，至少需要2个校准点")]

        x_vals = [p.nh3_mass for p in points]
        y_vals = [p.a_minus_a0 if p.a_minus_a0 is not None else p.absorbance
                  for p in points]

        # Save PDF-extracted values before recomputing
        extracted_a = record.calibration_curve.regression_a
        extracted_b = record.calibration_curve.regression_b
        extracted_r = record.calibration_curve.correlation_r

        a, b, r = linear_regression(x_vals, y_vals)
        record.calibration_curve.regression_a = a
        record.calibration_curve.regression_b = b
        record.calibration_curve.correlation_r = r

        items = []

        # Verify extracted regression matches computed values
        if extracted_a is not None and extracted_b is not None:
            a_diff = abs(a - extracted_a)
            b_diff = abs(b - extracted_b)
            if a_diff > 0.001 or b_diff > 0.0005:
                items.append(self._fail(
                    name="回归方程校核",
                    actual=f"记录: y={extracted_b:.4f}x+{extracted_a:.4f}",
                    limit=f"计算: y={b:.4f}x+{a:.4f}", hj_ref="7.1",
                    detail="记录中的回归方程与根据校准点重新计算的结果不一致",
                    suggestion="请检查原始记录中回归方程的计算或誊写是否有误"))
            else:
                items.append(self._pass(
                    name="回归方程校核",
                    actual=f"记录 y={extracted_b:.4f}x+{extracted_a:.4f} = 计算值",
                    limit="记录与计算一致", hj_ref="7.1"))

        r_display = f"r={r:.5f}"
        if extracted_r is not None and abs(r - extracted_r) > 0.001:
            items.append(self._warning(
                name="相关系数校核",
                actual=f"记录 r={extracted_r}",
                limit=f"计算 r={r:.5f}", hj_ref="7.1",
                detail="记录的相关系数与重新计算结果有差异，可能是舍入误差"))

        if b <= 0:
            items.append(self._fail(name="校准曲线斜率", actual=f"b={b:.5f}",
                                    limit="b > 0", hj_ref="7.1",
                                    detail="斜率为负值，标准曲线异常",
                                    suggestion="请检查标准溶液配制和仪器状态"))
            return items

        if r >= MIN_CORRELATION_R:
            items.append(self._pass(name="相关系数", actual=r_display,
                              limit=f"r ≥ {MIN_CORRELATION_R}", hj_ref="7.1"))
        elif r >= 0.995:
            items.append(self._fail(name="相关系数", actual=r_display,
                              limit=f"r ≥ {MIN_CORRELATION_R}", hj_ref="7.1",
                              detail="相关系数低于0.999，线性不够理想",
                              suggestion="检查标准溶液稀释精度和比色皿清洁度"))
        else:
            items.append(self._fail(name="相关系数", actual=r_display,
                          limit=f"r ≥ {MIN_CORRELATION_R}", hj_ref="7.1",
                          detail="相关系数严重偏低，校准曲线不可用",
                          suggestion="应重新配制标准系列，检查仪器并重测"))
        return items


class RegressionInfoRule(BaseAuditRule):
    """B2b: 回归方程信息"""
    code = "B2"
    category = "校准曲线"

    def audit(self, record: AnalysisRecord) -> list:
        a = record.calibration_curve.regression_a
        b = record.calibration_curve.regression_b
        if a is None or b is None:
            return []

        slope_ok = 0.005 <= b <= 0.012
        if slope_ok:
            return [self._pass(name="回归方程", actual=f"y={b:.4f}x+{a:.4f}",
                              limit="y=bx+a, b≈0.007-0.009", hj_ref="7.1",
                              detail="回归方程正常")]
        return [self._warning(name="回归方程", actual=f"y={b:.4f}x+{a:.4f}",
                              limit="y=bx+a, b≈0.007-0.009", hj_ref="7.1",
                              detail="斜率偏离经验范围，可能存在标准溶液或仪器问题")]

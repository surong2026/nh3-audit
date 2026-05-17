from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from utils.regression import calc_concentration


class FormulaVerificationRule(BaseAuditRule):
    """H1: 结果计算验证 ρN = (As - Ab - a) / (b × V) × f"""
    code = "H1"
    category = "计算"

    def audit(self, record: AnalysisRecord) -> list:
        a = record.calibration_curve.regression_a
        b = record.calibration_curve.regression_b

        if a is None or b is None:
            return [self._warning(name="公式验证", actual="校准曲线未回归",
                                  limit="ρN=(As-Ab-a)/(b×V)×f", hj_ref="8",
                                  detail="需先完成校准曲线回归才能验证计算")]

        if not record.samples:
            return [self._info(name="公式验证", actual="无样品数据",
                               limit="ρN=(As-Ab-a)/(b×V)×f", hj_ref="8")]

        items = []
        for s in record.samples:
            if s.calculated_conc is None:
                continue

            expected = calc_concentration(s.absorbance, record.lab_blank_absorbance,
                                          a, b, s.sample_volume, s.dilution_factor)
            diff = abs(expected - s.calculated_conc)
            divisor = max(abs(expected), abs(s.calculated_conc), 0.001)

            if diff / divisor > 0.05:  # 5% tolerance
                items.append(self._fail(
                    name=f"样品 {s.sample_id} 计算",
                    actual=f"记录值={s.calculated_conc:.4f}",
                    limit=f"计算值={expected:.4f} mg/L", hj_ref="8",
                    detail=f"计算结果偏差 {(diff/divisor)*100:.1f}% > 5%",
                    suggestion="请核对原始记录中的计算过程"))
            elif diff / divisor > 0.01:
                items.append(self._warning(
                    name=f"样品 {s.sample_id} 计算",
                    actual=f"记录值={s.calculated_conc:.4f}",
                    limit=f"计算值={expected:.4f} mg/L", hj_ref="8",
                    detail=f"计算结果存在轻微偏差 {(diff/divisor)*100:.1f}%，可能是舍入误差"))

        if not items:
            items.append(self._pass(name="结果计算公式验证",
                                    actual="各样品计算值验证通过",
                                    limit="ρN=(As-Ab-a)/(b×V)×f", hj_ref="8"))
        return items

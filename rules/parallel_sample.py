from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from config import PARALLEL_RPD_LIMITS


class ParallelRPDRule(BaseAuditRule):
    """G1: 平行样相对偏差"""
    code = "G1"
    category = "平行样"

    def audit(self, record: AnalysisRecord) -> list:
        if not record.parallels:
            return [self._info(name="平行样", actual="未设置平行样",
                               limit="每批样品至少测定10%的平行双样", hj_ref="8",
                               detail="未记录平行样，无法评估精密度")]

        items = []
        for p in record.parallels:
            if p.value_a is None or p.value_b is None:
                items.append(self._warning(name=f"平行样 {p.original_id}/{p.parallel_id}",
                                           actual="值缺失",
                                           limit="RPD ≤ 各浓度段最大允许值", hj_ref="8"))
                continue

            avg = (p.value_a + p.value_b) / 2
            if avg == 0:
                rpd = 0.0
            else:
                rpd = abs(p.value_a - p.value_b) / avg * 100
            p.rpd = rpd

            limit = self._get_rpd_limit(avg)
            if rpd <= limit:
                items.append(self._pass(
                    name=f"平行样 {p.original_id}/{p.parallel_id} RPD",
                    actual=f"{rpd:.1f}% (avg={avg:.3f} mg/L)",
                    limit=f"≤ {limit:.0f}%", hj_ref="8"))
            else:
                items.append(self._fail(
                    name=f"平行样 {p.original_id}/{p.parallel_id} RPD",
                    actual=f"{rpd:.1f}% (avg={avg:.3f} mg/L)",
                    limit=f"≤ {limit:.0f}%", hj_ref="8",
                    detail=f"平行样相对偏差{rpd:.1f}%超出{limit:.0f}%",
                    suggestion="检查分析方法精密度，考虑重新测定"))
        return items

    @staticmethod
    def _get_rpd_limit(avg_conc: float) -> float:
        for (low, high), limit in PARALLEL_RPD_LIMITS.items():
            if low <= avg_conc < high:
                return limit
        return PARALLEL_RPD_LIMITS.get((2.0, float('inf')), 10.0)

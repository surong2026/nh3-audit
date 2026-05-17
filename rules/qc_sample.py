from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from config import QC_RECOVERY_RANGES, QC_DEFAULT_RANGE


class QCRecoveryRule(BaseAuditRule):
    """F1: 质控样回收率"""
    code = "F1"
    category = "质控样"

    def audit(self, record: AnalysisRecord) -> list:
        if not record.qc_standards:
            return [self._info(name="质控样", actual="未检测质控样",
                               limit="每批样品应至少做一个有证标准物质", hj_ref="9",
                               detail="未检测质控标准样品，无法评估准确度")]

        items = []
        for qc in record.qc_standards:
            if qc.measured_value is None:
                items.append(self._warning(name=f"质控样 {qc.qc_id}",
                                           actual="未填写测定值",
                                           limit=f"标准值 {qc.certified_value} mg/L", hj_ref="9",
                                           detail="质控样缺少测定值"))
                continue

            recovery = (qc.measured_value / qc.certified_value) * 100
            qc.recovery_rate = recovery

            rounded = round(qc.certified_value, 1)
            lower, upper = QC_RECOVERY_RANGES.get(qc.certified_value,
                                                  QC_RECOVERY_RANGES.get(rounded,
                                                                         QC_DEFAULT_RANGE))

            if lower <= recovery <= upper:
                items.append(self._pass(name=f"质控样 {qc.qc_id} 回收率",
                                        actual=f"{recovery:.1f}%",
                                        limit=f"{lower:.0f}%-{upper:.0f}%", hj_ref="9"))
            else:
                items.append(self._fail(name=f"质控样 {qc.qc_id} 回收率",
                                        actual=f"{recovery:.1f}%",
                                        limit=f"{lower:.0f}%-{upper:.0f}%", hj_ref="9",
                                        detail=f"质控样回收率{recovery:.1f}%超出{lower:.0f}%-{upper:.0f}%",
                                        suggestion="核查标准溶液、校准曲线和操作过程"))
        return items

from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from config import DETECTION_LIMIT, LOWER_QUANTITATION, UPPER_LIMIT_20MM, UPPER_LIMIT_10MM


class DetectionRangeRule(BaseAuditRule):
    """I1: 测定范围检查"""
    code = "I1"
    category = "测定范围"

    def audit(self, record: AnalysisRecord) -> list:
        upper = UPPER_LIMIT_20MM if record.cuvette_path == 20 else UPPER_LIMIT_10MM
        items = []

        for s in record.samples:
            if s.calculated_conc is None:
                continue
            conc = s.calculated_conc

            if conc < DETECTION_LIMIT and conc >= 0:
                items.append(self._info(
                    name=f"样品 {s.sample_id} < 检出限",
                    actual=f"{conc:.4f} mg/L",
                    limit=f"检出限 {DETECTION_LIMIT} mg/L", hj_ref="1",
                    detail="测定值低于方法检出限，结果应报'未检出'"))
            elif conc < 0:
                items.append(self._warning(
                    name=f"样品 {s.sample_id} 负值",
                    actual=f"{conc:.4f} mg/L",
                    limit="≥ 0", hj_ref="8",
                    detail="计算结果为负值",
                    suggestion="负值可能因空白吸光度偏高或校准曲线截距引起，结果应报ND"))
            elif conc < LOWER_QUANTITATION:
                items.append(self._warning(
                    name=f"样品 {s.sample_id} < 测定下限",
                    actual=f"{conc:.4f} mg/L",
                    limit=f"测定下限 {LOWER_QUANTITATION} mg/L", hj_ref="1",
                    detail="测定值低于测定下限，结果仅供参考",
                    suggestion="增大取样量或改用更低检出限的方法"))
            elif conc > upper:
                items.append(self._fail(
                    name=f"样品 {s.sample_id} > 测定上限",
                    actual=f"{conc:.4f} mg/L",
                    limit=f"≤ {upper} mg/L ({record.cuvette_path}mm比色皿)", hj_ref="1",
                    detail=f"浓度超过测定上限{upper}mg/L，超出校准曲线范围",
                    suggestion="应减少取样量或稀释后重新测定"))

        if not items:
            return [self._pass(name="样品浓度范围", actual="全部结果在测定范围内",
                               limit=f"{DETECTION_LIMIT}-{upper} mg/L", hj_ref="1")]
        # Add pass items for samples within range
        pass_count = sum(1 for s in record.samples if s.calculated_conc is not None
                         and LOWER_QUANTITATION <= s.calculated_conc <= upper)
        if pass_count > 0:
            items.insert(0, self._pass(name="样品浓度范围",
                                       actual=f"{pass_count}个样品在测定范围内",
                                       limit=f"{LOWER_QUANTITATION}-{upper} mg/L", hj_ref="1"))
        return items

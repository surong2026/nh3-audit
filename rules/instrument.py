from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from config import WAVELENGTH, VALID_CUVETTES, COLOR_DEV_TIME


class WavelengthRule(BaseAuditRule):
    """D1: 测定波长 420 nm"""
    code = "D1"
    category = "仪器条件"

    def audit(self, record: AnalysisRecord) -> list:
        wl = record.wavelength
        if wl == WAVELENGTH:
            return [self._pass(name="测定波长", actual=f"{wl} nm",
                              limit=f"{WAVELENGTH} nm", hj_ref="7.1")]
        return [self._fail(name="测定波长", actual=f"{wl} nm",
                          limit=f"{WAVELENGTH} nm", hj_ref="7.1",
                          detail="测定波长不为420nm，偏离纳氏试剂的吸收峰",
                          suggestion="应将分光光度计波长设置为420nm")]


class CuvetteRule(BaseAuditRule):
    """D2: 比色皿规格"""
    code = "D2"
    category = "仪器条件"

    def audit(self, record: AnalysisRecord) -> list:
        cp = record.cuvette_path
        if cp not in VALID_CUVETTES:
            return [self._fail(name="比色皿规格", actual=f"{cp} mm",
                              limit=f"{VALID_CUVETTES[0]}或{VALID_CUVETTES[1]} mm",
                              hj_ref="7.1", detail="比色皿规格不符合方法要求")]
        if cp == 20:
            return [self._pass(name="比色皿规格", actual=f"{cp} mm",
                              limit="20 mm (标准)", hj_ref="7.1")]
        return [self._warning(name="比色皿规格", actual=f"{cp} mm",
                              limit="20 mm (标准)", hj_ref="7.1",
                              detail="使用10mm比色皿，测定灵敏度降低，上限相应降低至1.0mg/L",
                              suggestion="低浓度样品建议改用20mm比色皿")]


class ColorDevTimeRule(BaseAuditRule):
    """D3: 显色时间 10 min"""
    code = "D3"
    category = "仪器条件"

    def audit(self, record: AnalysisRecord) -> list:
        ct = record.color_dev_time
        if ct == COLOR_DEV_TIME:
            return [self._pass(name="显色时间", actual=f"{ct} min",
                              limit=f"{COLOR_DEV_TIME} min", hj_ref="6.1")]
        if 8 <= ct <= 15:
            return [self._warning(name="显色时间", actual=f"{ct} min",
                                  limit=f"{COLOR_DEV_TIME} min", hj_ref="6.1",
                                  detail="显色时间偏离标准值，可能影响吸光度",
                                  suggestion="尽量控制在10min")]
        return [self._fail(name="显色时间", actual=f"{ct} min",
                          limit=f"{COLOR_DEV_TIME} min", hj_ref="6.1",
                          detail="显色时间偏差过大，显色反应不充分或可能褪色")]

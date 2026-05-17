from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from config import (BLANK_ABSORBANCE_10MM, BLANK_ABSORBANCE_20MM,
                    DETECTION_LIMIT, SAMPLE_VOLUME)
from utils.regression import calc_concentration


class BlankAbsorbanceRule(BaseAuditRule):
    """C1: 空白吸光度 ≤ 限值"""
    code = "C1"
    category = "空白检验"

    def audit(self, record: AnalysisRecord) -> list:
        ab = record.lab_blank_absorbance
        cp = record.cuvette_path
        if cp == 10:
            limit = BLANK_ABSORBANCE_10MM
        elif cp == 20:
            limit = BLANK_ABSORBANCE_20MM
        else:
            return [self._warning(name="空白吸光度", actual=f"{ab:.4f} ({cp}mm)",
                                  limit="未知比色皿规格", hj_ref="10.1",
                                  detail=f"无法确定{cp}mm比色皿的空白限值")]

        if ab <= limit:
            return [self._pass(name="空白吸光度", actual=f"{ab:.4f}",
                              limit=f"≤ {limit:.3f} ({cp}mm比色皿)", hj_ref="10.1")]
        return [self._fail(name="空白吸光度", actual=f"{ab:.4f}",
                          limit=f"≤ {limit:.3f} ({cp}mm比色皿)", hj_ref="10.1",
                          detail="空白吸光度超标，试剂或水中可能含氨",
                          suggestion="检查纳氏试剂、无氨水质量，必要时重新制备")]


class LabBlankRule(BaseAuditRule):
    """C2: 实验室空白 < 检出限"""
    code = "C2"
    category = "空白检验"

    def audit(self, record: AnalysisRecord) -> list:
        a = record.calibration_curve.regression_a
        b = record.calibration_curve.regression_b
        ab = record.lab_blank_absorbance

        if a is None or b is None:
            return [self._warning(name="实验室空白", actual="校准曲线未回归",
                                  limit=f"< {DETECTION_LIMIT} mg/L", hj_ref="7.3",
                                  detail="需先审核校准曲线后判断空白是否合格")]

        blank_conc = calc_concentration(ab, 0, a, b, SAMPLE_VOLUME)

        if blank_conc < DETECTION_LIMIT:
            return [self._pass(name="实验室空白", actual=f"{blank_conc:.4f} mg/L",
                              limit=f"< {DETECTION_LIMIT} mg/L", hj_ref="7.3")]
        return [self._fail(name="实验室空白", actual=f"{blank_conc:.4f} mg/L",
                          limit=f"< {DETECTION_LIMIT} mg/L", hj_ref="7.3",
                          detail="实验室空白浓度高于方法检出限",
                          suggestion="检查试剂纯度、无氨水质量，分析过程是否受污染")]


class FieldBlankRule(BaseAuditRule):
    """C3: 全程序空白 < 检出限"""
    code = "C3"
    category = "空白检验"

    def audit(self, record: AnalysisRecord) -> list:
        if record.field_blank_absorbance is None:
            return [self._info(name="全程序/现场空白", actual="未检测",
                               limit=f"< {DETECTION_LIMIT} mg/L", hj_ref="7.2",
                               detail="未填写全程序空白吸光度")]

        a = record.calibration_curve.regression_a
        b = record.calibration_curve.regression_b

        if a is None or b is None:
            return [self._warning(name="全程序空白", actual="校准曲线未回归",
                                  limit=f"< {DETECTION_LIMIT} mg/L", hj_ref="7.2")]

        blank_conc = calc_concentration(record.field_blank_absorbance, 0, a, b, SAMPLE_VOLUME)

        if blank_conc < DETECTION_LIMIT:
            return [self._pass(name="全程序空白", actual=f"{blank_conc:.4f} mg/L",
                              limit=f"< {DETECTION_LIMIT} mg/L", hj_ref="7.2")]
        return [self._fail(name="全程序空白", actual=f"{blank_conc:.4f} mg/L",
                          limit=f"< {DETECTION_LIMIT} mg/L", hj_ref="7.2",
                          detail="全程序空白浓度高于方法检出限，可能存在交叉污染",
                          suggestion="检查采样、运输和前处理过程中是否存在氨污染")]

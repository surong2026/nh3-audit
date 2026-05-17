from datetime import date
from models.record import AnalysisRecord
from rules.base import BaseAuditRule
from config import STOCK_CONCENTRATIONS, WORKING_CONCENTRATION, STOCK_EXPIRY_DAYS


class StockConcentrationRule(BaseAuditRule):
    """A1: 贮备液浓度应为500或1000 μg/mL"""
    code = "A1"
    category = "标准溶液"

    def audit(self, record: AnalysisRecord) -> list:
        ss = record.calibration_curve.standard_solution
        conc = ss.stock_concentration
        expected = " 或 ".join(f"{c} μg/mL" for c in STOCK_CONCENTRATIONS)
        if conc in STOCK_CONCENTRATIONS:
            return [self._pass(name="贮备液浓度", actual=f"{conc} μg/mL",
                              limit=expected, hj_ref="4.14.1")]
        return [self._fail(name="贮备液浓度", actual=f"{conc} μg/mL",
                           limit=expected, hj_ref="4.14.1",
                           detail="贮备液浓度不符合标准要求",
                           suggestion="应配制500或1000 μg/mL的NH3-N标准贮备液")]


class StockExpiryRule(BaseAuditRule):
    """A2: 贮备液有效期 ≤ 30天"""
    code = "A2"
    category = "标准溶液"

    def audit(self, record: AnalysisRecord) -> list:
        ss = record.calibration_curve.standard_solution
        if ss.stock_prep_date is None:
            return [self._warning(name="贮备液有效期", actual="未填写配制日期",
                                  limit=f"2-5℃保存≤{STOCK_EXPIRY_DAYS}天", hj_ref="4.14.1",
                                  detail="未记录贮备液配制日期，无法判断是否过期",
                                  suggestion="请填写标准贮备液配制日期")]
        analysis_date = record.analysis_date or date.today()
        age = (analysis_date - ss.stock_prep_date).days
        if age < 0:
            return [self._fail(name="贮备液有效期", actual=f"配制日期 {ss.stock_prep_date} > 检测日期 {analysis_date}",
                              limit=f"≤{STOCK_EXPIRY_DAYS}天", hj_ref="4.14.1",
                              detail="配制日期晚于检测日期，日期填写可能有误")]
        if age > STOCK_EXPIRY_DAYS:
            return [self._fail(name="贮备液有效期", actual=f"已{age}天",
                              limit=f"≤{STOCK_EXPIRY_DAYS}天 (2-5℃保存)", hj_ref="4.14.1",
                              detail="贮备液存放超过1个月可能已变质",
                              suggestion="应重新配制标准贮备液")]
        if age > STOCK_EXPIRY_DAYS - 5:
            return [self._warning(name="贮备液有效期", actual=f"已{age}天",
                                  limit=f"≤{STOCK_EXPIRY_DAYS}天", hj_ref="4.14.1",
                                  detail="贮备液接近有效期末，建议提前重新配制")]
        return [self._pass(name="贮备液有效期", actual=f"{age}天",
                          limit=f"≤{STOCK_EXPIRY_DAYS}天 (2-5℃保存)", hj_ref="4.14.1")]


class WorkingSolutionRule(BaseAuditRule):
    """A3: 标准使用液临用现配，浓度10 μg/mL"""
    code = "A3"
    category = "标准溶液"

    def audit(self, record: AnalysisRecord) -> list:
        ss = record.calibration_curve.standard_solution
        items = []

        if ss.working_concentration != WORKING_CONCENTRATION:
            items.append(self._fail(name="使用液浓度",
                                    actual=f"{ss.working_concentration} μg/mL",
                                    limit=f"{WORKING_CONCENTRATION} μg/mL",
                                    hj_ref="4.14.2",
                                    detail="标准使用液浓度应为10 μg/mL",
                                    suggestion="由标准贮备液稀释50倍(或100倍)至10 μg/mL"))

        if ss.working_prep_date is None:
            items.append(self._warning(name="使用液临用现配", actual="未填写配制日期",
                                       limit="配定日期应与检测日期相同", hj_ref="4.14.2",
                                       detail="标准使用液应临用现配",
                                       suggestion="请填写使用液配制日期"))
        elif record.analysis_date and ss.working_prep_date != record.analysis_date:
            items.append(self._warning(name="使用液临用现配",
                                       actual=f"配制 {ss.working_prep_date} ≠ 检测 {record.analysis_date}",
                                       limit="配制日期应与检测日期一致", hj_ref="4.14.2",
                                       detail="标准使用液应临用现配以保证浓度准确"))

        if not items:
            items.append(self._pass(name="使用液浓度与配制",
                                    actual="10 μg/mL, 临用现配",
                                    limit="10 μg/mL, 临用现配", hj_ref="4.14.2"))
        return items

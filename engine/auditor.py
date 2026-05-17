from datetime import datetime
from models.record import AnalysisRecord
from models.audit_result import AuditReport


class Auditor:
    """审核引擎 — 注册全部规则，对 AnalysisRecord 执行全量审核"""

    def __init__(self):
        self._rules = []
        self._register_all_rules()

    def _register_all_rules(self):
        from rules.standard_solution import StockConcentrationRule, StockExpiryRule, WorkingSolutionRule
        from rules.calibration_curve import CalibrationPointsRule, CorrelationCoefficientRule, RegressionInfoRule
        from rules.blank_check import BlankAbsorbanceRule, LabBlankRule, FieldBlankRule
        from rules.instrument import WavelengthRule, CuvetteRule, ColorDevTimeRule
        from rules.pretreatment import PretreatmentMethodRule, ReagentQualityRule
        from rules.qc_sample import QCRecoveryRule
        from rules.parallel_sample import ParallelRPDRule
        from rules.calculation import FormulaVerificationRule
        from rules.detection_limit import DetectionRangeRule

        self._rules = [
            StockConcentrationRule(),
            StockExpiryRule(),
            WorkingSolutionRule(),
            CalibrationPointsRule(),
            CorrelationCoefficientRule(),
            RegressionInfoRule(),
            BlankAbsorbanceRule(),
            LabBlankRule(),
            FieldBlankRule(),
            WavelengthRule(),
            CuvetteRule(),
            ColorDevTimeRule(),
            PretreatmentMethodRule(),
            ReagentQualityRule(),
            QCRecoveryRule(),
            ParallelRPDRule(),
            FormulaVerificationRule(),
            DetectionRangeRule(),
        ]

    @property
    def rule_codes(self) -> dict:
        """按类别分组的规则代号列表"""
        cats: dict = {}
        for r in self._rules:
            cats.setdefault(r.category, []).append(r.code)
        return cats

    def audit(self, record: AnalysisRecord) -> AuditReport:
        """执行全量审核"""
        report = AuditReport(
            record_id=record.record_id,
            audit_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        for rule in self._rules:
            try:
                items = rule.audit(record)
                report.items.extend(items)
            except Exception as e:
                from models.audit_result import AuditItem, AuditStatus
                report.items.append(AuditItem(
                    code=rule.code, category=rule.category,
                    name=f"审核异常: {type(e).__name__}",
                    status=AuditStatus.WARNING,
                    detail=str(e), suggestion="请联系系统管理员"))
        return report

    def audit_category(self, record: AnalysisRecord, category: str) -> list:
        """按类别执行审核"""
        items = []
        for rule in self._rules:
            if rule.category == category:
                items.extend(rule.audit(record))
        return items

    def audit_code(self, record: AnalysisRecord, code: str) -> list:
        """按代号执行审核"""
        for rule in self._rules:
            if rule.code == code:
                return rule.audit(record)
        return []

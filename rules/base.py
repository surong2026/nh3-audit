from abc import ABC, abstractmethod
from models.record import AnalysisRecord
from models.audit_result import AuditItem


class BaseAuditRule(ABC):

    @property
    @abstractmethod
    def code(self) -> str: ...

    @property
    @abstractmethod
    def category(self) -> str: ...

    @abstractmethod
    def audit(self, record: AnalysisRecord) -> list:
        """返回 List[AuditItem]"""
        ...

    def _pass(self, name: str, actual: str = "", limit: str = "",
              hj_ref: str = "", detail: str = "") -> AuditItem:
        from models.audit_result import AuditStatus
        return AuditItem(code=self.code, category=self.category, name=name,
                         status=AuditStatus.PASS, actual_value=actual,
                         limit_value=limit, hj_ref=hj_ref, detail=detail)

    def _fail(self, name: str, actual: str = "", limit: str = "",
              hj_ref: str = "", detail: str = "", suggestion: str = "") -> AuditItem:
        from models.audit_result import AuditStatus
        return AuditItem(code=self.code, category=self.category, name=name,
                         status=AuditStatus.FAIL, actual_value=actual,
                         limit_value=limit, hj_ref=hj_ref, detail=detail,
                         suggestion=suggestion)

    def _warning(self, name: str, actual: str = "", limit: str = "",
                 hj_ref: str = "", detail: str = "", suggestion: str = "") -> AuditItem:
        from models.audit_result import AuditStatus
        return AuditItem(code=self.code, category=self.category, name=name,
                         status=AuditStatus.WARNING, actual_value=actual,
                         limit_value=limit, hj_ref=hj_ref, detail=detail,
                         suggestion=suggestion)

    def _info(self, name: str, actual: str = "", limit: str = "",
              hj_ref: str = "", detail: str = "") -> AuditItem:
        from models.audit_result import AuditStatus
        return AuditItem(code=self.code, category=self.category, name=name,
                         status=AuditStatus.INFO, actual_value=actual,
                         limit_value=limit, hj_ref=hj_ref, detail=detail)

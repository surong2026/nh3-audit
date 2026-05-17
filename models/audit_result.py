from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AuditStatus(Enum):
    PASS = "合格"
    FAIL = "不合格"
    WARNING = "警告"
    INFO = "提示"


@dataclass
class AuditItem:
    code: str
    category: str
    name: str
    status: AuditStatus
    actual_value: Optional[str] = None
    limit_value: str = ""
    hj_ref: str = ""
    detail: str = ""
    suggestion: str = ""


@dataclass
class AuditReport:
    record_id: str = ""
    audit_time: str = ""
    items: list = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for i in self.items if i.status == AuditStatus.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.items if i.status == AuditStatus.FAIL)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.items if i.status == AuditStatus.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.items if i.status == AuditStatus.INFO)

    @property
    def total_count(self) -> int:
        return len(self.items)

    @property
    def overall_pass(self) -> bool:
        return self.fail_count == 0

    @property
    def overall_verdict(self) -> str:
        if self.fail_count == 0 and self.warning_count == 0:
            return "合格 — 所有项目均符合 HJ 535-2009 要求"
        elif self.fail_count == 0:
            return f"有条件通过 — 存在 {self.warning_count} 项警告，无不合格项"
        else:
            return f"不合格 — 存在 {self.fail_count} 项不合格，需整改后重新审核"

from models.record import AnalysisRecord
from rules.base import BaseAuditRule


class PretreatmentMethodRule(BaseAuditRule):
    """E1: 前处理方法"""
    code = "E1"
    category = "前处理"

    def audit(self, record: AnalysisRecord) -> list:
        method = record.pretreatment_method.strip().lower()
        details = record.pretreatment_details.strip()
        items = []

        if not method:
            return [self._warning(name="前处理方法", actual="未记录",
                                 limit="絮凝沉淀法 / 预蒸馏法", hj_ref="6.2",
                                 detail="未记录前处理方法，无法审核",
                                 suggestion="请填写前处理方法")]
        is_flocculation = "flocculation" in method or "絮凝" in method or "絮凝沉淀" in record.pretreatment_method
        is_distillation = "pre-distillation" in method or "蒸馏" in method or "预蒸馏" in record.pretreatment_method or "预处理-蒸馏" in record.pretreatment_method

        if not is_flocculation and not is_distillation:
            return [self._warning(name="前处理方法", actual=record.pretreatment_method,
                                 limit="絮凝沉淀法 / 预蒸馏法", hj_ref="6.2",
                                 detail="前处理方法未识别为絮凝沉淀或预蒸馏")]
        if is_flocculation:
            items.extend(self._check_flocculation(details))
        elif is_distillation:
            items.extend(self._check_distillation(details))

        if not items:
            items.append(self._pass(name="前处理方法", actual=record.pretreatment_method,
                                    limit="絮凝沉淀法 / 预蒸馏法", hj_ref="6.2"))
        return items

    def _check_flocculation(self, details: str) -> list:
        items = []
        if "硫酸锌" not in details and "ZnSO4" not in details:
            items.append(self._warning(name="前处理试剂",
                                       actual="未提及硫酸锌",
                                       limit="需加入硫酸锌溶液(100g/L)", hj_ref="6.2.2",
                                       suggestion="絮凝沉淀法需使用硫酸锌溶液"))
        if "氢氧化钠" not in details and "NaOH" not in details:
            items.append(self._warning(name="前处理试剂",
                                       actual="未提及氢氧化钠",
                                       limit="需加入氢氧化钠溶液(250g/L)", hj_ref="6.2.2",
                                       suggestion="絮凝沉淀法需使用氢氧化钠溶液调节pH"))
        if "10.5" not in details and "pH" not in details:
            items.append(self._warning(name="絮凝pH条件",
                                       actual="未记录pH值",
                                       limit="pH ≈ 10.5", hj_ref="6.2.2",
                                       suggestion="应记录絮凝沉淀后的pH值"))
        return items

    def _check_distillation(self, details: str) -> list:
        items = []
        if "氧化镁" not in details and "MgO" not in details:
            items.append(self._warning(name="蒸馏试剂",
                                       actual="未提及氧化镁",
                                       limit="需加轻质氧化镁(0.25g/50mL)", hj_ref="6.2.3",
                                       suggestion="预蒸馏法需要加入轻质氧化镁"))
        if "硼酸" not in details:
            items.append(self._warning(name="吸收液",
                                       actual="未提及硼酸",
                                       limit="硼酸溶液(20g/L)吸收", hj_ref="6.2.3",
                                       suggestion="预蒸馏法需使用硼酸溶液作为吸收液"))
        if "200" not in details or "mL" not in details:
            items.append(self._warning(name="馏出液体积",
                                       actual="未明确记录馏出液体积",
                                       limit="约200 mL", hj_ref="6.2.3",
                                       suggestion="应记录馏出液收集量(约200mL)"))
        return items


class ReagentQualityRule(BaseAuditRule):
    """E2: 试剂质量"""
    code = "E2"
    category = "前处理"

    def audit(self, record: AnalysisRecord) -> list:
        items = []
        if not record.nessler_method:
            items.append(self._info(name="纳氏试剂配制方法", actual="未记录",
                                    limit="HgCl2-KI-KOH 或 HgI2-KI-NaOH", hj_ref="4.13"))
        else:
            items.append(self._pass(name="纳氏试剂配制方法",
                                    actual=record.nessler_method,
                                    limit="HgCl2-KI-KOH 或 HgI2-KI-NaOH", hj_ref="4.13"))

        if record.tartrate_boiled:
            items.append(self._pass(name="酒石酸钾钠除氨处理", actual="已煮沸除氨",
                                    limit="需煮沸以除去试剂中的氨", hj_ref="4.16"))
        else:
            items.append(self._warning(name="酒石酸钾钠除氨处理", actual="未确认",
                                       limit="需煮沸以除去试剂中的氨", hj_ref="4.16",
                                       suggestion="酒石酸钾钠溶液应加热煮沸以除去氨"))

        if record.ammonia_free_water:
            items.append(self._pass(name="无氨水使用", actual="使用无氨水",
                                    limit="应使用无氨水", hj_ref="4.1"))
        else:
            items.append(self._fail(name="无氨水使用", actual="未使用无氨水",
                                    limit="应使用无氨水或新制备的去离子水", hj_ref="4.1",
                                    detail="普通纯水中可能含氨，干扰测定",
                                    suggestion="须使用无氨水配制试剂和稀释样品"))
        return items

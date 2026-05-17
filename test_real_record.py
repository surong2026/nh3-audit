"""
使用实际分析记录数据（苏毅/卢露, 2026-05-08）测试审核引擎
数据来源: 分析记录-氨氮.pdf
"""
import json
from datetime import date
from models.record import (
    AnalysisRecord, CalibrationCurve, StandardSolution, CalibrationPoint,
    SampleResult, QCStandard, ParallelSample,
)
from engine.auditor import Auditor


def build_real_record() -> AnalysisRecord:
    """根据实际PDF记录构建 AnalysisRecord"""
    record = AnalysisRecord(
        analyst="苏毅",
        analysis_date=date(2026, 5, 8),
        instrument_model="可见分光光度计/V-5600PC",
        instrument_id="00218",
        method_reference="HJ 535-2009",
        temperature=25.0,
        humidity=58.0,
        experiment_water_batch="超纯水-20260507",
        wavelength=420,
        cuvette_path=20,
        color_dev_time=10,
        reference_solution="水",
        nessler_method="HgCl2-KI-KOH",
        tartrate_boiled=True,
        ammonia_free_water=True,
        lab_blank_absorbance=0.029,
        field_blank_absorbance=None,
        pretreatment_method="絮凝沉淀法",
        pretreatment_details="取100mL水样，加入1mL硫酸锌溶液(100g/L)和NaOH溶液(250g/L)，调节pH约10.5，静置沉降后取上清液",
        pretreatment_date=date(2026, 5, 8),
        record_id="20260508-氨氮",
    )

    # 标准溶液
    ss = StandardSolution(
        stock_concentration=500.0,
        stock_id="YLB20260306",
        stock_prep_date=date(2026, 4, 22),
        stock_expiry_date=date(2026, 5, 22),
        working_concentration=10.0,
        working_prep_date=date(2026, 5, 8),
    )

    # 校准曲线点 (来自PDF: 吸光度 [0.029, 0.077, 0.104, 0.173, 0.315, 0.456, 0.605, 0.749])
    masses = [0, 5, 10, 20, 40, 60, 80, 100]   # μg
    volumes = [0, 0.50, 1.00, 2.00, 4.00, 6.00, 8.00, 10.00]  # mL
    absorbances = [0.029, 0.077, 0.104, 0.173, 0.315, 0.456, 0.605, 0.749]
    a_minus_a0 = [0.000, 0.048, 0.075, 0.144, 0.286, 0.427, 0.576, 0.720]

    points = []
    for i, (mass, vol, abs_val, diff) in enumerate(zip(masses, volumes, absorbances, a_minus_a0)):
        points.append(CalibrationPoint(
            point_id=i, nh3_mass=mass, volume_taken=vol,
            working_conc=10.0, absorbance=abs_val, a_minus_a0=diff,
        ))

    cc = CalibrationCurve(
        standard_solution=ss,
        points=points,
        total_volume=50.0,
        regression_a=0.0035,
        regression_b=0.0071,
        correlation_r=0.9998,
    )
    record.calibration_curve = cc

    # 样品结果 (来自PDF第5-6页)
    sample_data = [
        # (编号, 吸光度, 稀释, 体积, 浓度)
        ("实验室空白", "", 0.029, 1.0, 50.0, 0.025),
        ("YLS260500014", "苏烟水库-中上", 0.293, 1.0, 50.0, 0.819),
        ("YLS260500037", "郁江引水工程-右上", 0.067, 1.0, 50.0, 0.179),
        ("YLS260500108", "郁江引水工程-右上-基体加标", 0.412, 1.0, 50.0, 1.144),
        ("YLB20260392", "密码标样B23190427(1.21mg/L)", 0.370, 1.0, 50.0, 1.034),
    ]

    samples = []
    for sid, sname, abs_val, dil, vol, conc in sample_data:
        samples.append(SampleResult(
            sample_id=sid, sample_name=sname, absorbance=abs_val,
            dilution_factor=dil, sample_volume=vol, calculated_conc=conc,
        ))

    # More samples from the record
    more_samples = [
        ("YLS260500054", "罗田水库-中上", 0.024, 1.0, 50.0, 0.066),
        ("YLS260500054-P", "罗田水库-中上-实验室平行", 0.023, 1.0, 50.0, 0.063),
        ("YLS260500061", "江口水库-中上", 0.040, 1.0, 50.0, 0.112),
        ("YLS260500085", "大容山水库-中上", 0.021, 1.0, 50.0, 0.057),
    ]
    for sid, sname, abs_val, dil, vol, conc in more_samples:
        samples.append(SampleResult(
            sample_id=sid, sample_name=sname, absorbance=abs_val,
            dilution_factor=dil, sample_volume=vol, calculated_conc=conc,
        ))
    record.samples = samples

    # 质控样
    record.qc_standards = [
        QCStandard(qc_id="B23190427", certified_value=1.21,
                    measured_value=1.034, recovery_rate=85.45),
    ]

    # 平行样
    record.parallels = [
        ParallelSample(
            original_id="YLS260500054",
            parallel_id="YLS260500054-P",
            value_a=0.066, value_b=0.063, rpd=None,
        ),
    ]

    return record


def main():
    record = build_real_record()
    auditor = Auditor()
    report = auditor.audit(record)

    print("=" * 70)
    print("  氨氮分析记录审核报告 — 苏毅 2026-05-08")
    print("=" * 70)
    print(f"审核时间: {report.audit_time}")
    print(f"总计: {report.total_count} 项")
    print(f"  ✅ 合格:   {report.pass_count}")
    print(f"  ❌ 不合格: {report.fail_count}")
    print(f"  ⚠️  警告:   {report.warning_count}")
    print(f"  ℹ️  提示:   {report.info_count}")
    print(f"\n总体结论: {report.overall_verdict}")
    print("=" * 70)

    for item in report.items:
        icon = {"合格": "✅", "不合格": "❌", "警告": "⚠️", "提示": "ℹ️"}.get(item.status.value, "?")
        print(f"\n{icon} [{item.code}] {item.name}")
        if item.actual_value:
            print(f"     实际值: {item.actual_value}")
        if item.limit_value:
            print(f"     标准要求: {item.limit_value}")
        if item.detail:
            print(f"     详情: {item.detail}")
        if item.suggestion:
            print(f"     建议: {item.suggestion}")
        print(f"     HJ 535-2009 {item.hj_ref}")

    # Save report
    report_json = {
        "items": [{
            "code": i.code, "category": i.category,
            "name": i.name, "status": i.status.value,
            "actual_value": i.actual_value,
            "limit_value": i.limit_value,
            "hj_ref": i.hj_ref, "detail": i.detail,
            "suggestion": i.suggestion,
        } for i in report.items],
        "summary": {
            "pass": report.pass_count,
            "fail": report.fail_count,
            "warning": report.warning_count,
            "info": report.info_count,
            "overall_pass": report.overall_pass,
            "verdict": report.overall_verdict,
        }
    }
    path = "/home/sr200/workspace/nh3_audit/data/saved_records/test_report.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存至: {path}")

    # Also save the full record
    rec_path = "/home/sr200/workspace/nh3_audit/data/saved_records/test_record.json"
    with open(rec_path, "w", encoding="utf-8") as f:
        json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"记录已保存至: {rec_path}")


if __name__ == "__main__":
    main()

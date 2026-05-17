"""
PDF 分析记录解析器 — 从 HJ 535-2009 氨氮分析记录 PDF 提取结构化数据
"""
import re
from datetime import date
from models.record import (
    AnalysisRecord, CalibrationCurve, StandardSolution, CalibrationPoint,
    SampleResult, QCStandard, ParallelSample,
)


def parse_pdf(file_bytes: bytes, filename: str) -> AnalysisRecord:
    import pymupdf
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    full_text = ""
    page_texts = []
    for i in range(len(doc)):
        t = doc[i].get_text()
        page_texts.append(t)
        full_text += t + "\n"
    doc.close()

    record = AnalysisRecord(record_id=filename.rsplit(".", 1)[0])
    _parse_basic_info(record, page_texts, full_text)
    _parse_standard_solution(record, page_texts, full_text)
    _parse_pretreatment(record, page_texts, full_text)
    _parse_calibration_table(record, page_texts, full_text)
    _parse_sample_results(record, page_texts, full_text)
    return record


def _parse_basic_info(record, pages, text):
    m = re.search(r'配制日期[：:]\s*(\d{4}-\d{2}-\d{2})', text)
    if m:
        record.analysis_date = date.fromisoformat(m.group(1))

    m = re.search(r'实验用水批号[：:]\s*(.+?)(?:\n|$)', text)
    if m and m.group(1).strip() not in ("/", ""):
        record.experiment_water_batch = m.group(1).strip()

    m = re.search(r'室温[：:]\s*([\d.]+)\s*℃', text)
    if m:
        record.temperature = float(m.group(1))

    m = re.search(r'相对湿度[：:]\s*(\d+)%', text)
    if m:
        record.humidity = float(m.group(1))

    m = re.search(r'仪器名称及型号[：:]\s*(.+?)(?:\n|$)', text)
    if m:
        record.instrument_model = m.group(1).strip()

    m = re.search(r'仪器编号[：:]\s*(\S+)', text)
    if m:
        record.instrument_id = m.group(1).strip()

    m = re.search(r'测定波长[：:]\s*(\d+)', text)
    if m:
        record.wavelength = int(m.group(1))

    m = re.search(r'比色皿厚度[：:]\s*([\d.]+)\s*cm', text)
    if m:
        record.cuvette_path = int(float(m.group(1)) * 10)

    m = re.search(r'显色时间[：:]\s*(\d+)', text)
    if m:
        record.color_dev_time = int(m.group(1))

    m = re.search(r'参比溶液[：:]\s*(.+?)(?:\n|$)', text)
    if m:
        record.reference_solution = m.group(1).strip()

    if "无氨水" in text:
        record.ammonia_free_water = True

    m = re.search(r'方法检出限[：:]\s*([\d.]+)', text)
    if m:
        record.notes += f"检出限={m.group(1)}mg/L; "

    m = re.search(r'分析人[：:]\s*(\S+)', text)
    if m:
        record.analyst = m.group(1).strip()


def _parse_standard_solution(record, pages, text):
    ss = StandardSolution()

    m = re.search(r'标准溶液浓度[：:]\s*(\d+)', text)
    if m:
        ss.stock_concentration = float(m.group(1))

    m = re.search(r'标准溶液编号[：:]\s*(\S+)', text)
    if m:
        ss.stock_id = m.group(1).strip()

    m = re.search(r'有效期至[：:]\s*(\d{4}-\d{2}-\d{2})', text)
    if m:
        ss.stock_expiry_date = date.fromisoformat(m.group(1))

    stock_info = re.search(
        r'标准溶液名称[：:]\s*(氨氮标准溶液|铵标准|NH3).*?'
        r'浓度[：:]\s*(\d+)',
        text, re.DOTALL
    )
    if stock_info and not ss.stock_concentration:
        ss.stock_concentration = float(stock_info.group(2))

    m = re.search(r'标准溶液使用配制日期[：:]\s*(\d{4}-\d{2}-\d{2})', text)
    if m:
        ss.working_prep_date = date.fromisoformat(m.group(1))

    m = re.search(r'标准使用液浓度[：:]\s*([\d.]+)', text)
    if m:
        ss.working_concentration = float(m.group(1))

    record.calibration_curve.standard_solution = ss


def _parse_calibration_table(record, pages, text):
    """解析分光光度法分析原始记录表中的校准曲线数据"""
    # 查找包含校准曲线数据的页面
    cal_page = ""
    for page in pages:
        if ('吸光度读数(A)' in page or '吸光度(A)' in page) and '回归方程' in page:
            cal_page = page
            break

    if not cal_page:
        return

    # 提取吸光度值 - 在 "吸光度读数(A)" 和 "A0-A" 之间
    abs_section = cal_page.split('吸光度读数(A)')[-1]
    abs_section = abs_section.split('□A0-A')[0].split('☑A-A0')[0]
    abs_vals = [float(x) for x in re.findall(r'\d+\.\d+', abs_section)]

    # 提取A-A0值 - 在 "A-A0" 标记之后
    aa0_pattern = r'[☑□]A-A0[^0-9]*([\d.\s/]{8,})'
    m = re.search(aa0_pattern, cal_page)
    aa0_vals = []
    if m:
        aa0_vals = [float(x) for x in re.findall(r'\d+\.\d+', m.group(1))]

    # 提取体积
    vol_section = cal_page.split('体积(mL)')[1].split('□浓度')[0]
    vol_lines = [l.strip() for l in vol_section.strip().split('\n') if l.strip()]
    vol_vals = []
    for v in vol_lines:
        try:
            vol_vals.append(float(v))
        except ValueError:
            if len(vol_vals) >= 8:
                break

    # 提取含量(μg)
    mass_section = cal_page.split('含量(μg)')[1].split('吸光度')[0]
    mass_lines = [l.strip() for l in mass_section.strip().split('\n') if l.strip()]
    mass_vals = []
    for v in mass_lines:
        try:
            mass_vals.append(float(v))
        except ValueError:
            if len(mass_vals) >= 8:
                break

    # 提取回归方程
    m = re.search(r'回归方程[：:]\s*y\s*=\s*([\d.]+)\s*x\s*\+?\s*([\d.\-]+)', cal_page)
    if m:
        record.calibration_curve.regression_b = float(m.group(1))
        record.calibration_curve.regression_a = float(m.group(2))

    m = re.search(r'相关系数[：:]\s*r\s*=\s*([\d.]+)', cal_page)
    if m:
        record.calibration_curve.correlation_r = float(m.group(1))

    n = min(len(abs_vals), 8)
    for i in range(n):
        mass = mass_vals[i] if i < len(mass_vals) else 0.0
        vol = vol_vals[i] if i < len(vol_vals) else 0.0
        aa0 = aa0_vals[i] if i < len(aa0_vals) else (abs_vals[i] - abs_vals[0] if i > 0 else 0.0)
        record.calibration_curve.points.append(CalibrationPoint(
            point_id=i, nh3_mass=mass, volume_taken=vol,
            working_conc=record.calibration_curve.standard_solution.working_concentration or 10.0,
            absorbance=abs_vals[i], a_minus_a0=aa0,
        ))

    if abs_vals and abs_vals[0] > 0:
        record.lab_blank_absorbance = abs_vals[0]

    # 校准曲线编号
    m = re.search(r'校准曲线编号[：:]\s*(.+)', cal_page)
    if m:
        record.notes += f"曲线={m.group(1).strip()}; "


def _parse_pretreatment(record, pages, text):
    method = ""
    if "絮凝" in text or "硫酸锌" in text:
        method = "絮凝沉淀法"
    elif "蒸馏" in text or "氧化镁" in text:
        method = "预蒸馏法"
    record.pretreatment_method = method

    m = re.search(r'前处理步骤[：:]\s*(.+?)(?=分析人|校核人|审核人|\Z)', text, re.DOTALL)
    if m:
        detail = m.group(1).strip()
        detail = re.sub(r'\s+', ' ', detail)
        record.pretreatment_details = detail[:500]

    m = re.search(r'处理日期[：:]\s*(\d{4})年(\d{2})月(\d{2})日', text)
    if m:
        record.pretreatment_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    if "HgI" in text or "碘化汞" in text:
        record.nessler_method = "HgI2-KI-NaOH"
    elif "HgCl" in text or "氯化汞" in text:
        record.nessler_method = "HgCl2-KI-KOH"

    if "酒石酸钾钠" in text:
        record.tartrate_boiled = True


def _parse_sample_results(record, pages, text):
    """解析样品结果表（第5-6页）"""
    samples = []
    seen_ids = set()
    seen_names = set()

    for page in pages:
        if '分光光度法分析原始记录表（水样' not in page:
            continue
        _extract_samples_from_page(page, samples, seen_ids, seen_names)

    record.samples = _deduplicate_samples(samples)
    _identify_qc_and_parallels(record)


def _extract_samples_from_page(page_text, samples, seen_ids, seen_names):
    """从单页提取样品数据 — 表格是列式布局，序号作为行分隔符"""
    lines = page_text.split('\n')

    # 找到样本数据起始：在表头之后，每个样本从序号数字开始
    # 收集非空行，跳过纯表头行
    data_lines = []
    in_header = True
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if '分析人' in s:
            break
        if in_header:
            # 表头区域：从 "序号" 到 "mg/L" 等
            if 'mg/L' in s:
                in_header = False
            continue
        data_lines.append(s)

    # 将数据行按序号分组
    # 每个样本以单数字开头（序号），后面跟着该样本的各个字段
    rows = []
    current_row = []
    for s in data_lines:
        if s.isdigit() and len(s) <= 2:
            if current_row:
                rows.append(current_row)
            current_row = []
            continue
        current_row.append(s)

    if current_row:
        rows.append(current_row)

    # 每个样本的字段顺序: 样品编号, 样品名称(maybe multi-line), 稀释, 体积, 吸光度, 补偿, A-A0, 含量, 结果, 备注
    for fields in rows:
        if len(fields) < 6:
            continue

        idx = 0
        # 样品编号
        sid = fields[idx]
        idx += 1

        # 样品名称 (可能跨多行)
        name_parts = []
        while idx < len(fields):
            f = fields[idx]
            try:
                float(f)
                # It's a number, stop collecting name
                break
            except ValueError:
                if f == '/':
                    break
                name_parts.append(f)
                idx += 1

        sname = _join_name(name_parts)
        if not sname:
            idx += 1  # skip '/' for name
            # try collecting name after the slash
            name_parts = []
            while idx < len(fields):
                f = fields[idx]
                try:
                    float(f)
                    break
                except ValueError:
                    if f == '/':
                        idx += 1
                        break
                    name_parts.append(f)
                    idx += 1
            sname = _join_name(name_parts)

        if not sname:
            continue

        # 稀释倍数
        dil = 1.0
        if idx < len(fields) and fields[idx] != '/':
            try:
                dil = float(fields[idx])
            except ValueError:
                pass
        idx += 1

        # 试样体积
        vol = 50.0
        if idx < len(fields):
            try:
                vol = float(fields[idx])
            except ValueError:
                pass
            idx += 1

        # 吸光度A
        abs_val = None
        if idx < len(fields):
            try:
                abs_val = float(fields[idx])
            except ValueError:
                pass
            idx += 1

        # 浊度补偿 (/ 或数字)
        if idx < len(fields) and fields[idx] == '/':
            idx += 1

        # A-A0
        if idx < len(fields):
            try:
                float(fields[idx])
                idx += 1
            except ValueError:
                pass

        # 样品含量(μg)
        if idx < len(fields):
            try:
                float(fields[idx])
                idx += 1
            except ValueError:
                pass

        # 样品结果(mg/L)
        conc_val = None
        if idx < len(fields):
            raw = fields[idx]
            if raw.upper().endswith('L'):
                try:
                    conc_val = float(raw.upper().replace('L', ''))
                except ValueError:
                    conc_val = 0.0
            else:
                try:
                    conc_val = float(raw)
                except ValueError:
                    pass

        if sid and abs_val is not None:
            if '空白' in sname and sid == '/':
                sid = sname

            key = sid + '|' + sname
            if key in seen_names:
                continue
            seen_names.add(key)
            seen_ids.add(sid)

            samples.append(SampleResult(
                sample_id=sid,
                sample_name=sname,
                absorbance=abs_val,
                dilution_factor=dil,
                sample_volume=vol,
                calculated_conc=conc_val,
            ))


def _deduplicate_samples(samples):
    """去重并排序"""
    seen = set()
    unique = []
    for s in samples:
        key = (s.sample_id, s.sample_name)
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def _join_name(parts):
    """智能合并被 PDF 换行拆分的样品名称"""
    if not parts:
        return ""
    result = parts[0]
    for p in parts[1:]:
        # If previous fragment ends with CJK char and next starts with CJK char,
        # OR next fragment is short (1-2 chars) continuation — join without space.
        prev_cjk = result and '一' <= result[-1] <= '鿿'
        curr_cjk = p and '一' <= p[0] <= '鿿'
        if prev_cjk and curr_cjk:
            result += p
        elif len(p) <= 2 and prev_cjk:
            result += p
        else:
            result += ' ' + p
    return result.strip()


def _identify_qc_and_parallels(record):
    """识别质控样、全程序空白和平行样"""
    for s in record.samples:
        name = s.sample_name

        # 全程序空白 / 现场空白
        if '全程序空白' in name or '现场空白' in name:
            record.field_blank_absorbance = s.absorbance

        # 质控样
        if any(kw in name for kw in ('质量控制', '密码标样', '明码标样')):
            certified = 0.0
            if s.calculated_conc and s.calculated_conc > 0:
                conc = s.calculated_conc
                for std in (1.21, 1.47, 0.501, 2.50):
                    if abs(conc - std) / std < 0.15:
                        certified = std
                        break
                if not certified:
                    certified = round(conc, 2)

            record.qc_standards.append(QCStandard(
                qc_id=s.sample_id, certified_value=certified,
                measured_value=s.calculated_conc,
            ))

        # 平行样 — normalize name (remove spaces from split CJK) for matching
        name_normalized = name.replace(' ', '')

        if '平行' in name_normalized and '现场' not in name_normalized and '密码' not in name_normalized:
            base = name_normalized.replace('-实验室平行', '').replace('-现场平行', '').strip()
            for orig in record.samples:
                orig_normalized = orig.sample_name.replace(' ', '')
                if '平行' in orig_normalized:
                    continue
                if (base in orig_normalized or orig_normalized in base
                    or orig.sample_id == s.sample_id.replace('-P', '')):
                    if orig.calculated_conc is not None and s.calculated_conc is not None:
                        record.parallels.append(ParallelSample(
                            original_id=orig.sample_id,
                            parallel_id=s.sample_id,
                            value_a=orig.calculated_conc,
                            value_b=s.calculated_conc,
                        ))
                        break

    # 现场平行配对
    for s in record.samples:
        name_normalized = s.sample_name.replace(' ', '')
        if '现场平行' in name_normalized:
            base = name_normalized.replace('-现场平行', '').strip()
            for orig in record.samples:
                orig_normalized = orig.sample_name.replace(' ', '')
                if orig.sample_id != s.sample_id and '平行' not in orig_normalized:
                    if base in orig_normalized or orig_normalized in base:
                        already = any(p.original_id == orig.sample_id
                                      for p in record.parallels)
                        if not already and orig.calculated_conc is not None:
                            record.parallels.append(ParallelSample(
                                original_id=orig.sample_id,
                                parallel_id=s.sample_id,
                                value_a=orig.calculated_conc,
                                value_b=s.calculated_conc or 0,
                            ))
                        break

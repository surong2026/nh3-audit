# HJ 535-2009 纳氏试剂分光光度法 — 审核参数配置

# 标准溶液 (4.14)
STOCK_CONCENTRATIONS = (500.0, 1000.0)  # 贮备液浓度 μg/mL
WORKING_CONCENTRATION = 10.0            # 使用液浓度 μg/mL
STOCK_EXPIRY_DAYS = 30                   # 贮备液有效期（2-5℃）
WORKING_FRESH_REQUIRED = True            # 使用液需临用现配

# 校准曲线 (7.1)
CALIBRATION_POINTS = [0.0, 5.0, 10.0, 20.0, 40.0, 60.0, 80.0, 100.0]  # NH3-N μg
CALIBRATION_TOTAL_VOLUME = 50.0          # 定容体积 mL
MIN_CORRELATION_R = 0.999                # 最小相关系数

# 空白吸光度 (10.1)
BLANK_ABSORBANCE_10MM = 0.030            # 10mm比色皿空白限值
BLANK_ABSORBANCE_20MM = 0.060            # 20mm比色皿空白限值(近似)

# 仪器条件 (7.1)
WAVELENGTH = 420                         # 波长 nm
VALID_CUVETTES = (10, 20)                # 有效比色皿规格 mm
COLOR_DEV_TIME = 10                      # 显色时间 min
SAMPLE_VOLUME = 50.0                     # 取样体积 mL

# 检出限与测定范围 (1, 3)
DETECTION_LIMIT = 0.025                  # mg/L
LOWER_QUANTITATION = 0.10                # 测定下限 mg/L
UPPER_LIMIT_20MM = 2.0                   # 20mm测定上限 mg/L
UPPER_LIMIT_10MM = 1.0                   # 10mm测定上限 mg/L

# 质控样回收率 (表1)
QC_RECOVERY_RANGES = {
    # 标准值 → (下限%, 上限%)
    1.21: (94.0, 104.0),
    1.47: (95.0, 105.0),
}
QC_DEFAULT_RANGE = (90.0, 110.0)          # 未识别标准值的通用范围

# 平行样相对偏差 (参照 HJ/T 91-2002)
PARALLEL_RPD_LIMITS = {
    # 浓度范围 (mg/L) → 最大RPD (%)
    (0.0, 0.1): 30.0,
    (0.1, 1.0): 20.0,
    (1.0, 2.0): 15.0,
    (2.0, float('inf')): 10.0,
}

# 计算公式
# ρN = (As - Ab - a) / (b × V) × f
# As: 样品吸光度  Ab: 空白吸光度  a: 截距  b: 斜率  V: 取样体积  f: 稀释倍数

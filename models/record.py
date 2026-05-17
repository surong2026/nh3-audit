from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

@dataclass
class StandardSolution:
    stock_concentration: float = 500.0
    stock_id: str = ""
    stock_prep_date: Optional[date] = None
    stock_expiry_date: Optional[date] = None
    working_concentration: float = 10.0
    working_prep_date: Optional[date] = None

@dataclass
class CalibrationPoint:
    point_id: int = 0
    nh3_mass: float = 0.0
    volume_taken: float = 0.0
    working_conc: float = 10.0
    absorbance: float = 0.0
    a_minus_a0: Optional[float] = None

@dataclass
class CalibrationCurve:
    standard_solution: StandardSolution = field(default_factory=StandardSolution)
    points: list = field(default_factory=list)
    total_volume: float = 50.0
    regression_a: Optional[float] = None
    regression_b: Optional[float] = None
    correlation_r: Optional[float] = None

@dataclass
class SampleResult:
    sample_id: str = ""
    sample_name: str = ""
    absorbance: float = 0.0
    dilution_factor: float = 1.0
    sample_volume: float = 50.0
    calculated_conc: Optional[float] = None
    remark: str = ""

@dataclass
class QCStandard:
    qc_id: str = ""
    certified_value: float = 0.0
    measured_value: Optional[float] = None
    recovery_rate: Optional[float] = None

@dataclass
class ParallelSample:
    original_id: str = ""
    parallel_id: str = ""
    value_a: float = 0.0
    value_b: float = 0.0
    rpd: Optional[float] = None

@dataclass
class AnalysisRecord:
    analyst: str = ""
    analysis_date: Optional[date] = None
    instrument_model: str = ""
    instrument_id: str = ""
    method_reference: str = "HJ 535-2009"
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    experiment_water_batch: str = ""

    calibration_curve: CalibrationCurve = field(default_factory=CalibrationCurve)

    pretreatment_method: str = ""
    pretreatment_details: str = ""
    pretreatment_date: Optional[date] = None

    wavelength: int = 420
    cuvette_path: int = 20
    color_dev_time: int = 10
    reference_solution: str = "水"

    nessler_method: str = ""
    tartrate_boiled: bool = True
    ammonia_free_water: bool = True

    lab_blank_absorbance: float = 0.0
    field_blank_absorbance: Optional[float] = None

    samples: list = field(default_factory=list)
    qc_standards: list = field(default_factory=list)
    parallels: list = field(default_factory=list)

    record_id: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        import dataclasses
        def _convert(obj):
            if dataclasses.is_dataclass(obj):
                result = {}
                for f in dataclasses.fields(obj):
                    val = getattr(obj, f.name)
                    result[f.name] = _convert(val)
                return result
            elif isinstance(obj, (list, tuple)):
                return [_convert(v) for v in obj]
            elif isinstance(obj, (date, datetime)):
                return obj.isoformat()
            return obj
        return _convert(self)

    @classmethod
    def from_dict(cls, d: dict):
        def _convert_date(v):
            if v is None:
                return None
            if isinstance(v, str):
                return date.fromisoformat(v)
            return v

        ss_d = d.get('calibration_curve', {}).get('standard_solution', {})
        ss = StandardSolution(
            stock_concentration=ss_d.get('stock_concentration', 500.0),
            stock_id=ss_d.get('stock_id', ''),
            stock_prep_date=_convert_date(ss_d.get('stock_prep_date')),
            stock_expiry_date=_convert_date(ss_d.get('stock_expiry_date')),
            working_concentration=ss_d.get('working_concentration', 10.0),
            working_prep_date=_convert_date(ss_d.get('working_prep_date')),
        )

        pts = []
        for p in d.get('calibration_curve', {}).get('points', []):
            pts.append(CalibrationPoint(**{k: v for k, v in p.items() if k in CalibrationPoint.__dataclass_fields__}))

        cc = CalibrationCurve(
            standard_solution=ss,
            points=pts,
            total_volume=d.get('calibration_curve', {}).get('total_volume', 50.0),
            regression_a=d.get('calibration_curve', {}).get('regression_a'),
            regression_b=d.get('calibration_curve', {}).get('regression_b'),
            correlation_r=d.get('calibration_curve', {}).get('correlation_r'),
        )

        samples = []
        for s in d.get('samples', []):
            samples.append(SampleResult(**{k: v for k, v in s.items() if k in SampleResult.__dataclass_fields__}))

        qc_items = []
        for q in d.get('qc_standards', []):
            qc_items.append(QCStandard(**{k: v for k, v in q.items() if k in QCStandard.__dataclass_fields__}))

        parallels = []
        for p in d.get('parallels', []):
            parallels.append(ParallelSample(**{k: v for k, v in p.items() if k in ParallelSample.__dataclass_fields__}))

        return cls(
            analyst=d.get('analyst', ''),
            analysis_date=_convert_date(d.get('analysis_date')),
            instrument_model=d.get('instrument_model', ''),
            instrument_id=d.get('instrument_id', ''),
            method_reference=d.get('method_reference', 'HJ 535-2009'),
            temperature=d.get('temperature'),
            humidity=d.get('humidity'),
            experiment_water_batch=d.get('experiment_water_batch', ''),
            calibration_curve=cc,
            pretreatment_method=d.get('pretreatment_method', ''),
            pretreatment_details=d.get('pretreatment_details', ''),
            pretreatment_date=_convert_date(d.get('pretreatment_date')),
            wavelength=d.get('wavelength', 420),
            cuvette_path=d.get('cuvette_path', 20),
            color_dev_time=d.get('color_dev_time', 10),
            reference_solution=d.get('reference_solution', '水'),
            nessler_method=d.get('nessler_method', ''),
            tartrate_boiled=d.get('tartrate_boiled', True),
            ammonia_free_water=d.get('ammonia_free_water', True),
            lab_blank_absorbance=d.get('lab_blank_absorbance', 0.0),
            field_blank_absorbance=d.get('field_blank_absorbance'),
            samples=samples,
            qc_standards=qc_items,
            parallels=parallels,
            record_id=d.get('record_id', ''),
            notes=d.get('notes', ''),
        )

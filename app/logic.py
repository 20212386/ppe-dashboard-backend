import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE_PATH = DATA_DIR / "input_logs.csv"

INPUT_REQUIRED_COLUMNS = [
    "date", "time", "worker_id", "team", "zone", "task_type",
    "ppe_type", "worn", "risk_exposure", "note"
]


# =========================
# 공통 / 페이지 1
# =========================
def load_logs(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def calculate_compliance_rate(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    compliant_count = (df["is_violated"] == 0).sum()
    total_count = len(df)

    return round((compliant_count / total_count) * 100, 2)


def get_weakest_zone(df: pd.DataFrame) -> dict:
    zone_risk_scores = get_zone_risk_scores(df)

    if not zone_risk_scores:
        return {"zone": None, "count": 0, "risk_score": 0.0}

    top_zone = zone_risk_scores[0]

    return {
        "zone": top_zone["zone"],
        "count": float(top_zone["risk_score"]),  # <- 프론트엔드가 읽을 수 있게 count에도 비율을 담아줍니다.
        "risk_score": float(top_zone["risk_score"])
    }


def get_most_missing_ppe(df: pd.DataFrame) -> dict:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return {"missed_ppe": None, "count": 0}

    ppe_counts = violated_df["missed_ppe"].value_counts()
    most_missing = ppe_counts.idxmax()
    count = int(ppe_counts.max())

    return {"missed_ppe": most_missing, "count": count}


def get_priority_task(df: pd.DataFrame) -> dict:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return {"time_slot": None, "zone": None, "text": None, "count": 0}

    combo_counts = (
        violated_df.groupby(["time_slot", "zone"])
        .size()
        .sort_values(ascending=False)
    )

    time_slot, zone = combo_counts.index[0]
    count = int(combo_counts.iloc[0])

    return {
        "time_slot": time_slot,
        "zone": zone,
        "text": f"{time_slot} {zone}",
        "count": count
    }


def get_today_date_str() -> str:
    return str(date.today())


def filter_by_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    return df[df["date"] == target_date].copy()


def get_hourly_violations(df: pd.DataFrame) -> list[dict]:
    violated_df = df[df["is_violated"] == 1]

    order = ["오전", "점심직후", "오후"]
    counts = violated_df["time_slot"].value_counts().to_dict()

    return [
        {"time_slot": slot, "count": int(counts.get(slot, 0))}
        for slot in order
    ]


def get_zone_risk_scores(df: pd.DataFrame) -> list[dict]:
    if df.empty or "zone" not in df.columns or "is_violated" not in df.columns:
        return []

    work_df = df.copy()
    work_df["zone"] = work_df["zone"].astype(str).str.strip()

    results = []

    for zone in work_df["zone"].dropna().unique():
        zone_df = work_df[work_df["zone"] == zone]
        zone_total = len(zone_df)

        if zone_total == 0:
            risk_score = 0.0
        else:
            violated_count = int((zone_df["is_violated"] == 1).sum())
            risk_score = round((violated_count / zone_total) * 100, 2)

        risk_score = max(0.0, min(100.0, risk_score))

        results.append({
            "zone": zone,
            "risk_score": risk_score
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


def get_safety_point(df: pd.DataFrame) -> str:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return "오늘은 위반 데이터가 없어 전반적으로 양호합니다."

    combo_counts = (
        violated_df.groupby(["time_slot", "zone", "missed_ppe"])
        .size()
        .sort_values(ascending=False)
    )

    time_slot, zone, missed_ppe = combo_counts.index[0]
    return f"{time_slot} {zone}에서 {missed_ppe} 미착용이 증가했습니다."


def get_safety_points(df: pd.DataFrame) -> list[str]:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return ["오늘은 위반 데이터가 없어 전반적으로 양호합니다."]

    points = []
    combo_counts = (
        violated_df.groupby(["time_slot", "zone", "missed_ppe"])
        .size()
        .sort_values(ascending=False)
    )

    top_items = combo_counts.head(3)

    for (time_slot, zone, missed_ppe), _count in top_items.items():
        points.append(f"{time_slot} {zone}에서 {missed_ppe} 미착용이 증가했습니다.")

    return points


# =========================
# 페이지 2 입력/업로드 공통
# =========================
def normalize_uploaded_df(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_input_df(df)


def validate_required_columns(df: pd.DataFrame) -> dict:
    return validate_input_columns(df)


def calculate_data_summary(df: pd.DataFrame, today_str: str | None = None) -> dict:
    return calculate_input_summary(df, today_str or get_today_date_str())


def calculate_quality_metrics(df: pd.DataFrame) -> dict:
    return calculate_input_quality(df)


def get_recent_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    return get_input_preview(df, n)


def load_input_logs() -> pd.DataFrame:
    if not INPUT_FILE_PATH.exists():
        return pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)

    df = pd.read_csv(INPUT_FILE_PATH)
    df = normalize_input_df(df)

    validation = validate_input_columns(df)
    if not validation["is_valid"]:
        return pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)

    return df


def normalize_input_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 컬럼명 정리
    rename_map = {
        "Date": "date",
        "Time": "time",
        "Worker_ID": "worker_id",
        "WorkerID": "worker_id",
        "Team": "team",
        "Zone": "zone",
        "Task_Type": "task_type",
        "TaskType": "task_type",
        "PPE_Type": "ppe_type",
        "PPEType": "ppe_type",
        "Worn": "worn",
        "Risk_Exposure": "risk_exposure",
        "RiskExposure": "risk_exposure",
        "Note": "note",
    }
    df = df.rename(columns=rename_map)

    # 누락 컬럼 채우기
    for col in INPUT_REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 순서 맞추기
    df = df[INPUT_REQUIRED_COLUMNS]

    # 문자열 정리
    for col in INPUT_REQUIRED_COLUMNS:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # 값 통일
    df["worn"] = df["worn"].replace({
        "착용": "O", "미착용": "X",
        "o": "O", "x": "X"
    }).str.upper()

    df["risk_exposure"] = df["risk_exposure"].replace({
        "노출": "O", "비노출": "X",
        "o": "O", "x": "X"
    }).str.upper()

    # 날짜 형식 최대한 통일
    if not df.empty:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        df["date"] = parsed.dt.strftime("%Y-%m-%d").fillna(df["date"])

    return df


def validate_input_columns(df: pd.DataFrame) -> dict:
    missing_columns = [col for col in INPUT_REQUIRED_COLUMNS if col not in df.columns]

    return {
        "is_valid": len(missing_columns) == 0,
        "missing_columns": missing_columns
    }


def calculate_input_summary(df: pd.DataFrame, today_str: str) -> dict:
    if df.empty:
        return {
            "total_rows": 0,
            "today_rows": 0,
            "risk_rows": 0,
            "not_worn_rows": 0,
            "normal_rows": 0,
        }

    today_rows = df[df["date"] == today_str]
    risk_rows = df[df["risk_exposure"] == "O"]
    not_worn_rows = df[df["worn"] == "X"]
    normal_rows = df[df["worn"] == "O"]

    return {
        "total_rows": int(len(df)),
        "today_rows": int(len(today_rows)),
        "risk_rows": int(len(risk_rows)),
        "not_worn_rows": int(len(not_worn_rows)),
        "normal_rows": int(len(normal_rows)),
    }


def calculate_input_quality(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "completeness_rate": 0,
            "validity_rate": 0,
            "duplicate_count": 0,
            "error_count": 0,
        }

    required_without_note = [
        "date", "time", "worker_id", "team", "zone",
        "task_type", "ppe_type", "worn", "risk_exposure"
    ]

    total_cells = len(df) * len(required_without_note)
    filled_cells = df[required_without_note].replace("", pd.NA).notna().sum().sum()
    completeness_rate = round((filled_cells / total_cells) * 100, 2) if total_cells > 0 else 0

    valid_worn = df["worn"].isin(["O", "X"]).sum()
    valid_risk = df["risk_exposure"].isin(["O", "X"]).sum()
    validity_rate = round(((valid_worn + valid_risk) / (2 * len(df))) * 100, 2) if len(df) > 0 else 0

    duplicate_count = int(df.duplicated().sum())

    error_count = int(
        len(df[
            (~df["worn"].isin(["O", "X"])) |
            (~df["risk_exposure"].isin(["O", "X"]))
        ])
    )

    return {
        "completeness_rate": completeness_rate,
        "validity_rate": validity_rate,
        "duplicate_count": duplicate_count,
        "error_count": error_count,
    }


def get_input_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    if df.empty:
        return []

    preview_df = df.tail(n).copy()
    return preview_df.to_dict(orient="records")


def append_manual_entry(row: dict) -> None:
    df = load_input_logs()

    new_row_df = pd.DataFrame([row])
    new_row_df = normalize_input_df(new_row_df)

    combined_df = pd.concat([df, new_row_df], ignore_index=True)
    combined_df.to_csv(INPUT_FILE_PATH, index=False, encoding="utf-8-sig")


# =========================
# 페이지 3 분석 상세 (완전 통합 무적 버전)
# =========================
def filter_input_data(
    df: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    site: str | None = None,
    zone: str | None = None,
    task_type: str | None = None,
    ppe_type: str | None = None,
    risk_exposure: str | None = None,
) -> pd.DataFrame:
    if df.empty: return df.copy()
    filtered_df = df.copy()

    if start_date: filtered_df = filtered_df[filtered_df["date"] >= start_date]
    if end_date: filtered_df = filtered_df[filtered_df["date"] <= end_date]
    
    # 💡 일치(==) 대신 포함(contains)으로 변경해서 띄어쓰기나 콤마 섞여있어도 다 찾아냄!
    if site and "site" in filtered_df.columns: 
        filtered_df = filtered_df[filtered_df["site"].astype(str).str.contains(site, na=False)]
    if zone and "zone" in filtered_df.columns: 
        filtered_df = filtered_df[filtered_df["zone"].astype(str).str.contains(zone, na=False)]
    if task_type and "task_type" in filtered_df.columns: 
        filtered_df = filtered_df[filtered_df["task_type"].astype(str).str.contains(task_type, na=False)]
    
    if ppe_type:
        if "missed_ppe" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["missed_ppe"].astype(str).str.contains(ppe_type, na=False)]
        elif "ppe_type" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["ppe_type"].astype(str).str.contains(ppe_type, na=False)]

    if risk_exposure:
        if "risk_exposure" in filtered_df.columns:
            val1 = "O" if risk_exposure == "O" else "X"
            val2 = "1" if risk_exposure == "O" else "0"
            filtered_df = filtered_df[filtered_df["risk_exposure"].astype(str).str.strip().isin([val1, val2])]

    return filtered_df.copy()

def _get_violation_series_p3(df: pd.DataFrame) -> pd.Series:
    """페이지 5와 동일한 무적의 위반 판독기"""
    if "is_violated" in df.columns:
        v = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0)
        if v.sum() > 0: return v == 1
    if "missed_ppe" in df.columns:
        m = df["missed_ppe"].astype(str).str.strip().replace(["nan", "None", "NaN", ""], "")
        if (m != "").sum() > 0: return m != ""
    if "note" in df.columns:
        return df["note"].astype(str).str.contains("미흡")
    if "worn" in df.columns:
        return df["worn"].astype(str).str.strip().str.upper() == "X"
    return pd.Series(False, index=df.index)

def _get_ppe_col(df: pd.DataFrame) -> str:
    if "missed_ppe" in df.columns: return "missed_ppe"
    if "ppe_type" in df.columns: return "ppe_type"
    return ""

def get_analysis_kpis(df: pd.DataFrame) -> dict:
    if df.empty: return {"top_time": "-", "top_zone": "-", "top_task_type": "-", "top_ppe": "-"}
    
    is_viol = _get_violation_series_p3(df)
    violated_df = df[is_viol].copy()
    
    if violated_df.empty:
        return {"top_time": "-", "top_zone": "-", "top_task_type": "-", "top_ppe": "-"}

    top_time = "-"
    if "time_slot" in violated_df.columns and not violated_df["time_slot"].empty:
        top_time = violated_df["time_slot"].value_counts().idxmax()
    elif "time" in violated_df.columns and not violated_df["time"].empty:
        top_time = violated_df["time"].astype(str).str[:2].value_counts().idxmax() + "시"

    top_zone = violated_df["zone"].value_counts().idxmax() if "zone" in violated_df.columns and not violated_df["zone"].empty else "-"
    top_task = violated_df["task_type"].value_counts().idxmax() if "task_type" in violated_df.columns and not violated_df["task_type"].empty else "-"
    
    ppe_col = _get_ppe_col(violated_df)
    top_ppe = violated_df[ppe_col].value_counts().idxmax() if ppe_col and not violated_df[ppe_col].empty else "-"

    return {"top_time": top_time, "top_zone": top_zone, "top_task_type": top_task, "top_ppe": top_ppe}

def get_analysis_charts(df: pd.DataFrame) -> dict:
    if df.empty: return {"time_chart": [], "ppe_chart": [], "zone_chart": [], "task_chart": []}

    is_viol = _get_violation_series_p3(df)
    violated_df = df[is_viol].copy()
    
    if violated_df.empty:
        return {"time_chart": [], "ppe_chart": [], "zone_chart": [], "task_chart": []}

    time_chart, ppe_chart, zone_chart, task_chart = [], [], [], []

    # 1. 시간대별
    if "time_slot" in violated_df.columns and not violated_df["time_slot"].isnull().all():
        t_counts = violated_df["time_slot"].value_counts()
        order = {"오전": 1, "점심직후": 2, "오후": 3}
        time_chart = [{"label": str(k), "count": int(v)} for k, v in sorted(t_counts.items(), key=lambda x: order.get(x[0], 99))]
    elif "time" in violated_df.columns:
        violated_df["hour"] = violated_df["time"].astype(str).str[:2]
        t_counts = violated_df["hour"].value_counts()
        time_chart = [{"label": f"{str(k).zfill(2)}시", "count": int(v)} for k, v in sorted(t_counts.items())]

    # 2. PPE별
    ppe_col = _get_ppe_col(violated_df)
    if ppe_col:
        p_counts = violated_df[ppe_col].value_counts()
        ppe_chart = [{"label": str(k), "count": int(v)} for k, v in p_counts.items() if str(k).strip() not in ["", "nan", "None"]]

    # 3. 구역별
    if "zone" in violated_df.columns:
        z_counts = violated_df["zone"].value_counts()
        zone_chart = [{"label": str(k), "count": int(v)} for k, v in z_counts.items() if str(k).strip() not in ["", "nan", "None"]]

    # 4. 작업유형별
    if "task_type" in violated_df.columns:
        ta_counts = violated_df["task_type"].value_counts()
        task_chart = [{"label": str(k), "count": int(v)} for k, v in ta_counts.items() if str(k).strip() not in ["", "nan", "None"]]

    return {
        "time_chart": time_chart,
        "ppe_chart": ppe_chart,
        "zone_chart": zone_chart,
        "task_chart": task_chart,
    }

def get_recommend_action(df: pd.DataFrame) -> str:
    if df.empty: return "현재 필터 조건에서 뚜렷한 위반 패턴이 없어 기본 PPE 점검을 유지하세요."
    
    is_viol = _get_violation_series_p3(df)
    violated_df = df[is_viol].copy()
    
    if violated_df.empty:
        return "현재 필터 조건에서 뚜렷한 위반 패턴이 없어 기본 PPE 점검을 유지하세요."

    ppe_col = _get_ppe_col(violated_df)
    top_ppe = violated_df[ppe_col].value_counts().idxmax() if ppe_col and not violated_df[ppe_col].empty else ""
    top_task = violated_df["task_type"].value_counts().idxmax() if "task_type" in violated_df.columns and not violated_df["task_type"].empty else ""

    if "랜야드" in str(top_ppe): return f"{top_task} 전 랜야드 체결 여부를 우선 점검하세요."
    if "안전모" in str(top_ppe): return f"{top_task} 전 안전모 착용 여부를 우선 점검하세요."
    if "장갑" in str(top_ppe): return f"{top_task} 전 장갑 착용 여부를 우선 점검하세요."

    return f"{top_task} 작업 전 PPE 착용 여부를 우선 점검하세요."


# =========================
# 페이지 4 TBM
# =========================
def get_yesterday_date_str() -> str:
    return str(datetime.today().date() - timedelta(days=1))


def get_tbm_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "compliance_rate": 0.0,
            "top_zone": None,
            "top_ppe": None,
            "top_time": None,
        }

    total_rows = len(df)
    normal_rows = (df["worn"] == "O").sum()
    compliance_rate = round((normal_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

    violated_df = df[df["worn"] == "X"]

    if violated_df.empty:
        return {
            "compliance_rate": compliance_rate,
            "top_zone": None,
            "top_ppe": None,
            "top_time": None,
        }

    top_zone = violated_df["zone"].value_counts().idxmax()
    top_ppe = violated_df["ppe_type"].value_counts().idxmax()
    top_time = violated_df["time"].astype(str).str[:2].value_counts().idxmax() + "시"

    return {
        "compliance_rate": compliance_rate,
        "top_zone": top_zone,
        "top_ppe": top_ppe,
        "top_time": top_time,
    }


def get_tbm_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_rows": 0,
            "risk_rows": 0,
            "not_worn_rows": 0,
            "normal_rows": 0,
        }

    return {
        "total_rows": int(len(df)),
        "risk_rows": int((df["risk_exposure"] == "O").sum()),
        "not_worn_rows": int((df["worn"] == "X").sum()),
        "normal_rows": int((df["worn"] == "O").sum()),
    }


def get_tbm_checklist(df: pd.DataFrame) -> list[str]:
    violated_df = df[df["worn"] == "X"]

    if violated_df.empty:
        return ["전일 위반 데이터가 없어 기본 PPE 점검만 수행하면 됩니다."]

    checklist = []

    top_zone = violated_df["zone"].value_counts().idxmax()
    top_ppe = violated_df["ppe_type"].value_counts().idxmax()

    checklist.append(f"{top_zone} 작업 전 현장 순찰 및 집중 점검")
    checklist.append(f"{top_ppe} 착용 여부 출입 전 확인")
    checklist.append("작업 시작 전 작업자 대상 PPE 재안내")

    if "고소작업구역" in violated_df["zone"].values:
        checklist.append("고소작업 전 랜야드 체결 상태 재확인")
    if "절단작업구역" in violated_df["zone"].values:
        checklist.append("절단작업 전 장갑·안전모 착용 점검")

    seen = set()
    result = []
    for item in checklist:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result[:5]


def get_tbm_briefing_text(df: pd.DataFrame, target_date: str) -> str:
    kpis = get_tbm_kpis(df)
    stats = get_tbm_stats(df)

    if stats["total_rows"] == 0:
        return f"{target_date} 전일 데이터가 없어 기본 안전수칙 중심으로 TBM을 진행하면 됩니다."

    if kpis["top_zone"] is None:
        return (
            f"{target_date} 전일 총 {stats['total_rows']}건의 작업 데이터가 기록되었고, "
            f"전반적 준수율은 {kpis['compliance_rate']}%였습니다. "
            "전일 미착용 위반이 없어 오늘도 현재 수준을 유지하는 것이 중요합니다."
        )

    return (
        f"{target_date} 전일 총 {stats['total_rows']}건의 작업 데이터가 기록되었고, "
        f"준수율은 {kpis['compliance_rate']}%였습니다. "
        f"가장 취약한 구역은 {kpis['top_zone']}이며, "
        f"가장 많이 누락된 PPE는 {kpis['top_ppe']}였습니다. "
        f"특히 {kpis['top_time']}대 위반이 집중되어 오늘 TBM에서는 해당 시간대와 구역을 중심으로 점검이 필요합니다."
    )


def get_tbm_focus_message(df: pd.DataFrame) -> str:
    violated_df = df[df["worn"] == "X"]

    if violated_df.empty:
        return "전일 위반이 없어 오늘은 현재의 착용 수준을 유지하는 데 집중하세요."

    top_zone = violated_df["zone"].value_counts().idxmax()
    top_ppe = violated_df["ppe_type"].value_counts().idxmax()

    return f"오늘은 {top_zone}에서 {top_ppe} 착용 여부를 최우선 관리사항으로 두고 작업 전 확인을 강화하세요."


def get_tbm_full_script(df: pd.DataFrame, target_date: str) -> str:
    briefing = get_tbm_briefing_text(df, target_date)
    checklist = get_tbm_checklist(df)
    focus = get_tbm_focus_message(df)

    checklist_text = " / ".join(checklist)

    return (
        f"[전일 브리핑] {briefing}\n\n"
        f"[오늘의 중점 관리사항] {focus}\n\n"
        f"[현장 체크리스트] {checklist_text}"
    )


# =========================
# =========================
# 페이지 5 개선 / 인센티브 (초강력 에러 방어 + 완벽 계산 버전)
# =========================
import pandas as pd

def get_violation_series(df: pd.DataFrame) -> pd.Series:
    """어떤 데이터가 들어와도 위반 여부를 찾아내는 함수"""
    if "is_violated" in df.columns:
        v = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0)
        if v.sum() > 0: return v == 1
    
    if "missed_ppe" in df.columns:
        m = df["missed_ppe"].astype(str).str.strip().replace(["nan", "None", "NaN"], "")
        if (m != "").sum() > 0: return m != ""
    
    if "note" in df.columns:
        return df["note"].astype(str).str.contains("미흡")
    
    if "worn" in df.columns:
        return df["worn"].astype(str).str.strip().str.upper() == "X"
    
    return pd.Series(False, index=df.index)

def calculate_weekly_compliance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["week", "compliance_rate"])
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_violation"] = get_violation_series(temp)
    temp["is_normal"] = ~temp["is_violation"]
    
    result = (
        temp.groupby("week_num")["is_normal"]
        .apply(lambda x: round((x.sum() / len(x)) * 100, 2) if len(x) > 0 else 0.0)
        .reset_index(name="compliance_rate")
        .sort_values("week_num")
    )
    result["week"] = result["week_num"].astype(str) + "주차"
    return result[["week", "compliance_rate"]]

def calculate_weekly_violation_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["week", "violation_count"])
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_violation"] = get_violation_series(temp).astype(int)
    
    result = temp.groupby("week_num")["is_violation"].sum().reset_index(name="violation_count").sort_values("week_num")
    result["week"] = result["week_num"].astype(str) + "주차"
    return result[["week", "violation_count"]]

def calculate_weekly_ppe_missed_counts(df: pd.DataFrame) -> pd.DataFrame:
    return calculate_weekly_violation_counts(df).rename(columns={"violation_count": "ppe_missed_count"})

def get_team_comparison_chart(df: pd.DataFrame) -> list[dict]:
    if df.empty or "team" not in df.columns: return []
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_normal"] = ~get_violation_series(temp)

    result = []
    for team in temp["team"].dropna().unique():
        t_df = temp[temp["team"] == team]
        t_weeks = sorted(t_df["week_num"].unique())
        if len(t_weeks) < 2: continue
        
        first_df = t_df[t_df["week_num"] == t_weeks[0]]
        last_df = t_df[t_df["week_num"] == t_weeks[-1]]
        
        first_rate = round((first_df["is_normal"].sum() / len(first_df)) * 100, 2) if len(first_df) > 0 else 0
        last_rate = round((last_df["is_normal"].sum() / len(last_df)) * 100, 2) if len(last_df) > 0 else 0
        result.append({"team": str(team), "initial_rate": first_rate, "current_rate": last_rate})
    return result

def get_team_incentive_summary(df: pd.DataFrame) -> list[str]:
    if df.empty or "team" not in df.columns: return ["팀 데이터가 없습니다."]
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_violation"] = get_violation_series(temp)
    temp["is_normal"] = ~temp["is_violation"]

    summaries = []
    for team in temp["team"].dropna().unique():
        t_df = temp[temp["team"] == team]
        t_weeks = sorted(t_df["week_num"].unique())
        if len(t_weeks) < 2: continue
        
        first_df = t_df[t_df["week_num"] == t_weeks[0]]
        last_df = t_df[t_df["week_num"] == t_weeks[-1]]
        
        first_rate = round((first_df["is_normal"].sum() / len(first_df)) * 100, 2) if len(first_df) > 0 else 0
        last_rate = round((last_df["is_normal"].sum() / len(last_df)) * 100, 2) if len(last_df) > 0 else 0
        first_missed = int(first_df["is_violation"].sum())
        last_missed = int(last_df["is_violation"].sum())
        
        reduction = round(((first_missed - last_missed) / first_missed) * 100, 2) if first_missed > 0 else 0.0
        summaries.append(f"{team}: 초기 준수율 {first_rate}% → 현재 {last_rate}%, PPE 미착용 {reduction}% 감소")
    
    return summaries if summaries else ["팀별 비교 데이터가 부족합니다."]

def get_improvement_metrics(df: pd.DataFrame) -> dict:
    weekly_compliance = calculate_weekly_compliance(df)
    weekly_violations = calculate_weekly_violation_counts(df)
    weekly_ppe = calculate_weekly_ppe_missed_counts(df)
    
    best_team = "-"
    team_chart = get_team_comparison_chart(df)
    if team_chart:
        best_item = max(team_chart, key=lambda x: x["current_rate"] - x["initial_rate"])
        best_team = best_item["team"]

    if len(weekly_compliance) < 2:
        return {"improvement_rate": 0.0, "repeat_ppe_reduction_rate": 0.0, "risk_recurrence_reduction_rate": 0.0, "best_team": best_team}
    
    first_compliance = float(weekly_compliance.iloc[0]["compliance_rate"])
    last_compliance = float(weekly_compliance.iloc[-1]["compliance_rate"])
    improvement_rate = round(last_compliance - first_compliance, 2)
    
    first_ppe = int(weekly_ppe.iloc[0]["ppe_missed_count"]) if not weekly_ppe.empty else 0
    last_ppe = int(weekly_ppe.iloc[-1]["ppe_missed_count"]) if not weekly_ppe.empty else 0
    repeat_ppe_reduction_rate = round(((first_ppe - last_ppe) / first_ppe) * 100, 2) if first_ppe > 0 else 0.0
    
    first_violation = int(weekly_violations.iloc[0]["violation_count"]) if not weekly_violations.empty else 0
    last_violation = int(weekly_violations.iloc[-1]["violation_count"]) if not weekly_violations.empty else 0
    risk_recurrence_reduction_rate = round(((first_violation - last_violation) / first_violation) * 100, 2) if first_violation > 0 else 0.0
    
    return {"improvement_rate": improvement_rate, "repeat_ppe_reduction_rate": repeat_ppe_reduction_rate, "risk_recurrence_reduction_rate": risk_recurrence_reduction_rate, "best_team": best_team}

def get_weekly_trend_charts(df: pd.DataFrame) -> dict:
    weekly_violations = calculate_weekly_violation_counts(df)
    weekly_ppe = calculate_weekly_ppe_missed_counts(df)
    violation_chart = weekly_violations.rename(columns={"week": "label", "violation_count": "count"}).to_dict(orient="records")
    ppe_chart = weekly_ppe.rename(columns={"week": "label", "ppe_missed_count": "count"}).to_dict(orient="records")
    return {"violation_trend_chart": violation_chart, "ppe_trend_chart": ppe_chart}
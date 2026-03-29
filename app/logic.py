import os
import re
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE_PATH = DATA_DIR / "input_logs.csv"

INPUT_REQUIRED_COLUMNS = [
    "date",
    "time_slot",
    "site",
    "zone",
    "task_type",
    "missed_ppe",
    "is_violated",
    "team",
    "note",
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
        results.append({"zone": zone, "risk_score": risk_score})
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

def get_weakest_zone(df: pd.DataFrame) -> dict:
    zone_risk_scores = get_zone_risk_scores(df)
    if not zone_risk_scores:
        return {"zone": None, "count": 0, "risk_score": 0.0}
    top_zone = zone_risk_scores[0]
    return {
        "zone": top_zone["zone"],
        "count": float(top_zone["risk_score"]),
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
    combo_counts = violated_df.groupby(["time_slot", "zone"]).size().sort_values(ascending=False)
    time_slot, zone = combo_counts.index[0]
    count = int(combo_counts.iloc[0])
    return {"time_slot": time_slot, "zone": zone, "text": f"{time_slot} {zone}", "count": count}

def get_today_date_str() -> str:
    return str(date.today())

def filter_by_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    return df[df["date"] == target_date].copy()

def get_hourly_violations(df: pd.DataFrame) -> list[dict]:
    violated_df = df[df["is_violated"] == 1]
    order = ["오전", "점심직후", "오후"]
    counts = violated_df["time_slot"].value_counts().to_dict()
    return [{"time_slot": slot, "count": int(counts.get(slot, 0))} for slot in order]

def get_safety_point(df: pd.DataFrame) -> str:
    violated_df = df[df["is_violated"] == 1]
    if violated_df.empty: return "오늘은 위반 데이터가 없어 전반적으로 양호합니다."
    combo_counts = violated_df.groupby(["time_slot", "zone", "missed_ppe"]).size().sort_values(ascending=False)
    time_slot, zone, missed_ppe = combo_counts.index[0]
    return f"{time_slot} {zone}에서 {missed_ppe} 미착용이 증가했습니다."

def get_safety_points(df: pd.DataFrame) -> list[str]:
    violated_df = df[df["is_violated"] == 1]
    if violated_df.empty: return ["오늘은 위반 데이터가 없어 전반적으로 양호합니다."]
    points = []
    combo_counts = violated_df.groupby(["time_slot", "zone", "missed_ppe"]).size().sort_values(ascending=False)
    for (time_slot, zone, missed_ppe), _ in combo_counts.head(3).items():
        points.append(f"{time_slot} {zone}에서 {missed_ppe} 미착용이 증가했습니다.")
    return points

# =========================
# 페이지 2 입력/업로드 공통
# =========================
def normalize_input_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        "Date": "date", "Time_Slot": "time_slot", "TimeSlot": "time_slot", "Site": "site", 
        "Zone": "zone", "Task_Type": "task_type", "TaskType": "task_type", "Missed_PPE": "missed_ppe", 
        "MissedPPE": "missed_ppe", "PPE_Type": "missed_ppe", "PPEType": "missed_ppe", "Is_Violated": "is_violated", 
        "IsViolated": "is_violated", "Risk_Exposure": "is_violated", "RiskExposure": "is_violated", "Team": "team", "Note": "note"
    }
    df = df.rename(columns=rename_map)
    for col in INPUT_REQUIRED_COLUMNS:
        if col not in df.columns: df[col] = ""
    df = df[INPUT_REQUIRED_COLUMNS]
    for col in ["date", "time_slot", "site", "zone", "task_type", "missed_ppe", "team", "note"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    if "is_violated" in df.columns:
        df["is_violated"] = df["is_violated"].fillna(0).astype(str).str.strip().replace({"O": "1", "X": "0", "o": "1", "x": "0", "True": "1", "False": "0", "true": "1", "false": "0"})
        df["is_violated"] = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0).astype(int)
    if not df.empty:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        df["date"] = parsed.dt.strftime("%Y-%m-%d").fillna(df["date"])
    return df

def normalize_uploaded_df(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_input_df(df)

def validate_input_columns(df: pd.DataFrame) -> dict:
    missing_columns = [col for col in INPUT_REQUIRED_COLUMNS if col not in df.columns]
    return {"is_valid": len(missing_columns) == 0, "missing_columns": missing_columns}

def validate_required_columns(df: pd.DataFrame) -> dict:
    return validate_input_columns(df)

def calculate_input_summary(df: pd.DataFrame, today_str: str) -> dict:
    if df.empty:
        return {"total_rows": 0, "today_rows": 0, "risk_rows": 0, "not_worn_rows": 0, "normal_rows": 0}
    today_rows = df[df["date"] == today_str]
    risk_rows = df[df["is_violated"] == 1]
    normal_rows = df[df["is_violated"] == 0]
    return {
        "total_rows": int(len(df)), "today_rows": int(len(today_rows)),
        "risk_rows": int(len(risk_rows)), "not_worn_rows": int(len(risk_rows)), "normal_rows": int(len(normal_rows))
    }

def calculate_data_summary(df: pd.DataFrame, today_str: str | None = None) -> dict:
    return calculate_input_summary(df, today_str or get_today_date_str())

def calculate_input_quality(df: pd.DataFrame) -> dict:
    if df.empty: return {"completeness_rate": 0, "validity_rate": 0, "duplicate_count": 0, "error_count": 0}
    required_without_note = ["date", "time_slot", "site", "zone", "task_type", "is_violated"]
    total_cells = len(df) * len(required_without_note)
    filled_cells = df[required_without_note].replace("", pd.NA).notna().sum().sum()
    completeness_rate = round((filled_cells / total_cells) * 100, 2) if total_cells > 0 else 0
    duplicate_count = int(df.duplicated().sum())
    return {"completeness_rate": completeness_rate, "validity_rate": 100, "duplicate_count": duplicate_count, "error_count": 0}

def calculate_quality_metrics(df: pd.DataFrame) -> dict:
    return calculate_input_quality(df)

def get_input_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    if df.empty: return []
    return df.tail(n).iloc[::-1].fillna("").to_dict(orient="records")

def get_recent_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    return get_input_preview(df, n)

def load_input_logs() -> pd.DataFrame:
    if not INPUT_FILE_PATH.exists(): return pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)
    df = pd.read_csv(INPUT_FILE_PATH)
    df = normalize_input_df(df)
    validation = validate_input_columns(df)
    if not validation["is_valid"]: return pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)
    return df

def append_manual_entry(entry: dict) -> dict:
    try:
        if os.path.exists("data/input_logs.csv"):
            df = pd.read_csv("data/input_logs.csv")
        else:
            df = pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)
        new_row = pd.DataFrame([entry])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("data/input_logs.csv", index=False)
        return {"status": "success", "message": "수동 입력 데이터가 저장되었습니다."}
    except Exception as e:
        return {"status": "error", "message": f"저장 실패: {str(e)}"}

# =========================
# 페이지 3 분석 상세
# =========================
def _extract_ppe_from_note(note: str) -> str:
    if not isinstance(note, str): return ""
    m = re.search(r"(장갑|안전모|랜야드)", note)
    return m.group(1) if m else ""

def _is_violation_from_note(note: str) -> bool:
    if not isinstance(note, str): return False
    return "미흡" in note

def _is_safe_from_note(note: str) -> bool:
    if not isinstance(note, str): return False
    return "정상 수행" in note

def filter_input_data(df: pd.DataFrame, start_date=None, end_date=None, site=None, zone=None, task_type=None, ppe_type=None, risk_exposure=None) -> pd.DataFrame:
    if df.empty: return df.copy()
    filtered_df = df.copy()
    if start_date and "date" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["date"].astype(str).str.strip() >= str(start_date).strip()].copy()
    if end_date and "date" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["date"].astype(str).str.strip() <= str(end_date).strip()].copy()
    if site and "site" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["site"].astype(str).str.strip() == str(site).strip()].copy()
    if zone and "zone" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["zone"].astype(str).str.strip() == str(zone).strip()].copy()
    if task_type and "task_type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["task_type"].astype(str).str.strip() == str(task_type).strip()].copy()
    if ppe_type and "missed_ppe" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["missed_ppe"].astype(str).str.strip() == str(ppe_type).strip()].copy()
    if risk_exposure is not None and "is_violated" in filtered_df.columns:
        risk_value = 1 if str(risk_exposure) in ["1", "O"] else 0
        filtered_df = filtered_df[pd.to_numeric(filtered_df["is_violated"], errors="coerce").fillna(0).astype(int) == risk_value].copy()
    return filtered_df

def get_analysis_kpis(df: pd.DataFrame) -> dict:
    if df.empty: return {"top_time": "-", "top_zone": "-", "top_task_type": "-", "top_ppe": "-"}
    top_time, top_zone, top_task_type, top_ppe = "-", "-", "-", "-"
    if "time_slot" in df.columns:
        ts = df["time_slot"].astype(str).str.strip()
        ts = ts[(ts != "") & (ts.str.lower() != "nan") & (ts.str.lower() != "none")]
        if not ts.empty: top_time = ts.value_counts().idxmax()
    if "zone" in df.columns:
        zs = df["zone"].astype(str).str.strip()
        zs = zs[(zs != "") & (zs.str.lower() != "nan") & (zs.str.lower() != "none")]
        if not zs.empty: top_zone = zs.value_counts().idxmax()
    if "task_type" in df.columns:
        tasks = df["task_type"].astype(str).str.strip()
        tasks = tasks[(tasks != "") & (tasks.str.lower() != "nan") & (tasks.str.lower() != "none")]
        if not tasks.empty: top_task_type = tasks.value_counts().idxmax()
    if "missed_ppe" in df.columns:
        ppes = df["missed_ppe"].astype(str).str.strip()
        ppes = ppes[(ppes != "") & (ppes.str.lower() != "nan") & (ppes.str.lower() != "none")]
        if not ppes.empty: top_ppe = ppes.value_counts().idxmax()
    return {"top_time": top_time, "top_zone": top_zone, "top_task_type": top_task_type, "top_ppe": top_ppe}

# 💡 [핵심 퍼센트 로직 추가 완료]
def get_analysis_charts(df: pd.DataFrame) -> dict:
    if df.empty: return {"time_chart": [], "ppe_chart": [], "zone_chart": [], "task_chart": []}
    time_chart, ppe_chart, zone_chart, task_chart = [], [], [], []
    
    if "time_slot" in df.columns:
        ts = df["time_slot"].astype(str).str.strip()
        ts = ts[(ts != "") & (ts.str.lower() != "nan") & (ts.str.lower() != "none")]
        if not ts.empty:
            counts = ts.value_counts()
            order = {"오전": 1, "점심직후": 2, "오후": 3}
            time_chart = [{"label": str(k), "count": int(v)} for k, v in sorted(counts.items(), key=lambda x: order.get(str(x[0]), 999))]

    if "missed_ppe" in df.columns:
        ppes = df["missed_ppe"].astype(str).str.strip()
        ppes = ppes[(ppes != "") & (ppes.str.lower() != "nan") & (ppes.str.lower() != "none")]
        if not ppes.empty:
            counts = ppes.value_counts()
            ppe_chart = [{"label": str(k), "count": int(v)} for k, v in counts.items()]

    if "zone" in df.columns:
        temp_z = df.copy()
        temp_z["zone"] = temp_z["zone"].astype(str).str.strip()
        temp_z = temp_z[(temp_z["zone"] != "") & (temp_z["zone"].str.lower() != "nan") & (temp_z["zone"].str.lower() != "none")]
        if not temp_z.empty:
            temp_z["is_viol"] = get_violation_series(temp_z)
            for z, group in temp_z.groupby("zone"):
                total = len(group)
                viol_count = int(group["is_viol"].sum())
                if total > 0:
                    risk_rate = round((viol_count / total) * 100, 1)
                    comp_rate = round(100.0 - risk_rate, 1)
                else:
                    risk_rate, comp_rate = 0.0, 0.0
                zone_chart.append({"label": str(z), "count": viol_count, "compliance_rate": comp_rate, "risk_rate": risk_rate})

    if "task_type" in df.columns:
        tasks = df["task_type"].astype(str).str.strip()
        tasks = tasks[(tasks != "") & (tasks.str.lower() != "nan") & (tasks.str.lower() != "none")]
        if not tasks.empty:
            counts = tasks.value_counts()
            task_chart = [{"label": str(k), "count": int(v)} for k, v in counts.items()]

    return {"time_chart": time_chart, "ppe_chart": ppe_chart, "zone_chart": zone_chart, "task_chart": task_chart}

def get_recommend_action(df: pd.DataFrame) -> str:
    if df.empty: return "현재 필터 조건에서 뚜렷한 위반 패턴이 없어 기본 PPE 점검을 유지하세요."
    top_zone, top_task, top_ppe = "-", "-", "-"
    if "zone" in df.columns:
        zs = df["zone"].astype(str).str.strip()
        zs = zs[(zs != "") & (zs.str.lower() != "nan") & (zs.str.lower() != "none")]
        if not zs.empty: top_zone = zs.value_counts().idxmax()
    if "task_type" in df.columns:
        tasks = df["task_type"].astype(str).str.strip()
        tasks = tasks[(tasks != "") & (tasks.str.lower() != "nan") & (tasks.str.lower() != "none")]
        if not tasks.empty: top_task = tasks.value_counts().idxmax()
    if "missed_ppe" in df.columns:
        ppes = df["missed_ppe"].astype(str).str.strip()
        ppes = ppes[(ppes != "") & (ppes.str.lower() != "nan") & (ppes.str.lower() != "none")]
        if not ppes.empty: top_ppe = ppes.value_counts().idxmax()

    if top_ppe != "-" and top_task != "-": return f"{top_task} 작업 전 {top_ppe} 착용 여부를 우선 점검하세요."
    if top_zone != "-": return f"{top_zone} 구역 반복 패턴을 우선 점검하세요."
    return "반복 위반 상위 조건을 우선 점검하세요."

# =========================
# 페이지 4 TBM
# =========================
def get_yesterday_date_str() -> str:
    return str(datetime.today().date() - timedelta(days=1))

def get_tbm_kpis(df: pd.DataFrame) -> dict:
    if df.empty: return {"compliance_rate": 0.0, "top_zone": None, "top_ppe": None, "top_time": None}
    total_rows = len(df)
    normal_rows = (df["is_violated"] == 0).sum()
    compliance_rate = round((normal_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0
    violated_df = df[df["is_violated"] == 1]
    if violated_df.empty: return {"compliance_rate": compliance_rate, "top_zone": None, "top_ppe": None, "top_time": None}
    top_zone = violated_df["zone"].value_counts().idxmax() if not violated_df["zone"].empty else ""
    top_ppe = violated_df["missed_ppe"].value_counts().idxmax() if not violated_df["missed_ppe"].empty else ""
    top_time = violated_df["time_slot"].astype(str).value_counts().idxmax() if not violated_df["time_slot"].empty else ""
    return {"compliance_rate": compliance_rate, "top_zone": top_zone, "top_ppe": top_ppe, "top_time": top_time}

def get_tbm_stats(df: pd.DataFrame) -> dict:
    if df.empty: return {"total_rows": 0, "risk_rows": 0, "not_worn_rows": 0, "normal_rows": 0}
    return {
        "total_rows": int(len(df)),
        "risk_rows": int((df["is_violated"] == 1).sum()),
        "not_worn_rows": int((df["is_violated"] == 1).sum()),
        "normal_rows": int((df["is_violated"] == 0).sum()),
    }

def get_tbm_checklist(df: pd.DataFrame) -> list[str]:
    violated_df = df[df["is_violated"] == 1]
    if violated_df.empty: return ["전일 위반 데이터가 없어 기본 PPE 점검만 수행하면 됩니다."]
    checklist = []
    top_zone = violated_df["zone"].value_counts().idxmax() if not violated_df["zone"].empty else ""
    top_ppe = violated_df["missed_ppe"].value_counts().idxmax() if not violated_df["missed_ppe"].empty else ""
    checklist.append(f"{top_zone} 작업 전 현장 순찰 및 집중 점검")
    checklist.append(f"{top_ppe} 착용 여부 출입 전 확인")
    checklist.append("작업 시작 전 작업자 대상 PPE 재안내")
    if "고소작업구역" in violated_df["zone"].values: checklist.append("고소작업 전 랜야드 체결 상태 재확인")
    if "절단작업구역" in violated_df["zone"].values: checklist.append("절단작업 전 장갑·안전모 착용 점검")
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
    if stats["total_rows"] == 0: return f"{target_date} 전일 데이터가 없어 기본 안전수칙 중심으로 TBM을 진행하면 됩니다."
    if kpis["top_zone"] is None:
        return f"{target_date} 전일 총 {stats['total_rows']}건의 작업 데이터가 기록되었고, 전반적 준수율은 {kpis['compliance_rate']}%였습니다. 전일 미착용 위반이 없어 오늘도 현재 수준을 유지하는 것이 중요합니다."
    return f"{target_date} 전일 총 {stats['total_rows']}건의 작업 데이터가 기록되었고, 준수율은 {kpis['compliance_rate']}%였습니다. 가장 취약한 구역은 {kpis['top_zone']}이며, 가장 많이 누락된 PPE는 {kpis['top_ppe']}였습니다. 특히 {kpis['top_time']}대 위반이 집중되어 오늘 TBM에서는 해당 시간대와 구역을 중심으로 점검이 필요합니다."

def get_tbm_focus_message(df: pd.DataFrame) -> str:
    violated_df = df[df["is_violated"] == 1]
    if violated_df.empty: return "전일 위반이 없어 오늘은 현재의 착용 수준을 유지하는 데 집중하세요."
    top_zone = violated_df["zone"].value_counts().idxmax() if not violated_df["zone"].empty else ""
    top_ppe = violated_df["missed_ppe"].value_counts().idxmax() if not violated_df["missed_ppe"].empty else ""
    return f"오늘은 {top_zone}에서 {top_ppe} 착용 여부를 최우선 관리사항으로 두고 작업 전 확인을 강화하세요."

def get_tbm_full_script(df: pd.DataFrame, target_date: str) -> str:
    briefing = get_tbm_briefing_text(df, target_date)
    checklist = get_tbm_checklist(df)
    focus = get_tbm_focus_message(df)
    checklist_text = " / ".join(checklist)
    return f"[전일 브리핑] {briefing}\n\n[오늘의 중점 관리사항] {focus}\n\n[현장 체크리스트] {checklist_text}"

# =========================
# 페이지 5 개선 / 인센티브
# =========================
def get_violation_series(df: pd.DataFrame) -> pd.Series:
    if "is_violated" in df.columns:
        v = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0)
        if v.sum() > 0: return v == 1
    if "missed_ppe" in df.columns:
        m = df["missed_ppe"].astype(str).str.strip().replace(["nan", "None", "NaN"], "")
        if (m != "").sum() > 0: return m != ""
    if "note" in df.columns:
        return df["note"].astype(str).str.contains("미흡")
    return pd.Series(False, index=df.index)

def calculate_weekly_compliance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["week", "compliance_rate"])
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_violation"] = get_violation_series(temp)
    temp["is_normal"] = ~temp["is_violation"]
    result = (temp.groupby("week_num")["is_normal"].apply(lambda x: round((x.sum() / len(x)) * 100, 2) if len(x) > 0 else 0.0).reset_index(name="compliance_rate").sort_values("week_num"))
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
import os
import re
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_FILE_PATH = DATA_DIR / "input_logs.csv"

INPUT_REQUIRED_COLUMNS = [
    "date", "time_slot", "site", "zone", "task_type",
    "missed_ppe", "is_violated", "team", "note",
]

# =========================
# 공통 / 페이지 1
# =========================
def load_logs(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def calculate_compliance_rate(df: pd.DataFrame) -> float:
    if df.empty: return 0.0
    compliant_count = (df["is_violated"] == 0).sum()
    return round((compliant_count / len(df)) * 100, 2)

def get_zone_risk_scores(df: pd.DataFrame) -> list[dict]:
    if df.empty or "zone" not in df.columns or "is_violated" not in df.columns: return []
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
        results.append({"zone": zone, "risk_score": min(100.0, risk_score)})
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

def get_weakest_zone(df: pd.DataFrame) -> dict:
    scores = get_zone_risk_scores(df)
    if not scores: return {"zone": None, "count": 0, "risk_score": 0.0}
    return {"zone": scores[0]["zone"], "count": float(scores[0]["risk_score"]), "risk_score": float(scores[0]["risk_score"])}

def get_most_missing_ppe(df: pd.DataFrame) -> dict:
    violated_df = df[df["is_violated"] == 1]
    if violated_df.empty: return {"missed_ppe": None, "count": 0}
    counts = violated_df["missed_ppe"].value_counts()
    return {"missed_ppe": counts.idxmax(), "count": int(counts.max())}

def get_priority_task(df: pd.DataFrame) -> dict:
    violated_df = df[df["is_violated"] == 1]
    if violated_df.empty: return {"time_slot": None, "zone": None, "text": None, "count": 0}
    combo = violated_df.groupby(["time_slot", "zone"]).size().sort_values(ascending=False)
    time_slot, zone = combo.index[0]
    return {"time_slot": time_slot, "zone": zone, "text": f"{time_slot} {zone}", "count": int(combo.iloc[0])}

def get_today_date_str() -> str:
    return str(date.today())

def filter_by_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    return df[df["date"] == target_date].copy()

def get_hourly_violations(df: pd.DataFrame) -> list[dict]:
    violated_df = df[df["is_violated"] == 1]
    counts = violated_df["time_slot"].value_counts().to_dict()
    return [{"time_slot": slot, "count": int(counts.get(slot, 0))} for slot in ["오전", "점심직후", "오후"]]

def get_safety_point(df: pd.DataFrame) -> str:
    v_df = df[df["is_violated"] == 1]
    if v_df.empty: return "오늘은 위반 데이터가 없어 전반적으로 양호합니다."
    combo = v_df.groupby(["time_slot", "zone", "missed_ppe"]).size().sort_values(ascending=False)
    t, z, p = combo.index[0]
    return f"{t} {z}에서 {p} 미착용이 증가했습니다."

def get_safety_points(df: pd.DataFrame) -> list[str]:
    v_df = df[df["is_violated"] == 1]
    if v_df.empty: return ["오늘은 위반 데이터가 없어 전반적으로 양호합니다."]
    combo = v_df.groupby(["time_slot", "zone", "missed_ppe"]).size().sort_values(ascending=False)
    return [f"{t} {z}에서 {p} 미착용이 증가했습니다." for (t, z, p), _ in combo.head(3).items()]

# =========================
# 페이지 2 입력/업로드 공통
# =========================
def normalize_input_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {"Date": "date", "Time_Slot": "time_slot", "TimeSlot": "time_slot", "Site": "site", "Zone": "zone", "Task_Type": "task_type", "TaskType": "task_type", "Missed_PPE": "missed_ppe", "MissedPPE": "missed_ppe", "PPE_Type": "missed_ppe", "PPEType": "missed_ppe", "Is_Violated": "is_violated", "IsViolated": "is_violated", "Risk_Exposure": "is_violated", "RiskExposure": "is_violated", "Team": "team", "Note": "note"}
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

def validate_input_columns(df: pd.DataFrame) -> dict:
    missing = [c for c in INPUT_REQUIRED_COLUMNS if c not in df.columns]
    return {"is_valid": len(missing) == 0, "missing_columns": missing}

def calculate_input_summary(df: pd.DataFrame, today_str: str) -> dict:
    if df.empty: return {"total_rows": 0, "today_rows": 0, "risk_rows": 0, "not_worn_rows": 0, "normal_rows": 0}
    return {
        "total_rows": int(len(df)),
        "today_rows": int(len(df[df["date"] == today_str])),
        "risk_rows": int((df["is_violated"] == 1).sum()),
        "not_worn_rows": int((df["is_violated"] == 1).sum()),
        "normal_rows": int((df["is_violated"] == 0).sum()),
    }

def get_input_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    if df.empty: return []
    return df.tail(n).iloc[::-1].fillna("").to_dict(orient="records")

def append_manual_entry(entry: dict) -> dict:
    try:
        df = pd.read_csv("data/input_logs.csv") if os.path.exists("data/input_logs.csv") else pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
        df.to_csv("data/input_logs.csv", index=False)
        return {"status": "success", "message": "수동 입력 데이터가 저장되었습니다."}
    except Exception as e:
        return {"status": "error", "message": f"저장 실패: {str(e)}"}

# =========================
# 페이지 3 분석 상세
# =========================
def filter_input_data(df: pd.DataFrame, start_date=None, end_date=None, site=None, zone=None, task_type=None, ppe_type=None, risk_exposure=None) -> pd.DataFrame:
    if df.empty: return df.copy()
    f_df = df.copy()
    if start_date: f_df = f_df[f_df["date"] >= str(start_date)]
    if end_date: f_df = f_df[f_df["date"] <= str(end_date)]
    if site: f_df = f_df[f_df["site"] == str(site)]
    if zone: f_df = f_df[f_df["zone"] == str(zone)]
    if task_type: f_df = f_df[f_df["task_type"] == str(task_type)]
    if ppe_type: f_df = f_df[f_df["missed_ppe"] == str(ppe_type)]
    if risk_exposure is not None:
        risk_val = 1 if str(risk_exposure) in ["1", "O"] else 0
        f_df = f_df[f_df["is_violated"] == risk_val]
    return f_df

def get_analysis_kpis(df: pd.DataFrame) -> dict:
    if df.empty: return {"top_time": "-", "top_zone": "-", "top_task_type": "-", "top_ppe": "-"}
    return {
        "top_time": df["time_slot"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["time_slot"].replace("", pd.NA).dropna().empty else "-",
        "top_zone": df["zone"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["zone"].replace("", pd.NA).dropna().empty else "-",
        "top_task_type": df["task_type"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["task_type"].replace("", pd.NA).dropna().empty else "-",
        "top_ppe": df["missed_ppe"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["missed_ppe"].replace("", pd.NA).dropna().empty else "-",
    }

# 💡 [핵심] 퍼센트(%) 계산 로직으로 업그레이드 된 구역별 차트 함수!
def get_analysis_charts(df: pd.DataFrame) -> dict:
    if df.empty: return {"time_chart": [], "ppe_chart": [], "zone_chart": [], "task_chart": []}
    
    t_counts = df["time_slot"].replace("", pd.NA).dropna().value_counts()
    order = {"오전": 1, "점심직후": 2, "오후": 3}
    time_chart = [{"label": str(k), "count": int(v)} for k, v in sorted(t_counts.items(), key=lambda x: order.get(str(x[0]), 999))]
    
    p_counts = df["missed_ppe"].replace("", pd.NA).dropna().value_counts()
    ppe_chart = [{"label": str(k), "count": int(v)} for k, v in p_counts.items()]
    
    task_counts = df["task_type"].replace("", pd.NA).dropna().value_counts()
    task_chart = [{"label": str(k), "count": int(v)} for k, v in task_counts.items()]

    zone_chart = []
    temp_z = df[df["zone"].astype(str).str.strip() != ""].copy()
    if not temp_z.empty:
        for z, group in temp_z.groupby("zone"):
            total = len(group)
            viol_count = int(group["is_violated"].sum())
            if total > 0:
                risk_rate = round((viol_count / total) * 100, 1)
                comp_rate = round(100.0 - risk_rate, 1)
            else:
                risk_rate, comp_rate = 0.0, 0.0
            zone_chart.append({"label": str(z), "count": viol_count, "compliance_rate": comp_rate, "risk_rate": risk_rate})

    return {"time_chart": time_chart, "ppe_chart": ppe_chart, "zone_chart": zone_chart, "task_chart": task_chart}

def get_recommend_action(df: pd.DataFrame) -> str:
    if df.empty: return "현재 필터 조건에서 뚜렷한 위반 패턴이 없어 기본 점검을 유지하세요."
    top_z = df["zone"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["zone"].replace("", pd.NA).dropna().empty else "-"
    top_t = df["task_type"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["task_type"].replace("", pd.NA).dropna().empty else "-"
    top_p = df["missed_ppe"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["missed_ppe"].replace("", pd.NA).dropna().empty else "-"
    
    if top_p != "-" and top_t != "-": return f"{top_t} 작업 전 {top_p} 착용 여부를 우선 점검하세요."
    if top_z != "-": return f"{top_z} 구역 반복 패턴을 우선 점검하세요."
    return "반복 위반 상위 조건을 우선 점검하세요."

# =========================
# 페이지 5 계산용 유틸리티 (에러 방지)
# =========================
def get_violation_series(df: pd.DataFrame) -> pd.Series:
    if "is_violated" in df.columns:
        return pd.to_numeric(df["is_violated"], errors="coerce").fillna(0) == 1
    return pd.Series(False, index=df.index)
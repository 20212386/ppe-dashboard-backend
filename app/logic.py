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
        violation_count = (zone_df["is_violated"] == 1).sum()
        
        # 💡 [핵심 수술 완료] 분모 통일 (최소 10명 보정)
        # 구역에 사람이 1~2명뿐이어도 무조건 최소 10명으로 나눠서 100%로 튀는 걸 막습니다!
        smoothed_total = max(zone_total, 10)
        
        risk_score = 0.0 if zone_total == 0 else round((violation_count / smoothed_total) * 100, 2)
        results.append({"zone": zone, "risk_score": min(100.0, risk_score)})
        
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

def get_weakest_zone(df: pd.DataFrame) -> dict:
    scores = get_zone_risk_scores(df)
    if not scores: return {"zone": None, "count": 0, "risk_score": 0.0}
    return {"zone": scores[0]["zone"], "count": float(scores[0]["risk_score"]), "risk_score": float(scores[0]["risk_score"])}

def get_most_missing_ppe(df: pd.DataFrame) -> dict:
    v_df = df[df["is_violated"] == 1]
    if v_df.empty: return {"missed_ppe": None, "count": 0}
    counts = v_df["missed_ppe"].value_counts()
    return {"missed_ppe": counts.idxmax(), "count": int(counts.max())}

def get_priority_task(df: pd.DataFrame) -> dict:
    v_df = df[df["is_violated"] == 1]
    if v_df.empty: return {"time_slot": None, "zone": None, "text": None, "count": 0}
    combo = v_df.groupby(["time_slot", "zone"]).size().sort_values(ascending=False)
    return {"time_slot": combo.index[0][0], "zone": combo.index[0][1], "text": f"{combo.index[0][0]} {combo.index[0][1]}", "count": int(combo.iloc[0])}

def get_today_date_str() -> str:
    return str(date.today())

def filter_by_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    return df[df["date"] == target_date].copy()

def get_hourly_violations(df: pd.DataFrame) -> list[dict]:
    counts = df[df["is_violated"] == 1]["time_slot"].value_counts().to_dict()
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
# 페이지 2 & 입력 공통
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

def normalize_uploaded_df(df: pd.DataFrame) -> pd.DataFrame: return normalize_input_df(df)
def validate_input_columns(df: pd.DataFrame) -> dict:
    missing = [c for c in INPUT_REQUIRED_COLUMNS if c not in df.columns]
    return {"is_valid": len(missing) == 0, "missing_columns": missing}
def validate_required_columns(df: pd.DataFrame) -> dict: return validate_input_columns(df)

# 💡 4페이지 통계 에러 방지 (완벽한 is_violated 동기화)
def calculate_input_summary(df: pd.DataFrame, today_str: str) -> dict:
    if df.empty: return {"total_rows": 0, "today_rows": 0, "risk_rows": 0, "not_worn_rows": 0, "normal_rows": 0}
    total = len(df)
    viol = int((df["is_violated"] == 1).sum())
    return {
        "total_rows": total,
        "today_rows": int(len(df[df["date"] == today_str])),
        "risk_rows": viol,
        "not_worn_rows": viol,
        "normal_rows": total - viol
    }

def calculate_data_summary(df: pd.DataFrame, today_str: str | None = None) -> dict:
    return calculate_input_summary(df, today_str or get_today_date_str())

def calculate_input_quality(df: pd.DataFrame) -> dict:
    if df.empty: return {"completeness_rate": 0, "validity_rate": 0, "duplicate_count": 0, "error_count": 0}
    req = ["date", "time_slot", "site", "zone", "task_type", "is_violated"]
    filled = df[req].replace("", pd.NA).notna().sum().sum()
    comp = round((filled / (len(df) * len(req))) * 100, 2) if len(df) > 0 else 0
    return {"completeness_rate": comp, "validity_rate": 100, "duplicate_count": int(df.duplicated().sum()), "error_count": 0}

def calculate_quality_metrics(df: pd.DataFrame) -> dict: return calculate_input_quality(df)
def get_input_preview(df: pd.DataFrame, n: int = 10) -> list[dict]: return df.tail(n).iloc[::-1].fillna("").to_dict(orient="records") if not df.empty else []
def get_recent_preview(df: pd.DataFrame, n: int = 10) -> list[dict]: return get_input_preview(df, n)

def load_input_logs() -> pd.DataFrame:
    if not INPUT_FILE_PATH.exists(): return pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)
    df = normalize_input_df(pd.read_csv(INPUT_FILE_PATH))
    return df if validate_input_columns(df)["is_valid"] else pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)

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
        r_val = 1 if str(risk_exposure) in ["1", "O"] else 0
        f_df = f_df[f_df["is_violated"] == r_val]
    return f_df

def get_analysis_kpis(df: pd.DataFrame) -> dict:
    if df.empty: return {"top_time": "-", "top_zone": "-", "top_task_type": "-", "top_ppe": "-"}
    return {
        "top_time": df["time_slot"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["time_slot"].replace("", pd.NA).dropna().empty else "-",
        "top_zone": df["zone"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["zone"].replace("", pd.NA).dropna().empty else "-",
        "top_task_type": df["task_type"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["task_type"].replace("", pd.NA).dropna().empty else "-",
        "top_ppe": df["missed_ppe"].replace("", pd.NA).dropna().value_counts().idxmax() if not df["missed_ppe"].replace("", pd.NA).dropna().empty else "-",
    }

def get_analysis_charts(df: pd.DataFrame) -> dict:
    t_cats = ["오전", "점심직후", "오후"]
    p_cats = ["안전모", "랜야드", "장갑"]
    z_cats = ["고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"]
    tm_cats = ["A팀", "B팀", "C팀", "D팀"]
    tsk_cats = ["고소작업", "절단작업", "자재운반", "설비점검"]

    if df.empty:
        return {
            "time_chart": [{"label": c, "count": 0} for c in t_cats],
            "ppe_chart": [{"label": c, "count": 0} for c in p_cats],
            "zone_chart": [
                {"label": c, "count": 0, "compliance_rate": 0.0, "risk_rate": 0.0}
                for c in z_cats
            ],
            "task_chart": [{"label": c, "count": 0} for c in tsk_cats],
            "team_chart": [{"label": c, "count": 0} for c in tm_cats],
        }

    # 1) 시간대 차트
    t_counts = (
        df["time_slot"].replace("", pd.NA).dropna().value_counts()
        if "time_slot" in df.columns else {}
    )
    time_chart = [{"label": c, "count": int(t_counts.get(c, 0))} for c in t_cats]

    # 2) PPE 차트
    p_counts = (
        df["missed_ppe"].replace("", pd.NA).dropna().value_counts()
        if "missed_ppe" in df.columns else {}
    )
    ppe_chart = [{"label": c, "count": int(p_counts.get(c, 0))} for c in p_cats]

    # 3) 작업유형 차트
    task_counts = (
        df["task_type"].replace("", pd.NA).dropna().value_counts()
        if "task_type" in df.columns else {}
    )
    task_chart = [{"label": c, "count": int(task_counts.get(c, 0))} for c in tsk_cats]

    # 4) 팀 차트
    team_counts = (
        df["team"].replace("", pd.NA).dropna().value_counts()
        if "team" in df.columns else {}
    )
    team_chart = [{"label": c, "count": int(team_counts.get(c, 0))} for c in tm_cats]

    # 5) 구역별 준수율 / 위험도 차트
    zone_chart = []
    if "zone" in df.columns and "is_violated" in df.columns:
        temp_z = df.copy()
        temp_z["zone"] = temp_z["zone"].astype(str).str.strip()

        for z in z_cats:
            group = temp_z[temp_z["zone"] == z]
            total = len(group)
            viol = int((group["is_violated"] == 1).sum())

            # 표본이 너무 적을 때 100%로 튀는 것 완화
            smoothed_total = max(total, 10)

            if total > 0:
                risk_rate = round((viol / smoothed_total) * 100, 1)
                compliance_rate = round(100.0 - risk_rate, 1)
            else:
                risk_rate = 0.0
                compliance_rate = 0.0

            zone_chart.append({
                "label": z,
                "count": viol,
                "compliance_rate": compliance_rate,
                "risk_rate": risk_rate
            })
    else:
        zone_chart = [
            {"label": c, "count": 0, "compliance_rate": 0.0, "risk_rate": 0.0}
            for c in z_cats
        ]

    return {
        "time_chart": time_chart,
        "ppe_chart": ppe_chart,
        "zone_chart": zone_chart,
        "task_chart": task_chart,
        "team_chart": team_chart,
    }


def get_recommend_action(df: pd.DataFrame) -> str:
    if df.empty:
        return "현재 필터 조건에서 뚜렷한 위반 패턴이 없어 기본 점검을 유지하세요."

    top_zone = (
        df["zone"].replace("", pd.NA).dropna().value_counts().idxmax()
        if "zone" in df.columns and not df["zone"].replace("", pd.NA).dropna().empty
        else "-"
    )
    top_task = (
        df["task_type"].replace("", pd.NA).dropna().value_counts().idxmax()
        if "task_type" in df.columns and not df["task_type"].replace("", pd.NA).dropna().empty
        else "-"
    )
    top_ppe = (
        df["missed_ppe"].replace("", pd.NA).dropna().value_counts().idxmax()
        if "missed_ppe" in df.columns and not df["missed_ppe"].replace("", pd.NA).dropna().empty
        else "-"
    )
    top_team = (
        df["team"].replace("", pd.NA).dropna().value_counts().idxmax()
        if "team" in df.columns and not df["team"].replace("", pd.NA).dropna().empty
        else "-"
    )

    if top_team != "-" and top_ppe != "-":
        return f"{top_team}의 {top_ppe} 착용 여부를 우선 점검하세요."

    if top_task != "-" and top_ppe != "-":
        return f"{top_task} 작업 전 {top_ppe} 착용 여부를 우선 점검하세요."

    if top_zone != "-":
        return f"{top_zone} 구역 반복 패턴을 우선 점검하세요."

    return "반복 위반 상위 조건을 우선 점검하세요."

# =========================
# 페이지 4 TBM
# =========================
def get_yesterday_date_str() -> str:
    return str(datetime.today().date() - timedelta(days=1))

def get_tbm_kpis(df: pd.DataFrame) -> dict:
    if df.empty: return {"compliance_rate": 0.0, "top_zone": None, "top_ppe": None, "top_time": None}
    tot = len(df)
    norm = (df["is_violated"] == 0).sum()
    c_rate = round((norm / tot) * 100, 2) if tot > 0 else 0.0
    v_df = df[df["is_violated"] == 1]
    if v_df.empty: return {"compliance_rate": c_rate, "top_zone": None, "top_ppe": None, "top_time": None}
    return {
        "compliance_rate": c_rate,
        "top_zone": v_df["zone"].replace("", pd.NA).dropna().value_counts().idxmax() if not v_df["zone"].replace("", pd.NA).dropna().empty else "",
        "top_ppe": v_df["missed_ppe"].replace("", pd.NA).dropna().value_counts().idxmax() if not v_df["missed_ppe"].replace("", pd.NA).dropna().empty else "",
        "top_time": v_df["time_slot"].replace("", pd.NA).dropna().value_counts().idxmax() if not v_df["time_slot"].replace("", pd.NA).dropna().empty else ""
    }

# 💡 페이지 4 하단 통계 완벽 동기화!
def get_tbm_stats(df: pd.DataFrame) -> dict:
    if df.empty: return {"total_rows": 0, "risk_rows": 0, "not_worn_rows": 0, "normal_rows": 0}
    total = int(len(df))
    viol = int((df["is_violated"] == 1).sum())
    return {"total_rows": total, "risk_rows": viol, "not_worn_rows": viol, "normal_rows": total - viol}

def get_tbm_checklist(df: pd.DataFrame) -> list[str]:
    v_df = df[df["is_violated"] == 1]
    if v_df.empty: return ["전일 위반 데이터가 없어 기본 PPE 점검만 수행하면 됩니다."]
    chk = []
    z = v_df["zone"].replace("", pd.NA).dropna().value_counts().idxmax() if not v_df["zone"].replace("", pd.NA).dropna().empty else ""
    p = v_df["missed_ppe"].replace("", pd.NA).dropna().value_counts().idxmax() if not v_df["missed_ppe"].replace("", pd.NA).dropna().empty else ""
    chk.extend([f"{z} 작업 전 현장 순찰 및 집중 점검", f"{p} 착용 여부 출입 전 확인", "작업 시작 전 작업자 대상 PPE 재안내"])
    if "고소작업구역" in v_df["zone"].values: chk.append("고소작업 전 랜야드 체결 상태 재확인")
    if "절단작업구역" in v_df["zone"].values: chk.append("절단작업 전 장갑·안전모 착용 점검")
    return list(dict.fromkeys(chk))[:5]

def get_tbm_briefing_text(df: pd.DataFrame, target_date: str) -> str:
    k = get_tbm_kpis(df)
    s = get_tbm_stats(df)
    if s["total_rows"] == 0: return f"{target_date} 전일 데이터가 없어 기본 안전수칙 중심으로 진행합니다."
    if k["top_zone"] is None: return f"{target_date} 전일 총 {s['total_rows']}건, 준수율 {k['compliance_rate']}%. 위반 내역이 없어 현재 수준을 유지합니다."
    return f"{target_date} 전일 총 {s['total_rows']}건, 준수율 {k['compliance_rate']}%. 취약 구역은 {k['top_zone']}이며, 가장 많이 누락된 PPE는 {k['top_ppe']}입니다. 특히 {k['top_time']}대 위반이 집중되어 해당 시간대 점검이 필요합니다."

def get_tbm_focus_message(df: pd.DataFrame) -> str:
    v_df = df[df["is_violated"] == 1]
    if v_df.empty: return "위반이 없어 오늘은 현재 착용 수준 유지에 집중하세요."
    z = v_df["zone"].replace("", pd.NA).dropna().value_counts().idxmax() if not v_df["zone"].replace("", pd.NA).dropna().empty else ""
    p = v_df["missed_ppe"].replace("", pd.NA).dropna().value_counts().idxmax() if not v_df["missed_ppe"].replace("", pd.NA).dropna().empty else ""
    return f"오늘은 {z}에서 {p} 착용 여부를 최우선 관리사항으로 두고 작업 전 확인을 강화하세요."

def get_tbm_full_script(df: pd.DataFrame, target_date: str) -> str:
    return f"[전일 브리핑] {get_tbm_briefing_text(df, target_date)}\n\n[오늘의 중점 관리사항] {get_tbm_focus_message(df)}\n\n[현장 체크리스트] {' / '.join(get_tbm_checklist(df))}"

# =========================
# 페이지 5 개선 / 인센티브 (정렬 및 스마트 증감 로직 추가!)
# =========================
def get_violation_series(df: pd.DataFrame) -> pd.Series:
    if "is_violated" in df.columns: return pd.to_numeric(df["is_violated"], errors="coerce").fillna(0) == 1
    return pd.Series(False, index=df.index)

def calculate_weekly_compliance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["week", "compliance_rate"])
    t = df.copy()
    t["week_num"] = pd.to_datetime(t["date"], errors='coerce').dt.isocalendar().week.astype(int)
    t["is_normal"] = ~get_violation_series(t)
    res = t.groupby("week_num")["is_normal"].apply(lambda x: round((x.sum() / len(x)) * 100, 2) if len(x) > 0 else 0.0).reset_index(name="compliance_rate").sort_values("week_num")
    res["week"] = res["week_num"].astype(str) + "주차"
    return res[["week", "compliance_rate"]]

def calculate_weekly_violation_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["week", "violation_count"])
    t = df.copy()
    t["week_num"] = pd.to_datetime(t["date"], errors='coerce').dt.isocalendar().week.astype(int)
    t["is_violation"] = get_violation_series(t).astype(int)
    res = t.groupby("week_num")["is_violation"].sum().reset_index(name="violation_count").sort_values("week_num")
    res["week"] = res["week_num"].astype(str) + "주차"
    return res[["week", "violation_count"]]

def calculate_weekly_ppe_missed_counts(df: pd.DataFrame) -> pd.DataFrame: return calculate_weekly_violation_counts(df).rename(columns={"violation_count": "ppe_missed_count"})

# 💡 A팀, B팀 예쁘게 알파벳 정렬! (sorted 추가)
def get_team_comparison_chart(df: pd.DataFrame) -> list[dict]:
    if df.empty or "team" not in df.columns: return []
    t = df.copy()
    t["week_num"] = pd.to_datetime(t["date"], errors='coerce').dt.isocalendar().week.astype(int)
    t["is_normal"] = ~get_violation_series(t)
    res = []
    for team in sorted(t["team"].replace("", pd.NA).dropna().unique()):
        t_df = t[t["team"] == team]
        t_weeks = sorted(t_df["week_num"].unique())
        if len(t_weeks) < 2: continue
        f_df, l_df = t_df[t_df["week_num"] == t_weeks[0]], t_df[t_df["week_num"] == t_weeks[-1]]
        res.append({
            "team": str(team),
            "initial_rate": round((f_df["is_normal"].sum() / len(f_df)) * 100, 2) if len(f_df) > 0 else 0,
            "current_rate": round((l_df["is_normal"].sum() / len(l_df)) * 100, 2) if len(l_df) > 0 else 0
        })
    return res

# 💡 마이너스면 '증가', 플러스면 '감소'로 똑똑하게 출력!
def get_team_incentive_summary(df: pd.DataFrame) -> list[str]:
    if df.empty or "team" not in df.columns: return ["팀 데이터가 없습니다."]
    t = df.copy()
    t["week_num"] = pd.to_datetime(t["date"], errors='coerce').dt.isocalendar().week.astype(int)
    t["is_violation"], t["is_normal"] = get_violation_series(t), ~get_violation_series(t)
    sums = []
    for team in sorted(t["team"].replace("", pd.NA).dropna().unique()):
        t_df = t[t["team"] == team]
        t_weeks = sorted(t_df["week_num"].unique())
        if len(t_weeks) < 2: continue
        f_df, l_df = t_df[t_df["week_num"] == t_weeks[0]], t_df[t_df["week_num"] == t_weeks[-1]]
        f_rate = round((f_df["is_normal"].sum() / len(f_df)) * 100, 2) if len(f_df) > 0 else 0
        l_rate = round((l_df["is_normal"].sum() / len(l_df)) * 100, 2) if len(l_df) > 0 else 0
        f_miss, l_miss = int(f_df["is_violation"].sum()), int(l_df["is_violation"].sum())
        
        reduction = round(((f_miss - l_miss) / f_miss) * 100, 2) if f_miss > 0 else 0.0
        trend = f"{abs(reduction)}% 증가 🚨" if reduction < 0 else f"{reduction}% 감소 📉"
        sums.append(f"{team}: 초기 준수율 {f_rate}% → 현재 {l_rate}%, PPE 누락 {trend}")
    return sums if sums else ["비교 가능한 팀 데이터가 부족합니다."]

def get_improvement_metrics(df: pd.DataFrame) -> dict:
    w_comp = calculate_weekly_compliance(df)
    w_viol = calculate_weekly_violation_counts(df)
    w_ppe = calculate_weekly_ppe_missed_counts(df)
    team_chart = get_team_comparison_chart(df)
    best_team = max(team_chart, key=lambda x: x["current_rate"] - x["initial_rate"])["team"] if team_chart else "-"
    
    if len(w_comp) < 2: return {"improvement_rate": 0.0, "repeat_ppe_reduction_rate": 0.0, "risk_recurrence_reduction_rate": 0.0, "best_team": best_team}
    
    first_ppe = int(w_ppe.iloc[0]["ppe_missed_count"]) if not w_ppe.empty else 0
    last_ppe = int(w_ppe.iloc[-1]["ppe_missed_count"]) if not w_ppe.empty else 0
    first_viol = int(w_viol.iloc[0]["violation_count"]) if not w_viol.empty else 0
    last_viol = int(w_viol.iloc[-1]["violation_count"]) if not w_viol.empty else 0

    return {
        "improvement_rate": round(float(w_comp.iloc[-1]["compliance_rate"]) - float(w_comp.iloc[0]["compliance_rate"]), 2),
        "repeat_ppe_reduction_rate": round(((first_ppe - last_ppe) / first_ppe) * 100, 2) if first_ppe > 0 else 0.0,
        "risk_recurrence_reduction_rate": round(((first_viol - last_viol) / first_viol) * 100, 2) if first_viol > 0 else 0.0,
        "best_team": best_team
    }

def get_weekly_trend_charts(df: pd.DataFrame) -> dict:
    return {
        "violation_trend_chart": calculate_weekly_violation_counts(df).rename(columns={"week": "label", "violation_count": "count"}).to_dict(orient="records"),
        "ppe_trend_chart": calculate_weekly_ppe_missed_counts(df).rename(columns={"week": "label", "ppe_missed_count": "count"}).to_dict(orient="records")
    }
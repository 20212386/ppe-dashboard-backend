from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
from io import StringIO

from app.logic import (
    load_logs,
    calculate_compliance_rate,
    get_weakest_zone,
    get_most_missing_ppe,
    get_priority_task,
    get_today_date_str,
    filter_by_date,
    get_hourly_violations,
    get_zone_risk_scores,
    get_safety_points,
    load_input_logs,
    normalize_input_df,
    validate_input_columns,
    calculate_input_summary,
    calculate_input_quality,
    get_input_preview,
    append_manual_entry,
    filter_input_data,
    get_analysis_kpis,
    get_analysis_charts,
    get_recommend_action,
    get_yesterday_date_str,
    get_tbm_kpis,
    get_tbm_stats,
    get_tbm_checklist,
    get_tbm_briefing_text,
    get_tbm_focus_message,
    get_tbm_full_script,
    get_improvement_metrics,
    get_weekly_trend_charts,
    get_team_comparison_chart,
    get_team_incentive_summary,
)

app = FastAPI(title="PPE Dashboard Backend")

DATA_FILE_PATH = "app/data/sample_logs.csv"


class ManualEntry(BaseModel):
    date: str
    time: str
    worker_id: str
    team: str
    zone: str
    task_type: str
    ppe_type: str
    worn: str
    risk_exposure: str
    note: str = ""


@app.get("/")
def root():
    return {"message": "PPE Dashboard Backend Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard/test-summary")
def test_summary():
    df = load_logs(DATA_FILE_PATH)

    compliance_rate = calculate_compliance_rate(filtered_df)
    weakest_zone = get_weakest_zone(filtered_df)
    most_missing_ppe = get_most_missing_ppe(df)
    priority_task = get_priority_task(df)

    return {
        "compliance_rate": compliance_rate,
        "weakest_zone": weakest_zone,
        "most_missing_ppe": most_missing_ppe,
        "priority_task": priority_task,
    }


@app.get("/dashboard/today")
def today_dashboard(
    target_date: str | None = None,
    site: str | None = None,
):
    df = load_logs(DATA_FILE_PATH)

    selected_date = target_date if target_date else get_today_date_str()
    filtered_df = filter_by_date(df, selected_date)

    if "site" in filtered_df.columns:
        filtered_df["site"] = filtered_df["site"].astype(str).str.strip()

    if site and site != "전체 현장" and "site" in filtered_df.columns:
        selected_site = (
            str(site)
            .strip()
            .replace("현장 1", "현장1")
            .replace("현장 2", "현장2")
            .replace("현장 3", "현장3")
        )
        filtered_df = filtered_df[filtered_df["site"] == selected_site].copy()

    compliance_rate = calculate_compliance_rate(filtered_df)
    weakest_zone = get_weakest_zone(filtered_df)
    most_missing_ppe = get_most_missing_ppe(filtered_df)
    priority_task = get_priority_task(filtered_df)

    hourly_violations = get_hourly_violations(filtered_df)
    zone_risk_scores = get_zone_risk_scores(filtered_df)
    safety_points = get_safety_points(filtered_df)

    weakest_zone_score = 0
    if zone_risk_scores and weakest_zone.get("zone"):
        for item in zone_risk_scores:
            if item["zone"] == weakest_zone["zone"]:
                weakest_zone_score = item["risk_score"]
                break

    return {
        "date": selected_date,
        "site": site if site else "전체 현장",
        "kpi": {
            "compliance_rate": compliance_rate,
            "compliance_rate_text": f"{compliance_rate}%",
            "weakest_zone_name": weakest_zone["zone"] if weakest_zone.get("zone") else "-",
            "weakest_zone_score": weakest_zone_score,
            "most_missing_ppe_name": most_missing_ppe["missed_ppe"] if most_missing_ppe.get("missed_ppe") else "-",
            "most_missing_ppe_count": most_missing_ppe["count"],
            "priority_task_text": priority_task["text"] if priority_task.get("text") else "-",
        },
        "charts": {
            "hourly_violations": hourly_violations,
            "zone_risk_scores": zone_risk_scores,
        },
        "safety_points": safety_points,
    }


@app.post("/data/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다.")

    content = await file.read()

    try:
        decoded = content.decode("utf-8-sig")
        df = pd.read_csv(StringIO(decoded))
        df = normalize_input_df(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV 읽기 실패: {e}")

    validation = validate_input_columns(df)
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"필수 컬럼 누락: {validation['missing_columns']}"
        )

    df.to_csv("app/data/input_logs.csv", index=False, encoding="utf-8-sig")

    return {
        "message": "CSV 업로드 완료",
        "file_name": file.filename,
        "rows": int(len(df)),
    }


@app.get("/data/summary")
def data_summary():
    df = load_input_logs()
    today_str = get_today_date_str()

    return {
        "date": today_str,
        "summary": calculate_input_summary(df, today_str),
        "quality": calculate_input_quality(df),
    }


@app.get("/data/preview")
def data_preview():
    df = load_input_logs()
    preview = get_input_preview(df, 10)

    return {
        "count": len(preview),
        "rows": preview,
    }


@app.post("/data/manual-entry")
def save_manual_entry(entry: ManualEntry):
    row = {
    "date": entry.date,
    "time": entry.time,
    "worker_id": entry.worker_id,
    "team": entry.team,
    "zone": entry.zone,
    "task_type": entry.task_type,
    "ppe_type": entry.ppe_type,
    "worn": entry.worn,
    "risk_exposure": entry.risk_exposure,
    "note": entry.note,
}

    append_manual_entry(row)

    return {
        "message": "수기 입력 저장 완료",
        "saved": row,
    }

@app.get("/analysis/detail")
def analysis_detail(
    start_date: str | None = None,
    end_date: str | None = None,
    zone: str | None = None,
    task_type: str | None = None,
    ppe_type: str | None = None,
    risk_exposure: str | None = None,
):
    df = load_input_logs()

    filtered_df = filter_input_data(
        df,
        start_date=start_date,
        end_date=end_date,
        zone=zone,
        task_type=task_type,
        ppe_type=ppe_type,
        risk_exposure=risk_exposure,
    )

    kpis = get_analysis_kpis(filtered_df)
    charts = get_analysis_charts(filtered_df)
    recommend_action = get_recommend_action(filtered_df)

    return {
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "zone": zone,
            "task_type": task_type,
            "ppe_type": ppe_type,
            "risk_exposure": risk_exposure,
        },
        "count": int(len(filtered_df)),
        "kpis": kpis,
        "charts": charts,
        "recommend_action": recommend_action,
    }

@app.get("/report/tbm")
def report_tbm(target_date: str | None = None):
    df = load_logs(DATA_FILE_PATH)

    # 사용자가 날짜를 고르면 그 날짜 기준,
    # 안 고르면 오늘 기준으로 동작
    selected_date = target_date if target_date else get_today_date_str()

    day_df = filter_by_date(df, selected_date)

    compliance_rate = calculate_compliance_rate(day_df)
    weakest_zone = get_weakest_zone(day_df)
    most_missing_ppe = get_most_missing_ppe(day_df)

    hourly_violations = get_hourly_violations(day_df)
    top_time = "-"
    if hourly_violations:
        top_time = max(hourly_violations, key=lambda x: x["count"])["time_slot"]

    total_rows = len(day_df)
    risk_rows = int((day_df["risk_exposure"] == "O").sum()) if "risk_exposure" in day_df.columns else 0
    not_worn_rows = int((day_df["worn"] == "X").sum()) if "worn" in day_df.columns else 0
    normal_rows = total_rows - not_worn_rows

    top_zone = weakest_zone["zone"] if weakest_zone and weakest_zone.get("zone") else "-"
    top_ppe = most_missing_ppe["missed_ppe"] if most_missing_ppe and most_missing_ppe.get("missed_ppe") else "-"

    if total_rows == 0:
        briefing_text = f"{selected_date} 기준 데이터가 없어 기본 안전수칙 중심으로 TBM을 진행하면 됩니다."
        checklist = [
            "기본 PPE 착용 상태 확인",
            "고소작업 전 랜야드 점검",
            "절단작업 전 장갑 착용 확인",
        ]
        focus_message = "입력 데이터가 없으므로 기본 안전수칙 재확인과 현장 순찰에 집중하세요."
    else:
        briefing_text = (
            f"{selected_date} 총 {total_rows}건의 작업 데이터가 기록되었고, "
            f"PPE 준수율은 {compliance_rate}%입니다. "
            f"가장 취약한 구역은 {top_zone}이며, "
            f"가장 많이 누락된 PPE는 {top_ppe}입니다. "
            f"특히 {top_time} 시간대 위반이 집중되어 해당 시간대 집중 점검이 필요합니다."
        )

        checklist = []
        if top_zone != "-":
            checklist.append(f"{top_zone} 작업 전 현장 순찰 및 집중 점검")
        if top_ppe != "-":
            checklist.append(f"{top_ppe} 착용 여부 작업 시작 전 재확인")
        if top_time != "-":
            checklist.append(f"{top_time} 시간대 집중 순찰 실시")
        checklist.append("작업 시작 전 작업자 대상 PPE 재안내")

        focus_message = (
            f"오늘은 {top_zone}에서 {top_ppe} 착용 여부를 우선 관리하고, "
            f"{top_time} 시간대 현장 점검을 강화하세요."
        )

    full_script = (
        f"[브리핑 기준일] {selected_date}\n\n"
        f"[핵심 브리핑]\n{briefing_text}\n\n"
        f"[오늘의 중점 관리사항]\n{focus_message}\n\n"
        f"[현장 체크리스트]\n- " + "\n- ".join(checklist)
    )

    return {
        "date": selected_date,
        "kpis": {
            "compliance_rate": compliance_rate,
            "top_zone": top_zone,
            "top_ppe": top_ppe,
            "top_time": top_time,
        },
        "stats": {
            "total_rows": total_rows,
            "risk_rows": risk_rows,
            "not_worn_rows": not_worn_rows,
            "normal_rows": normal_rows,
        },
        "briefing_text": briefing_text,
        "checklist": checklist,
        "focus_message": focus_message,
        "full_script": full_script,
    }

@app.get("/improvement/summary")
def improvement_summary():
    df = load_input_logs()

    metrics = get_improvement_metrics(df)
    charts = get_weekly_trend_charts(df)
    team_chart = get_team_comparison_chart(df)
    team_summary = get_team_incentive_summary(df)

    return {
        "kpis": metrics,
        "charts": charts,
        "team_comparison_chart": team_chart,
        "team_summary": team_summary,
    }
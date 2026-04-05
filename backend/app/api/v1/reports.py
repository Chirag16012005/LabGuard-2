from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ...services.report_service import ReportService

router = APIRouter()
report_service = ReportService()


@router.get("/reports/student/{student_report_id}", status_code=status.HTTP_200_OK)
async def get_student_report_by_id(student_report_id: str) -> dict:
	"""Get individual student report using only student_report_id."""
	entry = await report_service.get_student_report_entry_by_id(student_report_id)
	if not entry:
		raise HTTPException(status_code=404, detail="Student report entry not found")
	return {"message": "Student report entry retrieved", "data": entry}

@router.get("/assignments/{assignment_id}/reports", status_code=status.HTTP_200_OK)
async def list_assignment_reports(assignment_id: str) -> dict:
	reports = await report_service.list_assignment_reports(assignment_id)
	return {"message": "Reports retrieved", "data": reports}
	reports = await report_service.list_assignment_reports(assignment_id)
	return {"message": "Reports retrieved", "data": reports}


@router.get("/reports/{report_id}/matches", status_code=status.HTTP_200_OK)
async def get_report_matches(report_id: str) -> dict:
	result = await report_service.get_report_matches(report_id)
	if not result:
		raise HTTPException(status_code=404, detail="Report not found")
	return {"message": "Matches retrieved", "data": result}
	result = await report_service.get_report_matches(report_id)
	if not result:
		raise HTTPException(status_code=404, detail="Report not found")
	return {"message": "Matches retrieved", "data": result}



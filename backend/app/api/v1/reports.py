# from __future__ import annotations

import base64
import json

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# from ...services.report_service import ReportService

router = APIRouter()
report_service = ReportService()
bearer_scheme = HTTPBearer()


@router.get("/reports/student/{student_report_id}", status_code=status.HTTP_200_OK)
async def get_student_report_by_id(
    student_report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
	"""Get individual student report using only student_report_id."""
	try:
		payload_segment = credentials.credentials.split(".")[1]
		payload_segment += "=" * (-len(payload_segment) % 4)
		token_payload = json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
	except (IndexError, ValueError, json.JSONDecodeError):
		raise HTTPException(status_code=401, detail="Invalid token")

	if not token_payload.get("user_id") and not token_payload.get("sub"):
		raise HTTPException(status_code=401, detail="Invalid token")

	entry = await report_service.get_student_report_entry_by_id(student_report_id)
	if not entry:
		raise HTTPException(status_code=404, detail="Student report entry not found")
	return {"message": "Student report entry retrieved", "data": entry}


@router.get("/assignments/{assignment_id}/reports", status_code=status.HTTP_200_OK)
async def list_assignment_reports(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
	try:
		payload_segment = credentials.credentials.split(".")[1]
		payload_segment += "=" * (-len(payload_segment) % 4)
		token_payload = json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
	except (IndexError, ValueError, json.JSONDecodeError):
		raise HTTPException(status_code=401, detail="Invalid token")

	if not token_payload.get("user_id") and not token_payload.get("sub"):
		raise HTTPException(status_code=401, detail="Invalid token")

	reports = await report_service.list_assignment_reports(assignment_id)
	return {"message": "Reports retrieved", "data": reports}


@router.get("/reports/{report_id}/matches", status_code=status.HTTP_200_OK)
async def get_report_matches(
    report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
	try:
		payload_segment = credentials.credentials.split(".")[1]
		payload_segment += "=" * (-len(payload_segment) % 4)
		token_payload = json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
	except (IndexError, ValueError, json.JSONDecodeError):
		raise HTTPException(status_code=401, detail="Invalid token")

	if not token_payload.get("user_id") and not token_payload.get("sub"):
		raise HTTPException(status_code=401, detail="Invalid token")

	result = await report_service.get_report_matches(report_id)
	if not result:
		raise HTTPException(status_code=404, detail="Report not found")
	return {"message": "Matches retrieved", "data": result}



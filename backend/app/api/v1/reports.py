# from __future__ import annotations

# from fastapi import APIRouter, HTTPException, status

# from ...services.report_service import ReportService

# router = APIRouter()
# report_service = ReportService()


# @router.get("/reports/{report_id}", status_code=status.HTTP_200_OK)
# async def get_report(report_id: str) -> dict:
#     report = await report_service.get_report(report_id)
#     if not report:
#         raise HTTPException(status_code=404, detail="Report not found")
#     return {"message": "Report retrieved", "data": report}


# @router.get("/assignments/{assignment_id}/reports", status_code=status.HTTP_200_OK)
# async def list_assignment_reports(assignment_id: str) -> dict:
#     reports = await report_service.list_assignment_reports(assignment_id)
#     return {"message": "Reports retrieved", "data": reports}


# @router.get("/reports/{report_id}/matches", status_code=status.HTTP_200_OK)
# async def get_report_matches(report_id: str) -> dict:
#     result = await report_service.get_report_matches(report_id)
#     if not result:
#         raise HTTPException(status_code=404, detail="Report not found")
#     return {"message": "Matches retrieved", "data": result}


# @router.get("/reports/{report_id}/highlighted", status_code=status.HTTP_200_OK)
# async def get_report_highlighted(report_id: str) -> dict:
#     result = await report_service.get_report_highlighted(report_id)
#     if not result:
#         raise HTTPException(status_code=404, detail="Report not found")
#     return {"message": "Highlighted passages retrieved", "data": result}

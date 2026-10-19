from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid
from typing import List, Optional

from app.db.session import get_db
from app.models import Workflow, WorkflowRun, Job
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowInDB,
    WorkflowRunInDB, WorkflowRunTriggerRequest,
    WorkflowRunApproveRequest, WorkflowRunRejectRequest
)
from app.services.orchestrator.runner import WorkflowOrchestrator

router = APIRouter()

@router.post("/", response_model=WorkflowInDB)
async def create_workflow(workflow_in: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = Workflow(**workflow_in.model_dump())
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow

@router.get("/", response_model=List[WorkflowInDB])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    stmt = select(Workflow).order_by(Workflow.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{workflow_id}", response_model=WorkflowInDB)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    workflow = await db.get(Workflow, uid)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/{workflow_id}", response_model=WorkflowInDB)
async def update_workflow(workflow_id: str, workflow_in: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    workflow = await db.get(Workflow, uid)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    update_data = workflow_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(workflow, field, val)
        
    await db.commit()
    await db.refresh(workflow)
    return workflow

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    workflow = await db.get(Workflow, uid)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    await db.delete(workflow)
    await db.commit()
    return None

@router.post("/{workflow_id}/runs", response_model=WorkflowRunInDB)
async def start_workflow_run(
    workflow_id: str,
    trigger_req: Optional[WorkflowRunTriggerRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        uid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    orchestrator = WorkflowOrchestrator(db)
    trigger_type = trigger_req.trigger_type if trigger_req else "manual"
    company_ids = trigger_req.company_ids if trigger_req else None
    force = trigger_req.force if trigger_req else False

    try:
        run = await orchestrator.start_workflow(
            uid,
            trigger_type=trigger_type,
            company_ids=company_ids,
            force=force
        )
        return run
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

@router.get("/{workflow_id}/runs", response_model=List[WorkflowRunInDB])
async def list_workflow_runs(workflow_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    stmt = select(WorkflowRun).where(WorkflowRun.workflow_id == uid).order_by(WorkflowRun.started_at.desc().nulls_last())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/runs/{run_id}", response_model=WorkflowRunInDB)
async def get_workflow_run(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    run = await db.get(WorkflowRun, uid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/runs/{run_id}/jobs")
async def get_run_jobs(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    stmt = select(Job).where(Job.workflow_run_id == uid).order_by(Job.created_at.asc())
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return jobs

@router.post("/runs/{run_id}/cancel", response_model=WorkflowRunInDB)
async def cancel_run(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    orchestrator = WorkflowOrchestrator(db)
    try:
        run = await orchestrator.cancel_workflow_run(uid)
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/runs/{run_id}/retry", response_model=WorkflowRunInDB)
async def retry_run(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    orchestrator = WorkflowOrchestrator(db)
    try:
        run = await orchestrator.retry_workflow_run(uid)
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/runs/{run_id}/approve", response_model=WorkflowRunInDB)
async def approve_run(
    run_id: str,
    approve_req: Optional[WorkflowRunApproveRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        uid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    orchestrator = WorkflowOrchestrator(db)
    approved_by = approve_req.approved_by if approve_req else "human_reviewer"
    notes = approve_req.notes if approve_req else None
    try:
        run = await orchestrator.approve_workflow_run(uid, approved_by=approved_by, notes=notes)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/runs/{run_id}/reject", response_model=WorkflowRunInDB)
async def reject_run(
    run_id: str,
    reject_req: Optional[WorkflowRunRejectRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        uid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    orchestrator = WorkflowOrchestrator(db)
    rejected_by = reject_req.rejected_by if reject_req else "human_reviewer"
    reason = reject_req.reason if reject_req else "Rejected during review"
    try:
        run = await orchestrator.reject_workflow_run(uid, rejected_by=rejected_by, reason=reason)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/scheduler/tick", response_model=List[WorkflowRunInDB])
async def trigger_scheduler_tick(db: AsyncSession = Depends(get_db)):
    orchestrator = WorkflowOrchestrator(db)
    runs = await orchestrator.evaluate_scheduled_workflows()
    return runs

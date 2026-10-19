import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc

from app.models import (
    Company,
    CompanyContact,
    WebsiteScan,
    OpportunityProfile,
    MediaPlan,
    MediaPlanItem,
    PublisherRecord,
    OutreachDraft,
    OutreachMessage,
    CRMDeal,
    CRMTask,
    CRMActivity,
    CRMNote
)
from app.schemas.crm import (
    VALID_SALES_STAGES,
    VALID_DEAL_STAGES,
    VALID_TASK_TYPES,
    VALID_TASK_STATUSES,
    VALID_TASK_PRIORITIES,
    VALID_SERVICE_CATEGORIES,
    DealCreate,
    DealUpdate,
    TaskCreate,
    TaskUpdate,
    TaskCompleteRequest,
    NoteCreate,
    CRMReportMetrics,
    UnifiedProspectSummary,
    UnifiedProspectDetail,
    PipelineColumn,
    DealResponse,
    TaskResponse,
    NoteResponse,
    ActivityResponse
)

logger = logging.getLogger(__name__)


class CRMService:
    """
    Core CRM & Sales Pipeline service connecting company intelligence,
    SEO findings, publisher matching, media plans, and outreach into a unified sales system.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # 1. Pipeline Stage Management
    # =========================================================================

    async def update_prospect_stage(
        self,
        company_id: uuid.UUID,
        new_stage: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        actor: str = "human_reviewer"
    ) -> Company:
        stage_norm = new_stage.strip().upper()
        if stage_norm not in VALID_SALES_STAGES:
            raise ValueError(f"Invalid sales stage '{new_stage}'. Must be one of: {', '.join(VALID_SALES_STAGES)}")

        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        old_stage = company.sales_stage or "NEW"
        now_utc = datetime.now(timezone.utc)

        # Stage Transition Rules
        # - Do not automatically mark as CONTACTED without a confirmed sent outreach message
        if stage_norm == "CONTACTED" and old_stage not in ["CONTACTED", "REPLIED", "MEETING_SCHEDULED", "PROPOSAL_SENT", "NEGOTIATION", "WON"]:
            stmt_msg = select(func.count(OutreachMessage.id)).where(
                OutreachMessage.company_id == company_id,
                OutreachMessage.status.in_(["SENT", "DELIVERED"])
            )
            msg_count = (await self.session.execute(stmt_msg)).scalar() or 0
            if msg_count == 0 and actor != "human_reviewer":
                raise ValueError("Cannot mark prospect as 'CONTACTED' without confirmed dispatched outreach or explicit human reviewer action.")

        # Update company
        company.sales_stage = stage_norm
        company.stage_updated_at = now_utc
        if reason:
            company.stage_reason = reason
        if notes:
            company.qualification_notes = notes

        # Log Activity Audit Trail
        activity = CRMActivity(
            company_id=company_id,
            activity_type="STAGE_CHANGE",
            actor=actor,
            title=f"Stage moved from {old_stage} to {stage_norm}",
            details={
                "old_stage": old_stage,
                "new_stage": stage_norm,
                "reason": reason,
                "notes": notes,
                "timestamp": now_utc.isoformat()
            },
            created_at=now_utc
        )
        self.session.add(activity)

        await self.session.commit()
        await self.session.refresh(company)
        logger.info(f"Prospect {company_id} ({company.company_name}) stage transitioned: {old_stage} -> {stage_norm} by {actor}")
        return company

    # =========================================================================
    # 2. Unified Prospect Records
    # =========================================================================

    async def get_unified_prospect_detail(self, company_id: uuid.UUID) -> UnifiedProspectDetail:
        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # 1. Opportunity Profile
        stmt_opp = select(OpportunityProfile).where(OpportunityProfile.company_id == company_id).order_by(desc(OpportunityProfile.created_at))
        opp = (await self.session.execute(stmt_opp)).scalars().first()
        opp_data = None
        if opp:
            opp_data = {
                "id": str(opp.id),
                "recommended_service": opp.recommended_service,
                "opportunity_score": opp.opportunity_score,
                "supporting_evidence": opp.supporting_evidence,
                "identified_problems": opp.identified_problems,
                "confidence_level": opp.confidence_level,
                "data_freshness": opp.data_freshness,
                "methodology_version": opp.methodology_version,
                "created_at": opp.created_at.isoformat() if opp.created_at else None
            }

        # 2. Website Scan
        stmt_scan = select(WebsiteScan).where(WebsiteScan.company_id == company_id).order_by(desc(WebsiteScan.created_at))
        scan = (await self.session.execute(stmt_scan)).scalars().first()
        scan_data = None
        if scan:
            scan_data = {
                "id": str(scan.id),
                "url": scan.url,
                "title": scan.title,
                "meta_description": scan.meta_description,
                "http_status": scan.http_status,
                "technologies": scan.technology_signals,
                "cms_detected": scan.cms_detected,
                "created_at": scan.created_at.isoformat() if scan.created_at else None
            }

        # 3. Contacts
        stmt_contacts = select(CompanyContact).where(CompanyContact.company_id == company_id).order_by(desc(CompanyContact.created_at))
        contacts = (await self.session.execute(stmt_contacts)).scalars().all()
        contacts_data = [
            {
                "id": str(c.id),
                "email": c.email,
                "full_name": c.full_name,
                "job_title": c.job_title,
                "department": c.department,
                "source_type": c.source_type,
                "verification_status": c.verification_status,
                "confidence": c.confidence,
                "opt_out": c.opt_out,
                "retrieval_timestamp": c.retrieval_timestamp.isoformat() if c.retrieval_timestamp else None
            }
            for c in contacts
        ]

        # 4. Media Plans
        stmt_plans = select(MediaPlan).where(MediaPlan.company_id == company_id).order_by(desc(MediaPlan.created_at))
        plans = (await self.session.execute(stmt_plans)).scalars().all()
        plans_data = []
        for p in plans:
            stmt_items = select(MediaPlanItem, PublisherRecord).outerjoin(
                PublisherRecord, MediaPlanItem.publisher_id == PublisherRecord.id
            ).where(MediaPlanItem.media_plan_id == p.id)
            items_res = (await self.session.execute(stmt_items)).all()
            items_list = [
                {
                    "item_id": str(item.id),
                    "publisher_name": pub.publisher_name if pub else "Publisher",
                    "publisher_domain": pub.canonical_domain if pub else "",
                    "proposed_price": item.proposed_price,
                    "target_topic": item.target_topic
                }
                for item, pub in items_res
            ]
            plans_data.append({
                "id": str(p.id),
                "name": p.name,
                "status": p.status,
                "total_items": len(items_list),
                "items": items_list,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })

        # 5. Outreach Drafts
        stmt_drafts = select(OutreachDraft).where(OutreachDraft.company_id == company_id).order_by(desc(OutreachDraft.created_at))
        drafts = (await self.session.execute(stmt_drafts)).scalars().all()
        drafts_data = [
            {
                "id": str(d.id),
                "subject_line": d.subject_line,
                "recipient_email": d.recipient_email,
                "approval_status": d.approval_status,
                "status": d.status,
                "sequence_step": d.sequence_step,
                "is_follow_up": d.is_follow_up,
                "scheduled_send_at": d.scheduled_send_at.isoformat() if d.scheduled_send_at else None,
                "sent_at": d.sent_at.isoformat() if d.sent_at else None,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in drafts
        ]

        # 6. Outreach Messages (Audit Log)
        stmt_msgs = select(OutreachMessage).where(OutreachMessage.company_id == company_id).order_by(desc(OutreachMessage.sent_at))
        msgs = (await self.session.execute(stmt_msgs)).scalars().all()
        msgs_data = [
            {
                "id": str(m.id),
                "recipient_email": m.recipient_email,
                "subject_line": m.subject_line,
                "provider": m.provider,
                "status": m.status,
                "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                "replied_at": m.replied_at.isoformat() if m.replied_at else None
            }
            for m in msgs
        ]

        # 7. Deals
        stmt_deals = select(CRMDeal).where(CRMDeal.company_id == company_id).order_by(desc(CRMDeal.created_at))
        deals = (await self.session.execute(stmt_deals)).scalars().all()
        deals_dto = [DealResponse.model_validate(d) for d in deals]

        # 8. Tasks
        stmt_tasks = select(CRMTask).where(CRMTask.company_id == company_id).order_by(desc(CRMTask.created_at))
        tasks = (await self.session.execute(stmt_tasks)).scalars().all()
        tasks_dto = [TaskResponse.model_validate(t) for t in tasks]

        # 9. Notes
        stmt_notes = select(CRMNote).where(CRMNote.company_id == company_id).order_by(desc(CRMNote.created_at))
        notes = (await self.session.execute(stmt_notes)).scalars().all()
        notes_dto = [NoteResponse.model_validate(n) for n in notes]

        # 10. Activities
        stmt_act = select(CRMActivity).where(CRMActivity.company_id == company_id).order_by(desc(CRMActivity.created_at))
        acts = (await self.session.execute(stmt_act)).scalars().all()
        acts_dto = [ActivityResponse.model_validate(a) for a in acts]

        company_dict = {
            "id": str(company.id),
            "company_name": company.company_name or "Unnamed Prospect",
            "canonical_domain": company.canonical_domain,
            "website_url": company.website_url,
            "industry": company.industry,
            "sub_industry": company.sub_industry,
            "description": company.description,
            "country": company.country,
            "city": company.city,
            "created_at": company.created_at.isoformat() if company.created_at else None
        }

        return UnifiedProspectDetail(
            company=company_dict,
            sales_stage=company.sales_stage or "NEW",
            stage_updated_at=company.stage_updated_at or company.created_at,
            stage_reason=company.stage_reason,
            target_market=company.target_market,
            qualification_notes=company.qualification_notes,
            opportunity_profile=opp_data,
            website_scan=scan_data,
            contacts=contacts_data,
            media_plans=plans_data,
            outreach_drafts=drafts_data,
            outreach_messages=msgs_data,
            deals=deals_dto,
            tasks=tasks_dto,
            notes=notes_dto,
            activities=acts_dto
        )

    # =========================================================================
    # 3. Pipeline Kanban Board
    # =========================================================================

    async def get_pipeline_board(self) -> List[PipelineColumn]:
        columns = []
        for stage in VALID_SALES_STAGES:
            stage_title = stage.replace("_", " ").title()
            stmt_comp = select(Company).where(Company.sales_stage == stage).order_by(desc(Company.stage_updated_at)).limit(50)
            companies = (await self.session.execute(stmt_comp)).scalars().all()

            prospect_summaries = []
            col_deal_value = 0.0
            col_deals_count = 0

            for comp in companies:
                # Opportunity score
                stmt_opp = select(OpportunityProfile.opportunity_score, OpportunityProfile.recommended_service).where(
                    OpportunityProfile.company_id == comp.id
                ).order_by(desc(OpportunityProfile.created_at)).limit(1)
                opp_row = (await self.session.execute(stmt_opp)).first()
                opp_score = opp_row[0] if opp_row else None
                rec_svc = opp_row[1] if opp_row else None

                # Deals summary
                stmt_d = select(
                    func.count(CRMDeal.id),
                    func.coalesce(func.sum(CRMDeal.estimated_value), 0.0)
                ).where(
                    CRMDeal.company_id == comp.id,
                    CRMDeal.stage.notin_(["WON", "LOST"])
                )
                d_row = (await self.session.execute(stmt_d)).first()
                d_count = d_row[0] if d_row else 0
                d_val = float(d_row[1]) if d_row else 0.0

                col_deals_count += d_count
                col_deal_value += d_val

                # Pending tasks count
                stmt_t = select(func.count(CRMTask.id)).where(
                    CRMTask.company_id == comp.id,
                    CRMTask.status.in_(["PENDING", "IN_PROGRESS"])
                )
                t_count = (await self.session.execute(stmt_t)).scalar() or 0

                # Verified contacts count
                stmt_c = select(func.count(CompanyContact.id)).where(
                    CompanyContact.company_id == comp.id,
                    CompanyContact.verification_status == "VERIFIED"
                )
                c_count = (await self.session.execute(stmt_c)).scalar() or 0

                prospect_summaries.append(
                    UnifiedProspectSummary(
                        id=comp.id,
                        company_name=comp.company_name or comp.canonical_domain or "Unnamed Prospect",
                        canonical_domain=comp.canonical_domain,
                        website_url=comp.website_url,
                        industry=comp.industry,
                        target_market=comp.target_market,
                        sales_stage=comp.sales_stage or "NEW",
                        stage_updated_at=comp.stage_updated_at or comp.created_at,
                        stage_reason=comp.stage_reason,
                        opportunity_score=opp_score,
                        recommended_service=rec_svc,
                        total_deals=d_count,
                        open_deal_value=d_val,
                        pending_tasks_count=t_count,
                        verified_contacts_count=c_count,
                        created_at=comp.created_at
                    )
                )

            # Total count for the stage in DB
            stmt_cnt = select(func.count(Company.id)).where(Company.sales_stage == stage)
            stage_total = (await self.session.execute(stmt_cnt)).scalar() or 0

            columns.append(
                PipelineColumn(
                    stage=stage,
                    stage_name=stage_title,
                    prospects_count=stage_total,
                    open_deals_count=col_deals_count,
                    total_pipeline_value=col_deal_value,
                    prospects=prospect_summaries
                )
            )

        return columns

    # =========================================================================
    # 4. Deal Management
    # =========================================================================

    async def create_deal(self, data: DealCreate, actor: str = "human_reviewer") -> CRMDeal:
        company = await self.session.get(Company, data.company_id)
        if not company:
            raise ValueError(f"Company {data.company_id} not found")

        deal_dict = data.model_dump()
        deal = CRMDeal(**deal_dict)
        self.session.add(deal)
        await self.session.flush()

        # Audit Activity
        activity = CRMActivity(
            company_id=data.company_id,
            deal_id=deal.id,
            activity_type="DEAL_CREATED",
            actor=actor,
            title=f"Deal created: '{deal.deal_name}' (${deal.estimated_value:,.2f})",
            details={
                "deal_id": str(deal.id),
                "deal_name": deal.deal_name,
                "estimated_value": deal.estimated_value,
                "currency": deal.currency,
                "stage": deal.stage,
                "service_category": deal.service_category
            }
        )
        self.session.add(activity)

        await self.session.commit()
        await self.session.refresh(deal)
        logger.info(f"Created deal {deal.id} ('{deal.deal_name}') for company {data.company_id}")
        return deal

    async def update_deal(self, deal_id: uuid.UUID, data: DealUpdate) -> CRMDeal:
        deal = await self.session.get(CRMDeal, deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")

        actor = data.actor or "human_reviewer"
        old_stage = deal.stage
        now_utc = datetime.now(timezone.utc)

        update_dict = data.model_dump(exclude_unset=True, exclude={"actor"})
        for k, v in update_dict.items():
            setattr(deal, k, v)

        # Stage Transition & Win/Loss Integrity
        if "stage" in update_dict and update_dict["stage"] != old_stage:
            new_stage = update_dict["stage"]
            if new_stage not in VALID_DEAL_STAGES:
                raise ValueError(f"Invalid deal stage '{new_stage}'. Must be one of: {', '.join(VALID_DEAL_STAGES)}")

            if new_stage == "WON":
                deal.outcome = "WON"
                deal.actual_close_date = now_utc
                if deal.closed_amount is None:
                    deal.closed_amount = deal.proposed_value or deal.estimated_value
                
                # Activity: Deal Won
                act_won = CRMActivity(
                    company_id=deal.company_id,
                    deal_id=deal.id,
                    activity_type="DEAL_WON",
                    actor=actor,
                    title=f"Deal WON: '{deal.deal_name}' (${deal.closed_amount or 0.0:,.2f})",
                    details={
                        "closed_amount": deal.closed_amount,
                        "currency": deal.currency,
                        "win_reason": deal.win_reason
                    }
                )
                self.session.add(act_won)

                # Optionally sync company stage if not already WON
                company = await self.session.get(Company, deal.company_id)
                if company and company.sales_stage != "WON":
                    company.sales_stage = "WON"
                    company.stage_updated_at = now_utc
                    company.stage_reason = f"Deal won: {deal.deal_name}"

            elif new_stage == "LOST":
                deal.outcome = "LOST"
                deal.actual_close_date = now_utc
                # Activity: Deal Lost
                act_lost = CRMActivity(
                    company_id=deal.company_id,
                    deal_id=deal.id,
                    activity_type="DEAL_LOST",
                    actor=actor,
                    title=f"Deal LOST: '{deal.deal_name}'",
                    details={
                        "loss_reason": deal.loss_reason or "Unspecified"
                    }
                )
                self.session.add(act_lost)
            else:
                # Stage transition activity
                act_stage = CRMActivity(
                    company_id=deal.company_id,
                    deal_id=deal.id,
                    activity_type="DEAL_STAGE_CHANGE",
                    actor=actor,
                    title=f"Deal '{deal.deal_name}' moved to {new_stage}",
                    details={
                        "old_stage": old_stage,
                        "new_stage": new_stage
                    }
                )
                self.session.add(act_stage)

        await self.session.commit()
        await self.session.refresh(deal)
        return deal

    # =========================================================================
    # 5. Task Management & Idempotency
    # =========================================================================

    async def create_task(self, data: TaskCreate, actor: str = "human_reviewer") -> CRMTask:
        # Check idempotency to avoid duplicates when workflows retry
        if data.idempotency_key:
            stmt_existing = select(CRMTask).where(CRMTask.idempotency_key == data.idempotency_key)
            existing = (await self.session.execute(stmt_existing)).scalars().first()
            if existing:
                logger.info(f"Task with idempotency_key '{data.idempotency_key}' already exists (ID: {existing.id}). Returning existing task.")
                return existing

        task_dict = data.model_dump()
        task = CRMTask(**task_dict)
        self.session.add(task)
        await self.session.flush()

        activity = CRMActivity(
            company_id=data.company_id,
            deal_id=data.deal_id,
            contact_id=data.contact_id,
            activity_type="TASK_CREATED",
            actor=actor,
            title=f"Task created: [{task.task_type}] {task.title}",
            details={
                "task_id": str(task.id),
                "task_type": task.task_type,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None
            }
        )
        self.session.add(activity)

        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def complete_task(
        self,
        task_id: uuid.UUID,
        req: TaskCompleteRequest
    ) -> CRMTask:
        task = await self.session.get(CRMTask, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        now_utc = datetime.now(timezone.utc)
        task.status = "COMPLETED"
        task.completed_at = now_utc
        task.completed_by = req.completed_by or "human_reviewer"
        if req.completion_notes:
            task.completion_notes = req.completion_notes

        activity = CRMActivity(
            company_id=task.company_id,
            deal_id=task.deal_id,
            contact_id=task.contact_id,
            activity_type="TASK_COMPLETED",
            actor=task.completed_by,
            title=f"Task completed: {task.title}",
            details={
                "task_id": str(task.id),
                "completion_notes": req.completion_notes,
                "completed_at": now_utc.isoformat()
            }
        )
        self.session.add(activity)

        await self.session.commit()
        await self.session.refresh(task)
        return task

    # =========================================================================
    # 6. Notes & Timeline Activities
    # =========================================================================

    async def add_note(self, company_id: uuid.UUID, req: NoteCreate) -> CRMNote:
        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        note = CRMNote(
            company_id=company_id,
            deal_id=req.deal_id,
            author=req.author or "human_reviewer",
            content=req.content.strip()
        )
        self.session.add(note)
        await self.session.flush()

        activity = CRMActivity(
            company_id=company_id,
            deal_id=req.deal_id,
            activity_type="NOTE_ADDED",
            actor=note.author,
            title=f"Note added: '{note.content[:60]}...'",
            details={"note_id": str(note.id)}
        )
        self.session.add(activity)

        await self.session.commit()
        await self.session.refresh(note)
        return note

    # =========================================================================
    # 7. Reporting & Measurable Metrics
    # =========================================================================

    async def get_crm_metrics(self) -> CRMReportMetrics:
        # 1. Total prospects
        total_prospects = (await self.session.execute(select(func.count(Company.id)))).scalar() or 0

        # 2. Prospects by stage
        stmt_stages = select(Company.sales_stage, func.count(Company.id)).group_by(Company.sales_stage)
        stage_counts_rows = (await self.session.execute(stmt_stages)).all()
        stage_map = {s: 0 for s in VALID_SALES_STAGES}
        for st, count in stage_counts_rows:
            if st in stage_map:
                stage_map[st] = count
            else:
                stage_map[st] = count

        # 3. Qualified count
        qualified_stages = ["QUALIFIED", "CONTACTED", "REPLIED", "MEETING_SCHEDULED", "PROPOSAL_SENT", "NEGOTIATION", "WON"]
        stmt_qual = select(func.count(Company.id)).where(Company.sales_stage.in_(qualified_stages))
        qualified_count = (await self.session.execute(stmt_qual)).scalar() or 0

        # 4. Confirmed sent outreach
        stmt_outreach = select(func.count(OutreachMessage.id)).where(OutreachMessage.status.in_(["SENT", "DELIVERED"]))
        outreach_sent = (await self.session.execute(stmt_outreach)).scalar() or 0

        # 5. Confirmed replies
        stmt_replies = select(func.count(OutreachMessage.id)).where(
            or_(OutreachMessage.status == "REPLIED", OutreachMessage.replied_at.isnot(None))
        )
        replies_count = (await self.session.execute(stmt_replies)).scalar() or 0

        # 6. Meetings scheduled
        meetings_count = stage_map.get("MEETING_SCHEDULED", 0)

        # 7. Proposals sent
        proposals_count = stage_map.get("PROPOSAL_SENT", 0)

        # 8. Deals won and lost
        stmt_won = select(func.count(CRMDeal.id)).where(CRMDeal.outcome == "WON")
        won_deals = (await self.session.execute(stmt_won)).scalar() or 0

        stmt_lost = select(func.count(CRMDeal.id)).where(CRMDeal.outcome == "LOST")
        lost_deals = (await self.session.execute(stmt_lost)).scalar() or 0

        # 9. Open pipeline value (USD only, non-won, non-lost)
        stmt_pipeline_val = select(func.coalesce(func.sum(CRMDeal.estimated_value), 0.0)).where(
            CRMDeal.stage.notin_(["WON", "LOST"]),
            CRMDeal.currency == "USD"
        )
        open_pipeline_val = float((await self.session.execute(stmt_pipeline_val)).scalar() or 0.0)

        # 10. Closed won earned revenue (USD only)
        stmt_closed_rev = select(func.coalesce(func.sum(CRMDeal.closed_amount), 0.0)).where(
            CRMDeal.outcome == "WON",
            CRMDeal.currency == "USD"
        )
        closed_won_revenue = float((await self.session.execute(stmt_closed_rev)).scalar() or 0.0)

        # Conversion Rates
        lead_to_qual = (qualified_count / total_prospects * 100.0) if total_prospects > 0 else 0.0
        qual_to_outreach = (outreach_sent / qualified_count * 100.0) if qualified_count > 0 else 0.0
        outreach_to_reply = (replies_count / outreach_sent * 100.0) if outreach_sent > 0 else None
        
        closed_deals_total = won_deals + lost_deals
        deal_win_rate = (won_deals / closed_deals_total * 100.0) if closed_deals_total > 0 else None

        notes = [
            f"Open pipeline value (${open_pipeline_val:,.2f}) reflects active estimated deal opportunities.",
            f"Closed won revenue (${closed_won_revenue:,.2f}) reflects actual closed contracts verified in USD.",
            "All metrics are calculated directly from persisted PostgreSQL records."
        ]
        if outreach_sent == 0:
            notes.append("No outreach messages have been dispatched yet (EMAIL_PROVIDER is unconfigured or in safe mode).")

        return CRMReportMetrics(
            prospects_by_stage=stage_map,
            total_prospects=total_prospects,
            qualified_prospects_count=qualified_count,
            outreach_sent_count=outreach_sent,
            replies_received_count=replies_count,
            meetings_scheduled_count=meetings_count,
            proposals_sent_count=proposals_count,
            won_deals_count=won_deals,
            lost_deals_count=lost_deals,
            open_pipeline_value=open_pipeline_val,
            closed_won_revenue=closed_won_revenue,
            pipeline_currency="USD",
            conversion_rates={
                "lead_to_qualified_pct": round(lead_to_qual, 1),
                "qualified_to_outreach_pct": round(qual_to_outreach, 1),
                "outreach_to_reply_pct": round(outreach_to_reply, 1) if outreach_to_reply is not None else None,
                "deal_win_rate_pct": round(deal_win_rate, 1) if deal_win_rate is not None else None
            },
            notes=notes
        )

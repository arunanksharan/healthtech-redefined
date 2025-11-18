"""
Agents Service
Business logic for AI agent tool execution
"""
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc
from datetime import datetime
from loguru import logger

from shared.database.models import ToolRun
from modules.agents.schemas import (
    ToolDefinition,
    ToolRegistry,
    RunTool,
    ToolRunStatistics,
    ToolRunListFilters
)
from modules.tickets.service import TicketService
from modules.appointments.service import AppointmentService
from modules.patients.service import PatientService
from modules.notifications.service import NotificationService
from modules.analytics.service import AnalyticsService
from shared.events.publisher import publish_event, EventType


# ==================== Tool Registry ====================

TOOLS = [
    ToolDefinition(
        name="create_ticket",
        description="Create a support ticket",
        inputs={
            "category": "str",
            "priority": "str",
            "summary": "str",
            "description": "str (optional)"
        },
        scopes=["tickets:write"]
    ),
    ToolDefinition(
        name="confirm_appointment",
        description="Confirm an appointment with specific time",
        inputs={
            "appointment_id": "uuid",
            "confirmed_start": "iso_datetime",
            "confirmed_end": "iso_datetime"
        },
        scopes=["appointments:write"]
    ),
    ToolDefinition(
        name="send_notification",
        description="Send a notification via WhatsApp/SMS/Email",
        inputs={
            "channel": "str",
            "to": "str",
            "body": "str",
            "subject": "str (optional)"
        },
        scopes=["notifications:write"]
    ),
    ToolDefinition(
        name="update_patient",
        description="Update patient information",
        inputs={
            "patient_id": "uuid",
            "fields": "dict"
        },
        scopes=["patients:write"]
    ),
    # ==================== Analytics Tools ====================
    ToolDefinition(
        name="get_appointment_analytics",
        description="Get comprehensive appointment analytics and metrics",
        inputs={
            "time_period": "str (today, last_7_days, last_30_days, etc.)",
            "start_date": "str (optional, ISO date)",
            "end_date": "str (optional, ISO date)",
            "practitioner_id": "str (optional)",
            "department": "str (optional)",
            "include_breakdown": "bool (optional, default true)"
        },
        scopes=["analytics:read"]
    ),
    ToolDefinition(
        name="get_journey_analytics",
        description="Get patient journey analytics and progress metrics",
        inputs={
            "time_period": "str (today, last_7_days, last_30_days, etc.)",
            "start_date": "str (optional, ISO date)",
            "end_date": "str (optional, ISO date)",
            "department": "str (optional)",
            "include_breakdown": "bool (optional, default true)"
        },
        scopes=["analytics:read"]
    ),
    ToolDefinition(
        name="get_communication_analytics",
        description="Get messaging and conversation analytics",
        inputs={
            "time_period": "str (today, last_7_days, last_30_days, etc.)",
            "start_date": "str (optional, ISO date)",
            "end_date": "str (optional, ISO date)",
            "include_breakdown": "bool (optional, default true)"
        },
        scopes=["analytics:read"]
    ),
    ToolDefinition(
        name="get_voice_call_analytics",
        description="Get voice call performance analytics from Zucol/Zoice",
        inputs={
            "time_period": "str (today, last_7_days, last_30_days, etc.)",
            "start_date": "str (optional, ISO date)",
            "end_date": "str (optional, ISO date)",
            "include_breakdown": "bool (optional, default true)"
        },
        scopes=["analytics:read"]
    ),
    ToolDefinition(
        name="get_dashboard_overview",
        description="Get complete PRM dashboard overview with all metrics",
        inputs={
            "time_period": "str (today, last_7_days, last_30_days, etc.)",
            "start_date": "str (optional, ISO date)",
            "end_date": "str (optional, ISO date)"
        },
        scopes=["analytics:read"]
    ),
    ToolDefinition(
        name="query_analytics_nl",
        description="Query analytics using natural language (e.g., 'How many appointments did we have last week?')",
        inputs={
            "query": "str (natural language question)"
        },
        scopes=["analytics:read"]
    )
]


class AgentService:
    """Service for AI agent tool execution"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Tool Registry ====================

    def list_tools(self) -> ToolRegistry:
        """
        List all available tools

        Returns:
            ToolRegistry with list of tool definitions
        """
        return ToolRegistry(tools=TOOLS)

    # ==================== Tool Execution ====================

    async def execute_tool(
        self,
        org_id: UUID,
        payload: RunTool
    ) -> Dict[str, Any]:
        """
        Execute a tool and log the run

        Process:
          1. Create ToolRun record
          2. Validate tool exists
          3. Route to appropriate handler
          4. Execute tool
          5. Update ToolRun with result
          6. Publish event
          7. Return output

        Args:
            org_id: Organization ID
            payload: Tool execution request

        Returns:
            Tool output

        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        # Create ToolRun record
        tool_run = ToolRun(
            id=uuid4(),
            org_id=org_id,
            tool=payload.name,
            inputs=payload.args,
            success=True
        )
        self.db.add(tool_run)
        self.db.flush()

        try:
            # Route to appropriate handler
            if payload.name == "create_ticket":
                output = await self._execute_create_ticket(org_id, payload.args)

            elif payload.name == "confirm_appointment":
                output = await self._execute_confirm_appointment(org_id, payload.args)

            elif payload.name == "send_notification":
                output = await self._execute_send_notification(org_id, payload.args)

            elif payload.name == "update_patient":
                output = await self._execute_update_patient(org_id, payload.args)

            # Analytics tools
            elif payload.name == "get_appointment_analytics":
                output = await self._execute_get_appointment_analytics(org_id, payload.args)

            elif payload.name == "get_journey_analytics":
                output = await self._execute_get_journey_analytics(org_id, payload.args)

            elif payload.name == "get_communication_analytics":
                output = await self._execute_get_communication_analytics(org_id, payload.args)

            elif payload.name == "get_voice_call_analytics":
                output = await self._execute_get_voice_call_analytics(org_id, payload.args)

            elif payload.name == "get_dashboard_overview":
                output = await self._execute_get_dashboard_overview(org_id, payload.args)

            elif payload.name == "query_analytics_nl":
                output = await self._execute_query_analytics_nl(org_id, payload.args)

            else:
                raise ValueError(f"Unknown tool: {payload.name}")

            # Update ToolRun with output
            tool_run.outputs = output
            tool_run.success = True

            self.db.commit()

            # Publish event
            await publish_event(
                event_type=EventType.CUSTOM,
                org_id=org_id,
                resource_type="tool_run",
                resource_id=tool_run.id,
                data={
                    "tool": payload.name,
                    "success": True
                }
            )

            logger.info(f"Tool {payload.name} executed successfully: {tool_run.id}")

            return output

        except Exception as e:
            # Update ToolRun with error
            tool_run.success = False
            tool_run.error = str(e)[:400]  # Limit to 400 chars
            self.db.commit()

            # Publish event
            await publish_event(
                event_type=EventType.CUSTOM,
                org_id=org_id,
                resource_type="tool_run",
                resource_id=tool_run.id,
                data={
                    "tool": payload.name,
                    "success": False,
                    "error": str(e)
                }
            )

            logger.error(f"Tool {payload.name} failed: {e}", exc_info=True)

            raise

    # ==================== Tool Handlers ====================

    async def _execute_create_ticket(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute create_ticket tool"""
        from modules.tickets.schemas import TicketCreate

        ticket_service = TicketService(self.db)

        # Build TicketCreate payload
        ticket_data = TicketCreate(
            category=args.get("category", "general"),
            priority=args.get("priority", "medium"),
            summary=args["summary"],
            description=args.get("description")
        )

        ticket = await ticket_service.create_ticket(ticket_data)

        return {
            "ticket_id": str(ticket.id),
            "status": ticket.status
        }

    async def _execute_confirm_appointment(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute confirm_appointment tool"""
        from datetime import datetime

        appointment_service = AppointmentService(self.db)

        appointment_id = UUID(args["appointment_id"])
        confirmed_start = datetime.fromisoformat(args["confirmed_start"])
        confirmed_end = datetime.fromisoformat(args["confirmed_end"])

        # TODO: Implement appointment confirmation in AppointmentService
        # For now, return mock response
        return {
            "appointment_id": str(appointment_id),
            "confirmed": True,
            "start": args["confirmed_start"],
            "end": args["confirmed_end"]
        }

    async def _execute_send_notification(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute send_notification tool"""
        from modules.notifications.schemas import NotificationSend

        notification_service = NotificationService(self.db)

        notification_data = NotificationSend(
            channel=args["channel"],
            to=args["to"],
            subject=args.get("subject"),
            body=args["body"]
        )

        notification = await notification_service.send_notification(notification_data)

        return {
            "notification_id": str(notification.id),
            "status": notification.status,
            "channel": notification.channel
        }

    async def _execute_update_patient(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute update_patient tool"""
        from modules.patients.schemas import PatientUpdate

        patient_service = PatientService(self.db)

        patient_id = UUID(args["patient_id"])
        fields = args.get("fields", {})

        # Build PatientUpdate payload
        patient_data = PatientUpdate(**fields)

        patient = await patient_service.update_patient(patient_id, patient_data)

        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        return {
            "patient_id": str(patient.id),
            "updated": True
        }

    # ==================== Tool Run Management ====================

    async def list_tool_runs(
        self,
        org_id: UUID,
        filters: ToolRunListFilters
    ) -> List[ToolRun]:
        """
        List tool runs with filters

        Args:
            org_id: Organization ID
            filters: Filter criteria

        Returns:
            List of ToolRun objects
        """
        conditions = [
            ToolRun.org_id == org_id
        ]

        if filters.tool:
            conditions.append(ToolRun.tool == filters.tool)

        if filters.success is not None:
            conditions.append(ToolRun.success == filters.success)

        query = (
            select(ToolRun)
            .where(and_(*conditions))
            .order_by(desc(ToolRun.created_at))
            .limit(filters.limit)
            .offset(filters.offset)
        )

        result = self.db.execute(query)
        return result.scalars().all()

    async def get_tool_run(
        self,
        org_id: UUID,
        tool_run_id: UUID
    ) -> Optional[ToolRun]:
        """Get a single tool run by ID"""
        query = select(ToolRun).where(
            and_(
                ToolRun.id == tool_run_id,
                ToolRun.org_id == org_id
            )
        )

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_statistics(
        self,
        org_id: UUID
    ) -> ToolRunStatistics:
        """
        Get statistics about tool executions

        Returns:
            ToolRunStatistics with counts and success rates
        """
        # Total runs
        total_query = select(func.count(ToolRun.id)).where(
            ToolRun.org_id == org_id
        )
        total_result = self.db.execute(total_query)
        total_runs = total_result.scalar() or 0

        # Successful runs
        success_query = select(func.count(ToolRun.id)).where(
            and_(
                ToolRun.org_id == org_id,
                ToolRun.success == True
            )
        )
        success_result = self.db.execute(success_query)
        successful_runs = success_result.scalar() or 0

        failed_runs = total_runs - successful_runs
        success_rate = successful_runs / total_runs if total_runs > 0 else 0.0

        # By tool
        by_tool_query = (
            select(
                ToolRun.tool,
                func.count(ToolRun.id).label('count')
            )
            .where(ToolRun.org_id == org_id)
            .group_by(ToolRun.tool)
            .order_by(desc('count'))
        )
        by_tool_result = self.db.execute(by_tool_query)
        by_tool_rows = by_tool_result.all()
        by_tool = {row[0]: row[1] for row in by_tool_rows}

        most_used_tool = by_tool_rows[0][0] if by_tool_rows else None

        # Most failed tool
        failed_query = (
            select(
                ToolRun.tool,
                func.count(ToolRun.id).label('count')
            )
            .where(
                and_(
                    ToolRun.org_id == org_id,
                    ToolRun.success == False
                )
            )
            .group_by(ToolRun.tool)
            .order_by(desc('count'))
            .limit(1)
        )
        failed_result = self.db.execute(failed_query)
        failed_row = failed_result.first()
        most_failed_tool = failed_row[0] if failed_row else None

        return ToolRunStatistics(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            success_rate=success_rate,
            by_tool=by_tool,
            most_used_tool=most_used_tool,
            most_failed_tool=most_failed_tool
        )

    # ==================== Analytics Tool Handlers ====================

    async def _execute_get_appointment_analytics(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute get_appointment_analytics tool"""
        from modules.analytics.schemas import AnalyticsQueryParams, TimePeriod
        from datetime import date

        analytics_service = AnalyticsService(self.db)

        # Build query params
        params = AnalyticsQueryParams(
            tenant_id=org_id,
            time_period=TimePeriod(args.get("time_period", "last_30_days")),
            start_date=date.fromisoformat(args["start_date"]) if args.get("start_date") else None,
            end_date=date.fromisoformat(args["end_date"]) if args.get("end_date") else None,
            include_breakdown=args.get("include_breakdown", True),
            practitioner_id=UUID(args["practitioner_id"]) if args.get("practitioner_id") else None,
            department=args.get("department")
        )

        result = analytics_service.get_appointment_analytics(params)

        # Convert to dict for JSON serialization
        return {
            "summary": {
                "total_appointments": result.summary.total_appointments,
                "scheduled": result.summary.scheduled,
                "confirmed": result.summary.confirmed,
                "completed": result.summary.completed,
                "canceled": result.summary.canceled,
                "no_show": result.summary.no_show,
                "no_show_rate": result.summary.no_show_rate,
                "completion_rate": result.summary.completion_rate,
                "cancellation_rate": result.summary.cancellation_rate,
                "trend": [{"date": t.date.isoformat(), "value": t.value} for t in result.summary.trend]
            },
            "breakdown": {
                "by_channel": result.breakdown.by_channel if result.breakdown else {},
                "by_practitioner": result.breakdown.by_practitioner if result.breakdown else {},
                "by_department": result.breakdown.by_department if result.breakdown else {}
            } if result.breakdown else None,
            "time_period": result.time_period,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat()
        }

    async def _execute_get_journey_analytics(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute get_journey_analytics tool"""
        from modules.analytics.schemas import AnalyticsQueryParams, TimePeriod
        from datetime import date

        analytics_service = AnalyticsService(self.db)

        params = AnalyticsQueryParams(
            tenant_id=org_id,
            time_period=TimePeriod(args.get("time_period", "last_30_days")),
            start_date=date.fromisoformat(args["start_date"]) if args.get("start_date") else None,
            end_date=date.fromisoformat(args["end_date"]) if args.get("end_date") else None,
            include_breakdown=args.get("include_breakdown", True),
            department=args.get("department")
        )

        result = analytics_service.get_journey_analytics(params)

        return {
            "summary": {
                "total_active": result.summary.total_active,
                "completed": result.summary.completed,
                "paused": result.summary.paused,
                "canceled": result.summary.canceled,
                "completion_rate": result.summary.completion_rate,
                "avg_completion_time_days": result.summary.avg_completion_time_days,
                "overdue_steps": result.summary.overdue_steps,
                "trend": [{"date": t.date.isoformat(), "value": t.value} for t in result.summary.trend]
            },
            "breakdown": {
                "by_type": result.breakdown.by_type if result.breakdown else {},
                "by_department": result.breakdown.by_department if result.breakdown else {},
                "by_status": result.breakdown.by_status if result.breakdown else {}
            } if result.breakdown else None,
            "time_period": result.time_period,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat()
        }

    async def _execute_get_communication_analytics(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute get_communication_analytics tool"""
        from modules.analytics.schemas import AnalyticsQueryParams, TimePeriod
        from datetime import date

        analytics_service = AnalyticsService(self.db)

        params = AnalyticsQueryParams(
            tenant_id=org_id,
            time_period=TimePeriod(args.get("time_period", "last_30_days")),
            start_date=date.fromisoformat(args["start_date"]) if args.get("start_date") else None,
            end_date=date.fromisoformat(args["end_date"]) if args.get("end_date") else None,
            include_breakdown=args.get("include_breakdown", True)
        )

        result = analytics_service.get_communication_analytics(params)

        return {
            "summary": {
                "total_messages": result.summary.total_messages,
                "total_conversations": result.summary.total_conversations,
                "inbound_messages": result.summary.inbound_messages,
                "outbound_messages": result.summary.outbound_messages,
                "avg_response_time_minutes": result.summary.avg_response_time_minutes,
                "open_conversations": result.summary.open_conversations,
                "pending_conversations": result.summary.pending_conversations,
                "trend": [{"date": t.date.isoformat(), "value": t.value} for t in result.summary.trend]
            },
            "breakdown": {
                "by_channel": result.breakdown.by_channel if result.breakdown else {},
                "by_sentiment": result.breakdown.by_sentiment if result.breakdown else {},
                "by_status": result.breakdown.by_status if result.breakdown else {}
            } if result.breakdown else None,
            "time_period": result.time_period,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat()
        }

    async def _execute_get_voice_call_analytics(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute get_voice_call_analytics tool"""
        from modules.analytics.schemas import AnalyticsQueryParams, TimePeriod
        from datetime import date

        analytics_service = AnalyticsService(self.db)

        params = AnalyticsQueryParams(
            tenant_id=org_id,
            time_period=TimePeriod(args.get("time_period", "last_30_days")),
            start_date=date.fromisoformat(args["start_date"]) if args.get("start_date") else None,
            end_date=date.fromisoformat(args["end_date"]) if args.get("end_date") else None,
            include_breakdown=args.get("include_breakdown", True)
        )

        result = analytics_service.get_voice_call_analytics(params)

        return {
            "summary": {
                "total_calls": result.summary.total_calls,
                "completed_calls": result.summary.completed_calls,
                "failed_calls": result.summary.failed_calls,
                "avg_duration_minutes": result.summary.avg_duration_minutes,
                "total_duration_minutes": result.summary.total_duration_minutes,
                "avg_quality_score": result.summary.avg_quality_score,
                "booking_success_rate": result.summary.booking_success_rate,
                "trend": [{"date": t.date.isoformat(), "value": t.value} for t in result.summary.trend]
            },
            "breakdown": {
                "by_intent": result.breakdown.by_intent if result.breakdown else {},
                "by_outcome": result.breakdown.by_outcome if result.breakdown else {},
                "by_call_type": result.breakdown.by_call_type if result.breakdown else {}
            } if result.breakdown else None,
            "time_period": result.time_period,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat()
        }

    async def _execute_get_dashboard_overview(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute get_dashboard_overview tool"""
        from modules.analytics.schemas import TimePeriod
        from datetime import date

        analytics_service = AnalyticsService(self.db)

        time_period = TimePeriod(args.get("time_period", "last_30_days"))
        start_date = date.fromisoformat(args["start_date"]) if args.get("start_date") else None
        end_date = date.fromisoformat(args["end_date"]) if args.get("end_date") else None

        result = analytics_service.get_dashboard_overview(org_id, time_period, start_date, end_date)

        return {
            "appointments": {
                "total_appointments": result.appointments.total_appointments,
                "completion_rate": result.appointments.completion_rate,
                "no_show_rate": result.appointments.no_show_rate
            },
            "journeys": {
                "total_active": result.journeys.total_active,
                "completed": result.journeys.completed,
                "completion_rate": result.journeys.completion_rate
            },
            "communication": {
                "total_messages": result.communication.total_messages,
                "total_conversations": result.communication.total_conversations,
                "avg_response_time_minutes": result.communication.avg_response_time_minutes
            },
            "voice_calls": {
                "total_calls": result.voice_calls.total_calls,
                "booking_success_rate": result.voice_calls.booking_success_rate,
                "avg_duration_minutes": result.voice_calls.avg_duration_minutes
            },
            "time_period": result.time_period,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat()
        }

    async def _execute_query_analytics_nl(
        self,
        org_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute query_analytics_nl tool - Natural language analytics query"""
        query = args.get("query", "")

        # Simple keyword-based routing to appropriate analytics
        # In production, this would use an LLM to interpret the query
        query_lower = query.lower()

        # Determine intent based on keywords
        if any(word in query_lower for word in ["appointment", "booking", "scheduled"]):
            return await self._execute_get_appointment_analytics(org_id, {"time_period": "last_7_days"})

        elif any(word in query_lower for word in ["journey", "progress", "patient flow"]):
            return await self._execute_get_journey_analytics(org_id, {"time_period": "last_7_days"})

        elif any(word in query_lower for word in ["message", "conversation", "chat", "whatsapp"]):
            return await self._execute_get_communication_analytics(org_id, {"time_period": "last_7_days"})

        elif any(word in query_lower for word in ["call", "voice", "phone", "zoice", "zucol"]):
            return await self._execute_get_voice_call_analytics(org_id, {"time_period": "last_7_days"})

        elif any(word in query_lower for word in ["overview", "dashboard", "summary", "everything"]):
            return await self._execute_get_dashboard_overview(org_id, {"time_period": "last_7_days"})

        else:
            # Default to dashboard overview
            return await self._execute_get_dashboard_overview(org_id, {"time_period": "last_7_days"})

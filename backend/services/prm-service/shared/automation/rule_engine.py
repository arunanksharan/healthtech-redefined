"""
Business Rule Engine
EPIC-012: Intelligent Automation Platform - US-012.1

Provides:
- Rule definition and management
- Decision tables and decision trees
- Rule evaluation with complex conditions
- Rule versioning and conflict resolution
- Rule testing and simulation
- Rule analytics and monitoring
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from uuid import uuid4
import operator
import re
import json
from functools import lru_cache


class RuleType(Enum):
    """Types of rules"""
    SIMPLE = "simple"  # Single condition -> action
    COMPLEX = "complex"  # Multiple conditions with AND/OR logic
    DECISION_TABLE = "decision_table"  # Matrix of conditions and actions
    DECISION_TREE = "decision_tree"  # Hierarchical decision structure
    SCORING = "scoring"  # Weighted scoring rules
    FIRST_MATCH = "first_match"  # Stop on first matching rule
    ALL_MATCH = "all_match"  # Execute all matching rules


class RuleCategory(Enum):
    """Rule categories for healthcare"""
    CLINICAL = "clinical"
    ADMINISTRATIVE = "administrative"
    BILLING = "billing"
    COMPLIANCE = "compliance"
    SCHEDULING = "scheduling"
    PATIENT_OUTREACH = "patient_outreach"
    RISK_MANAGEMENT = "risk_management"
    QUALITY = "quality"


class RulePriority(Enum):
    """Rule execution priority"""
    CRITICAL = 1000
    HIGH = 750
    MEDIUM = 500
    LOW = 250
    BACKGROUND = 100


class ActionStatus(Enum):
    """Action execution status"""
    PENDING = "pending"
    EXECUTED = "executed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class RuleCondition:
    """Individual rule condition"""
    field: str
    operator: str
    value: Any
    logic: str = "AND"  # AND, OR
    negate: bool = False

    # Supported operators
    OPERATORS = {
        'eq': operator.eq,
        'ne': operator.ne,
        'gt': operator.gt,
        'gte': operator.ge,
        'lt': operator.lt,
        'lte': operator.le,
        'in': lambda x, y: x in y if y else False,
        'not_in': lambda x, y: x not in y if y else True,
        'contains': lambda x, y: y in str(x) if x else False,
        'not_contains': lambda x, y: y not in str(x) if x else True,
        'starts_with': lambda x, y: str(x).startswith(str(y)) if x else False,
        'ends_with': lambda x, y: str(x).endswith(str(y)) if x else False,
        'regex': lambda x, y: bool(re.match(y, str(x))) if x else False,
        'exists': lambda x, y: x is not None,
        'not_exists': lambda x, y: x is None,
        'is_empty': lambda x, y: not x,
        'is_not_empty': lambda x, y: bool(x),
        'between': lambda x, y: y[0] <= x <= y[1] if x and isinstance(y, (list, tuple)) and len(y) == 2 else False,
        'days_since': lambda x, y: (datetime.utcnow() - datetime.fromisoformat(str(x))).days >= y if x else False,
        'days_until': lambda x, y: (datetime.fromisoformat(str(x)) - datetime.utcnow()).days <= y if x else False,
    }

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate this condition against the context"""
        field_value = self._get_field_value(self.field, context)
        op_func = self.OPERATORS.get(self.operator)

        if not op_func:
            raise ValueError(f"Unknown operator: {self.operator}")

        try:
            result = op_func(field_value, self.value)
            return not result if self.negate else result
        except Exception:
            return False if not self.negate else True

    def _get_field_value(self, field_path: str, context: Dict) -> Any:
        """Get field value using dot notation"""
        # Handle special date expressions
        if field_path.startswith("today"):
            return datetime.utcnow().date().isoformat()

        parts = field_path.split('.')
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                value = value[idx] if idx < len(value) else None
            else:
                return None
        return value


@dataclass
class RuleAction:
    """Rule action definition"""
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

    # Common action types
    ACTION_TYPES = {
        "create_task": "Create a task",
        "send_alert": "Send an alert",
        "send_notification": "Send notification",
        "send_email": "Send email",
        "send_sms": "Send SMS",
        "schedule_appointment": "Schedule appointment",
        "add_care_gap": "Add care gap",
        "update_record": "Update record",
        "create_order": "Create order",
        "trigger_workflow": "Trigger workflow",
        "escalate": "Escalate to manager",
        "log_event": "Log event",
        "calculate_score": "Calculate score",
        "set_flag": "Set flag",
        "route_to_queue": "Route to queue",
    }


@dataclass
class Rule:
    """Complete rule definition"""
    id: str
    name: str
    description: Optional[str]
    type: RuleType
    category: RuleCategory
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    priority: int = RulePriority.MEDIUM.value
    enabled: bool = True
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


@dataclass
class DecisionTableRow:
    """Row in a decision table"""
    conditions: Dict[str, Any]  # field -> value mapping
    actions: List[RuleAction]
    priority: int = 0


@dataclass
class DecisionTable:
    """Decision table definition"""
    id: str
    name: str
    description: Optional[str]
    condition_columns: List[str]  # List of condition fields
    action_columns: List[str]  # List of action types
    rows: List[DecisionTableRow]
    hit_policy: str = "first"  # first, all, priority, unique
    enabled: bool = True
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DecisionTreeNode:
    """Node in a decision tree"""
    id: str
    condition: Optional[RuleCondition]
    true_node: Optional[str] = None  # Node ID for true branch
    false_node: Optional[str] = None  # Node ID for false branch
    actions: Optional[List[RuleAction]] = None  # Actions at leaf nodes
    is_leaf: bool = False


@dataclass
class DecisionTree:
    """Decision tree definition"""
    id: str
    name: str
    description: Optional[str]
    root_node_id: str
    nodes: Dict[str, DecisionTreeNode]
    enabled: bool = True
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScoringRule:
    """Scoring rule for weighted calculations"""
    id: str
    name: str
    description: Optional[str]
    scoring_factors: List[Dict[str, Any]]  # condition, weight pairs
    thresholds: Dict[str, float]  # score -> category mapping
    enabled: bool = True
    version: str = "1.0.0"


@dataclass
class RuleEvaluationResult:
    """Result of rule evaluation"""
    rule_id: str
    rule_name: str
    matched: bool
    conditions_evaluated: int
    conditions_matched: int
    actions: List[Dict[str, Any]]
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RuleSetResult:
    """Result of evaluating a rule set"""
    rules_evaluated: int
    rules_matched: int
    total_actions: int
    results: List[RuleEvaluationResult]
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BusinessRuleEngine:
    """
    Business rule engine for healthcare automation.
    Supports simple rules, decision tables, decision trees, and scoring rules.
    """

    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self.rule_sets: Dict[str, List[str]] = {}  # rule_set_id -> list of rule_ids
        self.decision_tables: Dict[str, DecisionTable] = {}
        self.decision_trees: Dict[str, DecisionTree] = {}
        self.scoring_rules: Dict[str, ScoringRule] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Setup default action handlers"""
        self.action_handlers = {
            "create_task": self._handle_create_task,
            "send_alert": self._handle_send_alert,
            "send_notification": self._handle_send_notification,
            "send_email": self._handle_send_email,
            "send_sms": self._handle_send_sms,
            "schedule_appointment": self._handle_schedule_appointment,
            "add_care_gap": self._handle_add_care_gap,
            "update_record": self._handle_update_record,
            "create_order": self._handle_create_order,
            "trigger_workflow": self._handle_trigger_workflow,
            "escalate": self._handle_escalate,
            "log_event": self._handle_log_event,
            "calculate_score": self._handle_calculate_score,
            "set_flag": self._handle_set_flag,
            "route_to_queue": self._handle_route_to_queue,
        }

    # ==================== Rule Management ====================

    def add_rule(self, rule: Rule) -> str:
        """Add a new rule"""
        self.rules[rule.id] = rule
        return rule.id

    def update_rule(self, rule_id: str, rule: Rule) -> bool:
        """Update an existing rule"""
        if rule_id not in self.rules:
            return False
        rule.updated_at = datetime.utcnow()
        rule.version = self._increment_version(self.rules[rule_id].version)
        self.rules[rule_id] = rule
        return True

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID"""
        return self.rules.get(rule_id)

    def list_rules(
        self,
        category: Optional[RuleCategory] = None,
        enabled: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> List[Rule]:
        """List rules with optional filtering"""
        rules = list(self.rules.values())

        if category:
            rules = [r for r in rules if r.category == category]

        if enabled is not None:
            rules = [r for r in rules if r.enabled == enabled]

        if tags:
            rules = [r for r in rules if any(t in r.tags for t in tags)]

        return rules

    # ==================== Rule Set Management ====================

    def create_rule_set(self, rule_set_id: str, rule_ids: List[str]) -> str:
        """Create a rule set from rule IDs"""
        # Validate all rules exist
        for rid in rule_ids:
            if rid not in self.rules:
                raise ValueError(f"Rule {rid} not found")
        self.rule_sets[rule_set_id] = rule_ids
        return rule_set_id

    def add_to_rule_set(self, rule_set_id: str, rule_id: str) -> bool:
        """Add a rule to a rule set"""
        if rule_set_id not in self.rule_sets:
            self.rule_sets[rule_set_id] = []
        if rule_id not in self.rule_sets[rule_set_id]:
            self.rule_sets[rule_set_id].append(rule_id)
            return True
        return False

    # ==================== Rule Evaluation ====================

    async def evaluate_rules(
        self,
        context: Dict[str, Any],
        rule_set_id: Optional[str] = None,
        category: Optional[RuleCategory] = None,
        stop_on_first_match: bool = False
    ) -> RuleSetResult:
        """Evaluate rules against a context"""
        start_time = datetime.utcnow()

        # Get applicable rules
        if rule_set_id and rule_set_id in self.rule_sets:
            rule_ids = self.rule_sets[rule_set_id]
            rules = [self.rules[rid] for rid in rule_ids if rid in self.rules]
        else:
            rules = list(self.rules.values())

        # Filter by category if specified
        if category:
            rules = [r for r in rules if r.category == category]

        # Filter active rules
        current_time = datetime.utcnow()
        rules = [
            r for r in rules
            if r.enabled
            and (not r.effective_date or r.effective_date <= current_time)
            and (not r.expiry_date or r.expiry_date >= current_time)
        ]

        # Sort by priority (descending)
        rules.sort(key=lambda x: x.priority, reverse=True)

        # Evaluate rules
        results = []
        total_actions = 0

        for rule in rules:
            result = await self._evaluate_rule(rule, context)
            results.append(result)

            if result.matched:
                total_actions += len(result.actions)

                if stop_on_first_match:
                    break

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return RuleSetResult(
            rules_evaluated=len(results),
            rules_matched=sum(1 for r in results if r.matched),
            total_actions=total_actions,
            results=results,
            execution_time_ms=execution_time
        )

    async def _evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a single rule"""
        start_time = datetime.utcnow()

        conditions_matched = 0
        conditions_evaluated = len(rule.conditions)

        # Evaluate conditions based on rule type
        if rule.type == RuleType.SIMPLE or rule.type == RuleType.COMPLEX:
            matched = self._evaluate_conditions(rule.conditions, context)
            conditions_matched = sum(1 for c in rule.conditions if c.evaluate(context))
        else:
            matched = self._evaluate_conditions(rule.conditions, context)
            conditions_matched = sum(1 for c in rule.conditions if c.evaluate(context))

        # Prepare actions if matched
        actions = []
        if matched:
            for action in rule.actions:
                prepared_action = await self._prepare_action(action, context)
                actions.append(prepared_action)

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return RuleEvaluationResult(
            rule_id=rule.id,
            rule_name=rule.name,
            matched=matched,
            conditions_evaluated=conditions_evaluated,
            conditions_matched=conditions_matched,
            actions=actions,
            execution_time_ms=execution_time
        )

    def _evaluate_conditions(self, conditions: List[RuleCondition], context: Dict) -> bool:
        """Evaluate a list of conditions with AND/OR logic"""
        if not conditions:
            return True

        # Group by logic operator
        and_conditions = [c for c in conditions if c.logic == "AND"]
        or_conditions = [c for c in conditions if c.logic == "OR"]

        # Evaluate AND conditions (all must be true)
        and_result = all(c.evaluate(context) for c in and_conditions) if and_conditions else True

        # Evaluate OR conditions (at least one must be true)
        or_result = any(c.evaluate(context) for c in or_conditions) if or_conditions else True

        return and_result and (or_result if or_conditions else True)

    async def _prepare_action(self, action: RuleAction, context: Dict) -> Dict[str, Any]:
        """Prepare action with resolved parameters"""
        resolved_params = {}

        for key, value in action.parameters.items():
            if isinstance(value, str) and "${" in value:
                resolved_params[key] = self._resolve_variable(value, context)
            else:
                resolved_params[key] = value

        return {
            "type": action.type,
            "parameters": resolved_params,
            "description": action.description
        }

    def _resolve_variable(self, expression: str, context: Dict) -> Any:
        """Resolve variable expression like ${patient.name}"""
        if not expression.startswith("${"):
            return expression

        # Extract variable path
        path = expression[2:-1]

        # Handle special variables
        if path == "today":
            return datetime.utcnow().date().isoformat()
        elif path.startswith("today + "):
            days = int(path.split("+")[1].strip().rstrip("d"))
            return (datetime.utcnow().date() + timedelta(days=days)).isoformat()
        elif path.startswith("today - "):
            days = int(path.split("-")[1].strip().rstrip("d"))
            return (datetime.utcnow().date() - timedelta(days=days)).isoformat()

        # Get from context
        return self._get_nested_value(path, context)

    def _get_nested_value(self, path: str, context: Dict) -> Any:
        """Get nested value from context"""
        parts = path.split('.')
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                value = value[idx] if idx < len(value) else None
            else:
                return None
        return value

    # ==================== Decision Table Evaluation ====================

    def add_decision_table(self, table: DecisionTable) -> str:
        """Add a decision table"""
        self.decision_tables[table.id] = table
        return table.id

    async def evaluate_decision_table(
        self,
        table_id: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Evaluate a decision table"""
        table = self.decision_tables.get(table_id)
        if not table or not table.enabled:
            return []

        matched_actions = []

        for row in table.rows:
            # Check if all conditions in the row match
            row_matches = True
            for field, expected_value in row.conditions.items():
                actual_value = self._get_nested_value(field, context)

                if isinstance(expected_value, dict):
                    # Complex condition
                    cond = RuleCondition(
                        field=field,
                        operator=expected_value.get("operator", "eq"),
                        value=expected_value.get("value")
                    )
                    if not cond.evaluate(context):
                        row_matches = False
                        break
                elif actual_value != expected_value:
                    row_matches = False
                    break

            if row_matches:
                for action in row.actions:
                    prepared = await self._prepare_action(action, context)
                    matched_actions.append(prepared)

                if table.hit_policy == "first":
                    break

        return matched_actions

    # ==================== Decision Tree Evaluation ====================

    def add_decision_tree(self, tree: DecisionTree) -> str:
        """Add a decision tree"""
        self.decision_trees[tree.id] = tree
        return tree.id

    async def evaluate_decision_tree(
        self,
        tree_id: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Evaluate a decision tree"""
        tree = self.decision_trees.get(tree_id)
        if not tree or not tree.enabled:
            return []

        # Traverse tree from root
        current_node_id = tree.root_node_id
        actions = []

        while current_node_id:
            node = tree.nodes.get(current_node_id)
            if not node:
                break

            if node.is_leaf:
                # Leaf node - execute actions
                if node.actions:
                    for action in node.actions:
                        prepared = await self._prepare_action(action, context)
                        actions.append(prepared)
                break

            # Evaluate condition and traverse
            if node.condition:
                if node.condition.evaluate(context):
                    current_node_id = node.true_node
                else:
                    current_node_id = node.false_node
            else:
                break

        return actions

    # ==================== Scoring Rules ====================

    def add_scoring_rule(self, rule: ScoringRule) -> str:
        """Add a scoring rule"""
        self.scoring_rules[rule.id] = rule
        return rule.id

    async def evaluate_scoring_rule(
        self,
        rule_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a scoring rule"""
        rule = self.scoring_rules.get(rule_id)
        if not rule or not rule.enabled:
            return {"score": 0, "category": "unknown"}

        total_score = 0.0

        for factor in rule.scoring_factors:
            condition = RuleCondition(
                field=factor.get("field", ""),
                operator=factor.get("operator", "exists"),
                value=factor.get("value")
            )

            if condition.evaluate(context):
                total_score += factor.get("weight", 0)

        # Determine category based on thresholds
        category = "low"
        for cat, threshold in sorted(rule.thresholds.items(), key=lambda x: x[1]):
            if total_score >= threshold:
                category = cat

        return {
            "score": total_score,
            "category": category,
            "rule_id": rule_id,
            "rule_name": rule.name
        }

    # ==================== Action Handlers ====================

    async def execute_actions(
        self,
        actions: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute a list of actions"""
        results = []

        for action in actions:
            action_type = action.get("type")
            handler = self.action_handlers.get(action_type)

            if handler:
                try:
                    result = await handler(action.get("parameters", {}), context)
                    results.append({
                        "action": action_type,
                        "status": ActionStatus.EXECUTED.value,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "action": action_type,
                        "status": ActionStatus.FAILED.value,
                        "error": str(e)
                    })
            else:
                results.append({
                    "action": action_type,
                    "status": ActionStatus.SKIPPED.value,
                    "reason": "No handler registered"
                })

        return results

    # Default action handlers
    async def _handle_create_task(self, params: Dict, context: Dict) -> Dict:
        return {"task_id": str(uuid4()), "status": "created", **params}

    async def _handle_send_alert(self, params: Dict, context: Dict) -> Dict:
        return {"alert_id": str(uuid4()), "status": "sent", **params}

    async def _handle_send_notification(self, params: Dict, context: Dict) -> Dict:
        return {"notification_id": str(uuid4()), "status": "sent", **params}

    async def _handle_send_email(self, params: Dict, context: Dict) -> Dict:
        return {"email_id": str(uuid4()), "status": "queued", **params}

    async def _handle_send_sms(self, params: Dict, context: Dict) -> Dict:
        return {"sms_id": str(uuid4()), "status": "queued", **params}

    async def _handle_schedule_appointment(self, params: Dict, context: Dict) -> Dict:
        return {"appointment_id": str(uuid4()), "status": "scheduled", **params}

    async def _handle_add_care_gap(self, params: Dict, context: Dict) -> Dict:
        return {"care_gap_id": str(uuid4()), "status": "created", **params}

    async def _handle_update_record(self, params: Dict, context: Dict) -> Dict:
        return {"status": "updated", **params}

    async def _handle_create_order(self, params: Dict, context: Dict) -> Dict:
        return {"order_id": str(uuid4()), "status": "created", **params}

    async def _handle_trigger_workflow(self, params: Dict, context: Dict) -> Dict:
        return {"workflow_execution_id": str(uuid4()), "status": "triggered", **params}

    async def _handle_escalate(self, params: Dict, context: Dict) -> Dict:
        return {"escalation_id": str(uuid4()), "status": "escalated", **params}

    async def _handle_log_event(self, params: Dict, context: Dict) -> Dict:
        return {"event_id": str(uuid4()), "status": "logged", **params}

    async def _handle_calculate_score(self, params: Dict, context: Dict) -> Dict:
        return {"score": 0, "status": "calculated", **params}

    async def _handle_set_flag(self, params: Dict, context: Dict) -> Dict:
        return {"status": "flag_set", **params}

    async def _handle_route_to_queue(self, params: Dict, context: Dict) -> Dict:
        return {"queue": params.get("queue"), "status": "routed"}

    # ==================== Utilities ====================

    def _increment_version(self, version: str) -> str:
        """Increment semantic version"""
        parts = version.split('.')
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
        return '.'.join(parts)

    def register_action_handler(self, action_type: str, handler: Callable):
        """Register a custom action handler"""
        self.action_handlers[action_type] = handler

    async def test_rule(self, rule: Rule, test_cases: List[Dict]) -> List[Dict]:
        """Test a rule against test cases"""
        results = []

        for i, test_case in enumerate(test_cases):
            context = test_case.get("context", {})
            expected_match = test_case.get("expected_match", True)

            result = await self._evaluate_rule(rule, context)

            results.append({
                "test_case": i + 1,
                "passed": result.matched == expected_match,
                "expected_match": expected_match,
                "actual_match": result.matched,
                "conditions_matched": result.conditions_matched,
                "actions": result.actions if result.matched else []
            })

        return results


# Pre-built healthcare rules
class HealthcareRules:
    """Factory for common healthcare rules"""

    @staticmethod
    def readmission_risk_rule() -> Rule:
        """Rule for high readmission risk patients"""
        return Rule(
            id="readmission_risk_001",
            name="High Readmission Risk Alert",
            description="Identify patients at high risk of readmission within 30 days",
            type=RuleType.COMPLEX,
            category=RuleCategory.CLINICAL,
            conditions=[
                RuleCondition(field="patient.readmission_score", operator="gte", value=0.7),
                RuleCondition(field="patient.discharge_date", operator="days_since", value=0),
                RuleCondition(field="patient.chronic_conditions_count", operator="gte", value=3, logic="OR"),
                RuleCondition(field="patient.age", operator="gte", value=65, logic="OR"),
            ],
            actions=[
                RuleAction(
                    type="create_task",
                    parameters={
                        "task_type": "follow_up_call",
                        "priority": "high",
                        "assigned_role": "care_coordinator",
                        "due_hours": 24
                    }
                ),
                RuleAction(
                    type="send_alert",
                    parameters={
                        "recipient": "${patient.primary_provider_id}",
                        "message": "Patient at high risk of readmission",
                        "severity": "warning"
                    }
                ),
                RuleAction(
                    type="schedule_appointment",
                    parameters={
                        "appointment_type": "follow_up",
                        "provider_id": "${patient.primary_provider_id}",
                        "timeframe_days": 7
                    }
                )
            ],
            priority=RulePriority.HIGH.value,
            tags=["readmission", "risk", "clinical"]
        )

    @staticmethod
    def diabetes_care_gap_rule() -> Rule:
        """Rule for diabetes care gaps"""
        return Rule(
            id="diabetes_care_gap_001",
            name="Diabetes HbA1c Screening Gap",
            description="Identify diabetic patients overdue for HbA1c testing",
            type=RuleType.SIMPLE,
            category=RuleCategory.QUALITY,
            conditions=[
                RuleCondition(field="patient.conditions", operator="contains", value="diabetes"),
                RuleCondition(field="patient.last_hba1c_date", operator="days_since", value=180),
            ],
            actions=[
                RuleAction(
                    type="add_care_gap",
                    parameters={
                        "gap_type": "lab_test",
                        "description": "HbA1c test overdue",
                        "priority": "high",
                        "measure_id": "NQF0059"
                    }
                ),
                RuleAction(
                    type="send_notification",
                    parameters={
                        "channel": "patient_portal",
                        "template": "lab_reminder",
                        "test_type": "HbA1c"
                    }
                )
            ],
            priority=RulePriority.MEDIUM.value,
            tags=["diabetes", "care_gap", "quality"]
        )

    @staticmethod
    def appointment_no_show_rule() -> Rule:
        """Rule for high no-show risk appointments"""
        return Rule(
            id="appointment_no_show_001",
            name="High No-Show Risk Intervention",
            description="Proactive intervention for appointments with high no-show probability",
            type=RuleType.COMPLEX,
            category=RuleCategory.SCHEDULING,
            conditions=[
                RuleCondition(field="appointment.no_show_probability", operator="gte", value=0.4),
                RuleCondition(field="appointment.days_until", operator="lte", value=3),
            ],
            actions=[
                RuleAction(
                    type="send_sms",
                    parameters={
                        "recipient": "${patient.phone}",
                        "template": "appointment_reminder_urgent",
                        "appointment_date": "${appointment.date}",
                        "appointment_time": "${appointment.time}"
                    }
                ),
                RuleAction(
                    type="create_task",
                    parameters={
                        "task_type": "confirmation_call",
                        "priority": "high",
                        "assigned_role": "scheduler",
                        "due_hours": 24
                    }
                )
            ],
            priority=RulePriority.HIGH.value,
            tags=["appointment", "no_show", "scheduling"]
        )

    @staticmethod
    def preventive_screening_rule(
        screening_type: str,
        age_min: int,
        age_max: Optional[int],
        interval_years: int
    ) -> Rule:
        """Generic rule for preventive screening"""
        conditions = [
            RuleCondition(field="patient.age", operator="gte", value=age_min),
            RuleCondition(
                field=f"patient.last_{screening_type}_date",
                operator="days_since",
                value=interval_years * 365
            ),
        ]

        if age_max:
            conditions.append(RuleCondition(field="patient.age", operator="lte", value=age_max))

        return Rule(
            id=f"preventive_{screening_type}_001",
            name=f"Preventive {screening_type.title()} Screening",
            description=f"Identify patients due for {screening_type} screening",
            type=RuleType.COMPLEX,
            category=RuleCategory.QUALITY,
            conditions=conditions,
            actions=[
                RuleAction(
                    type="add_care_gap",
                    parameters={
                        "gap_type": "preventive_screening",
                        "description": f"{screening_type.title()} screening due",
                        "priority": "medium"
                    }
                ),
                RuleAction(
                    type="send_notification",
                    parameters={
                        "channel": "patient_portal",
                        "template": "screening_reminder",
                        "screening_type": screening_type
                    }
                )
            ],
            priority=RulePriority.MEDIUM.value,
            tags=["preventive", "screening", screening_type]
        )


# Singleton instance
business_rule_engine = BusinessRuleEngine()


def get_business_rule_engine() -> BusinessRuleEngine:
    """Get the singleton business rule engine instance"""
    return business_rule_engine


# Import timedelta for date calculations
from datetime import timedelta

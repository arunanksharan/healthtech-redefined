"""
Remote Patient Monitoring (RPM) Module

This module provides comprehensive RPM capabilities including:
- Device integration (Withings, Apple Health, Google Fit, BLE devices)
- High-throughput biometric data ingestion
- Alert management with AI-powered anomaly detection
- Care protocol automation
- CPT billing code support (99453, 99454, 99457, 99458)
- Patient engagement features
- Trend analysis and population health metrics
"""

from modules.rpm.models import (
    # Enums
    DeviceType,
    DeviceStatus,
    DeviceVendor,
    ReadingType,
    ReadingStatus,
    AlertSeverity,
    AlertStatus,
    AlertType,
    ProtocolStatus,
    ProtocolTriggerType,
    ProtocolActionType,
    EnrollmentStatus,
    BillingCodeType,
    OutreachChannel,
    # Models
    RPMDevice,
    DeviceAssignment,
    DeviceReading,
    ReadingBatch,
    DataQualityMetric,
    AlertRule,
    PatientAlertRule,
    RPMAlert,
    AlertNotification,
    CareProtocol,
    ProtocolTrigger,
    ProtocolAction,
    ProtocolExecution,
    RPMEnrollment,
    MonitoringPeriod,
    ClinicalTimeEntry,
    RPMBillingEvent,
    PatientReminder,
    PatientGoal,
    EducationalContent,
    PatientContentEngagement,
    PatientTrendAnalysis,
    PopulationHealthMetric,
)

from modules.rpm.router import router

from modules.rpm.services import (
    DeviceService,
    ReadingService,
    AlertService,
    ProtocolService,
    EnrollmentService,
    BillingService,
    EngagementService,
    AnalyticsService,
    IntegrationService,
)

__all__ = [
    # Router
    "router",
    # Enums
    "DeviceType",
    "DeviceStatus",
    "DeviceVendor",
    "ReadingType",
    "ReadingStatus",
    "AlertSeverity",
    "AlertStatus",
    "AlertType",
    "ProtocolStatus",
    "ProtocolTriggerType",
    "ProtocolActionType",
    "EnrollmentStatus",
    "BillingCodeType",
    "OutreachChannel",
    # Models
    "RPMDevice",
    "DeviceAssignment",
    "DeviceReading",
    "ReadingBatch",
    "DataQualityMetric",
    "AlertRule",
    "PatientAlertRule",
    "RPMAlert",
    "AlertNotification",
    "CareProtocol",
    "ProtocolTrigger",
    "ProtocolAction",
    "ProtocolExecution",
    "RPMEnrollment",
    "MonitoringPeriod",
    "ClinicalTimeEntry",
    "RPMBillingEvent",
    "PatientReminder",
    "PatientGoal",
    "EducationalContent",
    "PatientContentEngagement",
    "PatientTrendAnalysis",
    "PopulationHealthMetric",
    # Services
    "DeviceService",
    "ReadingService",
    "AlertService",
    "ProtocolService",
    "EnrollmentService",
    "BillingService",
    "EngagementService",
    "AnalyticsService",
    "IntegrationService",
]

"""
Mobile Applications Module
EPIC-016: Mobile Platform for Healthcare

This module provides:
- Device registration and management
- Push notification infrastructure (FCM, APNs)
- Offline-first sync with delta updates
- Wearable device integration
- Health metrics and goals tracking
- Biometric authentication
- Mobile session management
- App analytics and crash reporting
"""

from modules.mobile.router import router
from modules.mobile.models import (
    MobileDevice, MobileSession, PushNotification,
    NotificationPreference, SyncCheckpoint, SyncQueue,
    SyncConflict, WearableDevice, HealthMetric,
    HealthMetricGoal, AppUsageEvent, AppCrashReport,
    MobileAuditLog
)
from modules.mobile.services import (
    DeviceService,
    PushNotificationService,
    MobileSyncService,
    WearableService,
    MobileAuthService
)

__all__ = [
    # Router
    "router",
    # Models
    "MobileDevice",
    "MobileSession",
    "PushNotification",
    "NotificationPreference",
    "SyncCheckpoint",
    "SyncQueue",
    "SyncConflict",
    "WearableDevice",
    "HealthMetric",
    "HealthMetricGoal",
    "AppUsageEvent",
    "AppCrashReport",
    "MobileAuditLog",
    # Services
    "DeviceService",
    "PushNotificationService",
    "MobileSyncService",
    "WearableService",
    "MobileAuthService"
]

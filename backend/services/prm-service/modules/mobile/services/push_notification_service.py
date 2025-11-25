"""
Push Notification Service
EPIC-016: FCM and APNs push notification handling
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import json
import hashlib
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc

from modules.mobile.models import (
    MobileDevice, PushNotification, NotificationPreference,
    DevicePlatform, DeviceStatus, NotificationType,
    NotificationPriority, NotificationStatus
)
from modules.mobile.schemas import (
    NotificationSend, NotificationBulkSend, NotificationResponse,
    NotificationListResponse, NotificationPreferenceUpdate,
    NotificationPreferenceResponse
)


class PushNotificationService:
    """
    Handles push notification delivery:
    - FCM (Firebase Cloud Messaging) for Android
    - APNs (Apple Push Notification Service) for iOS
    - Notification scheduling and batching
    - Delivery tracking and analytics
    """

    def __init__(self):
        # FCM and APNs clients would be initialized here
        self._fcm_client = None
        self._apns_client = None

    async def send_notification(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        data: NotificationSend,
        sender_id: UUID = None
    ) -> NotificationResponse:
        """Send a push notification to a user's devices"""

        # Get user's active devices with notifications enabled
        from modules.mobile.services.device_service import DeviceService
        device_service = DeviceService()
        devices = await device_service.get_devices_for_notification(
            db, user_id, tenant_id
        )

        if not devices:
            raise ValueError("No devices available for notification")

        # Check user preferences
        preferences = await self._get_user_preferences(db, user_id, tenant_id)
        if preferences and not self._should_send(data.notification_type, preferences):
            raise ValueError("User has disabled this notification type")

        # Check quiet hours
        if preferences and self._in_quiet_hours(preferences):
            if data.priority != NotificationPriority.CRITICAL:
                # Schedule for after quiet hours
                scheduled_time = self._get_quiet_hours_end(preferences)
                return await self.schedule_notification(
                    db, tenant_id, user_id, data, scheduled_time, sender_id
                )

        # Create notification record
        notification = PushNotification(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=NotificationType(data.notification_type.value),
            priority=NotificationPriority(data.priority.value) if data.priority else NotificationPriority.NORMAL,
            title=data.title,
            body=data.body,
            data_payload=data.data or {},
            image_url=data.image_url,
            action_url=data.action_url,
            action_type=data.action_type,
            category=data.category,
            thread_id=data.thread_id,
            collapse_key=data.collapse_key,
            badge_count=data.badge_count,
            sound=data.sound or "default",
            silent=data.silent or False,
            status=NotificationStatus.PENDING,
            reference_type=data.reference_type,
            reference_id=data.reference_id
        )
        db.add(notification)

        # Send to each device
        sent_count = 0
        failed_devices = []

        for device in devices:
            try:
                success = await self._send_to_device(
                    device, notification, data
                )
                if success:
                    sent_count += 1
                else:
                    failed_devices.append(device.id)
            except Exception as e:
                failed_devices.append(device.id)

        # Update notification status
        if sent_count > 0:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            notification.sent_to_devices = [str(d.id) for d in devices if d.id not in failed_devices]
        else:
            notification.status = NotificationStatus.FAILED
            notification.error_message = "Failed to deliver to any device"

        await db.commit()
        await db.refresh(notification)

        return self._notification_to_response(notification)

    async def send_bulk_notification(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: NotificationBulkSend,
        sender_id: UUID = None
    ) -> List[NotificationResponse]:
        """Send notification to multiple users"""

        results = []

        for user_id in data.user_ids:
            try:
                notification_data = NotificationSend(
                    notification_type=data.notification_type,
                    priority=data.priority,
                    title=data.title,
                    body=data.body,
                    data=data.data,
                    image_url=data.image_url,
                    action_url=data.action_url,
                    action_type=data.action_type,
                    category=data.category,
                    collapse_key=data.collapse_key
                )

                result = await self.send_notification(
                    db, tenant_id, user_id, notification_data, sender_id
                )
                results.append(result)
            except Exception:
                # Skip users where notification fails
                continue

        return results

    async def schedule_notification(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        data: NotificationSend,
        scheduled_time: datetime,
        sender_id: UUID = None
    ) -> NotificationResponse:
        """Schedule a notification for later delivery"""

        notification = PushNotification(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=NotificationType(data.notification_type.value),
            priority=NotificationPriority(data.priority.value) if data.priority else NotificationPriority.NORMAL,
            title=data.title,
            body=data.body,
            data_payload=data.data or {},
            image_url=data.image_url,
            action_url=data.action_url,
            action_type=data.action_type,
            category=data.category,
            thread_id=data.thread_id,
            collapse_key=data.collapse_key,
            badge_count=data.badge_count,
            sound=data.sound or "default",
            silent=data.silent or False,
            status=NotificationStatus.SCHEDULED,
            scheduled_at=scheduled_time,
            reference_type=data.reference_type,
            reference_id=data.reference_id
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return self._notification_to_response(notification)

    async def process_scheduled_notifications(
        self,
        db: AsyncSession
    ) -> int:
        """Process notifications that are due for delivery"""

        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(PushNotification).where(
                and_(
                    PushNotification.status == NotificationStatus.SCHEDULED,
                    PushNotification.scheduled_at <= now
                )
            ).limit(100)  # Process in batches
        )
        notifications = result.scalars().all()

        processed = 0
        for notification in notifications:
            try:
                # Get devices and send
                from modules.mobile.services.device_service import DeviceService
                device_service = DeviceService()
                devices = await device_service.get_devices_for_notification(
                    db, notification.user_id, notification.tenant_id
                )

                if devices:
                    sent_count = 0
                    for device in devices:
                        try:
                            success = await self._send_to_device_raw(
                                device,
                                notification.title,
                                notification.body,
                                notification.data_payload,
                                notification.priority
                            )
                            if success:
                                sent_count += 1
                        except Exception:
                            continue

                    if sent_count > 0:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = now
                        notification.sent_to_devices = [str(d.id) for d in devices]
                    else:
                        notification.status = NotificationStatus.FAILED
                        notification.error_message = "Failed to deliver"
                else:
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = "No devices available"

                processed += 1
            except Exception as e:
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(e)

        await db.commit()
        return processed

    async def mark_notification_read(
        self,
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID
    ) -> None:
        """Mark a notification as read"""

        await db.execute(
            update(PushNotification).where(
                and_(
                    PushNotification.id == notification_id,
                    PushNotification.user_id == user_id
                )
            ).values(
                read_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()

    async def mark_notification_clicked(
        self,
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID
    ) -> None:
        """Mark a notification as clicked/interacted"""

        await db.execute(
            update(PushNotification).where(
                and_(
                    PushNotification.id == notification_id,
                    PushNotification.user_id == user_id
                )
            ).values(
                clicked_at=datetime.now(timezone.utc),
                read_at=func.coalesce(
                    PushNotification.read_at,
                    datetime.now(timezone.utc)
                )
            )
        )
        await db.commit()

    async def cancel_notification(
        self,
        db: AsyncSession,
        notification_id: UUID,
        tenant_id: UUID
    ) -> None:
        """Cancel a scheduled notification"""

        result = await db.execute(
            select(PushNotification).where(
                and_(
                    PushNotification.id == notification_id,
                    PushNotification.tenant_id == tenant_id,
                    PushNotification.status == NotificationStatus.SCHEDULED
                )
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise ValueError("Notification not found or cannot be cancelled")

        notification.status = NotificationStatus.CANCELLED
        await db.commit()

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> NotificationListResponse:
        """Get notifications for a user"""

        query = select(PushNotification).where(
            and_(
                PushNotification.user_id == user_id,
                PushNotification.tenant_id == tenant_id,
                PushNotification.status.in_([
                    NotificationStatus.SENT,
                    NotificationStatus.DELIVERED
                ])
            )
        )

        if unread_only:
            query = query.where(PushNotification.read_at.is_(None))

        if notification_type:
            query = query.where(PushNotification.notification_type == notification_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(PushNotification.created_at))
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        notifications = result.scalars().all()

        # Count unread
        unread_query = select(func.count()).where(
            and_(
                PushNotification.user_id == user_id,
                PushNotification.tenant_id == tenant_id,
                PushNotification.status.in_([
                    NotificationStatus.SENT,
                    NotificationStatus.DELIVERED
                ]),
                PushNotification.read_at.is_(None)
            )
        )
        unread_result = await db.execute(unread_query)
        unread_count = unread_result.scalar()

        return NotificationListResponse(
            notifications=[self._notification_to_response(n) for n in notifications],
            total=total,
            unread_count=unread_count
        )

    async def mark_all_read(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> int:
        """Mark all notifications as read for a user"""

        result = await db.execute(
            update(PushNotification).where(
                and_(
                    PushNotification.user_id == user_id,
                    PushNotification.tenant_id == tenant_id,
                    PushNotification.read_at.is_(None)
                )
            ).values(
                read_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()
        return result.rowcount

    async def update_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        device_id: UUID,
        data: NotificationPreferenceUpdate
    ) -> NotificationPreferenceResponse:
        """Update notification preferences for a device"""

        result = await db.execute(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.tenant_id == tenant_id,
                    NotificationPreference.device_id == device_id
                )
            )
        )
        preferences = result.scalar_one_or_none()

        if not preferences:
            preferences = NotificationPreference(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                device_id=device_id
            )
            db.add(preferences)

        if data.enabled is not None:
            preferences.enabled = data.enabled
        if data.appointment_reminders is not None:
            preferences.appointment_reminders = data.appointment_reminders
        if data.medication_reminders is not None:
            preferences.medication_reminders = data.medication_reminders
        if data.health_alerts is not None:
            preferences.health_alerts = data.health_alerts
        if data.lab_results is not None:
            preferences.lab_results = data.lab_results
        if data.messages is not None:
            preferences.messages = data.messages
        if data.billing_alerts is not None:
            preferences.billing_alerts = data.billing_alerts
        if data.marketing is not None:
            preferences.marketing = data.marketing
        if data.quiet_hours_enabled is not None:
            preferences.quiet_hours_enabled = data.quiet_hours_enabled
        if data.quiet_hours_start is not None:
            preferences.quiet_hours_start = data.quiet_hours_start
        if data.quiet_hours_end is not None:
            preferences.quiet_hours_end = data.quiet_hours_end
        if data.quiet_hours_timezone is not None:
            preferences.quiet_hours_timezone = data.quiet_hours_timezone
        if data.frequency_limit is not None:
            preferences.frequency_limit = data.frequency_limit
        if data.sound_enabled is not None:
            preferences.sound_enabled = data.sound_enabled
        if data.vibration_enabled is not None:
            preferences.vibration_enabled = data.vibration_enabled
        if data.badge_enabled is not None:
            preferences.badge_enabled = data.badge_enabled

        preferences.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(preferences)

        return self._preferences_to_response(preferences)

    async def get_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        device_id: Optional[UUID] = None
    ) -> NotificationPreferenceResponse:
        """Get notification preferences"""

        query = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.tenant_id == tenant_id
            )
        )

        if device_id:
            query = query.where(NotificationPreference.device_id == device_id)

        result = await db.execute(query)
        preferences = result.scalar_one_or_none()

        if not preferences:
            # Return defaults
            return NotificationPreferenceResponse(
                enabled=True,
                appointment_reminders=True,
                medication_reminders=True,
                health_alerts=True,
                lab_results=True,
                messages=True,
                billing_alerts=True,
                marketing=False,
                quiet_hours_enabled=False,
                sound_enabled=True,
                vibration_enabled=True,
                badge_enabled=True
            )

        return self._preferences_to_response(preferences)

    async def send_topic_notification(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        topic: str,
        title: str,
        body: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send notification to a topic (broadcast)"""

        # FCM topic messaging would be implemented here
        # This is a placeholder for topic-based notifications

        return {
            "topic": topic,
            "status": "sent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def update_delivery_status(
        self,
        db: AsyncSession,
        notification_id: UUID,
        status: str,
        delivered_at: datetime = None,
        error_message: str = None
    ) -> None:
        """Update notification delivery status (called by FCM/APNs callback)"""

        values = {}
        if status == "delivered":
            values["status"] = NotificationStatus.DELIVERED
            values["delivered_at"] = delivered_at or datetime.now(timezone.utc)
        elif status == "failed":
            values["status"] = NotificationStatus.FAILED
            values["error_message"] = error_message

        if values:
            await db.execute(
                update(PushNotification).where(
                    PushNotification.id == notification_id
                ).values(**values)
            )
            await db.commit()

    async def get_notification_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get notification delivery statistics"""

        # Total sent
        sent_query = select(func.count()).where(
            and_(
                PushNotification.tenant_id == tenant_id,
                PushNotification.status.in_([
                    NotificationStatus.SENT,
                    NotificationStatus.DELIVERED
                ]),
                PushNotification.sent_at >= start_date,
                PushNotification.sent_at <= end_date
            )
        )
        sent_result = await db.execute(sent_query)
        total_sent = sent_result.scalar()

        # Delivered
        delivered_query = select(func.count()).where(
            and_(
                PushNotification.tenant_id == tenant_id,
                PushNotification.status == NotificationStatus.DELIVERED,
                PushNotification.delivered_at >= start_date,
                PushNotification.delivered_at <= end_date
            )
        )
        delivered_result = await db.execute(delivered_query)
        total_delivered = delivered_result.scalar()

        # Read
        read_query = select(func.count()).where(
            and_(
                PushNotification.tenant_id == tenant_id,
                PushNotification.read_at.isnot(None),
                PushNotification.read_at >= start_date,
                PushNotification.read_at <= end_date
            )
        )
        read_result = await db.execute(read_query)
        total_read = read_result.scalar()

        # Clicked
        clicked_query = select(func.count()).where(
            and_(
                PushNotification.tenant_id == tenant_id,
                PushNotification.clicked_at.isnot(None),
                PushNotification.clicked_at >= start_date,
                PushNotification.clicked_at <= end_date
            )
        )
        clicked_result = await db.execute(clicked_query)
        total_clicked = clicked_result.scalar()

        # By type
        type_query = select(
            PushNotification.notification_type,
            func.count()
        ).where(
            and_(
                PushNotification.tenant_id == tenant_id,
                PushNotification.sent_at >= start_date,
                PushNotification.sent_at <= end_date
            )
        ).group_by(PushNotification.notification_type)
        type_result = await db.execute(type_query)
        by_type = {str(row[0].value): row[1] for row in type_result}

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_sent": total_sent,
            "total_delivered": total_delivered,
            "total_read": total_read,
            "total_clicked": total_clicked,
            "delivery_rate": (total_delivered / total_sent * 100) if total_sent > 0 else 0,
            "read_rate": (total_read / total_sent * 100) if total_sent > 0 else 0,
            "click_rate": (total_clicked / total_sent * 100) if total_sent > 0 else 0,
            "by_type": by_type
        }

    # Private helper methods

    async def _get_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> Optional[NotificationPreference]:
        """Get user's notification preferences"""

        result = await db.execute(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.tenant_id == tenant_id
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    def _should_send(
        self,
        notification_type: NotificationType,
        preferences: NotificationPreference
    ) -> bool:
        """Check if notification should be sent based on preferences"""

        if not preferences.enabled:
            return False

        type_map = {
            NotificationType.APPOINTMENT_REMINDER: preferences.appointment_reminders,
            NotificationType.APPOINTMENT_CONFIRMATION: preferences.appointment_reminders,
            NotificationType.APPOINTMENT_CANCELLED: preferences.appointment_reminders,
            NotificationType.MEDICATION_REMINDER: preferences.medication_reminders,
            NotificationType.REFILL_REMINDER: preferences.medication_reminders,
            NotificationType.HEALTH_ALERT: preferences.health_alerts,
            NotificationType.VITAL_ALERT: preferences.health_alerts,
            NotificationType.LAB_RESULT: preferences.lab_results,
            NotificationType.MESSAGE: preferences.messages,
            NotificationType.SECURE_MESSAGE: preferences.messages,
            NotificationType.BILLING_ALERT: preferences.billing_alerts,
            NotificationType.PAYMENT_DUE: preferences.billing_alerts,
            NotificationType.PAYMENT_RECEIVED: preferences.billing_alerts,
            NotificationType.GENERAL: True,
            NotificationType.PROMOTIONAL: preferences.marketing
        }

        return type_map.get(notification_type, True)

    def _in_quiet_hours(self, preferences: NotificationPreference) -> bool:
        """Check if current time is within quiet hours"""

        if not preferences.quiet_hours_enabled:
            return False

        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False

        # Simple check - in production would use timezone
        now = datetime.now(timezone.utc).time()
        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end

        if start <= end:
            return start <= now <= end
        else:
            # Quiet hours span midnight
            return now >= start or now <= end

    def _get_quiet_hours_end(self, preferences: NotificationPreference) -> datetime:
        """Get datetime when quiet hours end"""

        now = datetime.now(timezone.utc)
        end_time = preferences.quiet_hours_end

        # Combine date with end time
        result = datetime.combine(now.date(), end_time, timezone.utc)

        # If end time already passed today, schedule for tomorrow
        if result < now:
            result = result + timedelta(days=1)

        return result

    async def _send_to_device(
        self,
        device: MobileDevice,
        notification: PushNotification,
        data: NotificationSend
    ) -> bool:
        """Send notification to a specific device"""

        return await self._send_to_device_raw(
            device,
            notification.title,
            notification.body,
            notification.data_payload,
            notification.priority
        )

    async def _send_to_device_raw(
        self,
        device: MobileDevice,
        title: str,
        body: str,
        data: Dict[str, Any],
        priority: NotificationPriority
    ) -> bool:
        """Send notification payload to device"""

        if not device.device_token:
            return False

        if device.platform == DevicePlatform.IOS:
            return await self._send_apns(device, title, body, data, priority)
        elif device.platform == DevicePlatform.ANDROID:
            return await self._send_fcm(device, title, body, data, priority)

        return False

    async def _send_fcm(
        self,
        device: MobileDevice,
        title: str,
        body: str,
        data: Dict[str, Any],
        priority: NotificationPriority
    ) -> bool:
        """Send via Firebase Cloud Messaging"""

        # In production, this would use firebase-admin SDK
        # Example implementation:
        #
        # message = messaging.Message(
        #     notification=messaging.Notification(
        #         title=title,
        #         body=body
        #     ),
        #     data=data,
        #     token=device.device_token,
        #     android=messaging.AndroidConfig(
        #         priority="high" if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else "normal"
        #     )
        # )
        # response = messaging.send(message)

        # Placeholder - would integrate with FCM
        return True

    async def _send_apns(
        self,
        device: MobileDevice,
        title: str,
        body: str,
        data: Dict[str, Any],
        priority: NotificationPriority
    ) -> bool:
        """Send via Apple Push Notification Service"""

        # In production, this would use aioapns or similar library
        # Example implementation:
        #
        # payload = {
        #     "aps": {
        #         "alert": {
        #             "title": title,
        #             "body": body
        #         },
        #         "sound": "default"
        #     },
        #     **data
        # }
        # await apns_client.send_notification(
        #     device_token=device.device_token,
        #     payload=payload
        # )

        # Placeholder - would integrate with APNs
        return True

    def _notification_to_response(self, notification: PushNotification) -> NotificationResponse:
        """Convert notification model to response"""
        return NotificationResponse(
            id=notification.id,
            notification_type=notification.notification_type.value,
            priority=notification.priority.value,
            title=notification.title,
            body=notification.body,
            data=notification.data_payload,
            image_url=notification.image_url,
            action_url=notification.action_url,
            action_type=notification.action_type,
            category=notification.category,
            status=notification.status.value,
            scheduled_at=notification.scheduled_at,
            sent_at=notification.sent_at,
            delivered_at=notification.delivered_at,
            read_at=notification.read_at,
            clicked_at=notification.clicked_at,
            created_at=notification.created_at
        )

    def _preferences_to_response(self, preferences: NotificationPreference) -> NotificationPreferenceResponse:
        """Convert preferences model to response"""
        return NotificationPreferenceResponse(
            enabled=preferences.enabled,
            appointment_reminders=preferences.appointment_reminders,
            medication_reminders=preferences.medication_reminders,
            health_alerts=preferences.health_alerts,
            lab_results=preferences.lab_results,
            messages=preferences.messages,
            billing_alerts=preferences.billing_alerts,
            marketing=preferences.marketing,
            quiet_hours_enabled=preferences.quiet_hours_enabled,
            quiet_hours_start=preferences.quiet_hours_start.isoformat() if preferences.quiet_hours_start else None,
            quiet_hours_end=preferences.quiet_hours_end.isoformat() if preferences.quiet_hours_end else None,
            quiet_hours_timezone=preferences.quiet_hours_timezone,
            frequency_limit=preferences.frequency_limit,
            sound_enabled=preferences.sound_enabled,
            vibration_enabled=preferences.vibration_enabled,
            badge_enabled=preferences.badge_enabled
        )

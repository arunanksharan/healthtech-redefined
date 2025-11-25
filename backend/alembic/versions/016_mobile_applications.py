"""Mobile Applications Platform

Revision ID: 016_mobile_applications
Revises: 015_provider_collaboration
Create Date: 2024-11-25

EPIC-016: Mobile Applications Platform
- Device registration and management
- Push notifications
- Mobile sync infrastructure
- Wearable device integration
- Health metrics tracking
- Mobile analytics
- Mobile audit logging
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '016_mobile_applications'
down_revision = '015_provider_collaboration'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    device_platform = postgresql.ENUM(
        'ios', 'android', 'web', 'watchos', 'wearos',
        name='deviceplatform'
    )
    device_platform.create(op.get_bind())

    device_status = postgresql.ENUM(
        'active', 'inactive', 'suspended', 'revoked',
        name='devicestatus'
    )
    device_status.create(op.get_bind())

    notification_type = postgresql.ENUM(
        'appointment_reminder', 'medication_reminder', 'lab_result',
        'message', 'health_alert', 'health_tip', 'emergency',
        'system', 'promotional',
        name='notificationtype'
    )
    notification_type.create(op.get_bind())

    notification_priority = postgresql.ENUM(
        'low', 'normal', 'high', 'critical',
        name='notificationpriority'
    )
    notification_priority.create(op.get_bind())

    notification_status = postgresql.ENUM(
        'pending', 'sent', 'delivered', 'read', 'failed', 'expired',
        name='notificationstatus'
    )
    notification_status.create(op.get_bind())

    sync_entity_type = postgresql.ENUM(
        'patient', 'appointment', 'health_record', 'medication',
        'message', 'document', 'provider', 'care_team', 'notification',
        name='syncentitytype'
    )
    sync_entity_type.create(op.get_bind())

    sync_operation_type = postgresql.ENUM(
        'create', 'update', 'delete',
        name='syncoperationtype'
    )
    sync_operation_type.create(op.get_bind())

    sync_status = postgresql.ENUM(
        'pending', 'in_progress', 'completed', 'failed', 'conflict',
        name='syncstatus'
    )
    sync_status.create(op.get_bind())

    wearable_type = postgresql.ENUM(
        'apple_watch', 'wear_os', 'fitbit', 'garmin',
        'samsung_galaxy', 'whoop', 'oura', 'other',
        name='wearabletype'
    )
    wearable_type.create(op.get_bind())

    health_metric_type = postgresql.ENUM(
        'heart_rate', 'heart_rate_variability', 'blood_oxygen',
        'blood_pressure', 'blood_glucose', 'steps', 'distance',
        'calories', 'active_minutes', 'sleep', 'weight',
        'body_temperature', 'respiratory_rate', 'ecg',
        'fall_detection', 'stress', 'mindfulness',
        name='healthmetrictype'
    )
    health_metric_type.create(op.get_bind())

    session_status = postgresql.ENUM(
        'active', 'expired', 'revoked', 'locked',
        name='sessionstatus'
    )
    session_status.create(op.get_bind())

    biometric_type = postgresql.ENUM(
        'face_id', 'touch_id', 'fingerprint', 'iris', 'voice',
        name='biometrictype'
    )
    biometric_type.create(op.get_bind())

    app_update_channel = postgresql.ENUM(
        'production', 'staging', 'beta', 'alpha',
        name='appupdatechannel'
    )
    app_update_channel.create(op.get_bind())

    # ==================== Device Management Tables ====================

    # Mobile Devices
    op.create_table(
        'mobile_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_type', sa.String(20), nullable=False),

        # Device identification
        sa.Column('device_id', sa.String(255), nullable=False),
        sa.Column('device_token', sa.Text),
        sa.Column('platform', sa.Enum('ios', 'android', 'web', 'watchos', 'wearos', name='deviceplatform'), nullable=False),
        sa.Column('platform_version', sa.String(50)),
        sa.Column('device_model', sa.String(100)),
        sa.Column('device_name', sa.String(255)),

        # App information
        sa.Column('app_version', sa.String(20), nullable=False),
        sa.Column('app_build', sa.String(20)),
        sa.Column('bundle_id', sa.String(255)),
        sa.Column('update_channel', sa.Enum('production', 'staging', 'beta', 'alpha', name='appupdatechannel'), default='production'),

        # Security
        sa.Column('status', sa.Enum('active', 'inactive', 'suspended', 'revoked', name='devicestatus'), default='active'),
        sa.Column('biometric_enabled', sa.Boolean, default=False),
        sa.Column('biometric_type', sa.Enum('face_id', 'touch_id', 'fingerprint', 'iris', 'voice', name='biometrictype')),
        sa.Column('pin_enabled', sa.Boolean, default=False),
        sa.Column('is_jailbroken', sa.Boolean, default=False),
        sa.Column('is_rooted', sa.Boolean, default=False),
        sa.Column('device_fingerprint', sa.String(255)),

        # Settings
        sa.Column('notification_enabled', sa.Boolean, default=True),
        sa.Column('notification_preferences', postgresql.JSONB, default=dict),
        sa.Column('locale', sa.String(10), default='en'),
        sa.Column('timezone', sa.String(50)),

        # Network
        sa.Column('last_ip_address', postgresql.INET),
        sa.Column('carrier', sa.String(100)),

        # Timestamps
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_sync_at', sa.DateTime(timezone=True)),
        sa.Column('token_updated_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.UniqueConstraint('tenant_id', 'device_id', name='uq_mobile_device_tenant_device'),
    )
    op.create_index('ix_mobile_devices_tenant_id', 'mobile_devices', ['tenant_id'])
    op.create_index('ix_mobile_device_user', 'mobile_devices', ['user_id', 'user_type'])
    op.create_index('ix_mobile_device_token', 'mobile_devices', ['device_token'])

    # Mobile Sessions
    op.create_table(
        'mobile_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Session
        sa.Column('session_token', sa.String(255), nullable=False, unique=True),
        sa.Column('refresh_token', sa.String(255)),
        sa.Column('status', sa.Enum('active', 'expired', 'revoked', 'locked', name='sessionstatus'), default='active'),

        # Authentication
        sa.Column('auth_method', sa.String(50), nullable=False),
        sa.Column('biometric_verified', sa.Boolean, default=False),
        sa.Column('mfa_verified', sa.Boolean, default=False),

        # Security
        sa.Column('ip_address', postgresql.INET),
        sa.Column('user_agent', sa.Text),
        sa.Column('location', postgresql.JSONB),

        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('app_state', postgresql.JSONB),
        sa.Column('failed_attempts', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_mobile_sessions_device_id', 'mobile_sessions', ['device_id'])
    op.create_index('ix_mobile_sessions_user_id', 'mobile_sessions', ['user_id'])
    op.create_index('ix_mobile_sessions_tenant_id', 'mobile_sessions', ['tenant_id'])
    op.create_index('ix_mobile_session_token', 'mobile_sessions', ['session_token'])
    op.create_index('ix_mobile_session_expires', 'mobile_sessions', ['expires_at'])

    # ==================== Push Notification Tables ====================

    # Push Notifications
    op.create_table(
        'push_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Content
        sa.Column('notification_type', sa.Enum(
            'appointment_reminder', 'medication_reminder', 'lab_result',
            'message', 'health_alert', 'health_tip', 'emergency',
            'system', 'promotional', name='notificationtype'
        ), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'critical', name='notificationpriority'), default='normal'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('subtitle', sa.String(255)),
        sa.Column('image_url', sa.Text),

        # Rich data
        sa.Column('data', postgresql.JSONB),
        sa.Column('action_url', sa.Text),
        sa.Column('actions', postgresql.JSONB),

        # Delivery
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'read', 'failed', 'expired', name='notificationstatus'), default='pending'),
        sa.Column('platform', sa.Enum('ios', 'android', 'web', 'watchos', 'wearos', name='deviceplatform')),
        sa.Column('fcm_message_id', sa.String(255)),
        sa.Column('apns_id', sa.String(255)),
        sa.Column('collapse_key', sa.String(255)),
        sa.Column('ttl', sa.Integer),

        # Tracking
        sa.Column('scheduled_at', sa.DateTime(timezone=True)),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('failed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text),

        # Analytics
        sa.Column('opened', sa.Boolean, default=False),
        sa.Column('opened_at', sa.DateTime(timezone=True)),
        sa.Column('dismissed', sa.Boolean, default=False),
        sa.Column('dismissed_at', sa.DateTime(timezone=True)),
        sa.Column('action_taken', sa.String(50)),
        sa.Column('action_taken_at', sa.DateTime(timezone=True)),

        # Source
        sa.Column('triggered_by', sa.String(100)),
        sa.Column('source_entity_type', sa.String(50)),
        sa.Column('source_entity_id', postgresql.UUID(as_uuid=True)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_push_notifications_tenant_id', 'push_notifications', ['tenant_id'])
    op.create_index('ix_push_notifications_device_id', 'push_notifications', ['device_id'])
    op.create_index('ix_push_notifications_user_id', 'push_notifications', ['user_id'])
    op.create_index('ix_push_notification_status', 'push_notifications', ['status'])
    op.create_index('ix_push_notification_type', 'push_notifications', ['notification_type'])
    op.create_index('ix_push_notification_scheduled', 'push_notifications', ['scheduled_at'])

    # Notification Preferences
    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Global settings
        sa.Column('push_enabled', sa.Boolean, default=True),
        sa.Column('email_enabled', sa.Boolean, default=True),
        sa.Column('sms_enabled', sa.Boolean, default=True),

        # Per-type settings
        sa.Column('type_preferences', postgresql.JSONB, default=dict),

        # Quiet hours
        sa.Column('quiet_hours_enabled', sa.Boolean, default=False),
        sa.Column('quiet_hours_start', sa.String(5)),
        sa.Column('quiet_hours_end', sa.String(5)),
        sa.Column('quiet_hours_days', postgresql.ARRAY(sa.Integer)),

        # Sound settings
        sa.Column('sound_enabled', sa.Boolean, default=True),
        sa.Column('vibration_enabled', sa.Boolean, default=True),
        sa.Column('custom_sound', sa.String(100)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.UniqueConstraint('tenant_id', 'user_id', name='uq_notification_pref_user'),
    )
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])

    # ==================== Sync Tables ====================

    # Sync Checkpoints
    op.create_table(
        'sync_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id'), nullable=False),
        sa.Column('entity_type', sa.Enum(
            'patient', 'appointment', 'health_record', 'medication',
            'message', 'document', 'provider', 'care_team', 'notification',
            name='syncentitytype'
        ), nullable=False),

        sa.Column('last_sync_token', sa.String(255)),
        sa.Column('last_sync_timestamp', sa.DateTime(timezone=True)),
        sa.Column('server_timestamp', sa.DateTime(timezone=True)),
        sa.Column('records_synced', sa.Integer, default=0),
        sa.Column('last_full_sync', sa.DateTime(timezone=True)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.UniqueConstraint('device_id', 'entity_type', name='uq_sync_checkpoint_device_entity'),
    )
    op.create_index('ix_sync_checkpoints_device_id', 'sync_checkpoints', ['device_id'])

    # Sync Queue
    op.create_table(
        'sync_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('operation_type', sa.Enum('create', 'update', 'delete', name='syncoperationtype'), nullable=False),
        sa.Column('entity_type', sa.Enum(
            'patient', 'appointment', 'health_record', 'medication',
            'message', 'document', 'provider', 'care_team', 'notification',
            name='syncentitytype'
        ), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_data', postgresql.JSONB),

        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed', 'conflict', name='syncstatus'), default='pending'),
        sa.Column('retries', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('error_message', sa.Text),

        sa.Column('local_version', sa.Integer),
        sa.Column('server_version', sa.Integer),
        sa.Column('conflict_data', postgresql.JSONB),
        sa.Column('resolution', sa.String(50)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_sync_queue_tenant_id', 'sync_queue', ['tenant_id'])
    op.create_index('ix_sync_queue_device_id', 'sync_queue', ['device_id'])
    op.create_index('ix_sync_queue_status', 'sync_queue', ['status'])
    op.create_index('ix_sync_queue_device_status', 'sync_queue', ['device_id', 'status'])

    # Sync Conflicts
    op.create_table(
        'sync_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sync_queue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sync_queue.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('entity_type', sa.Enum(
            'patient', 'appointment', 'health_record', 'medication',
            'message', 'document', 'provider', 'care_team', 'notification',
            name='syncentitytype'
        ), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('local_data', postgresql.JSONB, nullable=False),
        sa.Column('server_data', postgresql.JSONB, nullable=False),
        sa.Column('merged_data', postgresql.JSONB),

        sa.Column('resolved', sa.Boolean, default=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('resolution_type', sa.String(50)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_sync_conflicts_user_id', 'sync_conflicts', ['user_id'])

    # ==================== Wearable Integration Tables ====================

    # Wearable Devices
    op.create_table(
        'wearable_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mobile_device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id')),

        sa.Column('wearable_type', sa.Enum(
            'apple_watch', 'wear_os', 'fitbit', 'garmin',
            'samsung_galaxy', 'whoop', 'oura', 'other',
            name='wearabletype'
        ), nullable=False),
        sa.Column('device_name', sa.String(255)),
        sa.Column('model', sa.String(100)),
        sa.Column('manufacturer', sa.String(100)),
        sa.Column('serial_number', sa.String(255)),
        sa.Column('firmware_version', sa.String(50)),

        sa.Column('is_connected', sa.Boolean, default=True),
        sa.Column('connection_type', sa.String(50)),
        sa.Column('last_connected_at', sa.DateTime(timezone=True)),

        sa.Column('data_sources', postgresql.ARRAY(sa.String)),
        sa.Column('sync_enabled', sa.Boolean, default=True),
        sa.Column('auto_sync', sa.Boolean, default=True),
        sa.Column('sync_frequency_minutes', sa.Integer, default=15),

        sa.Column('access_token', sa.Text),
        sa.Column('refresh_token', sa.Text),
        sa.Column('token_expires_at', sa.DateTime(timezone=True)),

        sa.Column('battery_level', sa.Integer),
        sa.Column('is_charging', sa.Boolean),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_wearable_devices_tenant_id', 'wearable_devices', ['tenant_id'])
    op.create_index('ix_wearable_devices_user_id', 'wearable_devices', ['user_id'])
    op.create_index('ix_wearable_devices_mobile_device_id', 'wearable_devices', ['mobile_device_id'])

    # Health Metrics
    op.create_table(
        'health_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wearable_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wearable_devices.id')),

        sa.Column('metric_type', sa.Enum(
            'heart_rate', 'heart_rate_variability', 'blood_oxygen',
            'blood_pressure', 'blood_glucose', 'steps', 'distance',
            'calories', 'active_minutes', 'sleep', 'weight',
            'body_temperature', 'respiratory_rate', 'ecg',
            'fall_detection', 'stress', 'mindfulness',
            name='healthmetrictype'
        ), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),

        sa.Column('secondary_value', sa.Float),
        sa.Column('secondary_unit', sa.String(20)),
        sa.Column('metadata', postgresql.JSONB),

        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True)),
        sa.Column('end_time', sa.DateTime(timezone=True)),

        sa.Column('source', sa.String(100)),
        sa.Column('source_device_id', sa.String(255)),
        sa.Column('is_manual_entry', sa.Boolean, default=False),

        sa.Column('confidence', sa.Float),
        sa.Column('is_anomaly', sa.Boolean, default=False),
        sa.Column('is_abnormal', sa.Boolean, default=False),
        sa.Column('alert_triggered', sa.Boolean, default=False),
        sa.Column('reviewed_by_provider', sa.Boolean, default=False),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_health_metrics_tenant_id', 'health_metrics', ['tenant_id'])
    op.create_index('ix_health_metrics_user_id', 'health_metrics', ['user_id'])
    op.create_index('ix_health_metrics_wearable_id', 'health_metrics', ['wearable_id'])
    op.create_index('ix_health_metric_type_time', 'health_metrics', ['user_id', 'metric_type', 'recorded_at'])
    op.create_index('ix_health_metric_recorded', 'health_metrics', ['recorded_at'])

    # Health Metric Goals
    op.create_table(
        'health_metric_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('metric_type', sa.Enum(
            'heart_rate', 'heart_rate_variability', 'blood_oxygen',
            'blood_pressure', 'blood_glucose', 'steps', 'distance',
            'calories', 'active_minutes', 'sleep', 'weight',
            'body_temperature', 'respiratory_rate', 'ecg',
            'fall_detection', 'stress', 'mindfulness',
            name='healthmetrictype'
        ), nullable=False),
        sa.Column('target_value', sa.Float, nullable=False),
        sa.Column('target_unit', sa.String(20), nullable=False),
        sa.Column('frequency', sa.String(20), default='daily'),

        sa.Column('min_value', sa.Float),
        sa.Column('max_value', sa.Float),

        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('start_date', sa.Date),
        sa.Column('end_date', sa.Date),

        sa.Column('set_by_provider', sa.Boolean, default=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.UniqueConstraint('user_id', 'metric_type', name='uq_health_goal_user_metric'),
    )
    op.create_index('ix_health_metric_goals_user_id', 'health_metric_goals', ['user_id'])

    # ==================== Analytics Tables ====================

    # App Usage Events
    op.create_table(
        'app_usage_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),

        sa.Column('event_name', sa.String(100), nullable=False),
        sa.Column('event_category', sa.String(50)),
        sa.Column('screen_name', sa.String(100)),
        sa.Column('action', sa.String(100)),
        sa.Column('label', sa.String(255)),
        sa.Column('value', sa.Float),

        sa.Column('properties', postgresql.JSONB),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.Column('duration_ms', sa.Integer),
        sa.Column('memory_usage_mb', sa.Float),
        sa.Column('cpu_usage_percent', sa.Float),
        sa.Column('network_type', sa.String(20)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_app_usage_events_tenant_id', 'app_usage_events', ['tenant_id'])
    op.create_index('ix_app_usage_events_device_id', 'app_usage_events', ['device_id'])
    op.create_index('ix_app_usage_events_user_id', 'app_usage_events', ['user_id'])
    op.create_index('ix_app_usage_events_session_id', 'app_usage_events', ['session_id'])
    op.create_index('ix_app_usage_event_name', 'app_usage_events', ['event_name'])
    op.create_index('ix_app_usage_timestamp', 'app_usage_events', ['timestamp'])

    # App Crash Reports
    op.create_table(
        'app_crash_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),

        sa.Column('crash_type', sa.String(50), nullable=False),
        sa.Column('exception_type', sa.String(255)),
        sa.Column('exception_message', sa.Text),
        sa.Column('stack_trace', sa.Text),

        sa.Column('screen_name', sa.String(100)),
        sa.Column('app_state', postgresql.JSONB),
        sa.Column('user_actions', postgresql.JSONB),

        sa.Column('memory_free_mb', sa.Float),
        sa.Column('disk_free_mb', sa.Float),
        sa.Column('battery_level', sa.Integer),
        sa.Column('is_charging', sa.Boolean),
        sa.Column('network_type', sa.String(20)),

        sa.Column('app_version', sa.String(20)),
        sa.Column('app_build', sa.String(20)),

        sa.Column('is_resolved', sa.Boolean, default=False),
        sa.Column('resolved_in_version', sa.String(20)),
        sa.Column('issue_id', sa.String(100)),

        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_app_crash_reports_tenant_id', 'app_crash_reports', ['tenant_id'])
    op.create_index('ix_crash_report_type', 'app_crash_reports', ['crash_type'])
    op.create_index('ix_crash_report_version', 'app_crash_reports', ['app_version'])

    # Mobile Audit Logs
    op.create_table(
        'mobile_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mobile_devices.id')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),

        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('action_category', sa.String(50), nullable=False),
        sa.Column('action_description', sa.Text),

        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True)),

        sa.Column('details', postgresql.JSONB),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('location', postgresql.JSONB),

        sa.Column('success', sa.Boolean, default=True),
        sa.Column('error_message', sa.Text),

        sa.Column('phi_accessed', sa.Boolean, default=False),
        sa.Column('phi_types', postgresql.ARRAY(sa.String)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_mobile_audit_logs_tenant_id', 'mobile_audit_logs', ['tenant_id'])
    op.create_index('ix_mobile_audit_logs_user_id', 'mobile_audit_logs', ['user_id'])
    op.create_index('ix_mobile_audit_logs_device_id', 'mobile_audit_logs', ['device_id'])
    op.create_index('ix_mobile_audit_action', 'mobile_audit_logs', ['action'])
    op.create_index('ix_mobile_audit_category', 'mobile_audit_logs', ['action_category'])
    op.create_index('ix_mobile_audit_created', 'mobile_audit_logs', ['created_at'])


def downgrade():
    # Drop tables
    op.drop_table('mobile_audit_logs')
    op.drop_table('app_crash_reports')
    op.drop_table('app_usage_events')
    op.drop_table('health_metric_goals')
    op.drop_table('health_metrics')
    op.drop_table('wearable_devices')
    op.drop_table('sync_conflicts')
    op.drop_table('sync_queue')
    op.drop_table('sync_checkpoints')
    op.drop_table('notification_preferences')
    op.drop_table('push_notifications')
    op.drop_table('mobile_sessions')
    op.drop_table('mobile_devices')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS appupdatechannel")
    op.execute("DROP TYPE IF EXISTS biometrictype")
    op.execute("DROP TYPE IF EXISTS sessionstatus")
    op.execute("DROP TYPE IF EXISTS healthmetrictype")
    op.execute("DROP TYPE IF EXISTS wearabletype")
    op.execute("DROP TYPE IF EXISTS syncstatus")
    op.execute("DROP TYPE IF EXISTS syncoperationtype")
    op.execute("DROP TYPE IF EXISTS syncentitytype")
    op.execute("DROP TYPE IF EXISTS notificationstatus")
    op.execute("DROP TYPE IF EXISTS notificationpriority")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS devicestatus")
    op.execute("DROP TYPE IF EXISTS deviceplatform")

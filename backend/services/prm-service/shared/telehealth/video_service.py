"""
Video Service

WebRTC/LiveKit integration for video consultations:
- Signaling server communication
- Media quality management
- Screen sharing
- Connection handling

EPIC-007: US-007.1 Video Consultation Infrastructure
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class VideoQuality(str, Enum):
    """Video quality presets."""
    LOW = "low"  # 360p, 15fps
    MEDIUM = "medium"  # 720p, 30fps
    HIGH = "high"  # 1080p, 30fps
    AUTO = "auto"  # Adaptive


class ConnectionState(str, Enum):
    """WebRTC connection state."""
    NEW = "new"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class VideoConstraints:
    """Video constraints configuration."""
    width: int = 1280
    height: int = 720
    frame_rate: int = 30
    facing_mode: str = "user"  # user, environment


@dataclass
class AudioConstraints:
    """Audio constraints configuration."""
    echo_cancellation: bool = True
    noise_suppression: bool = True
    auto_gain_control: bool = True
    sample_rate: int = 48000


@dataclass
class MediaConstraints:
    """Combined media constraints."""
    video: VideoConstraints = field(default_factory=VideoConstraints)
    audio: AudioConstraints = field(default_factory=AudioConstraints)


@dataclass
class ConnectionStats:
    """WebRTC connection statistics."""
    # Timing
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Video stats
    video_bitrate_kbps: int = 0
    video_packets_sent: int = 0
    video_packets_lost: int = 0
    video_frame_rate: float = 0
    video_resolution: str = ""

    # Audio stats
    audio_bitrate_kbps: int = 0
    audio_packets_sent: int = 0
    audio_packets_lost: int = 0

    # Network stats
    round_trip_time_ms: float = 0
    available_bandwidth_kbps: int = 0
    jitter_ms: float = 0

    # Quality
    mos_score: float = 5.0  # 1-5 Mean Opinion Score

    @property
    def packet_loss_percent(self) -> float:
        total_sent = self.video_packets_sent + self.audio_packets_sent
        total_lost = self.video_packets_lost + self.audio_packets_lost
        if total_sent == 0:
            return 0
        return (total_lost / total_sent) * 100


@dataclass
class IceServer:
    """ICE server configuration."""
    urls: List[str]
    username: Optional[str] = None
    credential: Optional[str] = None


@dataclass
class SignalingMessage:
    """WebRTC signaling message."""
    message_id: str
    session_id: str
    sender_id: str
    message_type: str  # offer, answer, ice_candidate
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class VideoService:
    """
    Video service for WebRTC/LiveKit integration.

    Handles:
    - Signaling for peer connections
    - ICE server configuration
    - Media quality management
    - Screen sharing
    - Statistics collection
    """

    def __init__(
        self,
        stun_servers: Optional[List[str]] = None,
        turn_servers: Optional[List[Dict[str, Any]]] = None,
    ):
        # ICE servers
        self.ice_servers: List[IceServer] = []

        # Add default STUN server
        stun = stun_servers or ["stun:stun.l.google.com:19302"]
        self.ice_servers.append(IceServer(urls=stun))

        # Add TURN servers
        if turn_servers:
            for turn in turn_servers:
                self.ice_servers.append(IceServer(
                    urls=turn.get("urls", []),
                    username=turn.get("username"),
                    credential=turn.get("credential"),
                ))

        # Signaling channels
        self._signaling_handlers: Dict[str, Callable] = {}

        # Connection stats
        self._connection_stats: Dict[str, List[ConnectionStats]] = {}

        # Quality settings by preset
        self._quality_presets = {
            VideoQuality.LOW: MediaConstraints(
                video=VideoConstraints(width=640, height=360, frame_rate=15),
            ),
            VideoQuality.MEDIUM: MediaConstraints(
                video=VideoConstraints(width=1280, height=720, frame_rate=30),
            ),
            VideoQuality.HIGH: MediaConstraints(
                video=VideoConstraints(width=1920, height=1080, frame_rate=30),
            ),
        }

    def get_ice_servers_config(self) -> List[Dict[str, Any]]:
        """Get ICE servers configuration for WebRTC."""
        config = []
        for server in self.ice_servers:
            server_config = {"urls": server.urls}
            if server.username:
                server_config["username"] = server.username
            if server.credential:
                server_config["credential"] = server.credential
            config.append(server_config)
        return config

    def get_rtc_configuration(self) -> Dict[str, Any]:
        """Get full WebRTC peer connection configuration."""
        return {
            "iceServers": self.get_ice_servers_config(),
            "iceCandidatePoolSize": 10,
            "bundlePolicy": "max-bundle",
            "rtcpMuxPolicy": "require",
        }

    def get_media_constraints(
        self,
        quality: VideoQuality = VideoQuality.MEDIUM,
        video_enabled: bool = True,
        audio_enabled: bool = True,
    ) -> Dict[str, Any]:
        """Get media constraints for getUserMedia."""
        constraints: Dict[str, Any] = {}

        if video_enabled:
            preset = self._quality_presets.get(quality, self._quality_presets[VideoQuality.MEDIUM])
            constraints["video"] = {
                "width": {"min": 640, "ideal": preset.video.width, "max": 1920},
                "height": {"min": 480, "ideal": preset.video.height, "max": 1080},
                "frameRate": {"ideal": preset.video.frame_rate, "max": 30},
                "facingMode": preset.video.facing_mode,
            }
        else:
            constraints["video"] = False

        if audio_enabled:
            constraints["audio"] = {
                "echoCancellation": True,
                "noiseSuppression": True,
                "autoGainControl": True,
                "sampleRate": 48000,
            }
        else:
            constraints["audio"] = False

        return constraints

    def get_screen_share_constraints(
        self,
        share_audio: bool = False,
    ) -> Dict[str, Any]:
        """Get constraints for screen sharing."""
        return {
            "video": {
                "cursor": "always",
                "displaySurface": "monitor",
                "logicalSurface": True,
                "width": {"max": 1920},
                "height": {"max": 1080},
                "frameRate": {"max": 30},
            },
            "audio": share_audio,
        }

    async def send_signaling_message(
        self,
        session_id: str,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any],
    ) -> SignalingMessage:
        """Send a signaling message to another participant."""
        message = SignalingMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            sender_id=sender_id,
            message_type=message_type,
            payload=payload,
        )

        # Route to recipient's signaling handler
        handler = self._signaling_handlers.get(recipient_id)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error delivering signaling message: {e}")

        return message

    def register_signaling_handler(
        self,
        participant_id: str,
        handler: Callable[[SignalingMessage], None],
    ):
        """Register a signaling message handler for a participant."""
        self._signaling_handlers[participant_id] = handler

    def unregister_signaling_handler(self, participant_id: str):
        """Unregister a signaling handler."""
        self._signaling_handlers.pop(participant_id, None)

    async def report_stats(
        self,
        session_id: str,
        participant_id: str,
        stats: ConnectionStats,
    ):
        """Report connection statistics."""
        key = f"{session_id}:{participant_id}"

        if key not in self._connection_stats:
            self._connection_stats[key] = []

        self._connection_stats[key].append(stats)

        # Keep only last 100 stats entries
        if len(self._connection_stats[key]) > 100:
            self._connection_stats[key] = self._connection_stats[key][-100:]

        # Calculate MOS score
        stats.mos_score = self._calculate_mos(stats)

        # Alert on poor quality
        if stats.mos_score < 3.0:
            logger.warning(
                f"Poor connection quality for {participant_id} in session {session_id}: "
                f"MOS={stats.mos_score:.2f}, RTT={stats.round_trip_time_ms}ms, "
                f"loss={stats.packet_loss_percent:.2f}%"
            )

    def _calculate_mos(self, stats: ConnectionStats) -> float:
        """Calculate Mean Opinion Score (1-5) from connection stats."""
        # Simplified MOS calculation
        # Based on RTT, packet loss, and jitter

        base_score = 5.0

        # Penalize for high RTT
        if stats.round_trip_time_ms > 300:
            base_score -= 1.5
        elif stats.round_trip_time_ms > 200:
            base_score -= 1.0
        elif stats.round_trip_time_ms > 150:
            base_score -= 0.5

        # Penalize for packet loss
        loss = stats.packet_loss_percent
        if loss > 5:
            base_score -= 2.0
        elif loss > 2:
            base_score -= 1.0
        elif loss > 1:
            base_score -= 0.5

        # Penalize for jitter
        if stats.jitter_ms > 50:
            base_score -= 0.5
        elif stats.jitter_ms > 30:
            base_score -= 0.25

        return max(1.0, min(5.0, base_score))

    async def get_connection_stats(
        self,
        session_id: str,
        participant_id: str,
    ) -> List[ConnectionStats]:
        """Get historical connection stats."""
        key = f"{session_id}:{participant_id}"
        return self._connection_stats.get(key, [])

    async def get_session_quality_summary(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """Get quality summary for all participants in a session."""
        summaries = {}

        for key, stats_list in self._connection_stats.items():
            if not key.startswith(f"{session_id}:"):
                continue

            participant_id = key.split(":")[1]

            if not stats_list:
                continue

            avg_mos = sum(s.mos_score for s in stats_list) / len(stats_list)
            avg_rtt = sum(s.round_trip_time_ms for s in stats_list) / len(stats_list)
            avg_loss = sum(s.packet_loss_percent for s in stats_list) / len(stats_list)

            summaries[participant_id] = {
                "average_mos": round(avg_mos, 2),
                "average_rtt_ms": round(avg_rtt, 1),
                "average_packet_loss_percent": round(avg_loss, 2),
                "samples": len(stats_list),
            }

        return {
            "session_id": session_id,
            "participants": summaries,
        }

    def calculate_recommended_quality(
        self,
        bandwidth_kbps: int,
    ) -> VideoQuality:
        """Calculate recommended video quality based on bandwidth."""
        if bandwidth_kbps >= 2500:
            return VideoQuality.HIGH
        elif bandwidth_kbps >= 1000:
            return VideoQuality.MEDIUM
        else:
            return VideoQuality.LOW

    def get_simulcast_layers(
        self,
        quality: VideoQuality,
    ) -> List[Dict[str, Any]]:
        """Get simulcast layer configuration for SFU."""
        if quality == VideoQuality.HIGH:
            return [
                {"rid": "q", "scaleResolutionDownBy": 4, "maxBitrate": 150000},
                {"rid": "h", "scaleResolutionDownBy": 2, "maxBitrate": 500000},
                {"rid": "f", "scaleResolutionDownBy": 1, "maxBitrate": 2500000},
            ]
        elif quality == VideoQuality.MEDIUM:
            return [
                {"rid": "q", "scaleResolutionDownBy": 2, "maxBitrate": 150000},
                {"rid": "h", "scaleResolutionDownBy": 1, "maxBitrate": 800000},
            ]
        else:
            return [
                {"rid": "q", "scaleResolutionDownBy": 1, "maxBitrate": 300000},
            ]


# Global video service instance
video_service = VideoService()

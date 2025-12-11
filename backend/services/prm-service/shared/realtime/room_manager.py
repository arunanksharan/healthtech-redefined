"""
Room Management System

Manages conversation rooms with:
- Dynamic room creation/deletion
- Room membership management
- Room permissions
- Room metadata
- Room history

EPIC-001: US-001.6 Room Management System
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RoomType(str, Enum):
    """Types of rooms."""
    DIRECT = "direct"  # 1:1 conversation
    GROUP = "group"  # Group conversation
    CHANNEL = "channel"  # Public channel
    CARE_TEAM = "care_team"  # Patient care team
    BROADCAST = "broadcast"  # One-way broadcast


class RoomPermission(str, Enum):
    """Room permission levels."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class RoomVisibility(str, Enum):
    """Room visibility settings."""
    PUBLIC = "public"
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"


@dataclass
class RoomMember:
    """Room membership information."""
    user_id: str
    permission: RoomPermission = RoomPermission.WRITE
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    nickname: Optional[str] = None
    notification_settings: Dict[str, Any] = field(default_factory=dict)
    last_read_sequence: int = 0


@dataclass
class Room:
    """Room/conversation structure."""
    room_id: str
    tenant_id: str
    room_type: RoomType
    name: str
    description: Optional[str] = None
    visibility: RoomVisibility = RoomVisibility.PRIVATE
    owner_id: Optional[str] = None
    members: Dict[str, RoomMember] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    archived: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    pinned_messages: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roomId": self.room_id,
            "tenantId": self.tenant_id,
            "roomType": self.room_type.value,
            "name": self.name,
            "description": self.description,
            "visibility": self.visibility.value,
            "ownerId": self.owner_id,
            "members": {
                uid: {
                    "userId": m.user_id,
                    "permission": m.permission.value,
                    "joinedAt": m.joined_at.isoformat(),
                    "nickname": m.nickname,
                    "notificationSettings": m.notification_settings,
                    "lastReadSequence": m.last_read_sequence,
                }
                for uid, m in self.members.items()
            },
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "archived": self.archived,
            "metadata": self.metadata,
            "pinnedMessages": self.pinned_messages,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Room":
        members = {}
        for uid, m_data in data.get("members", {}).items():
            members[uid] = RoomMember(
                user_id=m_data["userId"],
                permission=RoomPermission(m_data.get("permission", "write")),
                joined_at=datetime.fromisoformat(m_data["joinedAt"]) if "joinedAt" in m_data else datetime.now(timezone.utc),
                nickname=m_data.get("nickname"),
                notification_settings=m_data.get("notificationSettings", {}),
                last_read_sequence=m_data.get("lastReadSequence", 0),
            )

        return cls(
            room_id=data["roomId"],
            tenant_id=data["tenantId"],
            room_type=RoomType(data.get("roomType", "group")),
            name=data["name"],
            description=data.get("description"),
            visibility=RoomVisibility(data.get("visibility", "private")),
            owner_id=data.get("ownerId"),
            members=members,
            created_at=datetime.fromisoformat(data["createdAt"]) if "createdAt" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updatedAt"]) if "updatedAt" in data else datetime.now(timezone.utc),
            archived=data.get("archived", False),
            metadata=data.get("metadata", {}),
            pinned_messages=data.get("pinnedMessages", []),
            settings=data.get("settings", {}),
        )


class RoomManager:
    """
    Manages rooms/conversations.

    Features:
    - Room lifecycle management
    - Membership management
    - Permission checking
    - Room search
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
    ):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._local_rooms: Dict[str, Room] = {}
        self._user_rooms: Dict[str, Set[str]] = {}  # user_id -> room_ids

    async def start(self):
        """Initialize the room manager."""
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("RoomManager connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using local storage.")
            self._redis = None

    async def stop(self):
        """Stop the room manager."""
        if self._redis:
            await self._redis.close()

    def _room_key(self, room_id: str) -> str:
        return f"room:{room_id}"

    def _user_rooms_key(self, user_id: str) -> str:
        return f"user_rooms:{user_id}"

    def _tenant_rooms_key(self, tenant_id: str) -> str:
        return f"tenant_rooms:{tenant_id}"

    async def create_room(
        self,
        tenant_id: str,
        room_type: RoomType,
        name: str,
        creator_id: str,
        description: Optional[str] = None,
        visibility: RoomVisibility = RoomVisibility.PRIVATE,
        member_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Room:
        """
        Create a new room.

        Args:
            tenant_id: Tenant ID
            room_type: Type of room
            name: Room name
            creator_id: User creating the room
            description: Room description
            visibility: Room visibility
            member_ids: Initial member IDs
            metadata: Additional metadata

        Returns:
            Created Room
        """
        room = Room(
            room_id=str(uuid4()),
            tenant_id=tenant_id,
            room_type=room_type,
            name=name,
            description=description,
            visibility=visibility,
            owner_id=creator_id,
            metadata=metadata or {},
        )

        # Add creator as owner
        room.members[creator_id] = RoomMember(
            user_id=creator_id,
            permission=RoomPermission.OWNER,
        )

        # Add other members
        for user_id in (member_ids or []):
            if user_id != creator_id:
                room.members[user_id] = RoomMember(
                    user_id=user_id,
                    permission=RoomPermission.WRITE,
                )

        # Store room
        await self._store_room(room)

        # Update user room lists
        for user_id in room.members.keys():
            await self._add_user_room(user_id, room.room_id)

        logger.info(f"Room created: {room.room_id} ({room.name})")
        return room

    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        if self._redis:
            try:
                data = await self._redis.get(self._room_key(room_id))
                if data:
                    return Room.from_dict(json.loads(data))
            except Exception as e:
                logger.error(f"Redis error getting room: {e}")

        return self._local_rooms.get(room_id)

    async def update_room(
        self,
        room_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[RoomVisibility] = None,
        metadata: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Optional[Room]:
        """Update room properties."""
        room = await self.get_room(room_id)
        if not room:
            return None

        if name is not None:
            room.name = name
        if description is not None:
            room.description = description
        if visibility is not None:
            room.visibility = visibility
        if metadata is not None:
            room.metadata.update(metadata)
        if settings is not None:
            room.settings.update(settings)

        room.updated_at = datetime.now(timezone.utc)
        await self._store_room(room)

        logger.info(f"Room updated: {room.room_id}")
        return room

    async def delete_room(self, room_id: str, hard_delete: bool = False):
        """
        Delete a room.

        Args:
            room_id: Room to delete
            hard_delete: If True, permanently delete; otherwise archive
        """
        room = await self.get_room(room_id)
        if not room:
            return

        if hard_delete:
            # Remove from user room lists
            for user_id in room.members.keys():
                await self._remove_user_room(user_id, room_id)

            # Delete room data
            if self._redis:
                try:
                    await self._redis.delete(self._room_key(room_id))
                except Exception as e:
                    logger.error(f"Redis error deleting room: {e}")

            self._local_rooms.pop(room_id, None)
            logger.info(f"Room deleted: {room_id}")
        else:
            room.archived = True
            room.updated_at = datetime.now(timezone.utc)
            await self._store_room(room)
            logger.info(f"Room archived: {room_id}")

    async def add_member(
        self,
        room_id: str,
        user_id: str,
        permission: RoomPermission = RoomPermission.WRITE,
        nickname: Optional[str] = None,
    ) -> bool:
        """Add a member to a room."""
        room = await self.get_room(room_id)
        if not room:
            return False

        room.members[user_id] = RoomMember(
            user_id=user_id,
            permission=permission,
            nickname=nickname,
        )
        room.updated_at = datetime.now(timezone.utc)

        await self._store_room(room)
        await self._add_user_room(user_id, room_id)

        logger.info(f"Added {user_id} to room {room_id}")
        return True

    async def remove_member(self, room_id: str, user_id: str) -> bool:
        """Remove a member from a room."""
        room = await self.get_room(room_id)
        if not room or user_id not in room.members:
            return False

        del room.members[user_id]
        room.updated_at = datetime.now(timezone.utc)

        await self._store_room(room)
        await self._remove_user_room(user_id, room_id)

        logger.info(f"Removed {user_id} from room {room_id}")
        return True

    async def update_member_permission(
        self,
        room_id: str,
        user_id: str,
        permission: RoomPermission,
    ) -> bool:
        """Update a member's permission level."""
        room = await self.get_room(room_id)
        if not room or user_id not in room.members:
            return False

        room.members[user_id].permission = permission
        room.updated_at = datetime.now(timezone.utc)
        await self._store_room(room)

        logger.info(f"Updated permission for {user_id} in room {room_id}")
        return True

    async def get_user_rooms(self, user_id: str) -> List[Room]:
        """Get all rooms a user is a member of."""
        rooms = []

        if self._redis:
            try:
                room_ids = await self._redis.smembers(self._user_rooms_key(user_id))
                for room_id in room_ids:
                    room = await self.get_room(room_id)
                    if room and not room.archived:
                        rooms.append(room)
            except Exception as e:
                logger.error(f"Redis error getting user rooms: {e}")

        # Also check local storage
        if user_id in self._user_rooms:
            for room_id in self._user_rooms[user_id]:
                room = self._local_rooms.get(room_id)
                if room and not room.archived and room not in rooms:
                    rooms.append(room)

        return rooms

    async def search_rooms(
        self,
        tenant_id: str,
        query: Optional[str] = None,
        room_type: Optional[RoomType] = None,
        visibility: Optional[RoomVisibility] = None,
        limit: int = 50,
    ) -> List[Room]:
        """
        Search rooms in a tenant.

        Args:
            tenant_id: Tenant to search in
            query: Search query for name/description
            room_type: Filter by room type
            visibility: Filter by visibility
            limit: Maximum results

        Returns:
            List of matching rooms
        """
        rooms = []

        # Get all tenant rooms
        if self._redis:
            try:
                room_ids = await self._redis.smembers(self._tenant_rooms_key(tenant_id))
                for room_id in room_ids:
                    room = await self.get_room(room_id)
                    if room:
                        rooms.append(room)
            except Exception as e:
                logger.error(f"Redis error searching rooms: {e}")

        # Filter
        filtered = []
        for room in rooms:
            if room.archived:
                continue
            if room_type and room.room_type != room_type:
                continue
            if visibility and room.visibility != visibility:
                continue
            if query:
                query_lower = query.lower()
                if query_lower not in room.name.lower() and (
                    not room.description or query_lower not in room.description.lower()
                ):
                    continue
            filtered.append(room)

        return filtered[:limit]

    async def get_or_create_direct_room(
        self,
        tenant_id: str,
        user_id_1: str,
        user_id_2: str,
    ) -> Room:
        """
        Get or create a direct message room between two users.

        Args:
            tenant_id: Tenant ID
            user_id_1: First user
            user_id_2: Second user

        Returns:
            The direct room
        """
        # Check if room exists
        user1_rooms = await self.get_user_rooms(user_id_1)
        for room in user1_rooms:
            if room.room_type == RoomType.DIRECT:
                if user_id_2 in room.members:
                    return room

        # Create new direct room
        room_name = f"Direct: {user_id_1[:8]}-{user_id_2[:8]}"
        return await self.create_room(
            tenant_id=tenant_id,
            room_type=RoomType.DIRECT,
            name=room_name,
            creator_id=user_id_1,
            member_ids=[user_id_2],
            visibility=RoomVisibility.PRIVATE,
        )

    async def pin_message(self, room_id: str, message_id: str) -> bool:
        """Pin a message in a room."""
        room = await self.get_room(room_id)
        if not room:
            return False

        if message_id not in room.pinned_messages:
            room.pinned_messages.append(message_id)
            room.updated_at = datetime.now(timezone.utc)
            await self._store_room(room)

        return True

    async def unpin_message(self, room_id: str, message_id: str) -> bool:
        """Unpin a message from a room."""
        room = await self.get_room(room_id)
        if not room:
            return False

        if message_id in room.pinned_messages:
            room.pinned_messages.remove(message_id)
            room.updated_at = datetime.now(timezone.utc)
            await self._store_room(room)

        return True

    async def check_permission(
        self,
        room_id: str,
        user_id: str,
        required: RoomPermission,
    ) -> bool:
        """
        Check if a user has required permission in a room.

        Args:
            room_id: Room to check
            user_id: User to check
            required: Required permission level

        Returns:
            True if user has permission
        """
        room = await self.get_room(room_id)
        if not room:
            return False

        member = room.members.get(user_id)
        if not member:
            return False

        # Permission hierarchy: OWNER > ADMIN > WRITE > READ
        hierarchy = {
            RoomPermission.READ: 1,
            RoomPermission.WRITE: 2,
            RoomPermission.ADMIN: 3,
            RoomPermission.OWNER: 4,
        }

        return hierarchy.get(member.permission, 0) >= hierarchy.get(required, 0)

    async def _store_room(self, room: Room):
        """Store room data."""
        if self._redis:
            try:
                await self._redis.set(
                    self._room_key(room.room_id),
                    json.dumps(room.to_dict()),
                )
                await self._redis.sadd(
                    self._tenant_rooms_key(room.tenant_id),
                    room.room_id,
                )
            except Exception as e:
                logger.error(f"Redis error storing room: {e}")
                self._local_rooms[room.room_id] = room
        else:
            self._local_rooms[room.room_id] = room

    async def _add_user_room(self, user_id: str, room_id: str):
        """Add room to user's room list."""
        if self._redis:
            try:
                await self._redis.sadd(self._user_rooms_key(user_id), room_id)
            except Exception as e:
                logger.error(f"Redis error adding user room: {e}")

        if user_id not in self._user_rooms:
            self._user_rooms[user_id] = set()
        self._user_rooms[user_id].add(room_id)

    async def _remove_user_room(self, user_id: str, room_id: str):
        """Remove room from user's room list."""
        if self._redis:
            try:
                await self._redis.srem(self._user_rooms_key(user_id), room_id)
            except Exception as e:
                logger.error(f"Redis error removing user room: {e}")

        if user_id in self._user_rooms:
            self._user_rooms[user_id].discard(room_id)


# Global room manager instance
room_manager = RoomManager()

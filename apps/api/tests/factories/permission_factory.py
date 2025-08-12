"""
UserAgentPermission factory for generating test permission data.

Provides realistic test data generation for permission scenarios including
different agent types and CRUD combinations.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict

from src.models.permission import UserAgentPermission, AgentName
from .base_factory import BaseFactory


class UserAgentPermissionFactory(BaseFactory):
    """Factory for creating UserAgentPermission test instances."""
    
    @classmethod
    def create_permission(
        self,
        user_id: Optional[uuid.UUID] = None,
        agent_name: Optional[AgentName] = None,
        can_create: bool = False,
        can_read: bool = False,
        can_update: bool = False,
        can_delete: bool = False,
        granted_by: Optional[uuid.UUID] = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True,
        **kwargs
    ) -> UserAgentPermission:
        """
        Create a UserAgentPermission instance with test data.
        
        Args:
            user_id: User ID receiving the permission
            agent_name: Agent type for the permission
            can_create: Create permission flag
            can_read: Read permission flag  
            can_update: Update permission flag
            can_delete: Delete permission flag
            granted_by: User ID who granted the permission
            expires_at: Optional expiration timestamp
            is_active: Active status
            **kwargs: Additional fields to override
            
        Returns:
            UserAgentPermission instance with test data
        """
        # Generate user_id if not provided
        if user_id is None:
            user_id = self.generate_uuid()
        
        # Generate agent_name if not provided
        if agent_name is None:
            agent_name = self.pick_random(list(AgentName))
        
        # Generate granted_by if not provided
        if granted_by is None:
            granted_by = self.generate_uuid()
        
        # Create permission data
        permission_data = {
            "user_id": user_id,
            "agent_name": agent_name,
            "can_create": can_create,
            "can_read": can_read,
            "can_update": can_update,
            "can_delete": can_delete,
            "granted_by": granted_by,
            "expires_at": expires_at,
            "is_active": is_active,
            **kwargs
        }
        
        return UserAgentPermission(**permission_data)
    
    @classmethod
    def create_full_access_permission(
        self,
        user_id: Optional[uuid.UUID] = None,
        agent_name: Optional[AgentName] = None,
        granted_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> UserAgentPermission:
        """Create a permission with full CRUD access."""
        return self.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_create=True,
            can_read=True,
            can_update=True,
            can_delete=True,
            granted_by=granted_by,
            **kwargs
        )
    
    @classmethod
    def create_read_only_permission(
        self,
        user_id: Optional[uuid.UUID] = None,
        agent_name: Optional[AgentName] = None,
        granted_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> UserAgentPermission:
        """Create a permission with read-only access."""
        return self.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_read=True,
            granted_by=granted_by,
            **kwargs
        )
    
    @classmethod
    def create_read_write_permission(
        self,
        user_id: Optional[uuid.UUID] = None,
        agent_name: Optional[AgentName] = None,
        granted_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> UserAgentPermission:
        """Create a permission with read and write access."""
        return self.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_create=True,
            can_read=True,
            can_update=True,
            granted_by=granted_by,
            **kwargs
        )
    
    @classmethod
    def create_expired_permission(
        self,
        user_id: Optional[uuid.UUID] = None,
        agent_name: Optional[AgentName] = None,
        days_expired: int = 1,
        granted_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> UserAgentPermission:
        """Create an expired permission."""
        expires_at = datetime.now(timezone.utc) - timedelta(days=days_expired)
        return self.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_read=True,
            expires_at=expires_at,
            granted_by=granted_by,
            **kwargs
        )
    
    @classmethod
    def create_expiring_permission(
        self,
        user_id: Optional[uuid.UUID] = None,
        agent_name: Optional[AgentName] = None,
        days_until_expiry: int = 7,
        granted_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> UserAgentPermission:
        """Create a permission that expires in the future."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)
        return self.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_read=True,
            expires_at=expires_at,
            granted_by=granted_by,
            **kwargs
        )
    
    @classmethod
    def create_inactive_permission(
        self,
        user_id: Optional[uuid.UUID] = None,
        agent_name: Optional[AgentName] = None,
        granted_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> UserAgentPermission:
        """Create an inactive permission."""
        return self.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_read=True,
            is_active=False,
            granted_by=granted_by,
            **kwargs
        )
    
    @classmethod
    def create_agent_permissions_for_user(
        self,
        user_id: uuid.UUID,
        granted_by: Optional[uuid.UUID] = None,
        permission_type: str = "read_only"
    ) -> List[UserAgentPermission]:
        """
        Create permissions for all agents for a specific user.
        
        Args:
            user_id: User ID to create permissions for
            granted_by: User ID who granted the permissions
            permission_type: Type of permissions ("full", "read_only", "read_write")
            
        Returns:
            List of UserAgentPermission instances for all agents
        """
        if granted_by is None:
            granted_by = self.generate_uuid()
        
        permissions = []
        for agent in AgentName:
            if permission_type == "full":
                permission = self.create_full_access_permission(
                    user_id=user_id,
                    agent_name=agent,
                    granted_by=granted_by
                )
            elif permission_type == "read_write":
                permission = self.create_read_write_permission(
                    user_id=user_id,
                    agent_name=agent,
                    granted_by=granted_by
                )
            else:  # read_only
                permission = self.create_read_only_permission(
                    user_id=user_id,
                    agent_name=agent,
                    granted_by=granted_by
                )
            permissions.append(permission)
        
        return permissions
    
    @classmethod
    def create_permission_scenarios(self) -> Dict[str, List[UserAgentPermission]]:
        """
        Create common permission scenarios for testing.
        
        Returns:
            Dictionary mapping scenario names to permission lists
        """
        user_id = self.generate_uuid()
        admin_id = self.generate_uuid()
        
        scenarios = {
            "full_access_user": self.create_agent_permissions_for_user(
                user_id=user_id,
                granted_by=admin_id,
                permission_type="full"
            ),
            "read_only_user": self.create_agent_permissions_for_user(
                user_id=user_id,
                granted_by=admin_id,
                permission_type="read_only"
            ),
            "mixed_permissions": [
                self.create_full_access_permission(
                    user_id=user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    granted_by=admin_id
                ),
                self.create_read_only_permission(
                    user_id=user_id,
                    agent_name=AgentName.PDF_PROCESSING,
                    granted_by=admin_id
                ),
                self.create_read_write_permission(
                    user_id=user_id,
                    agent_name=AgentName.REPORTS_ANALYSIS,
                    granted_by=admin_id
                ),
            ],
            "expired_permissions": [
                self.create_expired_permission(
                    user_id=user_id,
                    agent_name=agent,
                    granted_by=admin_id
                ) for agent in AgentName
            ],
        }
        
        return scenarios
    
    @classmethod
    def create_permission_matrix(
        self,
        users: List[uuid.UUID],
        admin_id: uuid.UUID
    ) -> List[UserAgentPermission]:
        """
        Create a permission matrix for multiple users with varying access levels.
        
        Args:
            users: List of user IDs
            admin_id: ID of admin granting permissions
            
        Returns:
            List of UserAgentPermission instances
        """
        permissions = []
        permission_types = ["full", "read_write", "read_only"]
        
        for i, user_id in enumerate(users):
            # Rotate permission types
            perm_type = permission_types[i % len(permission_types)]
            user_permissions = self.create_agent_permissions_for_user(
                user_id=user_id,
                granted_by=admin_id,
                permission_type=perm_type
            )
            permissions.extend(user_permissions)
        
        return permissions
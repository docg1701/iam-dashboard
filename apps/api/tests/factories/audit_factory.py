"""
AuditLog factory for generating test audit data.

Provides realistic test data generation for audit scenarios including
different actions, resources, and tracking information.
"""
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from src.models.audit import AuditLog, AuditAction
from .base_factory import BaseFactory


class AuditLogFactory(BaseFactory):
    """Factory for creating AuditLog test instances."""
    
    @classmethod
    def create_audit_log(
        self,
        action: Optional[AuditAction] = None,
        resource_type: str = "test_resource",
        actor_id: Optional[uuid.UUID] = None,
        resource_id: Optional[uuid.UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        description: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        **kwargs
    ) -> AuditLog:
        """
        Create an AuditLog instance with test data.
        
        Args:
            action: Audit action performed
            resource_type: Type of resource affected
            actor_id: User who performed the action
            resource_id: ID of affected resource
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            description: Human-readable description
            additional_data: Additional context data
            timestamp: Timestamp of the action
            **kwargs: Additional fields to override
            
        Returns:
            AuditLog instance with test data
        """
        # Generate action if not provided
        if action is None:
            # Exclude LOGIN/LOGOUT for default audit logs to ensure consistent behavior
            actions = [a for a in AuditAction if a not in [AuditAction.LOGIN, AuditAction.LOGOUT]]
            action = self.pick_random(actions)
        
        # Generate actor_id if not provided (can be None for system actions)
        if actor_id is None and action not in [AuditAction.LOGIN, AuditAction.LOGOUT]:
            actor_id = self.generate_uuid()
        
        # Generate resource_id if not provided (but only for actions that typically need one)
        if resource_id is None and action not in [AuditAction.LOGIN, AuditAction.LOGOUT]:
            resource_id = self.generate_uuid()
        
        # Generate IP address if not provided
        if ip_address is None:
            ip_address = self.generate_ip_address()
        
        # Generate user agent if not provided
        if user_agent is None:
            user_agent = self.generate_user_agent()
        
        # Generate session ID if not provided
        if session_id is None:
            session_id = self.generate_session_id()
        
        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = self.generate_datetime(past_days=0)  # Use current time by default
        
        # Create audit log data
        audit_data = {
            "action": action,
            "resource_type": resource_type,
            "actor_id": actor_id,
            "resource_id": resource_id,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": session_id,
            "description": description,
            "additional_data": additional_data,
            "timestamp": timestamp,
            **kwargs
        }
        
        return AuditLog(**audit_data)
    
    @classmethod
    def create_user_creation_audit(
        self,
        actor_id: uuid.UUID,
        user_id: uuid.UUID,
        user_email: str,
        user_role: str,
        **kwargs
    ) -> AuditLog:
        """Create an audit log for user creation."""
        new_values = {
            "email": user_email,
            "role": user_role,
            "is_active": True
        }
        
        return self.create_audit_log(
            action=AuditAction.CREATE,
            resource_type="user",
            actor_id=actor_id,
            resource_id=user_id,
            new_values=new_values,
            description=f"Created user with email {user_email}",
            **kwargs
        )
    
    @classmethod
    def create_user_update_audit(
        self,
        actor_id: uuid.UUID,
        user_id: uuid.UUID,
        old_email: str,
        new_email: str,
        **kwargs
    ) -> AuditLog:
        """Create an audit log for user update."""
        old_values = {"email": old_email}
        new_values = {"email": new_email}
        
        return self.create_audit_log(
            action=AuditAction.UPDATE,
            resource_type="user",
            actor_id=actor_id,
            resource_id=user_id,
            old_values=old_values,
            new_values=new_values,
            description=f"Updated user email from {old_email} to {new_email}",
            **kwargs
        )
    
    @classmethod
    def create_login_audit(
        self,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Create an audit log for user login."""
        return self.create_audit_log(
            action=AuditAction.LOGIN,
            resource_type="session",
            actor_id=user_id,
            resource_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            description="User logged in successfully",
            **kwargs
        )
    
    @classmethod
    def create_logout_audit(
        self,
        user_id: uuid.UUID,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Create an audit log for user logout."""
        return self.create_audit_log(
            action=AuditAction.LOGOUT,
            resource_type="session",
            actor_id=user_id,
            resource_id=None,
            session_id=session_id,
            description="User logged out",
            **kwargs
        )
    
    @classmethod
    def create_client_creation_audit(
        self,
        actor_id: uuid.UUID,
        client_id: uuid.UUID,
        client_name: str,
        client_cpf: str,
        **kwargs
    ) -> AuditLog:
        """Create an audit log for client creation."""
        # Mask CPF for security
        masked_cpf = f"{client_cpf[:3]}.***.{client_cpf[-2:]}"
        
        new_values = {
            "name": client_name,
            "cpf": masked_cpf,
            "is_active": True
        }
        
        return self.create_audit_log(
            action=AuditAction.CREATE,
            resource_type="client",
            actor_id=actor_id,
            resource_id=client_id,
            new_values=new_values,
            description=f"Created client {client_name}",
            **kwargs
        )
    
    @classmethod
    def create_permission_change_audit(
        self,
        actor_id: uuid.UUID,
        user_id: uuid.UUID,
        agent_name: str,
        old_permissions: Dict[str, bool],
        new_permissions: Dict[str, bool],
        **kwargs
    ) -> AuditLog:
        """Create an audit log for permission changes."""
        return self.create_audit_log(
            action=AuditAction.PERMISSION_CHANGE,
            resource_type="user_agent_permission",
            actor_id=actor_id,
            resource_id=user_id,
            old_values={"permissions": old_permissions, "agent": agent_name},
            new_values={"permissions": new_permissions, "agent": agent_name},
            description=f"Updated permissions for agent {agent_name}",
            **kwargs
        )
    
    @classmethod
    def create_delete_audit(
        self,
        actor_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        resource_data: Dict[str, Any],
        **kwargs
    ) -> AuditLog:
        """Create an audit log for resource deletion."""
        return self.create_audit_log(
            action=AuditAction.DELETE,
            resource_type=resource_type,
            actor_id=actor_id,
            resource_id=resource_id,
            old_values=resource_data,
            description=f"Deleted {resource_type} resource",
            **kwargs
        )
    
    @classmethod
    def create_audit_trail_for_user_session(
        self,
        user_id: uuid.UUID,
        session_duration_hours: int = 2,
        actions_count: int = 5
    ) -> List[AuditLog]:
        """
        Create a complete audit trail for a user session.
        
        Args:
            user_id: User ID for the session
            session_duration_hours: Duration of session in hours
            actions_count: Number of actions performed during session
            
        Returns:
            List of AuditLog instances representing a complete session
        """
        session_id = self.generate_session_id()
        ip_address = self.generate_ip_address()
        user_agent = self.generate_user_agent()
        
        # Start time
        login_time = datetime.now(timezone.utc) - timedelta(hours=session_duration_hours + 1)
        logout_time = login_time + timedelta(hours=session_duration_hours)
        
        audit_logs = []
        
        # Login audit
        audit_logs.append(
            self.create_login_audit(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                timestamp=login_time
            )
        )
        
        # Various actions during the session
        for i in range(actions_count):
            action_time = login_time + timedelta(
                minutes=random.randint(1, session_duration_hours * 60)
            )
            
            action = self.pick_random([
                AuditAction.CREATE,
                AuditAction.READ,
                AuditAction.UPDATE,
                AuditAction.DELETE
            ])
            
            resource_type = self.pick_random(["client", "user", "permission"])
            
            audit_logs.append(
                self.create_audit_log(
                    action=action,
                    resource_type=resource_type,
                    actor_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    timestamp=action_time
                )
            )
        
        # Logout audit
        audit_logs.append(
            self.create_logout_audit(
                user_id=user_id,
                session_id=session_id,
                timestamp=logout_time
            )
        )
        
        return audit_logs
    
    @classmethod
    def create_security_audit_logs(self) -> List[AuditLog]:
        """Create various security-related audit logs for testing."""
        user_id = self.generate_uuid()
        
        return [
            # Failed login attempt
            self.create_audit_log(
                action=AuditAction.LOGIN,
                resource_type="session",
                actor_id=user_id,
                description="Failed login attempt - invalid password",
                additional_data={"success": False, "reason": "invalid_password"}
            ),
            
            # Suspicious IP login
            self.create_audit_log(
                action=AuditAction.LOGIN,
                resource_type="session", 
                actor_id=user_id,
                ip_address="192.168.1.100",
                description="Login from new IP address",
                additional_data={"suspicious": True, "new_ip": True}
            ),
            
            # Permission escalation
            self.create_permission_change_audit(
                actor_id=self.generate_uuid(),
                user_id=user_id,
                agent_name="client_management",
                old_permissions={"can_read": True},
                new_permissions={"can_read": True, "can_create": True, "can_update": True}
            ),
        ]
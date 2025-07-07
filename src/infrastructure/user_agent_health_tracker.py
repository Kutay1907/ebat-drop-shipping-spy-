"""
User Agent Health Tracker

Tracks health status of user agents and manages rotation based on detection events.
Implements intelligent user agent management for bot protection.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from ..domain.interfaces import IUserAgentHealthTracker, ILogger
from ..domain.models import BotDetectionEvent, UserAgentHealthRecord, UserAgentHealth


class UserAgentHealthTracker(IUserAgentHealthTracker):
    """
    Service for tracking user agent health and intelligent rotation.
    
    Features:
    - Detection event tracking per user agent
    - Health status calculation based on failure patterns
    - Automatic tainted user agent rotation
    - Performance metrics and analytics
    """
    
    def __init__(
        self,
        logger: ILogger,
        detection_threshold: int = 3,
        degraded_threshold: int = 5,
        tainted_threshold: int = 10,
        health_decay_hours: int = 24
    ):
        """
        Initialize user agent health tracker.
        
        Args:
            logger: Logger instance for tracking operations
            detection_threshold: Detection count for DEGRADED status
            degraded_threshold: Detection count for TAINTED status  
            tainted_threshold: Detection count for BLOCKED status
            health_decay_hours: Hours after which to reset health scores
        """
        self.logger = logger
        self.detection_threshold = detection_threshold
        self.degraded_threshold = degraded_threshold
        self.tainted_threshold = tainted_threshold
        self.health_decay_hours = health_decay_hours
        
        # Health records storage
        self._health_records: Dict[str, UserAgentHealthRecord] = {}
        
        # Detection event counters
        self._detection_counts: Dict[str, int] = defaultdict(int)
        self._consecutive_failures: Dict[str, int] = defaultdict(int)
        self._last_detection: Dict[str, datetime] = {}
        self._last_success: Dict[str, datetime] = {}
        
        # Default healthy user agents
        self._default_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        ]
        
        # Initialize default user agents
        asyncio.create_task(self._initialize_default_agents())
    
    async def _initialize_default_agents(self) -> None:
        """Initialize health records for default user agents."""
        current_time = datetime.utcnow()
        
        for user_agent in self._default_user_agents:
            if user_agent not in self._health_records:
                self._health_records[user_agent] = UserAgentHealthRecord(
                    user_agent=user_agent,
                    health_status=UserAgentHealth.HEALTHY,
                    detection_count=0,
                    last_success=current_time,
                    consecutive_failures=0,
                    created_at=current_time,
                    updated_at=current_time
                )
        
        await self.logger.log_info(
            "Initialized default user agents",
            count=len(self._default_user_agents)
        )
    
    async def track_detection_event(self, user_agent: str, event: BotDetectionEvent) -> None:
        """
        Track bot detection event for specific user agent.
        
        Args:
            user_agent: User agent string that triggered detection
            event: Bot detection event details
        """
        current_time = datetime.utcnow()
        
        # Update detection counters
        self._detection_counts[user_agent] += 1
        self._consecutive_failures[user_agent] += 1
        self._last_detection[user_agent] = current_time
        
        # Get or create health record
        if user_agent not in self._health_records:
            self._health_records[user_agent] = UserAgentHealthRecord(
                user_agent=user_agent,
                health_status=UserAgentHealth.HEALTHY,
                detection_count=0,
                consecutive_failures=0,
                created_at=current_time,
                updated_at=current_time
            )
        
        # Update health record
        health_record = self._health_records[user_agent]
        health_record.detection_count = self._detection_counts[user_agent]
        health_record.consecutive_failures = self._consecutive_failures[user_agent]
        health_record.last_detection = current_time
        health_record.updated_at = current_time
        
        # Calculate new health status
        new_status = await self._calculate_health_status(user_agent)
        old_status = health_record.health_status
        health_record.health_status = new_status
        
        await self.logger.log_warning(
            "Bot detection event tracked",
            user_agent=user_agent[:50] + "..." if len(user_agent) > 50 else user_agent,
            event_type=event.event_type,
            detection_count=health_record.detection_count,
            consecutive_failures=health_record.consecutive_failures,
            old_status=old_status.value,
            new_status=new_status.value,
            url=event.url
        )
        
        # Alert if user agent became tainted
        if old_status != new_status and new_status in [UserAgentHealth.TAINTED, UserAgentHealth.BLOCKED]:
            await self.logger.log_error(
                "User agent health degraded significantly",
                user_agent=user_agent[:50] + "..." if len(user_agent) > 50 else user_agent,
                old_status=old_status.value,
                new_status=new_status.value,
                detection_count=health_record.detection_count
            )
    
    async def track_success_event(self, user_agent: str) -> None:
        """Track successful operation for user agent."""
        current_time = datetime.utcnow()
        
        # Reset consecutive failures
        self._consecutive_failures[user_agent] = 0
        self._last_success[user_agent] = current_time
        
        # Update health record
        if user_agent in self._health_records:
            health_record = self._health_records[user_agent]
            health_record.consecutive_failures = 0
            health_record.last_success = current_time
            health_record.updated_at = current_time
            
            # Recalculate health status (might improve)
            health_record.health_status = await self._calculate_health_status(user_agent)
    
    async def _calculate_health_status(self, user_agent: str) -> UserAgentHealth:
        """Calculate health status based on detection patterns."""
        detection_count = self._detection_counts.get(user_agent, 0)
        consecutive_failures = self._consecutive_failures.get(user_agent, 0)
        last_detection = self._last_detection.get(user_agent)
        last_success = self._last_success.get(user_agent)
        
        # Check if detections are recent
        current_time = datetime.utcnow()
        recent_detection = (
            last_detection and 
            (current_time - last_detection).total_seconds() < 3600  # 1 hour
        )
        
        # Check success ratio
        has_recent_success = (
            last_success and 
            (current_time - last_success).total_seconds() < 7200  # 2 hours
        )
        
        # Determine status based on thresholds
        if detection_count >= self.tainted_threshold:
            return UserAgentHealth.BLOCKED
        elif detection_count >= self.degraded_threshold or consecutive_failures >= 5:
            return UserAgentHealth.TAINTED
        elif detection_count >= self.detection_threshold or (recent_detection and not has_recent_success):
            return UserAgentHealth.DEGRADED
        else:
            return UserAgentHealth.HEALTHY
    
    async def is_user_agent_tainted(self, user_agent: str) -> bool:
        """
        Check if user agent should be rotated out.
        
        Args:
            user_agent: User agent string to check
            
        Returns:
            True if user agent is tainted or blocked
        """
        if user_agent not in self._health_records:
            return False
        
        health_record = self._health_records[user_agent]
        return health_record.health_status in [UserAgentHealth.TAINTED, UserAgentHealth.BLOCKED]
    
    async def get_healthy_user_agents(self) -> List[str]:
        """
        Get list of healthy user agents for rotation.
        
        Returns:
            List of healthy user agent strings
        """
        await self._cleanup_expired_records()
        
        healthy_agents = []
        
        for user_agent, health_record in self._health_records.items():
            if health_record.health_status == UserAgentHealth.HEALTHY:
                healthy_agents.append(user_agent)
        
        # If no healthy agents, return degraded ones as backup
        if not healthy_agents:
            for user_agent, health_record in self._health_records.items():
                if health_record.health_status == UserAgentHealth.DEGRADED:
                    healthy_agents.append(user_agent)
        
        # Ensure we always have at least one user agent
        if not healthy_agents:
            healthy_agents = self._default_user_agents[:3]
            await self.logger.log_warning(
                "No healthy user agents available, using defaults",
                default_count=len(healthy_agents)
            )
        
        await self.logger.log_info(
            "Retrieved healthy user agents",
            healthy_count=len(healthy_agents),
            total_tracked=len(self._health_records)
        )
        
        return healthy_agents
    
    async def reset_user_agent_health(self, user_agent: str) -> None:
        """
        Reset health status for user agent.
        
        Args:
            user_agent: User agent string to reset
        """
        current_time = datetime.utcnow()
        
        # Reset counters
        self._detection_counts[user_agent] = 0
        self._consecutive_failures[user_agent] = 0
        self._last_detection.pop(user_agent, None)
        self._last_success[user_agent] = current_time
        
        # Reset health record
        if user_agent in self._health_records:
            health_record = self._health_records[user_agent]
            health_record.health_status = UserAgentHealth.HEALTHY
            health_record.detection_count = 0
            health_record.consecutive_failures = 0
            health_record.last_detection = None
            health_record.last_success = current_time
            health_record.updated_at = current_time
        
        await self.logger.log_info(
            "User agent health reset",
            user_agent=user_agent[:50] + "..." if len(user_agent) > 50 else user_agent
        )
    
    async def _cleanup_expired_records(self) -> None:
        """Clean up old health records to prevent memory leaks."""
        current_time = datetime.utcnow()
        cleanup_cutoff = current_time - timedelta(hours=self.health_decay_hours * 2)
        
        expired_agents = [
            user_agent for user_agent, health_record in self._health_records.items()
            if (health_record.last_success and health_record.last_success < cleanup_cutoff and
                health_record.last_detection and health_record.last_detection < cleanup_cutoff)
        ]
        
        for user_agent in expired_agents:
            # Don't remove default user agents
            if user_agent not in self._default_user_agents:
                self._health_records.pop(user_agent, None)
                self._detection_counts.pop(user_agent, None)
                self._consecutive_failures.pop(user_agent, None)
                self._last_detection.pop(user_agent, None)
                self._last_success.pop(user_agent, None)
        
        if expired_agents:
            await self.logger.log_info(
                "Cleaned up expired user agent records",
                expired_count=len(expired_agents)
            )
    
    async def get_health_statistics(self) -> Dict[str, Any]:
        """Get comprehensive health statistics."""
        await self._cleanup_expired_records()
        
        status_counts = defaultdict(int)
        total_detections = 0
        total_agents = len(self._health_records)
        
        for health_record in self._health_records.values():
            status_counts[health_record.health_status.value] += 1
            total_detections += health_record.detection_count
        
        # Calculate averages
        avg_detections = total_detections / total_agents if total_agents > 0 else 0
        
        # Find most problematic user agents
        problematic_agents = [
            {
                'user_agent': ua[:50] + "..." if len(ua) > 50 else ua,
                'status': record.health_status.value,
                'detections': record.detection_count,
                'consecutive_failures': record.consecutive_failures
            }
            for ua, record in self._health_records.items()
            if record.health_status in [UserAgentHealth.TAINTED, UserAgentHealth.BLOCKED]
        ]
        
        return {
            'total_tracked_agents': total_agents,
            'status_distribution': dict(status_counts),
            'total_detections': total_detections,
            'average_detections_per_agent': round(avg_detections, 2),
            'thresholds': {
                'detection_threshold': self.detection_threshold,
                'degraded_threshold': self.degraded_threshold,
                'tainted_threshold': self.tainted_threshold
            },
            'problematic_agents': problematic_agents[:10],  # Top 10 worst
            'healthy_agents_count': status_counts.get('healthy', 0),
            'default_agents_count': len(self._default_user_agents)
        }
    
    async def get_user_agent_details(self, user_agent: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about specific user agent."""
        if user_agent not in self._health_records:
            return None
        
        health_record = self._health_records[user_agent]
        
        return {
            'user_agent': user_agent,
            'health_status': health_record.health_status.value,
            'detection_count': health_record.detection_count,
            'consecutive_failures': health_record.consecutive_failures,
            'last_detection': health_record.last_detection.isoformat() if health_record.last_detection else None,
            'last_success': health_record.last_success.isoformat() if health_record.last_success else None,
            'created_at': health_record.created_at.isoformat(),
            'updated_at': health_record.updated_at.isoformat(),
            'is_default': user_agent in self._default_user_agents
        } 
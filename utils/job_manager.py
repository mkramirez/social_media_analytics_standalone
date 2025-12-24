"""
Job Manager

Manages background monitoring jobs without APScheduler.
Uses Streamlit session state and manual refresh.
"""

import streamlit as st
from typing import Dict, List, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import time


@dataclass
class MonitoringJob:
    """Represents a monitoring job."""
    id: str
    platform: str  # 'twitch', 'twitter', 'youtube', 'reddit'
    entity_id: int
    entity_name: str
    interval_minutes: int
    last_run: datetime = None
    next_run: datetime = None
    is_active: bool = True
    total_runs: int = 0
    last_error: str = None

    def __post_init__(self):
        """Set initial next_run time."""
        if self.next_run is None:
            self.next_run = datetime.now()


class JobManager:
    """Manages monitoring jobs in session state."""

    @staticmethod
    def _get_jobs_dict() -> Dict[str, MonitoringJob]:
        """Get or create jobs dictionary in session state."""
        if 'monitoring_jobs' not in st.session_state:
            st.session_state.monitoring_jobs = {}
        return st.session_state.monitoring_jobs

    @staticmethod
    def add_job(
        platform: str,
        entity_id: int,
        entity_name: str,
        interval_minutes: int = 15
    ) -> str:
        """
        Add a new monitoring job.

        Returns:
            str: Job ID
        """
        jobs = JobManager._get_jobs_dict()

        # Generate job ID
        job_id = f"{platform}_{entity_id}_{int(time.time())}"

        # Create job
        job = MonitoringJob(
            id=job_id,
            platform=platform,
            entity_id=entity_id,
            entity_name=entity_name,
            interval_minutes=interval_minutes
        )

        jobs[job_id] = job
        return job_id

    @staticmethod
    def remove_job(job_id: str):
        """Remove a job."""
        jobs = JobManager._get_jobs_dict()
        if job_id in jobs:
            del jobs[job_id]

    @staticmethod
    def pause_job(job_id: str):
        """Pause a job."""
        jobs = JobManager._get_jobs_dict()
        if job_id in jobs:
            jobs[job_id].is_active = False

    @staticmethod
    def resume_job(job_id: str):
        """Resume a paused job."""
        jobs = JobManager._get_jobs_dict()
        if job_id in jobs:
            jobs[job_id].is_active = True
            jobs[job_id].next_run = datetime.now()

    @staticmethod
    def get_job(job_id: str) -> MonitoringJob:
        """Get a job by ID."""
        jobs = JobManager._get_jobs_dict()
        return jobs.get(job_id)

    @staticmethod
    def get_all_jobs() -> List[MonitoringJob]:
        """Get all jobs."""
        jobs = JobManager._get_jobs_dict()
        return list(jobs.values())

    @staticmethod
    def get_jobs_by_platform(platform: str) -> List[MonitoringJob]:
        """Get all jobs for a specific platform."""
        jobs = JobManager._get_jobs_dict()
        return [job for job in jobs.values() if job.platform == platform]

    @staticmethod
    def get_active_jobs() -> List[MonitoringJob]:
        """Get all active jobs."""
        jobs = JobManager._get_jobs_dict()
        return [job for job in jobs.values() if job.is_active]

    @staticmethod
    def get_jobs_due_for_run() -> List[MonitoringJob]:
        """Get all jobs that are due to run."""
        now = datetime.now()
        jobs = JobManager._get_jobs_dict()
        return [
            job for job in jobs.values()
            if job.is_active and job.next_run <= now
        ]

    @staticmethod
    def mark_job_run(job_id: str, success: bool = True, error: str = None):
        """Mark a job as run."""
        jobs = JobManager._get_jobs_dict()
        if job_id in jobs:
            job = jobs[job_id]
            job.last_run = datetime.now()
            job.next_run = datetime.now() + timedelta(minutes=job.interval_minutes)
            job.total_runs += 1

            if success:
                job.last_error = None
            else:
                job.last_error = error

    @staticmethod
    def clear_all_jobs():
        """Clear all jobs."""
        st.session_state.monitoring_jobs = {}

    @staticmethod
    def get_job_statistics() -> Dict[str, Any]:
        """Get job statistics."""
        jobs = JobManager.get_all_jobs()

        return {
            'total_jobs': len(jobs),
            'active_jobs': len([j for j in jobs if j.is_active]),
            'paused_jobs': len([j for j in jobs if not j.is_active]),
            'jobs_by_platform': {
                'twitch': len([j for j in jobs if j.platform == 'twitch']),
                'twitter': len([j for j in jobs if j.platform == 'twitter']),
                'youtube': len([j for j in jobs if j.platform == 'youtube']),
                'reddit': len([j for j in jobs if j.platform == 'reddit']),
            },
            'total_runs': sum(j.total_runs for j in jobs),
            'jobs_with_errors': len([j for j in jobs if j.last_error is not None])
        }


def check_and_run_due_jobs():
    """
    Check for jobs that are due and trigger them.

    This function should be called periodically (e.g., in sidebar).
    Note: Actual job execution happens in platform-specific functions.
    """
    due_jobs = JobManager.get_jobs_due_for_run()

    if due_jobs:
        st.session_state.jobs_to_run = [job.id for job in due_jobs]
        return len(due_jobs)

    return 0

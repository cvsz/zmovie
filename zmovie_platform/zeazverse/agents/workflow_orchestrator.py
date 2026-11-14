"""Agent 19 -- Workflow Orchestrator

Handles dependencies, queues, retries, checkpoints and failure recovery
per Spec #19.

Responsibilities:
- Manage workflow dependencies between agents and stages
- Queue jobs for execution with priority ordering
- Implement retry logic with exponential backoff
- Create checkpoints for recovery after failures
- Handle failure recovery and dead-letter queues
- Track workflow state through the full pipeline

Agent Outputs:
- workflow_run: Complete workflow execution record
- queue_job: Queued job with priority and dependencies
- checkpoint: Recovery point with state snapshot
- retry_policy: Retry configuration with backoff
- failure_recovery: Recovery actions after failure
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class JobStatus(Enum):
    """Job execution status."""
    PENDING = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    BLOCKED = auto()


class JobPriority(Enum):
    """Job priority levels."""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class CheckpointType(Enum):
    """Types of checkpoints."""
    PRE_AGENT = auto()
    POST_AGENT = auto()
    STAGE_BOUNDARY = auto()
    FAILURE_RECOVERY = auto()


class RetryPolicy(Enum):
    """Retry strategies."""
    FIXED_DELAY = auto()
    EXPONENTIAL_BACKOFF = auto()
    LINEAR_BACKOFF = auto()
    NO_RETRY = auto()


@dataclass
class JobDependency:
    """Dependency relationship between jobs."""
    depends_on_job_id: str
    dependency_type: str  # "blocks", "requires_output", "notify_on_complete"


@dataclass
class QueuedJob:
    """A job in the workflow queue."""
    job_id: str
    agent_id: str
    action: str
    parameters: dict[str, Any]
    priority: JobPriority
    status: JobStatus
    dependencies: list[JobDependency] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    base_delay_seconds: int = 1
    max_delay_seconds: int = 300
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None

    def next_retry_delay(self) -> int:
        """Calculate next retry delay based on policy."""
        if self.retry_policy == RetryPolicy.NO_RETRY:
            return 0
        elif self.retry_policy == RetryPolicy.FIXED_DELAY:
            return self.base_delay_seconds
        elif self.retry_policy == RetryPolicy.LINEAR_BACKOFF:
            return self.base_delay_seconds * (self.retry_count + 1)
        elif self.retry_policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            delay = int(self.base_delay_seconds * (2 ** self.retry_count))
            return min(delay, int(self.max_delay_seconds))
        return 0

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries


@dataclass
class Checkpoint:
    """A recovery checkpoint in a workflow."""
    checkpoint_id: str
    workflow_id: str
    checkpoint_type: CheckpointType
    stage: str
    state_snapshot: dict[str, Any]
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class WorkflowRun:
    """A complete workflow execution record."""
    workflow_id: str
    episode_id: str
    series_id: str
    status: JobStatus
    current_stage: str
    completed_stages: list[str]
    failed_stages: list[str]
    jobs: list[str]  # Job IDs
    checkpoints: list[str]  # Checkpoint IDs
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])
    updated_at: str = field(default_factory=lambda: uuid4().hex[:12])
    error_message: str | None = None


class WorkflowOrchestrator:
    """Agent 19 -- Workflow Orchestrator implementation."""

    AGENT_ID = "AGENT_19"
    AGENT_NAME = "Workflow Orchestrator"
    DESCRIPTION = "Handles dependencies, queues, retries, checkpoints and failure recovery"

    # Default pipeline stages per Spec #6-#13
    DEFAULT_PIPELINE_STAGES = [
        "creative_direction",
        "story_writing",
        "storyboard",
        "cinematography",
        "action_choreography",
        "image_production",
        "video_production",
        "audio_direction",
        "video_editing",
        "continuity_qa",
        "policy_rights",
        "youtube_seo",
        "publishing",
    ]

    def __init__(self) -> None:
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self._jobs: dict[str, QueuedJob] = {}
        self._workflows: dict[str, WorkflowRun] = {}
        self._checkpoints: dict[str, Checkpoint] = {}
        self._queue: list[str] = []  # Job IDs in queue order

    def create_job(
        self, agent_id: str, action: str, parameters: dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        dependencies: list[JobDependency] | None = None,
        max_retries: int = 3,
        retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF,
    ) -> QueuedJob:
        """Create a new job and add to queue."""
        job_id = f"job_{uuid4().hex[:8]}"

        job = QueuedJob(
            job_id=job_id,
            agent_id=agent_id,
            action=action,
            parameters=parameters,
            priority=priority,
            status=JobStatus.QUEUED,
            dependencies=dependencies or [],
            max_retries=max_retries,
            retry_policy=retry_policy,
        )
        self._jobs[job_id] = job
        self._queue.append(job_id)
        # Sort queue by priority
        self._queue.sort(key=lambda jid: self._jobs[jid].priority.value)

        return job

    def get_job(self, job_id: str) -> QueuedJob | None:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def start_job(self, job_id: str) -> dict[str, Any]:
        """Mark a job as running."""
        if job_id not in self._jobs:
            return {
                "status": "blocked",
                "error": f"Job {job_id} not found",
            }

        job = self._jobs[job_id]

        # Check dependencies
        for dep in job.dependencies:
            dep_job = self._jobs.get(dep.depends_on_job_id)
            if dep_job is None:
                return {
                    "status": "blocked",
                    "error": (
                        f"Dependency job {dep.depends_on_job_id} not found"
                    ),
                }
            if dep_job.status != JobStatus.COMPLETED:
                return {
                    "status": "blocked",
                    "error": (
                        f"Dependency job {dep.depends_on_job_id} not completed. "
                        f"Status: {dep_job.status.name}"
                    ),
                }

        job.status = JobStatus.RUNNING
        job.started_at = uuid4().hex[:12]
        if job_id in self._queue:
            self._queue.remove(job_id)

        return {
            "status": "completed",
            "job_id": job_id,
            "agent_id": job.agent_id,
            "action": job.action,
        }

    def complete_job(
        self, job_id: str, result: dict[str, Any],
    ) -> dict[str, Any]:
        """Mark a job as completed with result."""
        if job_id not in self._jobs:
            return {
                "status": "blocked",
                "error": f"Job {job_id} not found",
            }

        job = self._jobs[job_id]
        job.status = JobStatus.COMPLETED
        job.completed_at = uuid4().hex[:12]
        job.result = result

        return {
            "status": "completed",
            "job_id": job_id,
            "result": result,
        }

    def fail_job(
        self, job_id: str, error_message: str,
    ) -> dict[str, Any]:
        """Mark a job as failed and handle retry logic."""
        if job_id not in self._jobs:
            return {
                "status": "blocked",
                "error": f"Job {job_id} not found",
            }

        job = self._jobs[job_id]

        if job.can_retry():
            job.retry_count += 1
            delay = job.next_retry_delay()
            job.status = JobStatus.QUEUED
            self._queue.append(job_id)
            self._queue.sort(key=lambda jid: self._jobs[jid].priority.value)

            return {
                "status": "retry",
                "job_id": job_id,
                "retry_count": job.retry_count,
                "next_retry_delay_seconds": delay,
                "max_retries": job.max_retries,
            }
        else:
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.completed_at = uuid4().hex[:12]

            return {
                "status": "failed",
                "job_id": job_id,
                "error": error_message,
                "retry_count": job.retry_count,
            }

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Cancel a job."""
        if job_id not in self._jobs:
            return {
                "status": "blocked",
                "error": f"Job {job_id} not found",
            }

        job = self._jobs[job_id]
        job.status = JobStatus.CANCELLED
        if job_id in self._queue:
            self._queue.remove(job_id)

        return {
            "status": "completed",
            "job_id": job_id,
        }

    def create_checkpoint(
        self, workflow_id: str, checkpoint_type: CheckpointType,
        stage: str, state_snapshot: dict[str, Any],
    ) -> Checkpoint:
        """Create a recovery checkpoint."""
        checkpoint_id = f"checkpoint_{uuid4().hex[:8]}"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_id,
            checkpoint_type=checkpoint_type,
            stage=stage,
            state_snapshot=state_snapshot,
        )
        self._checkpoints[checkpoint_id] = checkpoint

        if workflow_id in self._workflows:
            self._workflows[workflow_id].checkpoints.append(checkpoint_id)
            self._workflows[workflow_id].updated_at = uuid4().hex[:12]

        return checkpoint

    def create_workflow(
        self, episode_id: str, series_id: str,
        stages: list[str] | None = None,
    ) -> WorkflowRun:
        """Create a new workflow run for an episode."""
        workflow_id = f"workflow_{uuid4().hex[:8]}"
        stages = stages or self.DEFAULT_PIPELINE_STAGES

        workflow = WorkflowRun(
            workflow_id=workflow_id,
            episode_id=episode_id,
            series_id=series_id,
            status=JobStatus.PENDING,
            current_stage=stages[0] if stages else "",
            completed_stages=[],
            failed_stages=[],
            jobs=[],
            checkpoints=[],
        )
        self._workflows[workflow_id] = workflow
        return workflow

    def advance_workflow_stage(
        self, workflow_id: str, completed_stage: str,
    ) -> dict[str, Any]:
        """Advance workflow to the next stage."""
        if workflow_id not in self._workflows:
            return {
                "status": "blocked",
                "error": f"Workflow {workflow_id} not found",
            }

        workflow = self._workflows[workflow_id]
        all_stages = self.DEFAULT_PIPELINE_STAGES

        if completed_stage not in workflow.completed_stages:
            workflow.completed_stages.append(completed_stage)

        # Find next stage
        try:
            current_index = all_stages.index(completed_stage)
            if current_index + 1 < len(all_stages):
                next_stage = all_stages[current_index + 1]
                workflow.current_stage = next_stage
                workflow.status = JobStatus.RUNNING
            else:
                workflow.current_stage = ""
                workflow.status = JobStatus.COMPLETED
        except ValueError:
            workflow.status = JobStatus.FAILED
            workflow.error_message = f"Unknown stage: {completed_stage}"

        workflow.updated_at = uuid4().hex[:12]

        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "completed_stage": completed_stage,
            "next_stage": workflow.current_stage,
            "workflow_status": workflow.status.name,
        }

    def fail_workflow_stage(
        self, workflow_id: str, failed_stage: str,
        error_message: str,
    ) -> dict[str, Any]:
        """Mark a workflow stage as failed."""
        if workflow_id not in self._workflows:
            return {
                "status": "blocked",
                "error": f"Workflow {workflow_id} not found",
            }

        workflow = self._workflows[workflow_id]
        workflow.failed_stages.append(failed_stage)
        workflow.status = JobStatus.FAILED
        workflow.error_message = error_message
        workflow.updated_at = uuid4().hex[:12]

        return {
            "status": "failed",
            "workflow_id": workflow_id,
            "failed_stage": failed_stage,
            "error": error_message,
        }

    def recover_from_checkpoint(
        self, checkpoint_id: str,
    ) -> dict[str, Any]:
        """Recover workflow from a checkpoint."""
        if checkpoint_id not in self._checkpoints:
            return {
                "status": "blocked",
                "error": f"Checkpoint {checkpoint_id} not found",
            }

        checkpoint = self._checkpoints[checkpoint_id]
        workflow_id = checkpoint.workflow_id

        if workflow_id not in self._workflows:
            return {
                "status": "blocked",
                "error": f"Workflow {workflow_id} not found",
            }

        workflow = self._workflows[workflow_id]
        workflow.current_stage = checkpoint.stage
        workflow.status = JobStatus.PENDING
        workflow.error_message = None
        workflow.updated_at = uuid4().hex[:12]

        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "recovered_to_stage": checkpoint.stage,
            "checkpoint_type": checkpoint.checkpoint_type.name,
            "state_snapshot": checkpoint.state_snapshot,
        }

    def get_queue(self) -> list[dict[str, Any]]:
        """Get current queue status."""
        return [
            {
                "job_id": job_id,
                "agent_id": self._jobs[job_id].agent_id,
                "action": self._jobs[job_id].action,
                "priority": self._jobs[job_id].priority.name,
                "status": self._jobs[job_id].status.name,
                "retry_count": self._jobs[job_id].retry_count,
            }
            for job_id in self._queue
        ]

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow run details."""
        if workflow_id not in self._workflows:
            return None
        workflow = self._workflows[workflow_id]
        return {
            "workflow_id": workflow.workflow_id,
            "episode_id": workflow.episode_id,
            "series_id": workflow.series_id,
            "status": workflow.status.name,
            "current_stage": workflow.current_stage,
            "completed_stages": workflow.completed_stages,
            "failed_stages": workflow.failed_stages,
            "jobs": workflow.jobs,
            "checkpoints": workflow.checkpoints,
            "error_message": workflow.error_message,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        queued = sum(1 for j in self._jobs.values() if j.status == JobStatus.QUEUED)
        running = sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)
        completed = sum(1 for j in self._jobs.values() if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED)

        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "workflow_orchestration",
            "total_jobs": len(self._jobs),
            "queued": queued,
            "running": running,
            "completed": completed,
            "failed": failed,
            "total_workflows": len(self._workflows),
            "total_checkpoints": len(self._checkpoints),
            "pipeline_stages": self.DEFAULT_PIPELINE_STAGES,
        }


# Module-level agent instance
agent = WorkflowOrchestrator()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Workflow Orchestrator action.

    Args:
        action: The action to execute
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "create_job":
        job = agent_obj.create_job(
            agent_id=kwargs.get("agent_id", ""),
            action=kwargs.get("target_action", ""),
            parameters=kwargs.get("parameters", {}),
            priority=JobPriority[kwargs.get("priority", "NORMAL")],
            dependencies=[
                JobDependency(
                    depends_on_job_id=d["depends_on_job_id"],
                    dependency_type=d.get("dependency_type", "blocks"),
                )
                for d in kwargs.get("dependencies", [])
            ],
            max_retries=kwargs.get("max_retries", 3),
            retry_policy=RetryPolicy[kwargs.get("retry_policy", "EXPONENTIAL_BACKOFF")],
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "create_job",
            "status": "completed",
            "job_id": job.job_id,
            "agent_id": job.agent_id,
            "job_action": job.action,
            "priority": job.priority.name,
            "job_status": job.status.name,
        }

    elif action == "start_job":
        result = agent_obj.start_job(kwargs.get("job_id", ""))
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "start_job",
            **result,
        }

    elif action == "complete_job":
        result = agent_obj.complete_job(
            job_id=kwargs.get("job_id", ""),
            result=kwargs.get("result", {}),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "complete_job",
            **result,
        }

    elif action == "fail_job":
        result = agent_obj.fail_job(
            job_id=kwargs.get("job_id", ""),
            error_message=kwargs.get("error_message", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "fail_job",
            **result,
        }

    elif action == "cancel_job":
        result = agent_obj.cancel_job(kwargs.get("job_id", ""))
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "cancel_job",
            **result,
        }

    elif action == "create_checkpoint":
        checkpoint = agent_obj.create_checkpoint(
            workflow_id=kwargs.get("workflow_id", ""),
            checkpoint_type=CheckpointType[kwargs.get("checkpoint_type", "PRE_AGENT")],
            stage=kwargs.get("stage", ""),
            state_snapshot=kwargs.get("state_snapshot", {}),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "create_checkpoint",
            "status": "completed",
            "checkpoint_id": checkpoint.checkpoint_id,
            "workflow_id": checkpoint.workflow_id,
            "checkpoint_type": checkpoint.checkpoint_type.name,
            "stage": checkpoint.stage,
        }

    elif action == "create_workflow":
        workflow = agent_obj.create_workflow(
            episode_id=kwargs.get("episode_id", ""),
            series_id=kwargs.get("series_id", ""),
            stages=kwargs.get("stages"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "create_workflow",
            "status": "completed",
            "workflow_id": workflow.workflow_id,
            "episode_id": workflow.episode_id,
            "series_id": workflow.series_id,
            "current_stage": workflow.current_stage,
            "workflow_status": workflow.status.name,
        }

    elif action == "advance_workflow_stage":
        result = agent_obj.advance_workflow_stage(
            workflow_id=kwargs.get("workflow_id", ""),
            completed_stage=kwargs.get("completed_stage", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "advance_workflow_stage",
            **result,
        }

    elif action == "fail_workflow_stage":
        result = agent_obj.fail_workflow_stage(
            workflow_id=kwargs.get("workflow_id", ""),
            failed_stage=kwargs.get("failed_stage", ""),
            error_message=kwargs.get("error_message", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "fail_workflow_stage",
            **result,
        }

    elif action == "recover_from_checkpoint":
        result = agent_obj.recover_from_checkpoint(
            checkpoint_id=kwargs.get("checkpoint_id", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "recover_from_checkpoint",
            **result,
        }

    elif action == "get_queue":
        queue = agent_obj.get_queue()
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_queue",
            "status": "completed",
            "queue": queue,
        }

    elif action == "get_workflow":
        workflow_data = agent_obj.get_workflow(kwargs.get("workflow_id", ""))
        if workflow_data is None:
            return {
                "agent": agent_obj.AGENT_ID,
                "action": "get_workflow",
                "status": "blocked",
                "error": "Workflow not found",
            }
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_workflow",
            "status": "completed",
            "workflow": workflow_data,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "WorkflowOrchestrator",
    "QueuedJob",
    "Checkpoint",
    "WorkflowRun",
    "JobDependency",
    "JobStatus",
    "JobPriority",
    "CheckpointType",
    "RetryPolicy",
    "execute_action",
    "agent",
]
import logging

logger = logging.getLogger(__name__)

class TaskResult:
    def __init__(self, task_id):
        self.id = task_id

class DataIndexingTask:
    """
    Stub for Celery task. 
    In a real production environment, this would be decorated with @shared_task.
    """
    def delay(self, project_id: str, do_reset: int = 0):
        """
        Simulates pushing a task to the queue.
        """
        logger.info(f"Queuing indexing task for project: {project_id} (reset={do_reset})")
        # Returning a mock task ID
        return TaskResult(task_id="task-uuid-simulated-12345")

# Export the instance to be used by the router
index_data_content = DataIndexingTask()

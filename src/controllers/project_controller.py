from pathlib import Path

class ProjectController:
    """Controller for managing project-specific structures."""
    
    def __init__(self, base_assets_path: str = "src/assets/files"):
        self.base_path = Path(base_assets_path)
    
    def get_project_path(self, project_id: str) -> Path:
        """Get the absolute path for a specific project's files."""
        return self.base_path / project_id
    
    def ensure_project_path(self, project_id: str) -> Path:
        """Create and return the project path if it doesn't exist."""
        path = self.get_project_path(project_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

# Create controller object
project_controller = ProjectController()

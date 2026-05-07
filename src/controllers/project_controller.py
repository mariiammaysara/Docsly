from pathlib import Path

class ProjectController:
    """
    Controller for managing project folders.
    It helps us create and find folders where we save user files (like PDFs).
    """
    
    def __init__(self, base_assets_path: str = "src/assets/files"):
        # The main folder where all files are stored
        self.base_path = Path(base_assets_path)
    
    def get_project_path(self, project_id: str) -> Path:
        """Get the exact folder path for a specific project."""
        return self.base_path / project_id
    
    def ensure_project_path(self, project_id: str) -> Path:
        """
        Check if the project folder exists. 
        If it does not exist, create it automatically.
        """
        path = self.get_project_path(project_id)
        # Create folder and its parents if missing. Do nothing if it already exists.
        path.mkdir(parents=True, exist_ok=True)
        return path

# Create a global object to be used across the app
project_controller = ProjectController()

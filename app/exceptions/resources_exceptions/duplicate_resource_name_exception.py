class DuplicateResourceNameException(Exception):
    def __init__(self, resource_name: str):
        super().__init__(f"A resource with name '{resource_name}' already exists.")

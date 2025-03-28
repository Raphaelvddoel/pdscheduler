class PagerDutyUser:
    """
    Represents a PagerDuty user with their essential information.
    This class handles user data from the PagerDuty API and provides
    a structured representation for scheduling and notifications.
    """

    def __init__(self, data):
        """
        Initialize a PagerDuty user with essential data.

        Args:
            data (dict): User data dictionary from PagerDuty API containing
                         'id', 'email', 'summary', and 'role' fields

        Raises:
            KeyError: If any required fields are missing from the data
        """
        # Extract required fields - will raise KeyError naturally if missing
        self.id = data["id"]
        self.email = data["email"]
        self.name = data["summary"]
        self.role = data["role"]

    def __str__(self):
        """Return a string representation of the user."""
        return f"{self.name} ({self.email}) - {self.role}"

    def __repr__(self):
        """Return a detailed string representation of the user."""
        return f"PagerDutyUser(id={self.id}, name={self.name}, email={self.email}, role={self.role})"

    def __eq__(self, other):
        """Check equality based on user ID."""
        if isinstance(other, PagerDutyUser):
            return self.id == other.id

        return False

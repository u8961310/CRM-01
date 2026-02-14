from app.models.user import User, Role
from app.models.parent import Parent
from app.models.student import Student, ParentStudent
from app.models.communication import CommunicationRecord, ContactType, FollowUp

__all__ = [
    "User",
    "Role",
    "Parent",
    "Student",
    "ParentStudent",
    "CommunicationRecord",
    "ContactType",
    "FollowUp",
]

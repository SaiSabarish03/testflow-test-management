# Import all models here so Base.metadata is fully populated.
# This file is imported by migrations/env.py via app.core.database.Base.
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.test_suite import TestSuite
from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.models.defect import Defect

__all__ = [
    "User",
    "Project",
    "ProjectMember",
    "TestSuite",
    "TestCase",
    "TestRun",
    "TestResult",
    "Defect",
]

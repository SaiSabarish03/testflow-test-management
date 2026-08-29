import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { AppLayout } from '../layouts/AppLayout';
import { LoginPage } from '../pages/Login/LoginPage';
import { DashboardPage } from '../pages/Dashboard/DashboardPage';
import { ProjectsPage } from '../pages/Projects/ProjectsPage';
import { ProjectDetailPage } from '../pages/Projects/ProjectDetailPage';
import { SuiteDetailPage } from '../pages/TestSuites/SuiteDetailPage';
import { TestCaseFormPage } from '../pages/TestCases/TestCaseFormPage';
import { TestCaseDetailPage } from '../pages/TestCases/TestCaseDetailPage';
import { CreateRunPage } from '../pages/TestRuns/CreateRunPage';
import { RunDetailPage } from '../pages/TestRuns/RunDetailPage';
import { DefectsPage } from '../pages/Defects/DefectsPage';
import { DefectDetailPage } from '../pages/Defects/DefectDetailPage';
import { UsersPage } from '../pages/Users/UsersPage';
import { NotFoundPage } from '../pages/NotFoundPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />

        {/* Projects */}
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route
          path="/projects/:projectId/runs/new"
          element={
            <ProtectedRoute requiredRoles={['ADMIN', 'QA_ENGINEER']}>
              <CreateRunPage />
            </ProtectedRoute>
          }
        />

        {/* Suites */}
        <Route path="/suites/:suiteId" element={<SuiteDetailPage />} />
        <Route path="/suites/:suiteId/test-cases/new" element={<TestCaseFormPage />} />

        {/* Test Cases */}
        <Route path="/test-cases/:testCaseId" element={<TestCaseDetailPage />} />
        <Route path="/test-cases/:testCaseId/edit" element={<TestCaseFormPage />} />

        {/* Test Runs */}
        <Route path="/runs/:runId" element={<RunDetailPage />} />

        {/* Defects */}
        <Route path="/defects" element={<DefectsPage />} />
        <Route path="/defects/:defectId" element={<DefectDetailPage />} />

        {/* Users — admin only */}
        <Route path="/users" element={<ProtectedRoute requiredRoles={['ADMIN']}><UsersPage /></ProtectedRoute>} />
      </Route>

      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}

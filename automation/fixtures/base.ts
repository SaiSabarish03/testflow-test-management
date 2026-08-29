import { test as base, expect } from '@playwright/test';
import { STORAGE_STATE } from '../config/storage-state';
import { LoginPage } from '../pages/LoginPage';
import { ProjectsPage } from '../pages/ProjectsPage';
import { ProjectDetailPage } from '../pages/ProjectDetailPage';
import { SuiteDetailPage } from '../pages/SuiteDetailPage';
import { TestCaseDetailPage } from '../pages/TestCaseDetailPage';
import { TestCaseFormPage } from '../pages/TestCaseFormPage';
import { CreateRunPage } from '../pages/CreateRunPage';
import { RunDetailPage } from '../pages/RunDetailPage';
import { DefectsPage } from '../pages/DefectsPage';
import { DefectDetailPage } from '../pages/DefectDetailPage';
import { UsersPage } from '../pages/UsersPage';

type Pages = {
  loginPage: LoginPage;
  projectsPage: ProjectsPage;
  projectDetailPage: ProjectDetailPage;
  suiteDetailPage: SuiteDetailPage;
  testCaseDetailPage: TestCaseDetailPage;
  testCaseFormPage: TestCaseFormPage;
  createRunPage: CreateRunPage;
  runDetailPage: RunDetailPage;
  defectsPage: DefectsPage;
  defectDetailPage: DefectDetailPage;
  usersPage: UsersPage;
};

export const test = base.extend<Pages>({
  loginPage: async ({ page }, use) => use(new LoginPage(page)),
  projectsPage: async ({ page }, use) => use(new ProjectsPage(page)),
  projectDetailPage: async ({ page }, use) => use(new ProjectDetailPage(page)),
  suiteDetailPage: async ({ page }, use) => use(new SuiteDetailPage(page)),
  testCaseDetailPage: async ({ page }, use) => use(new TestCaseDetailPage(page)),
  testCaseFormPage: async ({ page }, use) => use(new TestCaseFormPage(page)),
  createRunPage: async ({ page }, use) => use(new CreateRunPage(page)),
  runDetailPage: async ({ page }, use) => use(new RunDetailPage(page)),
  defectsPage: async ({ page }, use) => use(new DefectsPage(page)),
  defectDetailPage: async ({ page }, use) => use(new DefectDetailPage(page)),
  usersPage: async ({ page }, use) => use(new UsersPage(page)),
});

/** Admin-authenticated test — call test.use() inside describe blocks */
export const adminTest = test;
export const qaTest = test;
export const viewerTest = test;

export { expect, STORAGE_STATE };

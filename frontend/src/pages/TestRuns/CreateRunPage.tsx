import { useState } from 'react';
import { Form, Input, Button, Card, Typography, Table, notification, Space, Empty, Alert } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import type { TableRowSelection } from 'antd/es/table/interface';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../hooks/useAsync';
import { getProject } from '../../api/projects';
import { listSuites } from '../../api/testSuites';
import { listTestCases } from '../../api/testCases';
import { createRun } from '../../api/testRuns';
import { PageLoader } from '../../components/common/PageLoader';
import { PageError } from '../../components/common/PageError';
import { AppBreadcrumb } from '../../components/common/AppBreadcrumb';
import { StatusTag } from '../../components/common/StatusTag';
import { extractErrorMessage } from '../../api/client';
import { TEST_CASE_STATUS_LABELS } from '../../constants';
import type { TestCase } from '../../types';

const { Title } = Typography;

export function CreateRunPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);
  const id = Number(projectId);

  const { data: project, isLoading: projLoading, error: projError } = useAsync(() => getProject(id), [id]);

  // Load all READY test cases across all suites in this project
  const { data: suitesData } = useAsync(() => listSuites(id, { page: 1, page_size: 100 }), [id]);

  // Collect all READY test cases from all suites
  const suiteIds = suitesData?.items.map((s) => s.id) ?? [];
  const { data: casesData, isLoading: casesLoading } = useAsync(
    async () => {
      if (suiteIds.length === 0) return { items: [] as TestCase[], total: 0, page: 1, page_size: 100, pages: 1 };
      const results = await Promise.all(
        suiteIds.map((sid) => listTestCases(sid, { status: 'READY', page: 1, page_size: 100 })),
      );
      const items = results.flatMap((r) => r.items);
      return { items, total: items.length, page: 1, page_size: 100, pages: 1 };
    },
    [suiteIds.join(',')],
  );

  const readyCases = casesData?.items ?? [];
  const suiteNameById = new Map((suitesData?.items ?? []).map((suite) => [suite.id, suite.name]));

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (selectedIds.length === 0) {
        notification.warning({ message: 'Select at least one test case' });
        return;
      }
      setSaving(true);
      const run = await createRun(id, { ...values, test_case_ids: selectedIds });
      notification.success({ message: 'Test run created' });
      navigate(`/runs/${run.id}`);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const columns: ColumnsType<TestCase> = [
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Suite', dataIndex: 'suite_id', key: 'suite_id', render: (suiteId: number) => suiteNameById.get(suiteId) ?? `Suite #${suiteId}` },
    { title: 'Priority', dataIndex: 'priority', key: 'priority' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: keyof typeof TEST_CASE_STATUS_LABELS) => <StatusTag value={s} label={TEST_CASE_STATUS_LABELS[s]} /> },
  ];

  const rowSelection: TableRowSelection<TestCase> = {
    selectedRowKeys: selectedIds,
    onChange: (keys) => setSelectedIds(keys as number[]),
  };

  if (projLoading) return <PageLoader />;
  if (projError) return <PageError message={projError} />;
  if (!project) return null;

  return (
    <div>
      <AppBreadcrumb items={[
        { label: 'Projects', path: '/projects' },
        { label: project.name, path: `/projects/${id}` },
        { label: 'New Test Run' },
      ]} />
      <Title level={2}>New Test Run</Title>

      <Card style={{ maxWidth: 800 }}>
        <Form form={form} layout="vertical">
          <Form.Item label="Run Name" name="name" rules={[{ required: true, message: 'Name is required' }]}>
            <Input placeholder="Regression Run – Release 1.0" aria-label="Run name" />
          </Form.Item>
          <Form.Item label="Environment" name="environment" rules={[{ required: true, message: 'Environment is required' }]}>
            <Input placeholder="QA" aria-label="Environment" />
          </Form.Item>
        </Form>

        <Title level={5} style={{ marginTop: 16 }}>Select Test Cases</Title>
        {selectedIds.length === 0 && (
          <Alert message="Select at least one READY test case" type="info" showIcon style={{ marginBottom: 8 }} />
        )}
        <Table<TestCase>
          rowKey="id"
          rowSelection={rowSelection}
          columns={columns}
          dataSource={readyCases}
          loading={casesLoading}
          locale={{ emptyText: <Empty description="No READY test cases found in this project" /> }}
          pagination={false}
          size="small"
          aria-label="Select test cases"
        />

        <Space style={{ marginTop: 16 }}>
          <Button type="primary" onClick={handleSubmit} loading={saving} aria-label="Create Test Run">
            Create Run ({selectedIds.length} selected)
          </Button>
          <Button onClick={() => navigate(`/projects/${id}?tab=runs`)} aria-label="Cancel">Cancel</Button>
        </Space>
      </Card>
    </div>
  );
}

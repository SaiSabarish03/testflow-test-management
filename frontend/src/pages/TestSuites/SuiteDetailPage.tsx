import { useState } from 'react';
import { Typography, Table, Button, Input, Select, Space, Empty, Tag, Popconfirm, notification, Row, Col } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../hooks/useAsync';
import { getSuite } from '../../api/testSuites';
import { listTestCases, deprecateTestCase } from '../../api/testCases';
import { usePermissions } from '../../hooks/usePermissions';
import { PageLoader } from '../../components/common/PageLoader';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { AppBreadcrumb } from '../../components/common/AppBreadcrumb';
import { extractErrorMessage } from '../../api/client';
import { PAGE_SIZE_DEFAULT, TEST_CASE_STATUS_LABELS } from '../../constants';
import type { TestCase, TestCasePriority, TestCaseStatus } from '../../types';

const { Title } = Typography;
const { Option } = Select;

const PRIORITY_COLORS: Record<TestCasePriority, string> = {
  LOW: 'default', MEDIUM: 'blue', HIGH: 'orange', CRITICAL: 'red',
};

export function SuiteDetailPage() {
  const { suiteId } = useParams<{ suiteId: string }>();
  const navigate = useNavigate();
  const { canWrite } = usePermissions();
  const id = Number(suiteId);

  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<TestCasePriority | ''>('');
  const [statusFilter, setStatusFilter] = useState<TestCaseStatus | ''>('');
  const [page, setPage] = useState(1);

  const { data: suite, isLoading: suiteLoading, error: suiteError } = useAsync(() => getSuite(id), [id]);
  const { data, isLoading, error, reload } = useAsync(
    () => listTestCases(id, { search: search || undefined, priority: priorityFilter || undefined, status: statusFilter || undefined, page, page_size: PAGE_SIZE_DEFAULT }),
    [id, search, priorityFilter, statusFilter, page],
  );

  const handleDeprecate = async (tc: TestCase) => {
    try {
      await deprecateTestCase(tc.id);
      notification.success({ message: `"${tc.title}" deprecated` });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    }
  };

  if (suiteLoading) return <PageLoader />;
  if (suiteError) return <PageError message={suiteError} />;
  if (!suite) return null;

  const columns: ColumnsType<TestCase> = [
    {
      title: 'Title', dataIndex: 'title', key: 'title',
      render: (title: string, record) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/test-cases/${record.id}`)} aria-label={`Open test case ${title}`}>{title}</Button>
      ),
    },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', render: (p: TestCasePriority) => <Tag color={PRIORITY_COLORS[p]}>{p}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: TestCaseStatus) => <StatusTag value={s} label={TEST_CASE_STATUS_LABELS[s]} /> },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleDateString() },
    ...(canWrite ? [{
      title: '', key: 'actions',
      render: (_: unknown, record: TestCase) => (
        <Space>
          <Button size="small" onClick={() => navigate(`/test-cases/${record.id}`)} aria-label={`View ${record.title}`}>View</Button>
          {record.status !== 'DEPRECATED' && (
            <Popconfirm title="Deprecate this test case?" onConfirm={() => handleDeprecate(record)} okText="Deprecate" okButtonProps={{ danger: true }}>
              <Button size="small" danger aria-label={`Deprecate ${record.title}`}>Deprecate</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    }] : []),
  ];

  return (
    <div>
      <AppBreadcrumb items={[
        { label: 'Projects', path: '/projects' },
        { label: 'Project', path: `/projects/${suite.project_id}` },
        { label: suite.name },
      ]} />
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={2} style={{ margin: 0 }}>{suite.name}</Title></Col>
        {canWrite && (
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/suites/${id}/test-cases/new`)} aria-label="Create test case">
              New Test Case
            </Button>
          </Col>
        )}
      </Row>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input placeholder="Search test cases…" prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ width: 240 }} allowClear aria-label="Search test cases" />
        <Select value={priorityFilter} onChange={(v) => { setPriorityFilter(v); setPage(1); }} style={{ width: 140 }} aria-label="Filter by priority">
          <Option value="">All priorities</Option>
          {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as TestCasePriority[]).map((p) => <Option key={p} value={p}>{p}</Option>)}
        </Select>
        <Select value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1); }} style={{ width: 140 }} aria-label="Filter by status">
          <Option value="">All statuses</Option>
          {(['DRAFT', 'READY', 'DEPRECATED'] as TestCaseStatus[]).map((s) => <Option key={s} value={s}>{TEST_CASE_STATUS_LABELS[s]}</Option>)}
        </Select>
      </Space>
      {error && <PageError message={error} onRetry={reload} />}
      <Table<TestCase>
        rowKey="id" columns={columns} dataSource={data?.items ?? []} loading={isLoading}
        locale={{ emptyText: <Empty description="No test cases found" /> }}
        pagination={{ current: page, pageSize: PAGE_SIZE_DEFAULT, total: data?.total ?? 0, onChange: setPage }}
        aria-label="Test cases table"
      />
    </div>
  );
}

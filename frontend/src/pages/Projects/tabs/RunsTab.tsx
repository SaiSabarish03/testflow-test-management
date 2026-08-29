import { useState } from 'react';
import { Table, Button, Input, Select, Space, Empty } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../../hooks/useAsync';
import { listRuns } from '../../../api/testRuns';
import { usePermissions } from '../../../hooks/usePermissions';
import { PageError } from '../../../components/common/PageError';
import { StatusTag } from '../../../components/common/StatusTag';
import { PAGE_SIZE_DEFAULT, TEST_RUN_STATUS_LABELS } from '../../../constants';
import type { Project, TestRun, TestRunStatus } from '../../../types';

const { Option } = Select;
interface Props { project: Project }

export function RunsTab({ project }: Props) {
  const navigate = useNavigate();
  const { canWrite } = usePermissions();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<TestRunStatus | ''>('');
  const [environmentFilter, setEnvironmentFilter] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error, reload } = useAsync(
    () => listRuns(project.id, {
      search: search || undefined,
      status: statusFilter || undefined,
      environment: environmentFilter || undefined,
      page,
      page_size: PAGE_SIZE_DEFAULT,
    }),
    [project.id, search, statusFilter, environmentFilter, page],
  );

  const columns: ColumnsType<TestRun> = [
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      render: (name: string, record) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/runs/${record.id}`)} aria-label={`Open run ${name}`}>{name}</Button>
      ),
    },
    { title: 'Environment', dataIndex: 'environment', key: 'environment' },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: TestRunStatus) => <StatusTag value={s} label={TEST_RUN_STATUS_LABELS[s]} />,
    },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleDateString() },
    {
      title: '', key: 'actions',
      render: (_: unknown, record: TestRun) => (
        <Button size="small" onClick={() => navigate(`/runs/${record.id}`)} aria-label={`View run ${record.name}`}>View</Button>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 12 }} wrap>
        <Input placeholder="Search runs…" prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ width: 220 }} allowClear aria-label="Search runs" />
        <Input
          placeholder="Environment"
          value={environmentFilter}
          onChange={(e) => { setEnvironmentFilter(e.target.value); setPage(1); }}
          style={{ width: 180 }}
          allowClear
          aria-label="Filter by environment"
        />
        <Select value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1); }} style={{ width: 160 }} aria-label="Filter by status">
          <Option value="">All statuses</Option>
          {(['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ABORTED'] as TestRunStatus[]).map((s) => (
            <Option key={s} value={s}>{TEST_RUN_STATUS_LABELS[s]}</Option>
          ))}
        </Select>
        {canWrite && project.status === 'ACTIVE' && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/projects/${project.id}/runs/new`)} aria-label="Create Test Run">
            New Run
          </Button>
        )}
      </Space>

      {error && <PageError message={error} onRetry={reload} />}

      <Table<TestRun>
        rowKey="id" columns={columns} dataSource={data?.items ?? []} loading={isLoading}
        locale={{ emptyText: <Empty description="No test runs found" /> }}
        pagination={{ current: page, pageSize: PAGE_SIZE_DEFAULT, total: data?.total ?? 0, onChange: setPage }}
        aria-label="Test runs table"
      />
    </div>
  );
}

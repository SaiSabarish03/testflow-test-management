import { useState } from 'react';
import { Table, Button, Input, Select, Space, Empty } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../../hooks/useAsync';
import { listDefects } from '../../../api/defects';
import { usePermissions } from '../../../hooks/usePermissions';
import { PageError } from '../../../components/common/PageError';
import { StatusTag } from '../../../components/common/StatusTag';
import { PAGE_SIZE_DEFAULT, DEFECT_STATUS_LABELS, DEFECT_SEVERITY_LABELS } from '../../../constants';
import type { Project, Defect, DefectStatus, DefectSeverity } from '../../../types';

const { Option } = Select;
interface Props { project: Project }

export function DefectsTab({ project }: Props) {
  const navigate = useNavigate();
  const { canWrite } = usePermissions();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<DefectStatus | ''>('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error, reload } = useAsync(
    () => listDefects({ project_id: project.id, search: search || undefined, status: statusFilter || undefined, page, page_size: PAGE_SIZE_DEFAULT }),
    [project.id, search, statusFilter, page],
  );

  const columns: ColumnsType<Defect> = [
    {
      title: 'Title', dataIndex: 'title', key: 'title',
      render: (title: string, record) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/defects/${record.id}`)} aria-label={`Open defect ${title}`}>{title}</Button>
      ),
    },
    { title: 'Severity', dataIndex: 'severity', key: 'severity', render: (s: DefectSeverity) => <StatusTag value={s} label={DEFECT_SEVERITY_LABELS[s]} /> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: DefectStatus) => <StatusTag value={s} label={DEFECT_STATUS_LABELS[s]} /> },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleDateString() },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 12 }} wrap>
        <Input placeholder="Search defects…" prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ width: 220 }} allowClear aria-label="Search defects" />
        <Select value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1); }} style={{ width: 160 }} aria-label="Filter by status">
          <Option value="">All statuses</Option>
          {(['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED'] as DefectStatus[]).map((s) => (
            <Option key={s} value={s}>{DEFECT_STATUS_LABELS[s]}</Option>
          ))}
        </Select>
        {canWrite && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/defects?project_id=${project.id}&create=1`)} aria-label="Create defect">
            New Defect
          </Button>
        )}
      </Space>

      {error && <PageError message={error} onRetry={reload} />}

      <Table<Defect>
        rowKey="id" columns={columns} dataSource={data?.items ?? []} loading={isLoading}
        locale={{ emptyText: <Empty description="No defects found" /> }}
        pagination={{ current: page, pageSize: PAGE_SIZE_DEFAULT, total: data?.total ?? 0, onChange: setPage }}
        aria-label="Defects table"
      />
    </div>
  );
}

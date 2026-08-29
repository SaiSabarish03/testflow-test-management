import { useState } from 'react';
import { Table, Button, Input, Space, Empty, Form, Modal, Popconfirm, notification, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, FolderOpenOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../../hooks/useAsync';
import { listSuites, createSuite, updateSuite, deleteSuite } from '../../../api/testSuites';
import { usePermissions } from '../../../hooks/usePermissions';
import { PageError } from '../../../components/common/PageError';
import { extractErrorMessage } from '../../../api/client';
import { PAGE_SIZE_DEFAULT } from '../../../constants';
import type { Project, TestSuite } from '../../../types';

interface Props { project: Project }

export function SuitesTab({ project }: Props) {
  const navigate = useNavigate();
  const { canWrite } = usePermissions();
  const [form] = Form.useForm();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editSuite, setEditSuite] = useState<TestSuite | null>(null);
  const [saving, setSaving] = useState(false);

  const { data, isLoading, error, reload } = useAsync(
    () => listSuites(project.id, { search: search || undefined, page, page_size: PAGE_SIZE_DEFAULT }),
    [project.id, search, page],
  );

  const openCreate = () => { form.resetFields(); setEditSuite(null); setModalOpen(true); };
  const openEdit = (suite: TestSuite) => { form.setFieldsValue({ name: suite.name, description: suite.description }); setEditSuite(suite); setModalOpen(true); };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editSuite) {
        await updateSuite(editSuite.id, values);
        notification.success({ message: 'Suite updated' });
      } else {
        await createSuite(project.id, values);
        notification.success({ message: 'Suite created' });
      }
      setModalOpen(false);
      reload();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (suite: TestSuite) => {
    try {
      await deleteSuite(suite.id);
      notification.success({ message: 'Suite deleted' });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    }
  };

  const columns: ColumnsType<TestSuite> = [
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      render: (name: string, record) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/suites/${record.id}`)} aria-label={`Open suite ${name}`}>
          {name}
        </Button>
      ),
    },
    {
      title: 'Description', dataIndex: 'description', key: 'description',
      render: (d: string | null) => d ?? <Typography.Text type="secondary">—</Typography.Text>,
    },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleDateString() },
    ...(canWrite ? [{
      title: '', key: 'actions',
      render: (_: unknown, record: TestSuite) => (
        <Space>
          <Button size="small" icon={<FolderOpenOutlined />} onClick={() => navigate(`/suites/${record.id}`)} aria-label={`View suite ${record.name}`}>View</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} aria-label={`Edit suite ${record.name}`} />
          <Popconfirm title="Delete this suite?" onConfirm={() => handleDelete(record)} okText="Delete" okButtonProps={{ danger: true }}>
            <Button size="small" icon={<DeleteOutlined />} danger aria-label={`Delete suite ${record.name}`} />
          </Popconfirm>
        </Space>
      ),
    }] : []),
  ];

  return (
    <div>
      <Space style={{ marginBottom: 12 }} wrap>
        <Input placeholder="Search suites…" prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ width: 220 }} allowClear aria-label="Search suites" />
        {canWrite && project.status === 'ACTIVE' && (
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} aria-label="Create suite">New Suite</Button>
        )}
      </Space>

      {error && <PageError message={error} onRetry={reload} />}

      <Table<TestSuite>
        rowKey="id" columns={columns} dataSource={data?.items ?? []} loading={isLoading}
        locale={{ emptyText: <Empty description="No test suites found" /> }}
        pagination={{ current: page, pageSize: PAGE_SIZE_DEFAULT, total: data?.total ?? 0, onChange: setPage }}
        aria-label="Test suites table"
      />

      <Modal
        title={editSuite ? 'Edit Suite' : 'New Suite'} open={modalOpen}
        onCancel={() => setModalOpen(false)} onOk={handleSave}
        confirmLoading={saving} okText={editSuite ? 'Save' : 'Create'} destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item label="Name" name="name" rules={[{ required: true, message: 'Name is required' }]}>
            <Input aria-label="Suite name" />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} aria-label="Suite description" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

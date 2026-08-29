import { useState } from 'react';
import {
  Typography, Table, Input, Select, Space, Button, Tag, Empty, Row, Col,
  Form, Modal, notification, Popconfirm,
} from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../hooks/useAsync';
import { listUsers, createUser, updateUser, deactivateUser } from '../../api/users';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { extractErrorMessage } from '../../api/client';
import { PAGE_SIZE_DEFAULT } from '../../constants';
import type { User, UserRole, UserStatus } from '../../types';

const { Title } = Typography;
const { Option } = Select;

const ROLE_COLORS: Record<UserRole, string> = { ADMIN: 'red', QA_ENGINEER: 'blue', VIEWER: 'default' };

export function UsersPage() {
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | ''>('');
  const [statusFilter, setStatusFilter] = useState<UserStatus | ''>('');
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<User | null>(null);
  const [saving, setSaving] = useState(false);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const { data, isLoading, error, reload } = useAsync(
    () => listUsers({ search: search || undefined, role: roleFilter || undefined, status: statusFilter || undefined, page, page_size: PAGE_SIZE_DEFAULT }),
    [search, roleFilter, statusFilter, page],
  );

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      setSaving(true);
      await createUser(values);
      notification.success({ message: 'User created' });
      setCreateOpen(false);
      createForm.resetFields();
      reload();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = async () => {
    if (!editTarget) return;
    try {
      const values = await editForm.validateFields();
      setSaving(true);
      await updateUser(editTarget.id, values);
      notification.success({ message: 'User updated' });
      setEditTarget(null);
      reload();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (user: User) => {
    try {
      await deactivateUser(user.id);
      notification.success({ message: `${user.name} deactivated` });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    }
  };

  const columns: ColumnsType<User> = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Role', dataIndex: 'role', key: 'role', render: (r: UserRole) => <Tag color={ROLE_COLORS[r]}>{r}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: UserStatus) => <StatusTag value={s} /> },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleDateString() },
    {
      title: '', key: 'actions',
      render: (_: unknown, record: User) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => { editForm.setFieldsValue({ name: record.name, email: record.email, role: record.role }); setEditTarget(record); }} aria-label={`Edit ${record.name}`} />
          {record.status === 'ACTIVE' && (
            <Popconfirm title={`Deactivate ${record.name}?`} onConfirm={() => handleDeactivate(record)} okText="Deactivate" okButtonProps={{ danger: true }}>
              <Button size="small" danger aria-label={`Deactivate ${record.name}`}>Deactivate</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={2} style={{ margin: 0 }}>Users</Title></Col>
        <Col>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} aria-label="Create user">New User</Button>
        </Col>
      </Row>

      <Space style={{ marginBottom: 16 }} wrap>
        <Input placeholder="Search users…" prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ width: 240 }} allowClear aria-label="Search users" />
        <Select value={roleFilter} onChange={(v) => { setRoleFilter(v); setPage(1); }} style={{ width: 160 }} aria-label="Filter by role">
          <Option value="">All roles</Option>
          <Option value="ADMIN">Admin</Option>
          <Option value="QA_ENGINEER">QA Engineer</Option>
          <Option value="VIEWER">Viewer</Option>
        </Select>
        <Select value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1); }} style={{ width: 160 }} aria-label="Filter by status">
          <Option value="">All statuses</Option>
          <Option value="ACTIVE">Active</Option>
          <Option value="INACTIVE">Inactive</Option>
        </Select>
      </Space>

      {error && <PageError message={error} onRetry={reload} />}

      <Table<User>
        rowKey="id" columns={columns} dataSource={data?.items ?? []} loading={isLoading}
        locale={{ emptyText: <Empty description="No users found" /> }}
        pagination={{ current: page, pageSize: PAGE_SIZE_DEFAULT, total: data?.total ?? 0, onChange: setPage, showTotal: (t) => `${t} user${t !== 1 ? 's' : ''}` }}
        aria-label="Users table"
      />

      <Modal title="New User" open={createOpen} onCancel={() => { setCreateOpen(false); createForm.resetFields(); }} onOk={handleCreate} confirmLoading={saving} okText="Create" destroyOnClose>
        <Form form={createForm} layout="vertical">
          <Form.Item label="Name" name="name" rules={[{ required: true }]}><Input aria-label="Name" /></Form.Item>
          <Form.Item label="Email" name="email" rules={[{ required: true }, { type: 'email' }]}><Input aria-label="Email" /></Form.Item>
          <Form.Item label="Password" name="password" rules={[{ required: true }, { min: 8, message: 'At least 8 characters' }]}>
            <Input.Password aria-label="Password" />
          </Form.Item>
          <Form.Item label="Role" name="role" rules={[{ required: true }]}>
            <Select aria-label="Role">
              <Option value="ADMIN">Admin</Option>
              <Option value="QA_ENGINEER">QA Engineer</Option>
              <Option value="VIEWER">Viewer</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="Edit User" open={Boolean(editTarget)} onCancel={() => setEditTarget(null)} onOk={handleEdit} confirmLoading={saving} okText="Save" destroyOnClose>
        <Form form={editForm} layout="vertical">
          <Form.Item label="Name" name="name" rules={[{ required: true }]}><Input aria-label="Name" /></Form.Item>
          <Form.Item label="Email" name="email" rules={[{ required: true }, { type: 'email' }]}><Input aria-label="Email" /></Form.Item>
          <Form.Item label="Role" name="role" rules={[{ required: true }]}>
            <Select aria-label="Role">
              <Option value="ADMIN">Admin</Option>
              <Option value="QA_ENGINEER">QA Engineer</Option>
              <Option value="VIEWER">Viewer</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

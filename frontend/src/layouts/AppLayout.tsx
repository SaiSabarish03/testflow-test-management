import { useState } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Typography, Space } from 'antd';
import {
  DashboardOutlined, ProjectOutlined, BugOutlined,
  UserOutlined, LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePermissions } from '../hooks/usePermissions';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { canManageUsers } = usePermissions();

  const menuItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/projects', icon: <ProjectOutlined />, label: 'Projects' },
    { key: '/defects', icon: <BugOutlined />, label: 'Defects' },
    ...(canManageUsers ? [{ key: '/users', icon: <UserOutlined />, label: 'Users' }] : []),
  ];

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: () => { logout(); navigate('/login'); },
    },
  ];

  const selectedKey = '/' + location.pathname.split('/')[1];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} trigger={null} width={220} style={{ background: '#001529' }}>
        <div style={{
          height: 64, display: 'flex', alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? 0 : '0 24px',
          color: '#fff', fontSize: collapsed ? 20 : 18, fontWeight: 700,
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          {collapsed ? 'TF' : 'TestFlow'}
        </div>
        <Menu
          theme="dark" mode="inline" selectedKeys={[selectedKey]}
          items={menuItems} onClick={({ key }) => navigate(key)}
          aria-label="Main navigation"
        />
      </Sider>

      <Layout>
        <Header style={{
          background: '#fff', padding: '0 24px', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0', position: 'sticky', top: 0, zIndex: 10,
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }} aria-label="User menu">
              <Avatar icon={<UserOutlined />} />
              <Text>{user?.name ?? user?.email}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>{user?.role}</Text>
            </Space>
          </Dropdown>
        </Header>

        <Content style={{ margin: 24, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

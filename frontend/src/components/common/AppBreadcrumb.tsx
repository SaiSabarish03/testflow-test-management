import { Breadcrumb } from 'antd';
import { Link } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface Props {
  items: BreadcrumbItem[];
}

export function AppBreadcrumb({ items }: Props) {
  return (
    <Breadcrumb
      style={{ marginBottom: 16 }}
      items={items.map((item) => ({
        title: item.path ? <Link to={item.path}>{item.label}</Link> : item.label,
      }))}
    />
  );
}

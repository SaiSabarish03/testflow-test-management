import { Spin } from 'antd';

export function PageLoader() {
  return (
    <div
      style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}
      aria-label="Loading"
      role="status"
    >
      <Spin size="large" />
    </div>
  );
}

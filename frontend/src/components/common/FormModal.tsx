import { Modal } from 'antd';
import type { FormInstance } from 'antd';

interface Props {
  title: string;
  open: boolean;
  onCancel: () => void;
  onOk: () => void;
  confirmLoading?: boolean;
  form?: FormInstance;
  children: React.ReactNode;
  okText?: string;
  width?: number;
}

export function FormModal({
  title, open, onCancel, onOk, confirmLoading, children, okText = 'Save', width = 560,
}: Props) {
  return (
    <Modal
      title={title}
      open={open}
      onCancel={onCancel}
      onOk={onOk}
      confirmLoading={confirmLoading}
      okText={okText}
      destroyOnClose
      width={width}
      aria-label={title}
    >
      {children}
    </Modal>
  );
}

import { Button, Input, Space, Typography } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';

export interface StepItem {
  action: string;
}

interface Props {
  value?: StepItem[];
  onChange?: (steps: StepItem[]) => void;
}

export function StepEditor({ value = [], onChange }: Props) {
  const steps = value;

  const update = (next: StepItem[]) => onChange?.(next);

  const addStep = () => update([...steps, { action: '' }]);

  const removeStep = (index: number) => update(steps.filter((_, i) => i !== index));

  const changeAction = (index: number, action: string) => {
    const next = steps.map((s, i) => (i === index ? { action } : s));
    update(next);
  };

  return (
    <div>
      {steps.map((step, index) => (
        <Space key={index} style={{ display: 'flex', marginBottom: 8 }} align="start">
          <Typography.Text style={{ minWidth: 60, paddingTop: 5 }} type="secondary">
            Step {index + 1}
          </Typography.Text>
          <Input
            value={step.action}
            onChange={(e) => changeAction(index, e.target.value)}
            placeholder="Describe the action…"
            aria-label={`Step ${index + 1} action`}
            style={{ width: 380 }}
          />
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => removeStep(index)}
            aria-label={`Remove step ${index + 1}`}
          />
        </Space>
      ))}
      <Button icon={<PlusOutlined />} onClick={addStep} aria-label="Add step" size="small">
        Add Step
      </Button>
    </div>
  );
}

/** Convert UI StepItem[] to backend format with order field. */
export function stepsToPayload(steps: StepItem[]): Array<{ order: number; action: string }> {
  return steps
    .filter((s) => s.action.trim() !== '')
    .map((s, i) => ({ order: i + 1, action: s.action.trim() }));
}

/** Convert backend steps to UI StepItem[]. */
export function payloadToSteps(steps: Array<{ order: number; action: string }> | null | undefined): StepItem[] {
  if (!steps) return [];
  return [...steps].sort((a, b) => a.order - b.order).map((s) => ({ action: s.action }));
}

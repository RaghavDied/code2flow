import React from 'react';
import { Handle, Position } from 'reactflow';

export default function FlowNode({ data }) {
  const { type, label, is_loop_header } = data;

  // Determine styles based on CFG node type
  let background = '#ffffff';
  let borderColor = '#cbd5e1';
  let borderRadius = '4px';
  let shapeStyle = {};

  if (type === 'start' || type === 'end') {
    background = '#e2e8f0';
    borderColor = '#64748b';
    borderRadius = '20px'; // Rounded pill shape for start/end
  } else if (type === 'decision') {
    background = '#fef08a';
    borderColor = '#ca8a04'; // Yellow diamond-like styling for decisions
  } else if (type === 'io') {
    background = '#bae6fd';
    borderColor = '#0284c7'; // Blue styling for I/O (printf/scanf)
  }

  if (is_loop_header) {
    borderColor = '#9333ea'; // Purple border highlight for loop headers
  }

  return (
    <div
      style={{
        padding: '10px 15px',
        borderRadius: borderRadius,
        background: background,
        border: `2px solid ${borderColor}`,
        fontSize: '12px',
        fontFamily: 'monospace',
        fontWeight: 'bold',
        textAlign: 'center',
        minWidth: '120px',
        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        ...shapeStyle,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: '#64748b' }} />
      <div>{label}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: '#64748b' }} />
    </div>
  );
}
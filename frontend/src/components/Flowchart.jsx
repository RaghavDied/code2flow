import React from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';

// Simple default nodes and edges for testing the flowchart view
const initialNodes = [
  { id: 'B0', position: { x: 250, y: 0 }, data: { label: 'START' }, type: 'input' },
  { id: 'B1', position: { x: 250, y: 100 }, data: { label: 'int x = 5;' } },
  { id: 'B2', position: { x: 250, y: 200 }, data: { label: 'END' }, type: 'output' },
];

const initialEdges = [
  { id: 'e0-1', source: 'B0', target: 'B1' },
  { id: 'e1-2', source: 'B1', target: 'B2' },
];

export default function Flowchart() {
  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        fitView
      >
        <Background variant="dots" gap={12} size={1} />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
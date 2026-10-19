import React from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import FlowNode from './FlowNode';

// Register custom node types
const nodeTypes = {
  flowNode: FlowNode,
};

// Test nodes using the custom 'flowNode' type
const initialNodes = [
  { 
    id: 'B0', 
    type: 'flowNode', 
    position: { x: 250, y: 0 }, 
    data: { type: 'start', label: 'START' } 
  },
  { 
    id: 'B1', 
    type: 'flowNode', 
    position: { x: 250, y: 100 }, 
    data: { type: 'process', label: 'int x = 5;' } 
  },
  { 
    id: 'B2', 
    type: 'flowNode', 
    position: { x: 250, y: 200 }, 
    data: { type: 'end', label: 'END' } 
  },
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
        nodeTypes={nodeTypes}
        fitView
      >
        <Background variant="dots" gap={12} size={1} />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
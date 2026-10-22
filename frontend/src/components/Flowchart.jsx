import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, MiniMap, useNodesState, useEdgesState } from 'reactflow';
import 'reactflow/dist/style.css';
import FlowNode from './FlowNode';
import { getLayoutedElements } from '../layout/autoLayout';

const nodeTypes = {
  flowNode: FlowNode,
};

export default function Flowchart({ cfgData, onNodeSelect, highlightLine }) {
  // Convert CFG JSON nodes & edges into React Flow format with Dagre auto-layout
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!cfgData || !cfgData.nodes || !cfgData.edges) {
      return { nodes: [], edges: [] };
    }

    const rfNodes = cfgData.nodes.map((node) => ({
      id: node.id,
      type: 'flowNode',
      data: {
        type: node.type,
        label: node.label,
        is_loop_header: node.is_loop_header,
        lines: node.lines,
        isHighlighted: node.lines && node.lines.includes(highlightLine),
      },
      position: { x: 0, y: 0 },
    }));

    const rfEdges = cfgData.edges.map((edge, idx) => ({
      id: `e-${idx}-${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      animated: edge.is_back_edge,
      style: { stroke: edge.label === 'TRUE' ? '#16a34a' : edge.label === 'FALSE' ? '#dc2626' : '#64748b' },
    }));

    return getLayoutedElements(rfNodes, rfEdges, 'TB');
  }, [cfgData, highlightLine]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Handle node selection for highlighting lines back to the source code
  const handleNodeClick = (_, node) => {
    if (onNodeSelect && node.data.lines && node.data.lines.length > 0) {
      onNodeSelect(node.data.lines[0]);
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
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
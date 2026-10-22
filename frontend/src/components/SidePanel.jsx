import React, { useState } from 'react';

export default function SidePanel({ tokens, ast, tac, log, metrics }) {
  const [activeTab, setActiveTab] = useState('tokens');

  const renderContent = () => {
    switch (activeTab) {
      case 'tokens':
        return (
          <pre style={{ margin: 0, fontSize: '12px' }}>
            {tokens ? JSON.stringify(tokens, null, 2) : 'No tokens available. Click Generate.'}
          </pre>
        );
      case 'ast':
        return (
          <pre style={{ margin: 0, fontSize: '12px' }}>
            {ast ? JSON.stringify(ast, null, 2) : 'No AST available. Click Generate.'}
          </pre>
        );
      case 'tac':
        return (
          <pre style={{ margin: 0, fontSize: '12px' }}>
            {tac ? JSON.stringify(tac, null, 2) : 'No TAC available. Click Generate.'}
          </pre>
        );
      case 'optlog':
        return (
          <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>
            {log && log.length > 0 ? (
              log.map((entry, idx) => (
                <div
                  key={`log-${idx}`}
                  style={{
                    padding: '0.4rem',
                    borderBottom: '1px solid #e2e8f0',
                    background: idx % 2 === 0 ? '#ffffff' : '#f8fafc',
                  }}
                >
                  <span style={{ fontWeight: 'bold', color: '#2563eb' }}>[{entry.pass_name}]</span> Line {entry.line} (Instr #{entry.instr_id}):{' '}
                  <span style={{ color: '#dc2626' }}>{entry.before}</span> ➔ <span style={{ color: '#16a34a' }}>{entry.after}</span>
                </div>
              ))
            ) : (
              'No optimisation log available. Run Optimiser.'
            )}
          </div>
        );
      case 'metrics':
        return (
          <pre style={{ margin: 0, fontSize: '12px' }}>
            {metrics ? JSON.stringify(metrics, null, 2) : 'No metrics available. Click Generate.'}
          </pre>
        );
      default:
        return null;
    }
  };

  const tabs = [
    { id: 'tokens', label: 'Tokens' },
    { id: 'ast', label: 'AST' },
    { id: 'tac', label: 'TAC' },
    { id: 'optlog', label: 'OptLog' },
    { id: 'metrics', label: 'Metrics' },
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#ffffff',
        borderLeft: '1px solid #cbd5e1',
      }}
    >
      <div style={{ display: 'flex', background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: 1,
              padding: '0.5rem 0.25rem',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid #2563eb' : 'none',
              background: activeTab === tab.id ? '#ffffff' : 'transparent',
              fontWeight: activeTab === tab.id ? 'bold' : 'normal',
              color: activeTab === tab.id ? '#2563eb' : '#64748b',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div style={{ flex: 1, padding: '0.75rem', overflowY: 'auto', background: '#fafafa' }}>{renderContent()}</div>
    </div>
  );
}
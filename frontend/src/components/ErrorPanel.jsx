import React from 'react';

export default function ErrorPanel({ errors = [], warnings = [] }) {
  if (!errors.length && !warnings.length) return null;

  return (
    <div
      style={{
        background: '#fef2f2',
        borderTop: '2px solid #ef4444',
        padding: '0.75rem 1rem',
        maxHeight: '150px',
        overflowY: 'auto',
        fontSize: '13px',
        fontFamily: 'monospace',
      }}
    >
      <div style={{ fontWeight: 'bold', color: '#991b1b', marginBottom: '0.5rem' }}>
        Diagnostics ({errors.length} error(s), {warnings.length} warning(s))
      </div>
      
      {errors.map((err, idx) => (
        <div key={`err-${idx}`} style={{ color: '#dc2626', marginBottom: '0.25rem' }}>
          ❌ <strong>[{err.phase.toUpperCase()}]</strong> Line {err.line}:{err.col} - {err.message}
        </div>
      ))}

      {warnings.map((warn, idx) => (
        <div key={`warn-${idx}`} style={{ color: '#d97706', marginBottom: '0.25rem' }}>
          ⚠️ <strong>[{warn.phase.toUpperCase()}]</strong> Line {warn.line}:{warn.col} - {warn.message}
        </div>
      ))}
    </div>
  );
}
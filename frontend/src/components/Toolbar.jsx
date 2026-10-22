import React from 'react';

export default function Toolbar({ onGenerate, onOptimize, isLoading }) {
  return (
    <div
      style={{
        padding: '0.5rem 1rem',
        background: '#f1f5f9',
        borderBottom: '1px solid #cbd5e1',
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'center',
      }}
    >
      <button
        onClick={onGenerate}
        disabled={isLoading}
        style={{
          background: '#2563eb',
          color: '#ffffff',
          border: 'none',
          padding: '0.4rem 0.8rem',
          borderRadius: '4px',
          fontWeight: 'bold',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          opacity: isLoading ? 0.7 : 1,
        }}
      >
        {isLoading ? 'Processing...' : '▶ Generate Flowchart'}
      </button>

      <button
        onClick={onOptimize}
        disabled={isLoading}
        style={{
          background: '#059669',
          color: '#ffffff',
          border: 'none',
          padding: '0.4rem 0.8rem',
          borderRadius: '4px',
          fontWeight: 'bold',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          opacity: isLoading ? 0.7 : 1,
        }}
      >
        ⚡ Run Optimiser
      </button>
    </div>
  );
}
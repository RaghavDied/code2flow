import React, { useState } from 'react'

export default function App() {
  const [activeTab, setActiveTab] = useState('original')

  return (
    <div style={{ fontFamily: 'sans-serif', height: '100vh', display: 'flex', flexDirection: 'column', margin: 0, padding: 0 }}>
      <header style={{ background: '#1e293b', color: '#fff', padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.25rem' }}>Code2Flow: Compiler-Based Code-to-Flowchart Generator</h1>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            style={{ background: activeTab === 'original' ? '#3b82f6' : '#475569', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={() => setActiveTab('original')}
          >
            Original
          </button>
          <button 
            style={{ background: activeTab === 'optimized' ? '#3b82f6' : '#475569', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={() => setActiveTab('optimized')}
          >
            Optimised
          </button>
          <button 
            style={{ background: activeTab === 'sidebyside' ? '#3b82f6' : '#475569', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={() => setActiveTab('sidebyside')}
          >
            Side-by-Side
          </button>
        </div>
      </header>
      <div style={{ flex: 1, display: 'flex', background: '#f8fafc' }}>
        <div style={{ width: '40%', borderRight: '1px solid #cbd5e1', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
          <h2>C Source Code Editor</h2>
          <div style={{ flex: 1, background: '#fff', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '0.5rem', fontFamily: 'monospace' }}>
            int main() &#123;<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;int x = 5;<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;return x;<br/>
            &#125;
          </div>
        </div>
        <div style={{ flex: 60, padding: '1rem', display: 'flex', flexDirection: 'column' }}>
          <h2>Flowchart Viewer ({activeTab})</h2>
          <div style={{ flex: 1, background: '#fff', border: '1px solid #cbd5e1', borderRadius: '4px', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#64748b' }}>
            React Flow Canvas Placeholder
          </div>
        </div>
      </div>
    </div>
  )
}
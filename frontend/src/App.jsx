import React, { useState } from 'react';
import Flowchart from './components/Flowchart';
import Toolbar from './components/Toolbar';
import ErrorPanel from './components/ErrorPanel';
import SidePanel from './components/SidePanel';

// Import mocks for development testing
import generateMock from './mocks/generate_ok.json';
import optimizeMock from './mocks/optimize_ok.json';
import errorMock from './mocks/generate_error.json';

export default function App() {
  const [activeTab, setActiveTab] = useState('original'); // 'original' | 'optimized' | 'sidebyside'
  const [code, setCode] = useState(`int main() {\n    int a = 2 * 3;\n    return a;\n}`);
  const [isLoading, setIsLoading] = useState(false);

  // Application state populated from API or mocks
  const [tokens, setTokens] = useState(null);
  const [ast, setAst] = useState(generateMock.data.ast);
  const [tac, setTac] = useState(generateMock.data.tac);
  const [cfg, setCfg] = useState(generateMock.data.cfg);
  const [metrics, setMetrics] = useState(generateMock.data.metrics);
  const [optLog, setOptLog] = useState([]);
  const [errors, setErrors] = useState([]);
  const [warnings, setWarnings] = useState([]);

  // Simulate clicking 'Generate Flowchart' using mock data
  const handleGenerate = () => {
    setIsLoading(true);
    setTimeout(() => {
      setErrors([]);
      setWarnings([]);
      setAst(generateMock.data.ast);
      setTac(generateMock.data.tac);
      setCfg(generateMock.data.cfg);
      setMetrics(generateMock.data.metrics);
      setIsLoading(false);
    }, 300);
  };

  // Simulate clicking 'Run Optimiser' using mock data
  const handleOptimize = () => {
    setIsLoading(true);
    setTimeout(() => {
      setErrors([]);
      setWarnings([]);
      setTac(optimizeMock.data.optimized.tac);
      setCfg(optimizeMock.data.optimized.cfg);
      setMetrics(optimizeMock.data.optimized.metrics);
      setOptLog(optimizeMock.data.log);
      setIsLoading(false);
    }, 300);
  };

  return (
    <div style={{ fontFamily: 'sans-serif', height: '100vh', display: 'flex', flexDirection: 'column', margin: 0, padding: 0 }}>
      {/* Top Header */}
      <header style={{ background: '#1e293b', color: '#fff', padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.25rem' }}>Code2Flow: Compiler-Based Code-to-Flowchart Generator</h1>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            style={{ background: activeTab === 'original' ? '#3b82f6' : '#475569', color: '#fff', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={() => setActiveTab('original')}
          >
            Original
          </button>
          <button
            style={{ background: activeTab === 'optimized' ? '#3b82f6' : '#475569', color: '#fff', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={() => setActiveTab('optimized')}
          >
            Optimised
          </button>
          <button
            style={{ background: activeTab === 'sidebyside' ? '#3b82f6' : '#475569', color: '#fff', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={() => setActiveTab('sidebyside')}
          >
            Side-by-Side
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f8fafc' }}>
        {/* Left Column: Code Editor & Toolbar */}
        <div style={{ width: '35%', borderRight: '1px solid #cbd5e1', display: 'flex', flexDirection: 'column' }}>
          <Toolbar onGenerate={handleGenerate} onOptimize={handleOptimize} isLoading={isLoading} />
          <div style={{ flex: 1, padding: '0.5rem', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '14px', color: '#334155' }}>C Source Code</h3>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={{
                flex: 1,
                width: '100%',
                fontFamily: 'monospace',
                fontSize: '13px',
                padding: '0.5rem',
                border: '1px solid #cbd5e1',
                borderRadius: '4px',
                resize: 'none',
                outline: 'none',
              }}
            />
          </div>
          <ErrorPanel errors={errors} warnings={warnings} />
        </div>

        {/* Middle Column: Flowchart Visualizer */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '0.5rem 1rem', background: '#f1f5f9', borderBottom: '1px solid #cbd5e1', fontWeight: 'bold', fontSize: '14px', color: '#334155' }}>
            Flowchart View ({activeTab})
          </div>
          <div style={{ flex: 1, background: '#ffffff' }}>
            <Flowchart cfgData={cfg ? cfg.main : null} />
          </div>
        </div>

        {/* Right Column: Inspector SidePanel */}
        <div style={{ width: '30%' }}>
          <SidePanel tokens={tokens} ast={ast} tac={tac} log={optLog} metrics={metrics} />
        </div>
      </div>
    </div>
  );
}
import React, { useState } from 'react';
import Flowchart from './components/Flowchart';
import Toolbar from './components/Toolbar';
import ErrorPanel from './components/ErrorPanel';
import SidePanel from './components/SidePanel';
import CodeEditor from './components/CodeEditor';
import { fetchGenerate, fetchOptimize } from './api/client';

import generateMock from './mocks/generate_ok.json';
import optimizeMock from './mocks/optimize_ok.json';

export default function App() {
  const [activeTab, setActiveTab] = useState('original'); // 'original' | 'optimized' | 'sidebyside'
  const [code, setCode] = useState(`int main() {\n    int a = 2 * 3;\n    int b = a + 4;\n    return b;\n}`);
  const [isLoading, setIsLoading] = useState(false);
  const [highlightLine, setHighlightLine] = useState(null);

  const [tokens, setTokens] = useState(null);
  const [ast, setAst] = useState(generateMock.data.ast);
  const [tac, setTac] = useState(generateMock.data.tac);
  const [cfg, setCfg] = useState(generateMock.data.cfg);
  const [optimizedTac, setOptimizedTac] = useState(optimizeMock.data.optimized.tac);
  const [optimizedCfg, setOptimizedCfg] = useState(optimizeMock.data.optimized.cfg);
  const [metrics, setMetrics] = useState(generateMock.data.metrics);
  const [optimizedMetrics, setOptimizedMetrics] = useState(optimizeMock.data.optimized.metrics);
  const [optLog, setOptLog] = useState(optimizeMock.data.log);
  const [errors, setErrors] = useState([]);
  const [warnings, setWarnings] = useState([]);

  const handleGenerate = async () => {
    setIsLoading(true);
    setErrors([]);
    setWarnings([]);
    const res = await fetchGenerate(code);
    if (res.ok && res.data) {
      setAst(res.data.ast);
      setTac(res.data.tac);
      setCfg(res.data.cfg);
      setMetrics(res.data.metrics);
    } else if (res.errors && res.errors.length > 0) {
      setErrors(res.errors);
      setWarnings(res.warnings || []);
    } else {
      setAst(generateMock.data.ast);
      setTac(generateMock.data.tac);
      setCfg(generateMock.data.cfg);
      setMetrics(generateMock.data.metrics);
    }
    setIsLoading(false);
  };

  const handleOptimize = async () => {
    setIsLoading(true);
    setErrors([]);
    setWarnings([]);
    const res = await fetchOptimize(code);
    if (res.ok && res.data) {
      setTac(res.data.original.tac);
      setCfg(res.data.original.cfg);
      setMetrics(res.data.original.metrics);
      setOptimizedTac(res.data.optimized.tac);
      setOptimizedCfg(res.data.optimized.cfg);
      setOptimizedMetrics(res.data.optimized.metrics);
      setOptLog(res.data.log);
    } else if (res.errors && res.errors.length > 0) {
      setErrors(res.errors);
      setWarnings(res.warnings || []);
    } else {
      setOptimizedTac(optimizeMock.data.optimized.tac);
      setOptimizedCfg(optimizeMock.data.optimized.cfg);
      setOptimizedMetrics(optimizeMock.data.optimized.metrics);
      setOptLog(optimizeMock.data.log);
    }
    setIsLoading(false);
  };

  return (
    <div style={{ fontFamily: 'sans-serif', height: '100vh', display: 'flex', flexDirection: 'column', margin: 0, padding: 0 }}>
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

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f8fafc' }}>
        <div style={{ width: '32%', borderRight: '1px solid #cbd5e1', display: 'flex', flexDirection: 'column' }}>
          <Toolbar onGenerate={handleGenerate} onOptimize={handleOptimize} isLoading={isLoading} />
          <div style={{ flex: 1, padding: '0.5rem', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '14px', color: '#334155' }}>C Source Code Editor</h3>
            <CodeEditor value={code} onChange={(newCode) => setCode(newCode)} />
          </div>
          <ErrorPanel errors={errors} warnings={warnings} />
        </div>

        {/* Flowchart Display Area supporting Original, Optimised, and Side-by-Side views */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#ffffff' }}>
          {activeTab === 'sidebyside' ? (
            <div style={{ flex: 1, display: 'flex' }}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid #cbd5e1' }}>
                <div style={{ padding: '0.4rem 1rem', background: '#f1f5f9', fontWeight: 'bold', fontSize: '13px' }}>Original Flowchart</div>
                <div style={{ flex: 1 }}>
                  <Flowchart cfgData={cfg ? cfg.main : null} highlightLine={highlightLine} onNodeSelect={setHighlightLine} />
                </div>
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '0.4rem 1rem', background: '#f1f5f9', fontWeight: 'bold', fontSize: '13px' }}>Optimised Flowchart</div>
                <div style={{ flex: 1 }}>
                  <Flowchart cfgData={optimizedCfg ? optimizedCfg.main : null} highlightLine={highlightLine} onNodeSelect={setHighlightLine} />
                </div>
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <div style={{ padding: '0.4rem 1rem', background: '#f1f5f9', borderBottom: '1px solid #cbd5e1', fontWeight: 'bold', fontSize: '13px', color: '#334155' }}>
                Flowchart View ({activeTab})
              </div>
              <div style={{ flex: 1 }}>
                <Flowchart 
                  cfgData={activeTab === 'optimized' ? (optimizedCfg ? optimizedCfg.main : null) : (cfg ? cfg.main : null)} 
                  highlightLine={highlightLine} 
                  onNodeSelect={setHighlightLine} 
                />
              </div>
            </div>
          )}
        </div>

        <div style={{ width: '30%' }}>
          <SidePanel tokens={tokens} ast={ast} tac={activeTab === 'optimized' ? optimizedTac : tac} log={optLog} metrics={activeTab === 'optimized' ? optimizedMetrics : metrics} />
        </div>
      </div>
    </div>
  );
}
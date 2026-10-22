import React, { useState, useRef, useEffect } from 'react';
import Flowchart from './components/Flowchart';
import Toolbar from './components/Toolbar';
import ErrorPanel from './components/ErrorPanel';
import SidePanel from './components/SidePanel';
import CodeEditor from './components/CodeEditor';
import { fetchTokens, fetchAst, fetchGenerate, fetchOptimize } from './api/client';

const DEFAULT_CODE = `int main() {\n    int a = 2 * 3;\n    int b = a + 4;\n    return b;\n}`;

const EMPTY_RESULT = {
  functions: [],
  tokens: null,
  ast: null,
  tac: null,
  cfg: null,
  metrics: null,
  optimizedTac: null,
  optimizedCfg: null,
  optimizedMetrics: null,
  optLog: [],
};

const tabStyle = (active) => ({
  background: active ? '#3b82f6' : '#475569',
  color: '#fff',
  border: 'none',
  padding: '0.4rem 0.8rem',
  borderRadius: '4px',
  cursor: 'pointer',
  fontWeight: '500',
  fontSize: '13px',
});

const fnTabStyle = (active) => ({
  background: active ? '#e0f2fe' : 'transparent',
  color: '#0f172a',
  border: 'none',
  borderBottom: active ? '2px solid #3b82f6' : '2px solid transparent',
  padding: '0.35rem 0.9rem',
  fontSize: '13px',
  cursor: 'pointer',
});

const panelHeader = {
  padding: '0.4rem 1rem',
  background: '#f1f5f9',
  fontWeight: 'bold',
  fontSize: '13px',
  color: '#334155',
};

/** Pick one function's graph out of a { fnName: graph } object. */
const forFn = (byFn, fn) => (byFn && fn && byFn[fn] ? byFn[fn] : null);

export default function App() {
  const [viewMode, setViewMode] = useState('original'); // 'original' | 'optimized' | 'sidebyside'
  const [code, setCode] = useState(DEFAULT_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [highlightLine, setHighlightLine] = useState(null);

  const [result, setResult] = useState(EMPTY_RESULT);
  const [activeFn, setActiveFn] = useState(null);
  const [errors, setErrors] = useState([]);
  const [warnings, setWarnings] = useState([]);

  // Panel sizing states (% of total width)
  const [leftWidth, setLeftWidth] = useState(28); // Editor % width
  const [rightWidth, setRightWidth] = useState(28); // Inspector % width
  const [isLeftCollapsed, setIsLeftCollapsed] = useState(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState(false);

  // Dragging states
  const [isDraggingLeft, setIsDraggingLeft] = useState(false);
  const [isDraggingRight, setIsDraggingRight] = useState(false);

  // Ignore responses from older requests if the user clicks again quickly.
  const requestId = useRef(0);

  // Mouse drag listeners for resizable dividers
  useEffect(() => {
    const handleMouseMove = (e) => {
      const totalWidth = window.innerWidth;
      if (isDraggingLeft) {
        const newPercent = Math.max(12, Math.min(50, (e.clientX / totalWidth) * 100));
        setLeftWidth(newPercent);
        setIsLeftCollapsed(false);
      } else if (isDraggingRight) {
        const newPercent = Math.max(12, Math.min(45, ((totalWidth - e.clientX) / totalWidth) * 100));
        setRightWidth(newPercent);
        setIsRightCollapsed(false);
      }
    };

    const handleMouseUp = () => {
      setIsDraggingLeft(false);
      setIsDraggingRight(false);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    };

    if (isDraggingLeft || isDraggingRight) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDraggingLeft, isDraggingRight]);

  const clearOutput = () => {
    setResult(EMPTY_RESULT);
    setActiveFn(null);
    setHighlightLine(null);
  };

  const showFailure = (res, fallbackMessage) => {
    clearOutput();
    if (res && res.errors && res.errors.length > 0) {
      setErrors(res.errors);
      setWarnings(res.warnings || []);
    } else {
      setErrors([{ phase: 'frontend', severity: 'error', message: fallbackMessage, line: 0, col: 0 }]);
    }
  };

  const handleGenerate = async () => {
    const myId = ++requestId.current;
    setIsLoading(true);
    setErrors([]);
    setWarnings([]);

    const [res, tokRes] = await Promise.all([fetchGenerate(code), fetchTokens(code)]);
    if (myId !== requestId.current) return;

    if (res && res.ok && res.data) {
      const fns = res.data.functions || Object.keys(res.data.cfg || {});
      setResult({
        ...EMPTY_RESULT,
        functions: fns,
        tokens: tokRes && tokRes.ok && tokRes.data ? tokRes.data.tokens : null,
        ast: res.data.ast,
        tac: res.data.tac,
        cfg: res.data.cfg,
        metrics: res.data.metrics,
      });
      setActiveFn(fns.includes('main') ? 'main' : fns[0] || null);
      setWarnings(res.warnings || []);
      if (viewMode !== 'original') setViewMode('original');
    } else {
      showFailure(res, 'Failed to communicate with backend API or compile error.');
    }
    setIsLoading(false);
  };

  const handleOptimize = async () => {
    const myId = ++requestId.current;
    setIsLoading(true);
    setErrors([]);
    setWarnings([]);

    const [res, tokRes, astRes] = await Promise.all([
      fetchOptimize(code),
      fetchTokens(code),
      fetchAst(code),
    ]);
    if (myId !== requestId.current) return;

    if (res && res.ok && res.data) {
      const fns = res.data.functions || Object.keys(res.data.original.cfg || {});
      setResult({
        functions: fns,
        tokens: tokRes && tokRes.ok && tokRes.data ? tokRes.data.tokens : null,
        ast: astRes && astRes.ok && astRes.data ? astRes.data.ast : null,
        tac: res.data.original.tac,
        cfg: res.data.original.cfg,
        metrics: res.data.original.metrics,
        optimizedTac: res.data.optimized.tac,
        optimizedCfg: res.data.optimized.cfg,
        optimizedMetrics: res.data.optimized.metrics,
        optLog: res.data.log || [],
      });
      setActiveFn(fns.includes('main') ? 'main' : fns[0] || null);
      setWarnings([...(res.warnings || []), ...(res.data.warnings_dead_code || [])]);
      setViewMode('sidebyside');
    } else {
      showFailure(res, 'Failed to optimize code via backend API.');
    }
    setIsLoading(false);
  };

  const originalGraph = forFn(result.cfg, activeFn);
  const optimizedGraph = forFn(result.optimizedCfg, activeFn);
  const showOptimized = viewMode === 'optimized';

  return (
    <div style={{ fontFamily: 'sans-serif', height: '100vh', display: 'flex', flexDirection: 'column', margin: 0, padding: 0 }}>
      {/* Top Header */}
      <header
        style={{
          background: '#1e293b',
          color: '#fff',
          padding: '0.65rem 1rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
        }}
      >
        <h1 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600, letterSpacing: '-0.01em' }}>
          Code2Flow: Compiler-Based Code-to-Flowchart Generator with Code Optimisation
        </h1>

        {/* View Mode Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button style={tabStyle(viewMode === 'original')} onClick={() => setViewMode('original')}>Original</button>
          <button style={tabStyle(viewMode === 'optimized')} onClick={() => setViewMode('optimized')}>Optimised</button>
          <button style={tabStyle(viewMode === 'sidebyside')} onClick={() => setViewMode('sidebyside')}>Side-by-Side</button>
        </div>
      </header>

      {/* Main Workspace */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f8fafc', position: 'relative' }}>
        {/* Left Column: Toolbar, Editor, Errors */}
        {!isLeftCollapsed && (
          <div
            style={{
              width: `${leftWidth}%`,
              display: 'flex',
              flexDirection: 'column',
              minWidth: '220px',
              maxWidth: '50%',
              background: '#f8fafc',
            }}
          >
            <Toolbar onGenerate={handleGenerate} onOptimize={handleOptimize} isLoading={isLoading} />
            <div style={{ flex: 1, padding: '0.5rem', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <h3 style={{ margin: 0, fontSize: '13px', color: '#334155' }}>C Source Code Editor</h3>
              </div>
              <CodeEditor value={code} onChange={setCode} />
            </div>
            <ErrorPanel errors={errors} warnings={warnings} />
          </div>
        )}

        {/* Left Resizer Splitter */}
        <div
          onMouseDown={() => setIsDraggingLeft(true)}
          style={{
            width: '6px',
            cursor: 'col-resize',
            background: isDraggingLeft ? '#3b82f6' : '#cbd5e1',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.15s',
            zIndex: 10,
            userSelect: 'none',
          }}
          title="Drag to resize Editor / Flowchart. Double click to collapse/expand."
          onDoubleClick={() => setIsLeftCollapsed(!isLeftCollapsed)}
        >
          <div style={{ width: '2px', height: '24px', background: isDraggingLeft ? '#ffffff' : '#64748b', borderRadius: '1px' }} />
        </div>

        {/* Middle Column: Function tabs + Flowcharts */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#ffffff', minWidth: '300px' }}>
          {result.functions.length > 0 && (
            <div style={{ display: 'flex', borderBottom: '1px solid #cbd5e1', background: '#f8fafc' }}>
              {result.functions.map((fn) => (
                <button key={fn} style={fnTabStyle(fn === activeFn)} onClick={() => setActiveFn(fn)}>
                  {fn}()
                </button>
              ))}
            </div>
          )}

          {viewMode === 'sidebyside' ? (
            <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid #cbd5e1' }}>
                <div style={panelHeader}>Original Flowchart</div>
                <div style={{ flex: 1 }}>
                  <Flowchart key={`orig-${activeFn}`} cfgData={originalGraph} highlightLine={highlightLine} onNodeSelect={setHighlightLine} />
                </div>
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <div style={panelHeader}>Optimised Flowchart</div>
                <div style={{ flex: 1 }}>
                  <Flowchart key={`opt-${activeFn}`} cfgData={optimizedGraph} highlightLine={highlightLine} onNodeSelect={setHighlightLine} />
                </div>
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <div style={{ ...panelHeader, borderBottom: '1px solid #cbd5e1' }}>
                Flowchart View ({viewMode === 'optimized' ? 'Optimised' : 'Original'})
              </div>
              <div style={{ flex: 1 }}>
                <Flowchart
                  key={`${viewMode}-${activeFn}`}
                  cfgData={showOptimized ? optimizedGraph : originalGraph}
                  highlightLine={highlightLine}
                  onNodeSelect={setHighlightLine}
                />
              </div>
            </div>
          )}
        </div>

        {/* Right Resizer Splitter */}
        <div
          onMouseDown={() => setIsDraggingRight(true)}
          style={{
            width: '6px',
            cursor: 'col-resize',
            background: isDraggingRight ? '#3b82f6' : '#cbd5e1',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.15s',
            zIndex: 10,
            userSelect: 'none',
          }}
          title="Drag to resize Flowchart / Inspector. Double click to collapse/expand."
          onDoubleClick={() => setIsRightCollapsed(!isRightCollapsed)}
        >
          <div style={{ width: '2px', height: '24px', background: isDraggingRight ? '#ffffff' : '#64748b', borderRadius: '1px' }} />
        </div>

        {/* Right Column: Inspector SidePanel */}
        {!isRightCollapsed ? (
          <div
            style={{
              width: `${rightWidth}%`,
              minWidth: '240px',
              maxWidth: '45%',
              display: 'flex',
              flexDirection: 'column',
              background: '#ffffff',
            }}
          >
            <SidePanel
              tokens={result.tokens}
              ast={result.ast}
              tac={showOptimized ? result.optimizedTac : result.tac}
              log={result.optLog}
              metrics={showOptimized ? result.optimizedMetrics : result.metrics}
            />
          </div>
        ) : (
          <div
            onClick={() => setIsRightCollapsed(false)}
            style={{
              writingMode: 'vertical-rl',
              textOrientation: 'mixed',
              background: '#f1f5f9',
              borderLeft: '1px solid #cbd5e1',
              color: '#64748b',
              padding: '1rem 0.35rem',
              cursor: 'pointer',
              fontSize: '11px',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              letterSpacing: '0.05em',
            }}
            title="Click to expand Inspector panel"
          >
            ◀ Open Inspector ({result.optLog.length > 0 ? `${result.optLog.length} Opts` : 'SidePanel'})
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState, useRef, useEffect } from 'react';
import AceEditor from 'react-ace';
import { 
  Play, 
  Copy, 
  Download, 
  Maximize2, 
  Minimize2,
  Code
} from 'lucide-react';
import './CodeEditor.css';

// Import Ace Editor modes and themes
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/mode-java';
import 'ace-builds/src-noconflict/mode-c_cpp';
import 'ace-builds/src-noconflict/mode-csharp';
import 'ace-builds/src-noconflict/mode-golang';
import 'ace-builds/src-noconflict/mode-rust';
import 'ace-builds/src-noconflict/mode-typescript';
import 'ace-builds/src-noconflict/mode-php';
import 'ace-builds/src-noconflict/mode-ruby';
import 'ace-builds/src-noconflict/mode-swift';
import 'ace-builds/src-noconflict/mode-kotlin';
import 'ace-builds/src-noconflict/mode-scala';

import 'ace-builds/src-noconflict/theme-monokai';
import 'ace-builds/src-noconflict/theme-github';
import 'ace-builds/src-noconflict/theme-tomorrow_night';

import 'ace-builds/src-noconflict/ext-language_tools';
// Ensure Ace resolves workers/snippets correctly under webpack/Cra
import 'ace-builds/webpack-resolver';

const CodeEditor = ({ isVisible, onClose, initialCode, onCodeChange }) => {
  const [code, setCode] = useState(initialCode || '// Welcome to the coding interview!\n// Choose your language and start coding...\n\nconsole.log("Hello, World!");');

  // Handle code changes and notify parent
  const handleCodeChange = (newCode) => {
    setCode(newCode);
    if (onCodeChange) {
      onCodeChange(newCode, language);
    }
  };
  const [language, setLanguage] = useState('javascript');
  const [theme, setTheme] = useState('monokai');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fontSize, setFontSize] = useState(14);

  // Update code when initialCode prop changes
  useEffect(() => {
    if (initialCode) {
      // Handle both old string format and new object format
      if (typeof initialCode === 'string') {
        setCode(initialCode);
      } else if (typeof initialCode === 'object' && initialCode[language]) {
        setCode(initialCode[language]);
      } else if (typeof initialCode === 'object' && initialCode.python) {
        // Default to Python if current language not available
        setCode(initialCode.python);
        setLanguage('python');
      }
    }
  }, [initialCode, language]);
  const editorRef = useRef(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runOutput, setRunOutput] = useState('');
  const [pyodide, setPyodide] = useState(null);
  const [isPyodideLoading, setIsPyodideLoading] = useState(false);

  // Popular programming languages for interviews (Ace Editor modes)
  const languages = [
    { value: 'javascript', mode: 'javascript', label: 'JavaScript', defaultCode: '// JavaScript\nconsole.log("Hello, World!");' },
    { value: 'python', mode: 'python', label: 'Python', defaultCode: '# Python\nprint("Hello, World!")' },
    { value: 'java', mode: 'java', label: 'Java', defaultCode: '// Java\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}' },
    { value: 'cpp', mode: 'c_cpp', label: 'C++', defaultCode: '// C++\n#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, World!" << endl;\n    return 0;\n}' },
    { value: 'c', mode: 'c_cpp', label: 'C', defaultCode: '// C\n#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}' },
    { value: 'csharp', mode: 'csharp', label: 'C#', defaultCode: '// C#\nusing System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine("Hello, World!");\n    }\n}' },
    { value: 'go', mode: 'golang', label: 'Go', defaultCode: '// Go\npackage main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}' },
    { value: 'rust', mode: 'rust', label: 'Rust', defaultCode: '// Rust\nfn main() {\n    println!("Hello, World!");\n}' },
    { value: 'typescript', mode: 'typescript', label: 'TypeScript', defaultCode: '// TypeScript\nconsole.log("Hello, World!");' },
    { value: 'php', mode: 'php', label: 'PHP', defaultCode: '<?php\n// PHP\necho "Hello, World!";\n?>' },
    { value: 'ruby', mode: 'ruby', label: 'Ruby', defaultCode: '# Ruby\nputs "Hello, World!"' },
    { value: 'swift', mode: 'swift', label: 'Swift', defaultCode: '// Swift\nprint("Hello, World!")' },
    { value: 'kotlin', mode: 'kotlin', label: 'Kotlin', defaultCode: '// Kotlin\nfun main() {\n    println("Hello, World!")\n}' },
    { value: 'scala', mode: 'scala', label: 'Scala', defaultCode: '// Scala\nobject Main extends App {\n    println("Hello, World!")\n}' }
  ];

  const themes = [
    { value: 'monokai', label: 'Dark' },
    { value: 'github', label: 'Light' },
    { value: 'tomorrow_night', label: 'High Contrast' }
  ];

  // Handle language change
  const handleLanguageChange = (newLanguage) => {
    const langConfig = languages.find(lang => lang.value === newLanguage);
    if (langConfig) {
      setLanguage(newLanguage);
      
      // Use template for the new language if available, otherwise use default
      if (typeof initialCode === 'object' && initialCode[newLanguage]) {
        handleCodeChange(initialCode[newLanguage]);
      } else {
        handleCodeChange(langConfig.defaultCode);
      }
    }
  };

  // Copy code to clipboard
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  // Download code as file
  const handleDownload = () => {
    const langConfig = languages.find(lang => lang.value === language);
    const extensions = {
      javascript: 'js',
      python: 'py',
      java: 'java',
      cpp: 'cpp',
      c: 'c',
      csharp: 'cs',
      go: 'go',
      rust: 'rs',
      typescript: 'ts',
      php: 'php',
      ruby: 'rb',
      swift: 'swift',
      kotlin: 'kt',
      scala: 'scala'
    };
    
    const extension = extensions[language] || 'txt';
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview-code.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Handle editor load
  const handleEditorLoad = (editor) => {
    editorRef.current = editor;
    
    // Add keyboard shortcuts
    editor.commands.addCommand({
      name: 'saveFile',
      bindKey: { win: 'Ctrl-S', mac: 'Cmd-S' },
      exec: () => {
        handleDownload();
      }
    });
  };

  // Toggle fullscreen
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Runtime helpers
  const runJavaScript = async () => {
    const logs = [];
    const originalLog = console.log;
    console.log = (...args) => {
      logs.push(args.map(a => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' '));
    };
    try {
      // eslint-disable-next-line no-new-func
      const fn = new Function(code);
      const result = fn();
      if (result !== undefined) logs.push(String(result));
      setRunOutput(logs.join('\n'));
    } catch (err) {
      setRunOutput(`Error: ${err.message}`);
    } finally {
      console.log = originalLog;
    }
  };

  const ensurePyodide = async () => {
    if (pyodide) return pyodide;
    if (isPyodideLoading) return null;
    setIsPyodideLoading(true);
    try {
      // Load pyodide from CDN
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js';
        script.onload = resolve;
        script.onerror = reject;
        document.body.appendChild(script);
      });
      // @ts-ignore
      const instance = await window.loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/' });
      setPyodide(instance);
      return instance;
    } catch (e) {
      setRunOutput(`Error initializing Python runtime: ${e.message}`);
      return null;
    } finally {
      setIsPyodideLoading(false);
    }
  };

  const runPython = async () => {
    const py = await ensurePyodide();
    if (!py) return;
    try {
      const wrapped = [
        'import sys, io',
        '_old = sys.stdout',
        'sys.stdout = io.StringIO()',
        code,
        '_out = sys.stdout.getvalue()',
        'sys.stdout = _old',
        '_out'
      ].join('\n');
      const result = await py.runPythonAsync(wrapped);
      setRunOutput(String(result));
    } catch (e) {
      setRunOutput(`Error: ${e.message}`);
    }
  };

  const handleRun = async () => {
    setIsRunning(true);
    setRunOutput('');
    try {
      if (language === 'javascript') {
        await runJavaScript();
      } else if (language === 'python') {
        await runPython();
      } else {
        // Use backend universal runner (Judge0)
        const resp = await fetch('http://localhost:8000/code/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ language, code })
        });
        const result = await resp.json();
        if (!resp.ok || result.success === false) {
          setRunOutput(`Error: ${result.detail || result.error || 'Execution failed'}`);
        } else {
          const combined = [
            result.compile_output && `Compile Output:\n${result.compile_output}`,
            result.stdout && `Output:\n${result.stdout}`,
            result.stderr && `Error:\n${result.stderr}`,
            `Status: ${result.status}`,
            (result.time || result.memory) && `Time: ${result.time || '-'}s  Memory: ${result.memory || '-'} KB`
          ].filter(Boolean).join('\n\n');
          setRunOutput(combined || '');
        }
      }
    } finally {
      setIsRunning(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`code-editor-container ${isFullscreen ? 'fullscreen' : ''}`}>
      {/* Header */}
      <div className="code-editor-header">
        <div className="header-left">
          <div className="editor-title">
            <Code size={20} />
            <span>Code Editor</span>
          </div>
        </div>
        
        <div className="header-controls">
          {/* Language Selector */}
          <select 
            value={language} 
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="language-select"
          >
            {languages.map(lang => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>

          {/* Theme Selector */}
          <select 
            value={theme} 
            onChange={(e) => setTheme(e.target.value)}
            className="theme-select"
          >
            {themes.map(t => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>

          {/* Font Size */}
          <div className="font-size-control">
            <label>Size:</label>
            <input
              type="range"
              min="10"
              max="24"
              value={fontSize}
              onChange={(e) => {
                const newSize = parseInt(e.target.value);
                setFontSize(newSize);
              }}
              className="font-size-slider"
            />
            <span>{fontSize}px</span>
          </div>

          {/* Action Buttons */}
          <button 
            className="action-btn" 
            onClick={handleRun} 
            disabled={isRunning || isPyodideLoading}
            title={isRunning ? 'Running...' : 'Run Code'}
          >
            <Play size={16} />
          </button>
          <button className="action-btn" onClick={handleCopy} title="Copy Code">
            <Copy size={16} />
          </button>
          
          <button className="action-btn" onClick={handleDownload} title="Download Code">
            <Download size={16} />
          </button>
          
          <button className="action-btn" onClick={toggleFullscreen} title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="editor-wrapper">
        <AceEditor
          mode={languages.find(l => l.value === language)?.mode || 'javascript'}
          theme={theme}
          value={code}
          onChange={handleCodeChange}
          onLoad={handleEditorLoad}
          name="code-editor"
          width="100%"
          height="100%"
          fontSize={fontSize}
          showPrintMargin={true}
          showGutter={true}
          highlightActiveLine={true}
          setOptions={{
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: true,
            enableSnippets: true,
            showLineNumbers: true,
            tabSize: 2,
            useWorker: false
          }}
        />
      </div>

      {/* Output */}
      <div className="code-run-output">
        {runOutput ? (
          <pre>{runOutput}</pre>
        ) : (
          <span className="muted">Output will appear here after you run the code.</span>
        )}
      </div>

      {/* Footer */}
      <div className="code-editor-footer">
        <div className="footer-left">
          <span className="language-indicator">{languages.find(l => l.value === language)?.label}</span>
          <span className="lines-indicator">Lines: {code.split('\n').length}</span>
          <span className="chars-indicator">Characters: {code.length}</span>
        </div>
        
        <div className="footer-right">
          <span className="help-text">
            Press Ctrl+S to download • Use Ctrl+/ for comments • Tab for autocomplete
          </span>
        </div>
      </div>
    </div>
  );
};

export default CodeEditor;

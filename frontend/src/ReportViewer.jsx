import React, { useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';

const ReportViewer = ({ code, language, report, qualityScore }) => {
    const editorRef = useRef(null);
    
    const handleEditorDidMount = (editor, monaco) => {
        editorRef.current = editor;
        
        if (report && report.length > 0) {
            const markers = report.map((item) => ({
                startLineNumber: item.line,
                startColumn: item.column,
                endLineNumber: item.line,
                endColumn: item.column + 5,
                message: `[${item.rule_code}] ${item.message}`,
                severity:
                    item.severity === 'Security' || item.severity === 'Warning'
                        ? monaco.MarkerSeverity.Error
                        : monaco.MarkerSeverity.Warning,
            }));

            monaco.editor.setModelMarkers(editor.getModel(), 'linter', markers);
        }
    };

    const getScoreBadgeColor = (score) => {
        if (score >= 85) return 'bg-green-950 text-green-200 border-green-800';
        if (score >= 70) return 'bg-yellow-950 text-yellow-200 border-yellow-800';
        return 'bg-red-950 text-red-200 border-red-800';
    };

    return (
        <div className="flex h-full flex-col bg-black p-6 font-sans text-gray-100">
            {/* Header Bar */}
            <div className="flex justify-between items-center bg-neutral-950 p-4 rounded-lg shadow-sm mb-4 border border-neutral-800">
                <div>
                    <h1 className="text-xl font-bold text-gray-100">Submission Quality Report</h1>
                    <p className="text-sm text-gray-400">Language: {language.toUpperCase()}</p>
                </div>
                <div className={`px-4 py-2 rounded-full border text-lg font-extrabold ${getScoreBadgeColor(qualityScore)}`}>
                    Quality Score: {qualityScore !== null ? `${qualityScore} / 100` : 'Evaluating...'}
                </div>
            </div>

            {/* Main Content Layout */}
            <div className="grid grid-cols-3 gap-4 flex-1 overflow-hidden">
                {/* Monaco Editor Code Display */}
                <div className="col-span-2 bg-neutral-950 border border-neutral-800 rounded-lg overflow-hidden shadow-sm">
                    <Editor
                        height="100%"
                        language={language.toLowerCase()}
                        value={code}
                        theme="vs-dark"
                        options={{ readOnly: true, minimap: { enabled: false }, scrollBeyondLastLine: false }}
                        onMount={handleEditorDidMount}
                    />
                </div>

                {/* Diagnostic Issues Sidebar */}
                <div className="col-span-1 bg-neutral-950 border border-neutral-800 rounded-lg p-4 shadow-sm overflow-y-auto">
                    <h2 className="text-md font-semibold text-gray-100 border-b border-neutral-800 pb-2 mb-3">
                        Detected Issues ({report ? report.length : 0})
                    </h2>
                    {report && report.length > 0 ? (
                        <div className="space-y-3">
                            {report.map((issue, idx) => (
                                <div key={idx} className="p-3 border border-neutral-800 rounded-md bg-neutral-900 hover:bg-neutral-800 transition">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-200">
                                            {issue.rule_code}
                                        </span>
                                        <span className="text-xs text-gray-400">
                                            Ln {issue.line}, Col {issue.column}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-200">{issue.message}</p>
                                    <span className={`inline-block mt-2 text-xs font-medium px-2 py-0.5 rounded ${
                                        issue.severity === 'Security' ? 'bg-red-950 text-red-200' : 'bg-amber-950 text-amber-200'
                                    }`}>
                                        {issue.severity}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-gray-400">No issues detected.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ReportViewer;
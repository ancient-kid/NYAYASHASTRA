import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { API_BASE_URL } from '@/services/api';

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  summary?: DocumentSummary;
  error?: string;
}

interface DocumentSummary {
  keyArguments: string[];
  verdict: string;
  citedSections: Array<{ act: string; section: string }>;
  parties?: string;
  courtName?: string;
  date?: string;
}

interface DocumentUploadProps {
  language: 'en' | 'hi';
  onDocumentProcessed?: (summary: DocumentSummary) => void;
}

export const DocumentUpload = ({ language, onDocumentProcessed }: DocumentUploadProps) => {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    processFiles(files);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      processFiles(files);
    }
  }, []);

  const processFiles = (files: File[]) => {
    files.forEach((file) => {
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        const doc: UploadedDocument = {
          id: Math.random().toString(36).substr(2, 9),
          name: file.name,
          size: file.size,
          status: 'uploading',
          progress: 0,
        };
        
        setDocuments((prev) => [...prev, doc]);

        // Use real API for upload and processing
        simulateProcessing(doc.id, file);
      }
    });
  };

  const simulateProcessing = async (docId: string, file: File) => {
    try {
      // Use real API for upload
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      const data = await response.json();
      const serverDocId = data.document_id;
      
      // Update to processing state
      setDocuments((prev) =>
        prev.map((d) =>
          d.id === docId ? { ...d, status: 'processing', progress: 100 } : d
        )
      );
      
      // Poll for status
      const pollStatus = async () => {
        try {
          const statusResponse = await fetch(`${API_BASE_URL}/api/documents/status/${serverDocId}`);
          if (!statusResponse.ok) {
            throw new Error('Status check failed');
          }
          
          const statusData = await statusResponse.json();
          
          if (statusData.status === 'completed' && statusData.summary) {
            const summary: DocumentSummary = {
              keyArguments: statusData.summary.key_arguments || [],
              verdict: statusData.summary.verdict || 'Processing completed',
              citedSections: (statusData.summary.cited_sections || []).map((s: any) => ({
                act: s.act || 'IPC',
                section: s.section || ''
              })),
              parties: statusData.summary.parties,
              courtName: statusData.summary.court_name,
              date: statusData.summary.date,
            };
            
            setDocuments((prev) =>
              prev.map((d) =>
                d.id === docId ? { ...d, status: 'completed', summary } : d
              )
            )
            
            onDocumentProcessed?.(summary);
          } else if (statusData.status === 'error') {
            throw new Error(statusData.error_message || 'Processing failed');
          } else {
            // Still processing, poll again
            setTimeout(() => pollStatus(), 2000);
          }
        } catch (pollError: any) {
          console.error('Polling error:', pollError);
          setDocuments((prev) =>
            prev.map((d) =>
              d.id === docId ? { ...d, status: 'error', error: pollError.message } : d
            )
          );
        }
      };
      
      pollStatus();
    } catch (error: any) {
      console.error('Document processing error:', error);
      setDocuments((prev) =>
        prev.map((d) =>
          d.id === docId ? { ...d, status: 'error', error: error.message } : d
        )
      );
    }
  };

  const removeDocument = (docId: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="glass-strong rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="border-b border-border p-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          {language === 'en' ? 'Document Summarization' : 'दस्तावेज़ सारांश'}
        </h3>
        <p className="text-xs text-muted-foreground mt-1">
          {language === 'en' 
            ? 'Upload court orders, judgments, or legal documents for AI analysis'
            : 'AI विश्लेषण के लिए अदालती आदेश, निर्णय या कानूनी दस्तावेज़ अपलोड करें'}
        </p>
      </div>

      {/* Upload Area */}
      <div className="p-4">
        <motion.div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          animate={{
            scale: isDragging ? 1.02 : 1,
            borderColor: isDragging ? 'hsl(var(--primary))' : 'hsl(var(--border))',
          }}
          className={`relative rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
            isDragging ? 'bg-primary/5' : 'bg-muted/20'
          }`}
        >
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <Upload className={`h-10 w-10 mx-auto mb-3 ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
          <p className="text-sm text-foreground font-medium">
            {language === 'en' ? 'Drop PDF files here or click to browse' : 'PDF फ़ाइलें यहाँ छोड़ें या ब्राउज़ करने के लिए क्लिक करें'}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {language === 'en' ? 'Supports court orders, judgments, FIRs, and legal notices' : 'अदालती आदेश, निर्णय, FIR और कानूनी नोटिस का समर्थन करता है'}
          </p>
        </motion.div>
      </div>

      {/* Document List */}
      <AnimatePresence>
        {documents.length > 0 && (
          <div className="border-t border-border p-4 space-y-3">
            {documents.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="rounded-xl border border-border bg-card/50 overflow-hidden"
              >
                {/* Document Header */}
                <div className="flex items-center gap-3 p-3">
                  <div className={`p-2 rounded-lg ${
                    doc.status === 'completed' ? 'bg-accent/20' : 
                    doc.status === 'error' ? 'bg-destructive/20' : 
                    'bg-primary/20'
                  }`}>
                    {doc.status === 'uploading' && <Loader2 className="h-4 w-4 text-primary animate-spin" />}
                    {doc.status === 'processing' && <Loader2 className="h-4 w-4 text-primary animate-spin" />}
                    {doc.status === 'completed' && <CheckCircle className="h-4 w-4 text-accent" />}
                    {doc.status === 'error' && <AlertCircle className="h-4 w-4 text-destructive" />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{doc.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(doc.size)} • 
                      {doc.status === 'uploading' && (language === 'en' ? ' Uploading...' : ' अपलोड हो रहा है...')}
                      {doc.status === 'processing' && (language === 'en' ? ' AI Processing...' : ' AI प्रसंस्करण...')}
                      {doc.status === 'completed' && (language === 'en' ? ' Analysis Complete' : ' विश्लेषण पूर्ण')}
                      {doc.status === 'error' && (
                        <span>
                          {language === 'en' ? ' Error' : ' त्रुटि'}
                          {doc.error && `: ${doc.error}`}
                        </span>
                      )}
                    </p>
                  </div>

                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={() => removeDocument(doc.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Progress Bar */}
                {(doc.status === 'uploading' || doc.status === 'processing') && (
                  <div className="px-3 pb-3">
                    <Progress value={doc.status === 'processing' ? 100 : doc.progress} className="h-1" />
                  </div>
                )}

                {/* Summary */}
                {doc.status === 'completed' && doc.summary && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    className="border-t border-border p-3 space-y-3"
                  >
                    {/* Court & Date */}
                    {(doc.summary.courtName || doc.summary.date) && (
                      <div className="flex flex-wrap gap-2">
                        {doc.summary.courtName && (
                          <span className="text-xs bg-secondary/20 text-secondary px-2 py-0.5 rounded-full">
                            {doc.summary.courtName}
                          </span>
                        )}
                        {doc.summary.date && (
                          <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">
                            {doc.summary.date}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Key Arguments */}
                    <div>
                      <p className="text-xs font-semibold text-foreground mb-1">
                        {language === 'en' ? 'Key Arguments' : 'मुख्य तर्क'}
                      </p>
                      <ul className="space-y-1">
                        {doc.summary.keyArguments.map((arg, idx) => (
                          <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                            <span className="text-primary">•</span>
                            {arg}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Verdict */}
                    <div className="rounded-lg bg-accent/10 p-2">
                      <p className="text-xs font-semibold text-accent mb-1">
                        {language === 'en' ? 'Verdict' : 'निर्णय'}
                      </p>
                      <p className="text-xs text-foreground">{doc.summary.verdict}</p>
                    </div>

                    {/* Cited Sections */}
                    <div>
                      <p className="text-xs font-semibold text-foreground mb-1">
                        {language === 'en' ? 'Cited Sections' : 'उद्धृत धाराएं'}
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {doc.summary.citedSections.map((section, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full"
                          >
                            {section.act} §{section.section}
                          </span>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

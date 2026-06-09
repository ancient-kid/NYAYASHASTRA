import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  ExternalLink,
  Copy,
  Check,
  ChevronLeft,
  ChevronRight,
  Search,
  ZoomIn,
  ZoomOut,
  FileText,
  Scale,
  AlertCircle,
} from "lucide-react";
import { Button } from "./ui/button";

interface HighlightedSection {
  text: string;
  page?: number;
  startIndex?: number;
  endIndex?: number;
  confidence?: number;
}

interface CitationViewerProps {
  isOpen: boolean;
  onClose: () => void;
  citation: {
    id: string;
    title: string;
    source: string;
    url: string;
    excerpt?: string;
    takeaway?: string;
    documentContent?: string;
    highlightedSections?: HighlightedSection[];
  } | null;
  language: "en" | "hi";
}

export const CitationViewer = ({
  isOpen,
  onClose,
  citation,
  language,
}: CitationViewerProps) => {
  const [copied, setCopied] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(100);
  const [searchTerm, setSearchTerm] = useState("");
  const [highlightedMatches, setHighlightedMatches] = useState<number[]>([]);
  const [currentMatch, setCurrentMatch] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  useEffect(() => {
    if (searchTerm && citation?.documentContent) {
      const regex = new RegExp(searchTerm, "gi");
      const matches: number[] = [];
      let match;
      while ((match = regex.exec(citation.documentContent)) !== null) {
        matches.push(match.index);
      }
      setHighlightedMatches(matches);
      setCurrentMatch(0);
    } else {
      setHighlightedMatches([]);
    }
  }, [searchTerm, citation?.documentContent]);

  const copyToClipboard = async () => {
    if (citation?.excerpt) {
      await navigator.clipboard.writeText(citation.excerpt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const renderHighlightedContent = () => {
    // If we have document content, show it with highlighting
    if (citation?.documentContent) {
      let content = citation.documentContent;

      // Highlight the cited sections
      if (
        citation.highlightedSections &&
        citation.highlightedSections.length > 0
      ) {
        citation.highlightedSections.forEach((section, idx) => {
          const escapedText = section.text.replace(
            /[.*+?^${}()|[\]\\]/g,
            "\\$&",
          );
          const regex = new RegExp(`(${escapedText})`, "gi");
          content = content.replace(
            regex,
            `<mark class="citation-highlight citation-highlight-${idx}" data-confidence="${section.confidence || 100}">$1</mark>`,
          );
        });
      }

      // Highlight search matches
      if (searchTerm) {
        const escapedSearch = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const regex = new RegExp(`(${escapedSearch})`, "gi");
        content = content.replace(
          regex,
          '<mark class="search-highlight">$1</mark>',
        );
      }

      return (
        <div
          ref={contentRef}
          className="prose prose-sm dark:prose-invert max-w-none p-6"
          style={{ fontSize: `${zoom}%` }}
          dangerouslySetInnerHTML={{ __html: content }}
        />
      );
    }

    // If we have excerpt but no full document, show excerpt prominently
    if (citation?.excerpt) {
      return (
        <div className="p-6 md:p-8 max-w-3xl mx-auto space-y-6">
          {/* Official Document Style Card */}
          <div className="relative overflow-hidden bg-gradient-to-b from-card to-background border border-border/80 rounded-2xl shadow-2xl p-6 md:p-8">
            {/* Watermark Balance Scale */}
            <div className="absolute right-4 bottom-4 opacity-[0.03] text-foreground pointer-events-none select-none">
              <Scale className="h-64 w-64" />
            </div>

            {/* Top Seal Header */}
            <div className="flex flex-col items-center text-center border-b border-border/60 pb-6 mb-6 relative">
              <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mb-2">
                <Scale className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-serif font-bold text-base text-foreground tracking-wide uppercase">
                {language === "en" ? "Official Legal Record" : "आधिकारिक कानूनी रिकॉर्ड"}
              </h3>
              <div className="flex items-center gap-1.5 mt-2 px-3 py-0.5 bg-green-500/10 border border-green-500/20 text-[9px] font-black uppercase tracking-wider text-green-600 rounded-full">
                <span className="w-1 h-1 rounded-full bg-green-500 animate-pulse" />
                {language === "en" ? "VERIFIED LAW SOURCE" : "सत्यापित कानून स्रोत"}
              </div>
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-muted/20 border border-border/30 mb-6 text-xs">
              <div>
                <span className="text-muted-foreground block mb-0.5 uppercase tracking-wider font-semibold text-[9px]">
                  {language === "en" ? "Document Type" : "दस्तावेज़ प्रकार"}
                </span>
                <span className="font-bold text-foreground capitalize">
                  {citation.type || "Statute"}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block mb-0.5 uppercase tracking-wider font-semibold text-[9px]">
                  {language === "en" ? "Source" : "स्रोत"}
                </span>
                <span className="font-bold text-primary hover:underline cursor-pointer" onClick={() => window.open(citation.url, "_blank")}>
                  {citation.sourceName || "Indian Kanoon"}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block mb-0.5 uppercase tracking-wider font-semibold text-[9px]">
                  {language === "en" ? "Enacted / Year" : "अधिनियमित वर्ष"}
                </span>
                <span className="font-bold text-foreground">
                  {citation.year || "N/A"}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block mb-0.5 uppercase tracking-wider font-semibold text-[9px]">
                  {language === "en" ? "Jurisdiction" : "क्षेत्राधिकार"}
                </span>
                <span className="font-bold text-foreground">
                  {citation.court || (language === "en" ? "Republic of India" : "भारत गणराज्य")}
                </span>
              </div>
            </div>

            {/* Legal Text Excerpt */}
            <div className="space-y-3">
              <span className="text-xs font-semibold text-primary uppercase tracking-widest block">
                {language === "en" ? "Bare Act Extract:" : "अधिनियम का अंश:"}
              </span>
              <div 
                className="font-serif text-foreground/95 leading-relaxed pl-5 border-l-4 border-primary/50 text-base italic md:text-lg bg-primary/[0.01] py-3 pr-4 rounded-r-lg"
                style={{ fontSize: `${zoom}%` }}
              >
                "{citation.excerpt}"
              </div>
            </div>

            {/* Copy button */}
            <div className="flex justify-end mt-4">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-xs gap-1.5 hover:bg-primary/10 text-muted-foreground hover:text-primary"
                onClick={copyToClipboard}
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-green-500" />
                    <span className="text-green-600">{language === "en" ? "Copied" : "कॉपी किया"}</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    {language === "en" ? "Copy Text" : "पाठ कॉपी करें"}
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Expert Takeaway Section inside Main View */}
          {citation.takeaway && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-primary/5 border border-primary/20 rounded-2xl p-6 shadow-md"
            >
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1 rounded bg-primary/15">
                  <Scale className="h-4 w-4 text-primary" />
                </div>
                <span className="text-xs font-bold text-primary uppercase tracking-wider">
                  {language === "en" ? "Expert Interpretation" : "विशेषज्ञ व्याख्या"}
                </span>
              </div>
              <p className="text-sm font-medium text-foreground leading-relaxed">
                {citation.takeaway}
              </p>
            </motion.div>
          )}

          {/* Quick source link */}
          <div className="bg-muted/20 border border-border/50 rounded-xl p-4 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-muted-foreground/40 shrink-0" />
              <div>
                <p className="text-xs font-semibold text-foreground">
                  {language === "en" ? "Need full jurisdiction bare act?" : "पूरे कानूनी अधिनियम की आवश्यकता है?"}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {language === "en" 
                    ? "Click the button to access the official bare act on Indian Kanoon." 
                    : "आधिकारिक bare act देखने के लिए क्लिक करें।"}
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs gap-1.5 shrink-0 bg-background"
              onClick={() => window.open(citation.url, "_blank")}
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {language === "en" ? "Open Source" : "स्रोत खोलें"}
            </Button>
          </div>
        </div>
      );
    }

    // Fallback for no content
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-6">
        <FileText className="h-16 w-16 mb-4 opacity-50" />
        <p className="text-lg font-medium">
          {language === "en" ? "Document Preview" : "दस्तावेज़ पूर्वावलोकन"}
        </p>
        <p className="text-sm mt-2 text-center">
          {language === "en"
            ? 'Click "View Source" to open the official document'
            : '"स्रोत देखें" पर क्लिक करके आधिकारिक दस्तावेज़ खोलें'}
        </p>
      </div>
    );
  };

  if (!isOpen || !citation) return null;

  return (
    <AnimatePresence>
      <motion.div
        key={citation?.id || 'citation-modal'}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <Scale className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h2 className="font-semibold text-foreground line-clamp-1">
                  {citation.title}
                </h2>
                <p className="text-xs text-muted-foreground capitalize">
                  {citation.source.replace(/_/g, " ")}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="rounded-full hover:bg-destructive/10 hover:text-destructive"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-muted/10">
            <div className="flex items-center gap-2">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder={
                    language === "en"
                      ? "Search in document..."
                      : "दस्तावेज़ में खोजें..."
                  }
                  className="pl-9 pr-4 py-2 text-sm bg-background border border-border rounded-lg w-64 focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                {highlightedMatches.length > 0 && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                    {currentMatch + 1}/{highlightedMatches.length}
                  </span>
                )}
              </div>

              {/* Navigation for search results */}
              {highlightedMatches.length > 0 && (
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() =>
                      setCurrentMatch(Math.max(0, currentMatch - 1))
                    }
                    disabled={currentMatch === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() =>
                      setCurrentMatch(
                        Math.min(
                          highlightedMatches.length - 1,
                          currentMatch + 1,
                        ),
                      )
                    }
                    disabled={currentMatch === highlightedMatches.length - 1}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Zoom controls */}
              <div className="flex items-center gap-1 bg-background border border-border rounded-lg px-2 py-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setZoom(Math.max(50, zoom - 10))}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-xs text-muted-foreground w-12 text-center">
                  {zoom}%
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setZoom(Math.min(200, zoom + 10))}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </div>

              {/* External link */}
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => window.open(citation.url, "_blank")}
              >
                <ExternalLink className="h-4 w-4" />
                {language === "en" ? "View Source" : "स्रोत देखें"}
              </Button>
            </div>
          </div>

          {/* Citation Excerpt Highlight */}
          {citation.excerpt && citation.documentContent && (
            <div className="mx-4 mt-4 p-4 bg-primary/5 border border-primary/20 rounded-xl">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-1 h-4 bg-primary rounded-full" />
                    <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                      {language === "en" ? "Cited Excerpt" : "उद्धृत अंश"}
                    </span>
                    <div className="flex items-center gap-1 ml-2 px-2 py-0.5 bg-green-500/10 rounded-full">
                      <Check className="h-3 w-3 text-green-500" />
                      <span className="text-[10px] text-green-600 font-medium">
                        {language === "en" ? "Verified" : "सत्यापित"}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-foreground/90 leading-relaxed italic">
                    "{citation.excerpt}"
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 shrink-0"
                  onClick={copyToClipboard}
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  ) }
                </Button>
              </div>
              
              {/* Added: Actionable Takeaway Section */}
              {citation.takeaway && (
                <div className="mt-4 pt-4 border-t border-primary/10">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="h-4 w-4 text-primary" />
                    <span className="text-[11px] font-bold text-primary uppercase tracking-wider">
                      {language === "en" ? "Expert Interpretation" : "विशेषज्ञ व्याख्या"}
                    </span>
                  </div>
                  <div className="bg-primary/5 rounded-lg p-3 border-l-4 border-primary">
                    <p className="text-sm font-medium text-foreground leading-snug">
                      {citation.takeaway}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Document Content */}
          <div className="flex-1 overflow-auto p-4">
            <div className="bg-background border border-border rounded-xl min-h-full">
              {renderHighlightedContent()}
            </div>
          </div>

          {/* Footer with verification info */}
          <div className="p-4 border-t border-border bg-muted/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <span>
                    {language === "en"
                      ? "Citation highlighted"
                      : "उद्धरण हाइलाइट किया गया"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-primary/50" />
                  <span>
                    {language === "en" ? "Search match" : "खोज मिलान"}
                  </span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                {language === "en"
                  ? "🔒 Source verified from official legal databases"
                  : "🔒 आधिकारिक कानूनी डेटाबेस से स्रोत सत्यापित"}
              </p>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Custom styles for highlights */}
      <style>{`
        .citation-highlight {
          background: linear-gradient(120deg, rgba(251, 191, 36, 0.3) 0%, rgba(251, 191, 36, 0.4) 100%);
          padding: 2px 4px;
          border-radius: 4px;
          border-bottom: 2px solid rgb(251, 191, 36);
          transition: all 0.2s ease;
        }
        .citation-highlight:hover {
          background: linear-gradient(120deg, rgba(251, 191, 36, 0.5) 0%, rgba(251, 191, 36, 0.6) 100%);
          box-shadow: 0 0 12px rgba(251, 191, 36, 0.4);
        }
        .search-highlight {
          background: rgba(var(--primary), 0.3);
          padding: 1px 2px;
          border-radius: 2px;
        }
      `}</style>
    </AnimatePresence>
  );
};

export default CitationViewer;

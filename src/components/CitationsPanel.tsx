import { motion, AnimatePresence } from 'framer-motion';
import { ExternalLink, FileText, Scale, Building2, BookOpen } from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';

export interface Citation {
  id: string;
  title: string;
  titleHi?: string;
  source: 'gazette' | 'supreme_court' | 'high_court' | 'law_commission' | 'indiankanoon';
  sourceName?: string;
  url: string;
  excerpt?: string;
  takeaway?: string;
  year?: number;
  court?: string;
  type?: string;
  isLandmark?: boolean;
  verified?: boolean;
}

interface CitationsPanelProps {
  citations: Citation[];
  language: 'en' | 'hi';
  onSelectCitation?: (citation: Citation) => void;
}

const getSourceIcon = (source: Citation['source']) => {
  switch (source) {
    case 'gazette':
      return FileText;
    case 'supreme_court':
      return Scale;
    case 'high_court':
      return Building2;
    case 'law_commission':
      return BookOpen;
    case 'indiankanoon':
      return BookOpen;
    default:
      return FileText;
  }
};

const getSourceLabel = (source: Citation['source'], language: 'en' | 'hi') => {
  const labels: Record<string, { en: string; hi: string }> = {
    gazette: { en: 'Official Gazette', hi: 'सरकारी राजपत्र' },
    supreme_court: { en: 'Supreme Court', hi: 'सर्वोच्च न्यायालय' },
    high_court: { en: 'High Court', hi: 'उच्च न्यायालय' },
    law_commission: { en: 'Law Commission', hi: 'विधि आयोग' },
    indiankanoon: { en: 'Indian Kanoon', hi: 'इंडियन कानून' },
  };
  const labelObj = labels[source] || { en: String(source), hi: String(source) };
  return labelObj[language];
};

const getSourceColor = (source: Citation['source']) => {
  switch (source) {
    case 'gazette':
      return 'bg-primary/20 text-primary border-primary/30';
    case 'supreme_court':
      return 'bg-secondary/20 text-secondary border-secondary/30';
    case 'high_court':
      return 'bg-accent/20 text-accent border-accent/30';
    case 'law_commission':
      return 'bg-chart-4/20 text-chart-4 border-chart-4/30';
    case 'indiankanoon':
      return 'bg-chart-2/20 text-chart-2 border-chart-2/30';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

export const CitationsPanel = ({ citations = [], language, onSelectCitation }: CitationsPanelProps) => {
  return (
    <div className="glass-strong rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <ExternalLink className="h-4 w-4 text-primary" />
            {language === 'en' ? 'Verified Citations' : 'सत्यापित उद्धरण'}
          </h3>
          <Badge variant="outline" className="text-xs border-accent text-accent">
            {citations.length} {language === 'en' ? 'sources' : 'स्रोत'}
          </Badge>
        </div>
      </div>

      <ScrollArea className="h-[300px]">
        <div className="p-4 space-y-3">
          <AnimatePresence>
            {citations.map((citation, idx) => {
              const Icon = getSourceIcon(citation.source);
              return (
                <motion.a
                  key={citation.id}
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => {
                    if (onSelectCitation) {
                      e.preventDefault();
                      onSelectCitation(citation);
                    }
                  }}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="block rounded-xl border border-border bg-card/50 p-3 transition-all duration-300 hover:border-primary/50 hover:bg-card group cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    {/* Citation Number */}
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary shrink-0">
                      {idx + 1}
                    </div>

                    <div className="flex-1 min-w-0">
                      {/* Source Badge */}
                      <Badge variant="outline" className={`text-xs mb-2 ${getSourceColor(citation.source)}`}>
                        <Icon className="h-3 w-3 mr-1" />
                        {getSourceLabel(citation.source, language)}
                        {citation.year && <span className="ml-1">• {citation.year}</span>}
                      </Badge>

                      {/* Title */}
                      <h4 className="text-sm font-medium text-foreground group-hover:text-primary transition-colors line-clamp-2">
                        {language === 'hi' && citation.titleHi ? citation.titleHi : citation.title}
                      </h4>

                      {/* Excerpt */}
                      {citation.excerpt && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          "{citation.excerpt}"
                        </p>
                      )}

                      {/* Court info */}
                      {citation.court && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {citation.court}
                        </p>
                      )}
                    </div>

                    {/* External link icon */}
                    <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                  </div>
                </motion.a>
              );
            })}
          </AnimatePresence>
        </div>
      </ScrollArea>

      {/* Disclaimer */}
      <div className="border-t border-border p-3 bg-muted/20">
        <p className="text-xs text-muted-foreground text-center">
          {language === 'en' 
            ? '🔗 All citations link to official government or authorized legal databases'
            : '🔗 सभी उद्धरण आधिकारिक सरकारी या अधिकृत कानूनी डेटाबेस से जुड़े हैं'}
        </p>
      </div>
    </div>
  );
};

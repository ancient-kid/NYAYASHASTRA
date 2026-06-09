import { motion } from 'framer-motion';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { BookOpen } from 'lucide-react';
import type { Statute } from '../services/api';

interface RetrievedStatutesPanelProps {
  statutes: Statute[];
  language: 'en' | 'hi';
  onSelectStatute?: (statute: Statute) => void;
}

const getActColor = (act: string) => {
  switch (act) {
    case 'IPC':
      return 'bg-secondary/20 text-secondary border-secondary/30';
    case 'BNS':
      return 'bg-primary/20 text-primary border-primary/30';
    case 'CrPC':
    case 'BSA':
      return 'bg-accent/20 text-accent border-accent/30';
    case 'Constitution':
      return 'bg-chart-4/20 text-chart-4 border-chart-4/30';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

export const RetrievedStatutesPanel = ({ statutes = [], language, onSelectStatute }: RetrievedStatutesPanelProps) => {
  return (
    <div className="glass-strong rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-primary" />
            {language === 'en' ? 'Retrieved Statutes' : 'प्राप्त विधियाँ'}
          </h3>
          <Badge variant="outline" className="text-xs">
            {statutes.length} {language === 'en' ? 'found' : 'मिले'}
          </Badge>
        </div>
      </div>

      <ScrollArea className="h-[280px]">
        <div className="p-4 space-y-3">
          {statutes.map((statute, idx) => (
            <motion.div
              key={statute.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => onSelectStatute?.(statute)}
              className="rounded-xl border border-border bg-card/50 p-3 hover:border-primary/50 transition-all duration-300 group cursor-pointer"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  {/* Act Badge & Section */}
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className={`text-xs ${getActColor(statute.actCode)}`}>
                      {statute.actCode}
                    </Badge>
                    <span className="text-sm font-bold text-foreground">§{statute.sectionNumber}</span>
                  </div>

                  {/* Title */}
                  <h4 className="text-sm font-medium text-foreground mb-1 group-hover:text-primary transition-colors line-clamp-2">
                    {language === 'hi' && statute.titleHi ? statute.titleHi : statute.titleEn}
                  </h4>

                  {/* Content Preview */}
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {language === 'hi' && statute.contentHi ? statute.contentHi : statute.contentEn}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

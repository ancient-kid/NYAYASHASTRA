import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Gavel,
    Calendar,
    Building2,
    Star,
    ExternalLink,
    ChevronDown,
    ChevronUp,
    BookOpen,
    Scale,
    Quote
} from 'lucide-react';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Button } from './ui/button';

interface CaseLaw {
    id: string;
    caseNumber: string;
    caseName: string;
    caseNameHi?: string;
    court: string;
    courtName?: string;
    judgmentDate?: string;
    reportingYear?: number;
    summaryEn?: string;
    summaryHi?: string;
    isLandmark?: boolean;
    citationString?: string;
    sourceUrl?: string;
    keyHoldings?: string[];
    domain?: string;
    citedSections?: string[];
}

interface CaseLawsPanelProps {
    cases?: CaseLaw[];
    language: 'en' | 'hi';
}

const sampleCases: CaseLaw[] = [
    {
        id: '1',
        caseNumber: 'Criminal Appeal No. 567/1980',
        caseName: 'Bachan Singh v. State of Punjab',
        caseNameHi: 'बचन सिंह बनाम पंजाब राज्य',
        court: 'supreme_court',
        courtName: 'Supreme Court of India',
        judgmentDate: '1980-05-09',
        reportingYear: 1980,
        summaryEn: 'Landmark judgment establishing the "rarest of rare" doctrine for imposition of death penalty in India. The Constitution Bench held that death penalty is constitutional but should be imposed only in exceptional circumstances.',
        summaryHi: 'भारत में मृत्युदंड के लिए "दुर्लभतम में दुर्लभ" सिद्धांत स्थापित करने वाला ऐतिहासिक निर्णय।',
        isLandmark: true,
        citationString: '1980 AIR 898, 1980 SCR (2) 684',
        sourceUrl: 'https://indiankanoon.org/doc/1691677',
        keyHoldings: [
            'Death penalty is constitutional',
            'Rarest of rare doctrine established',
            'Aggravating and mitigating circumstances must be balanced'
        ],
        domain: 'criminal',
        citedSections: ['302', '354(3)']
    },
    {
        id: '2',
        caseNumber: 'Writ Petition (Criminal) No. 666-70/1992',
        caseName: 'Vishaka v. State of Rajasthan',
        caseNameHi: 'विशाखा बनाम राजस्थान राज्य',
        court: 'supreme_court',
        courtName: 'Supreme Court of India',
        judgmentDate: '1997-08-13',
        reportingYear: 1997,
        summaryEn: 'Landmark judgment on sexual harassment at workplace. The Supreme Court laid down guidelines to prevent sexual harassment, which remained in force until the 2013 Act.',
        summaryHi: 'कार्यस्थल पर यौन उत्पीड़न पर ऐतिहासिक निर्णय।',
        isLandmark: true,
        citationString: 'AIR 1997 SC 3011',
        sourceUrl: 'https://indiankanoon.org/doc/1031794',
        keyHoldings: [
            'Sexual harassment violates fundamental rights',
            'Employers must constitute complaints committee',
            'Guidelines for prevention mandatory'
        ],
        domain: 'criminal',
        citedSections: ['354', '509']
    },
    {
        id: '3',
        caseNumber: 'Writ Petition (Civil) No. 494/2012',
        caseName: 'K.S. Puttaswamy v. Union of India',
        caseNameHi: 'के.एस. पुट्टास्वामी बनाम भारत संघ',
        court: 'supreme_court',
        courtName: 'Supreme Court of India',
        judgmentDate: '2017-08-24',
        reportingYear: 2017,
        summaryEn: 'Nine-judge Constitution Bench unanimously held that the right to privacy is a fundamental right protected under Article 21.',
        summaryHi: 'निजता का अधिकार मौलिक अधिकार है।',
        isLandmark: true,
        citationString: '(2017) 10 SCC 1',
        sourceUrl: 'https://indiankanoon.org/doc/127517806',
        keyHoldings: [
            'Right to privacy is a fundamental right',
            'Protected under Article 21'
        ],
        domain: 'constitutional'
    }
];

const getCourtColor = (court: string) => {
    switch (court) {
        case 'supreme_court': return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
        case 'delhi_high_court': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
        case 'bombay_high_court': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
        default: return 'bg-muted text-muted-foreground';
    }
};

const getCourtLabel = (court: string) => {
    switch (court) {
        case 'supreme_court': return 'Supreme Court';
        case 'delhi_high_court': return 'Delhi HC';
        case 'bombay_high_court': return 'Bombay HC';
        default: return court;
    }
};

export const CaseLawsPanel = ({ cases = [], language }: CaseLawsPanelProps) => {
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [filter, setFilter] = useState<'all' | 'landmark'>('all');

    const filteredCases = filter === 'landmark'
        ? cases.filter(c => c.isLandmark)
        : cases;

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <Gavel className="h-4 w-4 text-primary" />
                    {language === 'en' ? 'Case Laws' : 'न्यायदृष्टांत'}
                </h3>
                <div className="flex gap-1">
                    <Button
                        variant={filter === 'all' ? 'secondary' : 'ghost'}
                        size="sm"
                        onClick={() => setFilter('all')}
                        className="text-xs h-7"
                    >
                        All
                    </Button>
                    <Button
                        variant={filter === 'landmark' ? 'secondary' : 'ghost'}
                        size="sm"
                        onClick={() => setFilter('landmark')}
                        className="text-xs h-7"
                    >
                        <Star className="h-3 w-3 mr-1" />
                        Landmark
                    </Button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-2">
                <div className="glass-subtle rounded-lg p-2 text-center">
                    <div className="text-lg font-bold text-primary">{cases.length}</div>
                    <div className="text-xs text-muted-foreground">Total</div>
                </div>
                <div className="glass-subtle rounded-lg p-2 text-center">
                    <div className="text-lg font-bold text-amber-400">
                        {cases.filter(c => c.isLandmark).length}
                    </div>
                    <div className="text-xs text-muted-foreground">Landmark</div>
                </div>
                <div className="glass-subtle rounded-lg p-2 text-center">
                    <div className="text-lg font-bold text-chart-2">
                        {cases.filter(c => c.court === 'supreme_court').length}
                    </div>
                    <div className="text-xs text-muted-foreground">SC</div>
                </div>
            </div>

            {/* Cases List */}
            <ScrollArea className="h-[350px]">
                <div className="space-y-3 pr-2">
                    {filteredCases.map((caseItem, idx) => {
                        const isExpanded = expandedId === caseItem.id;

                        return (
                            <motion.div
                                key={caseItem.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                className="glass rounded-xl overflow-hidden"
                            >
                                {/* Case Header */}
                                <button
                                    onClick={() => setExpandedId(isExpanded ? null : caseItem.id)}
                                    className="w-full p-3 text-left hover:bg-accent/5 transition-colors"
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            {/* Badges Row */}
                                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                                                {caseItem.isLandmark && (
                                                    <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30">
                                                        <Star className="h-3 w-3 mr-1 fill-current" />
                                                        Landmark
                                                    </Badge>
                                                )}
                                                <Badge variant="outline" className={getCourtColor(caseItem.court)}>
                                                    <Building2 className="h-3 w-3 mr-1" />
                                                    {getCourtLabel(caseItem.court)}
                                                </Badge>
                                                {caseItem.reportingYear && (
                                                    <Badge variant="outline" className="text-muted-foreground">
                                                        <Calendar className="h-3 w-3 mr-1" />
                                                        {caseItem.reportingYear}
                                                    </Badge>
                                                )}
                                            </div>

                                            {/* Case Name */}
                                            <h4 className="text-sm font-medium text-foreground line-clamp-2">
                                                {language === 'hi' && caseItem.caseNameHi
                                                    ? caseItem.caseNameHi
                                                    : caseItem.caseName}
                                            </h4>

                                            {/* Citation */}
                                            {caseItem.citationString && (
                                                <p className="text-xs text-muted-foreground mt-1 font-mono">
                                                    {caseItem.citationString}
                                                </p>
                                            )}
                                        </div>

                                        {isExpanded ? (
                                            <ChevronUp className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                        ) : (
                                            <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                        )}
                                    </div>
                                </button>

                                {/* Expanded Content */}
                                <AnimatePresence>
                                    {isExpanded && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            <div className="px-3 pb-3 space-y-3 border-t border-border/50">
                                                {/* Summary */}
                                                <div className="pt-3">
                                                    <div className="flex items-start gap-2">
                                                        <Quote className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                                            {language === 'hi' && caseItem.summaryHi
                                                                ? caseItem.summaryHi
                                                                : caseItem.summaryEn}
                                                        </p>
                                                    </div>
                                                </div>

                                                {/* Key Holdings */}
                                                {caseItem.keyHoldings && caseItem.keyHoldings.length > 0 && (
                                                    <div className="space-y-2">
                                                        <h5 className="text-xs font-semibold text-foreground flex items-center gap-1">
                                                            <BookOpen className="h-3 w-3" />
                                                            {language === 'en' ? 'Key Holdings' : 'मुख्य निर्णय'}
                                                        </h5>
                                                        <ul className="space-y-1">
                                                            {caseItem.keyHoldings.map((holding, hidx) => (
                                                                <li
                                                                    key={hidx}
                                                                    className="text-xs text-muted-foreground flex items-start gap-2"
                                                                >
                                                                    <span className="text-primary">•</span>
                                                                    {holding}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {/* Cited Sections */}
                                                {caseItem.citedSections && caseItem.citedSections.length > 0 && (
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <Scale className="h-3 w-3 text-muted-foreground" />
                                                        <span className="text-xs text-muted-foreground">Sections cited:</span>
                                                        {caseItem.citedSections.map((section, sidx) => (
                                                            <Badge
                                                                key={sidx}
                                                                variant="outline"
                                                                className="text-xs bg-primary/10"
                                                            >
                                                                §{section}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                )}

                                                {/* Source Link */}
                                                {caseItem.sourceUrl && (
                                                    <a
                                                        href={caseItem.sourceUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                                                    >
                                                        <ExternalLink className="h-3 w-3" />
                                                        {language === 'en' ? 'View Full Judgment' : 'पूर्ण निर्णय देखें'}
                                                    </a>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        );
                    })}
                </div>
            </ScrollArea>

            {/* Empty State */}
            {filteredCases.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                    <Gavel className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">
                        {language === 'en'
                            ? 'No case laws found'
                            : 'कोई मामला नहीं मिला'}
                    </p>
                </div>
            )}
        </div>
    );
};

export default CaseLawsPanel;

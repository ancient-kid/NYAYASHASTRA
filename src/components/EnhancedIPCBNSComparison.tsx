import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Scale,
    ChevronDown,
    ChevronUp,
    AlertTriangle,
    ArrowRight,
    TrendingUp,
    TrendingDown,
    Minus,
    FileText,
    Gavel,
    BookOpen,
    Filter,
    Table,
    LayoutGrid,
    Info
} from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';

interface Change {
    type: 'added' | 'removed' | 'modified';
    description: string;
}

interface PunishmentChange {
    old: string;
    new: string;
    increased: boolean;
}

interface ComparisonItem {
    id: string;
    ipcSection: string;
    ipcTitle: string;
    ipcContent: string;
    bnsSection: string;
    bnsTitle: string;
    bnsContent: string;
    changes: Change[];
    punishmentChange?: PunishmentChange;
}

interface EnhancedIPCBNSComparisonProps {
    comparisons?: ComparisonItem[];
    language: 'en' | 'hi';
}

export const EnhancedIPCBNSComparison = ({
    comparisons = [],
    language
}: EnhancedIPCBNSComparisonProps) => {
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
    const [filterType, setFilterType] = useState<'all' | 'modified' | 'unchanged'>('all');
    
    const displayComparisons = comparisons.filter(item => {
        if (filterType === 'all') return true;
        if (filterType === 'modified') return item.changes.length > 0 || item.punishmentChange?.increased;
        if (filterType === 'unchanged') return item.changes.length === 0;
        return true;
    });

    const getChangeTypeLabel = (item: ComparisonItem) => {
        if (item.changes.length === 0) return { label: 'No Change', color: 'bg-green-500/20 text-green-600 border-green-500/30' };
        if (item.punishmentChange?.increased) return { label: 'Punishment ↑', color: 'bg-red-500/20 text-red-600 border-red-500/30' };
        return { label: 'Modified', color: 'bg-amber-500/20 text-amber-600 border-amber-500/30' };
    };

    const modifiedCount = comparisons.filter(c => c.changes.length > 0).length;
    const unchangedCount = comparisons.filter(c => c.changes.length === 0).length;

    return (
        <div className="space-y-6">
            {/* Header with Stats */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <div className="p-3 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/20">
                        <Scale className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-foreground">
                            {language === 'en' ? 'IPC to BNS Transition Guide' : 'IPC से BNS संक्रमण गाइड'}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                            {language === 'en'
                                ? 'Complete mapping of Indian Penal Code (1860) to Bhartiya Nyaya Sanhita (2023)'
                                : 'भारतीय दंड संहिता (1860) से भारतीय न्याय संहिता (2023) की संपूर्ण मैपिंग'}
                        </p>
                    </div>
                </div>

                {/* Stats Pills */}
                <div className="flex flex-wrap gap-2">
                    <div className="px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-sm">
                        <span className="font-semibold text-primary">{comparisons.length}</span>
                        <span className="text-muted-foreground ml-1">Total</span>
                    </div>
                    <div className="px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-sm">
                        <span className="font-semibold text-amber-600">{modifiedCount}</span>
                        <span className="text-muted-foreground ml-1">Modified</span>
                    </div>
                    <div className="px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-sm">
                        <span className="font-semibold text-green-600">{unchangedCount}</span>
                        <span className="text-muted-foreground ml-1">Unchanged</span>
                    </div>
                </div>
            </div>

            {/* Controls Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-muted/30 border border-border/50">
                {/* Filter Buttons */}
                <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <div className="flex rounded-xl overflow-hidden border border-border/50">
                        <button
                            onClick={() => setFilterType('all')}
                            className={`px-3 py-1.5 text-sm transition-all ${filterType === 'all'
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-background hover:bg-muted'
                                }`}
                        >
                            All ({comparisons.length})
                        </button>
                        <button
                            onClick={() => setFilterType('modified')}
                            className={`px-3 py-1.5 text-sm transition-all border-x border-border/50 ${filterType === 'modified'
                                    ? 'bg-amber-500 text-white'
                                    : 'bg-background hover:bg-muted'
                                }`}
                        >
                            Modified ({modifiedCount})
                        </button>
                        <button
                            onClick={() => setFilterType('unchanged')}
                            className={`px-3 py-1.5 text-sm transition-all ${filterType === 'unchanged'
                                    ? 'bg-green-500 text-white'
                                    : 'bg-background hover:bg-muted'
                                }`}
                        >
                            Unchanged ({unchangedCount})
                        </button>
                    </div>
                </div>

                {/* View Toggle */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setViewMode('table')}
                        className={`p-2 rounded-lg transition-all ${viewMode === 'table'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-background hover:bg-muted border border-border/50'
                            }`}
                        title="Table View"
                    >
                        <Table className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => setViewMode('cards')}
                        className={`p-2 rounded-lg transition-all ${viewMode === 'cards'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-background hover:bg-muted border border-border/50'
                            }`}
                        title="Card View"
                    >
                        <LayoutGrid className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Table View */}
            {viewMode === 'table' ? (
                <div className="rounded-2xl border border-border/50 overflow-hidden bg-card">
                    {/* Table Header */}
                    <div className="grid grid-cols-12 gap-2 p-4 bg-muted/50 border-b border-border/50 font-semibold text-sm">
                        <div className="col-span-2 flex items-center gap-2">
                            <FileText className="h-4 w-4 text-chart-1" />
                            <span>{language === 'en' ? 'IPC Section' : 'IPC धारा'}</span>
                        </div>
                        <div className="col-span-3">
                            <span className="text-chart-1">{language === 'en' ? 'IPC Title & Description' : 'IPC शीर्षक और विवरण'}</span>
                        </div>
                        <div className="col-span-2 flex items-center gap-2">
                            <Gavel className="h-4 w-4 text-chart-2" />
                            <span>{language === 'en' ? 'BNS Section' : 'BNS धारा'}</span>
                        </div>
                        <div className="col-span-3">
                            <span className="text-chart-2">{language === 'en' ? 'BNS Title & Description' : 'BNS शीर्षक और विवरण'}</span>
                        </div>
                        <div className="col-span-2 text-center">
                            <span>{language === 'en' ? 'Change Status' : 'परिवर्तन स्थिति'}</span>
                        </div>
                    </div>

                    {/* Table Body */}
                    <ScrollArea className="h-[550px]">
                        <div className="divide-y divide-border/30">
                            {displayComparisons.map((item, index) => {
                                const isExpanded = expandedId === item.id;
                                const changeInfo = getChangeTypeLabel(item);

                                return (
                                    <motion.div
                                        key={item.id}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: index * 0.02 }}
                                        className="group"
                                    >
                                        {/* Main Row */}
                                        <button
                                            onClick={() => setExpandedId(isExpanded ? null : item.id)}
                                            className="w-full grid grid-cols-12 gap-2 p-4 text-left hover:bg-muted/30 transition-colors"
                                        >
                                            {/* IPC Section Number */}
                                            <div className="col-span-2 flex items-center gap-2">
                                                <Badge variant="outline" className="bg-chart-1/10 text-chart-1 border-chart-1/30 font-mono text-sm px-3 py-1">
                                                    §{item.ipcSection}
                                                </Badge>
                                            </div>

                                            {/* IPC Title & Content */}
                                            <div className="col-span-3">
                                                <p className="font-medium text-foreground text-sm line-clamp-1">
                                                    {item.ipcTitle || 'No title'}
                                                </p>
                                                <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                                                    {item.ipcContent || 'No description available'}
                                                </p>
                                            </div>

                                            {/* Arrow */}
                                            <div className="hidden lg:flex items-center justify-center">
                                                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                            </div>

                                            {/* BNS Section Number */}
                                            <div className="col-span-2 flex items-center gap-2">
                                                <Badge variant="outline" className="bg-chart-2/10 text-chart-2 border-chart-2/30 font-mono text-sm px-3 py-1">
                                                    §{item.bnsSection}
                                                </Badge>
                                            </div>

                                            {/* BNS Title & Content */}
                                            <div className="col-span-3">
                                                <p className="font-medium text-foreground text-sm line-clamp-1">
                                                    {item.bnsTitle || 'No title'}
                                                </p>
                                                <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                                                    {item.bnsContent || 'No description available'}
                                                </p>
                                            </div>

                                            {/* Change Status */}
                                            <div className="col-span-2 flex items-center justify-center gap-2">
                                                <Badge className={`${changeInfo.color} border text-xs`}>
                                                    {item.changes.length > 0 && (
                                                        <AlertTriangle className="h-3 w-3 mr-1" />
                                                    )}
                                                    {changeInfo.label}
                                                </Badge>
                                                {isExpanded ? (
                                                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                                                ) : (
                                                    <ChevronDown className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                                )}
                                            </div>
                                        </button>

                                        {/* Expanded Details */}
                                        <AnimatePresence>
                                            {isExpanded && (
                                                <motion.div
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: 'auto', opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    transition={{ duration: 0.2 }}
                                                    className="overflow-hidden"
                                                >
                                                    <div className="p-6 bg-gradient-to-b from-muted/20 to-transparent border-t border-border/30">
                                                        {/* Side-by-Side Full Comparison */}
                                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                                                            {/* IPC Card */}
                                                            <div className="p-5 rounded-2xl bg-chart-1/5 border border-chart-1/20">
                                                                <div className="flex items-center gap-3 mb-4">
                                                                    <div className="p-2 rounded-lg bg-chart-1/20">
                                                                        <BookOpen className="h-5 w-5 text-chart-1" />
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-xs text-muted-foreground uppercase tracking-wide">Indian Penal Code, 1860</p>
                                                                        <p className="font-semibold text-chart-1">Section {item.ipcSection}</p>
                                                                    </div>
                                                                </div>
                                                                <h4 className="font-medium text-foreground mb-2">{item.ipcTitle}</h4>
                                                                <p className="text-sm text-muted-foreground leading-relaxed">
                                                                    {item.ipcContent || 'Detailed description not available for this section.'}
                                                                </p>
                                                                {item.punishmentChange?.old && (
                                                                    <div className="mt-4 p-3 rounded-lg bg-chart-1/10 border border-chart-1/20">
                                                                        <p className="text-xs text-muted-foreground mb-1">Punishment</p>
                                                                        <p className="text-sm font-medium text-chart-1">{item.punishmentChange.old}</p>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            {/* BNS Card */}
                                                            <div className="p-5 rounded-2xl bg-chart-2/5 border border-chart-2/20">
                                                                <div className="flex items-center gap-3 mb-4">
                                                                    <div className="p-2 rounded-lg bg-chart-2/20">
                                                                        <Gavel className="h-5 w-5 text-chart-2" />
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-xs text-muted-foreground uppercase tracking-wide">Bhartiya Nyaya Sanhita, 2023</p>
                                                                        <p className="font-semibold text-chart-2">Section {item.bnsSection}</p>
                                                                    </div>
                                                                </div>
                                                                <h4 className="font-medium text-foreground mb-2">{item.bnsTitle}</h4>
                                                                <p className="text-sm text-muted-foreground leading-relaxed">
                                                                    {item.bnsContent || 'Detailed description not available for this section.'}
                                                                </p>
                                                                {item.punishmentChange?.new && (
                                                                    <div className="mt-4 p-3 rounded-lg bg-chart-2/10 border border-chart-2/20">
                                                                        <p className="text-xs text-muted-foreground mb-1">Punishment</p>
                                                                        <p className="text-sm font-medium text-chart-2">{item.punishmentChange.new}</p>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Changes Section */}
                                                        {item.changes.length > 0 && (
                                                            <div className="p-5 rounded-2xl bg-amber-500/5 border border-amber-500/20">
                                                                <div className="flex items-center gap-2 mb-4">
                                                                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                                                                    <h4 className="font-semibold text-foreground">
                                                                        {language === 'en' ? 'Key Changes in BNS' : 'BNS में मुख्य परिवर्तन'}
                                                                    </h4>
                                                                </div>
                                                                <div className="space-y-2">
                                                                    {item.changes.map((change, idx) => (
                                                                        <div
                                                                            key={idx}
                                                                            className="flex items-start gap-3 p-3 rounded-xl bg-background/50 border border-border/30"
                                                                        >
                                                                            <div className={`p-1 rounded-full ${change.type === 'added' ? 'bg-green-500/20 text-green-500' :
                                                                                    change.type === 'removed' ? 'bg-red-500/20 text-red-500' :
                                                                                        'bg-amber-500/20 text-amber-500'
                                                                                }`}>
                                                                                {change.type === 'added' && <span className="text-xs font-bold">+</span>}
                                                                                {change.type === 'removed' && <span className="text-xs font-bold">−</span>}
                                                                                {change.type === 'modified' && <span className="text-xs font-bold">~</span>}
                                                                            </div>
                                                                            <p className="text-sm text-foreground">{change.description}</p>
                                                                        </div>
                                                                    ))}
                                                                </div>

                                                                {/* Punishment Comparison */}
                                                                {item.punishmentChange && (
                                                                    <div className="mt-4 p-4 rounded-xl bg-background/50 border border-border/30">
                                                                        <div className="flex items-center gap-2 mb-3">
                                                                            <Scale className="h-4 w-4 text-primary" />
                                                                            <span className="font-semibold text-sm">Punishment Comparison</span>
                                                                            {item.punishmentChange.increased && (
                                                                                <Badge className="bg-red-500/20 text-red-500 border-red-500/30 text-xs">
                                                                                    <TrendingUp className="h-3 w-3 mr-1" />
                                                                                    Increased
                                                                                </Badge>
                                                                            )}
                                                                        </div>
                                                                        <div className="grid grid-cols-2 gap-4">
                                                                            <div>
                                                                                <p className="text-xs text-muted-foreground mb-1">IPC (Old)</p>
                                                                                <p className="text-sm font-medium text-chart-1">{item.punishmentChange.old || 'N/A'}</p>
                                                                            </div>
                                                                            <div>
                                                                                <p className="text-xs text-muted-foreground mb-1">BNS (New)</p>
                                                                                <p className="text-sm font-medium text-chart-2">{item.punishmentChange.new || 'N/A'}</p>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}

                                                        {/* No Changes Message */}
                                                        {item.changes.length === 0 && (
                                                            <div className="p-4 rounded-2xl bg-green-500/5 border border-green-500/20 flex items-center gap-3">
                                                                <div className="p-2 rounded-lg bg-green-500/20">
                                                                    <Info className="h-4 w-4 text-green-500" />
                                                                </div>
                                                                <p className="text-sm text-muted-foreground">
                                                                    {language === 'en'
                                                                        ? 'This section has been retained without significant changes in the BNS 2023.'
                                                                        : 'इस धारा को BNS 2023 में बिना महत्वपूर्ण परिवर्तन के बरकरार रखा गया है।'}
                                                                </p>
                                                            </div>
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
                </div>
            ) : (
                /* Card View */
                <ScrollArea className="h-[600px]">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {displayComparisons.map((item, index) => {
                            const changeInfo = getChangeTypeLabel(item);

                            return (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.02 }}
                                    className="p-5 rounded-2xl bg-card border border-border/50 hover:border-primary/30 hover:shadow-lg transition-all cursor-pointer"
                                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                                >
                                    {/* Header */}
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <Badge variant="outline" className="bg-chart-1/10 text-chart-1 border-chart-1/30 font-mono">
                                                IPC §{item.ipcSection}
                                            </Badge>
                                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                            <Badge variant="outline" className="bg-chart-2/10 text-chart-2 border-chart-2/30 font-mono">
                                                BNS §{item.bnsSection}
                                            </Badge>
                                        </div>
                                        <Badge className={`${changeInfo.color} border text-xs`}>
                                            {changeInfo.label}
                                        </Badge>
                                    </div>

                                    {/* Title */}
                                    <h4 className="font-semibold text-foreground mb-2">{item.ipcTitle}</h4>
                                    <p className="text-sm text-muted-foreground line-clamp-2">{item.ipcContent}</p>

                                    {/* Changes Preview */}
                                    {item.changes.length > 0 && (
                                        <div className="mt-4 pt-4 border-t border-border/30">
                                            <p className="text-xs text-amber-600 font-medium">
                                                {item.changes.length} change{item.changes.length > 1 ? 's' : ''} in BNS
                                            </p>
                                        </div>
                                    )}
                                </motion.div>
                            );
                        })}
                    </div>
                </ScrollArea>
            )}

            {/* Empty State */}
            {displayComparisons.length === 0 && (
                <div className="text-center py-16">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted/50 mb-4">
                        <Scale className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                        {language === 'en' ? 'No Comparisons Found' : 'कोई तुलना नहीं मिली'}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        {language === 'en'
                            ? 'Try adjusting your search or filter criteria'
                            : 'अपनी खोज या फ़िल्टर मानदंड समायोजित करने का प्रयास करें'}
                    </p>
                </div>
            )}
        </div>
    );
};

export default EnhancedIPCBNSComparison;

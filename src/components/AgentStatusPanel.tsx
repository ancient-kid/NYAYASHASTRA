import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  BookOpen, 
  Scale, 
  Shield, 
  Link2, 
  FileText, 
  MessageSquare,
  CheckCircle2,
  Loader2,
  Circle
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  nameHindi: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const agents: Agent[] = [
  { id: 'query', name: 'Query Understanding', nameHindi: 'प्रश्न समझ', icon: Brain, color: 'text-[hsl(195,100%,50%)]' },
  { id: 'statute', name: 'Statute Retrieval', nameHindi: 'विधि खोज', icon: BookOpen, color: 'text-[hsl(280,100%,65%)]' },
  { id: 'case', name: 'Case Law Intelligence', nameHindi: 'न्यायदृष्टांत', icon: Scale, color: 'text-[hsl(160,100%,45%)]' },
  { id: 'regulatory', name: 'Regulatory Filter', nameHindi: 'नियामक फ़िल्टर', icon: Shield, color: 'text-[hsl(45,100%,50%)]' },
  { id: 'citation', name: 'Citation Agent', nameHindi: 'उद्धरण एजेंट', icon: Link2, color: 'text-[hsl(330,100%,60%)]' },
  { id: 'summary', name: 'Summarization', nameHindi: 'सारांश', icon: FileText, color: 'text-[hsl(200,100%,60%)]' },
  { id: 'response', name: 'Response Synthesis', nameHindi: 'प्रतिक्रिया', icon: MessageSquare, color: 'text-[hsl(270,100%,70%)]' },
];

interface AgentStatusPanelProps {
  activeAgent: string | null;
  completedAgents: string[];
  processingAgents: string[];
  language: 'en' | 'hi';
}

export const AgentStatusPanel = ({ 
  activeAgent, 
  completedAgents, 
  processingAgents,
  language 
}: AgentStatusPanelProps) => {
  return (
    <div className="glass-strong rounded-2xl p-4">
      <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
        <Brain className="h-4 w-4 text-primary" />
        {language === 'en' ? 'AI Agent Pipeline' : 'AI एजेंट पाइपलाइन'}
      </h3>

      <div className="space-y-2">
        <AnimatePresence>
          {agents.map((agent, idx) => {
            const Icon = agent.icon;
            const isActive = activeAgent === agent.id;
            const isProcessing = processingAgents.includes(agent.id);
            const isCompleted = completedAgents.includes(agent.id);

            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-300 ${
                  isActive ? 'bg-primary/10 glow-primary' : ''
                } ${isProcessing ? 'bg-muted/50' : ''}`}
              >
                {/* Status indicator */}
                <div className="relative">
                  {isCompleted ? (
                    <CheckCircle2 className="h-4 w-4 text-accent" />
                  ) : isProcessing ? (
                    <Loader2 className="h-4 w-4 text-primary animate-spin" />
                  ) : (
                    <Circle className="h-4 w-4 text-muted-foreground/30" />
                  )}
                </div>

                {/* Icon */}
                <div className={`p-1.5 rounded-lg ${isActive || isProcessing ? 'bg-card' : 'bg-muted/30'}`}>
                  <Icon className={`h-4 w-4 ${isActive || isProcessing ? agent.color : 'text-muted-foreground'}`} />
                </div>

                {/* Label */}
                <span className={`text-xs font-medium ${
                  isActive || isProcessing ? 'text-foreground' : 'text-muted-foreground'
                } ${language === 'hi' ? 'text-hindi' : ''}`}>
                  {language === 'hi' ? agent.nameHindi : agent.name}
                </span>

                {/* Active pulse */}
                {isActive && (
                  <motion.div
                    className="ml-auto h-2 w-2 rounded-full bg-primary"
                    animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  />
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
};

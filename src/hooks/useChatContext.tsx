
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { ChatMessage, Statute, Citation, CaseLaw, IPCBNSMapping } from '../services/api';

interface ChatContextType {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  currentStatutes: Statute[];
  setCurrentStatutes: (statutes: Statute[]) => void;
  currentCitations: Citation[];
  setCurrentCitations: (citations: Citation[]) => void;
  currentCaseLaws: CaseLaw[];
  setCurrentCaseLaws: (caseLaws: CaseLaw[]) => void;
  currentMappings: IPCBNSMapping[];
  setCurrentMappings: (mappings: IPCBNSMapping[]) => void;
  clearChat: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentStatutes, setCurrentStatutes] = useState<Statute[]>([]);
  const [currentCitations, setCurrentCitations] = useState<Citation[]>([]);
  const [currentCaseLaws, setCurrentCaseLaws] = useState<CaseLaw[]>([]);
  const [currentMappings, setCurrentMappings] = useState<IPCBNSMapping[]>([]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setCurrentStatutes([]);
    setCurrentCitations([]);
    setCurrentCaseLaws([]);
    setCurrentMappings([]);
  }, []);

  return (
    <ChatContext.Provider value={{
      messages,
      setMessages,
      sessionId,
      setSessionId,
      currentStatutes,
      setCurrentStatutes,
      currentCitations,
      setCurrentCitations,
      currentCaseLaws,
      setCurrentCaseLaws,
      currentMappings,
      setCurrentMappings,
      clearChat
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChatState = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatState must be used within a ChatProvider');
  }
  return context;
};

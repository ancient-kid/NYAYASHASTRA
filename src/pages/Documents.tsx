import { useState } from 'react';
import { Header } from '@/components/Header';
import { DocumentUpload } from '@/components/DocumentUpload';
import { motion } from 'framer-motion';

export const Documents = () => {
    const [language, setLanguage] = useState<'en' | 'hi'>('en');

    const handleDocumentProcessed = (summary: any) => {
        console.log('Document processed:', summary);
    };

    return (
        <div className="min-h-screen flex flex-col bg-background">
            <Header
                language={language}
                onLanguageChange={setLanguage}
            />
            <main className="flex-1 container mx-auto px-4 py-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="max-w-4xl mx-auto"
                >
                    <div className="mb-8">
                        <h1 className="text-3xl font-serif font-bold text-foreground mb-2">
                            {language === 'en' ? 'Legal Document Analysis' : 'कानूनी दस्तावेज़ विश्लेषण'}
                        </h1>
                        <p className="text-muted-foreground italic">
                            {language === 'en' 
                                ? 'Upload court orders, judgments, or legal documents for AI-powered summary extraction' 
                                : 'AI-संचालित सारांश निष्कर्षण के लिए कोर्ट आदेश, निर्णय या कानूनी दस्तावेज़ अपलोड करें'}
                        </p>
                    </div>
                    
                    <DocumentUpload 
                        language={language} 
                        onDocumentProcessed={handleDocumentProcessed} 
                    />

                    {/* Info Cards */}
                    <div className="grid md:grid-cols-3 gap-4 mt-8">
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="glass rounded-xl p-4"
                        >
                            <h3 className="font-semibold text-foreground mb-2">
                                {language === 'en' ? '📄 Supported Documents' : '📄 समर्थित दस्तावेज़'}
                            </h3>
                            <ul className="text-sm text-muted-foreground space-y-1">
                                <li>• {language === 'en' ? 'Supreme Court Judgments' : 'सुप्रीम कोर्ट के निर्णय'}</li>
                                <li>• {language === 'en' ? 'High Court Orders' : 'हाई कोर्ट के आदेश'}</li>
                                <li>• {language === 'en' ? 'FIRs' : 'FIR'}</li>
                                <li>• {language === 'en' ? 'Legal Notices' : 'कानूनी नोटिस'}</li>
                                <li>• {language === 'en' ? 'Contracts' : 'अनुबंध'}</li>
                            </ul>
                        </motion.div>
                        
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="glass rounded-xl p-4"
                        >
                            <h3 className="font-semibold text-foreground mb-2">
                                {language === 'en' ? '🤖 AI Extracts' : '🤖 AI निकालता है'}
                            </h3>
                            <ul className="text-sm text-muted-foreground space-y-1">
                                <li>• {language === 'en' ? 'Key Arguments' : 'मुख्य तर्क'}</li>
                                <li>• {language === 'en' ? 'Final Verdict' : 'अंतिम निर्णय'}</li>
                                <li>• {language === 'en' ? 'Cited Sections' : 'उद्धृत धाराएं'}</li>
                                <li>• {language === 'en' ? 'Parties Involved' : 'शामिल पक्ष'}</li>
                                <li>• {language === 'en' ? 'Court & Date' : 'न्यायालय और तारीख'}</li>
                            </ul>
                        </motion.div>
                        
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="glass rounded-xl p-4"
                        >
                            <h3 className="font-semibold text-foreground mb-2">
                                {language === 'en' ? '⚡ How It Works' : '⚡ यह कैसे काम करता है'}
                            </h3>
                            <ol className="text-sm text-muted-foreground space-y-1">
                                <li>1. {language === 'en' ? 'Upload PDF file' : 'PDF फ़ाइल अपलोड करें'}</li>
                                <li>2. {language === 'en' ? 'AI extracts text' : 'AI टेक्स्ट निकालता है'}</li>
                                <li>3. {language === 'en' ? 'Document is analyzed' : 'दस्तावेज़ का विश्लेषण होता है'}</li>
                                <li>4. {language === 'en' ? 'Summary generated' : 'सारांश उत्पन्न होता है'}</li>
                            </ol>
                        </motion.div>
                    </div>
                </motion.div>
            </main>
        </div>
    );
};

export default Documents;

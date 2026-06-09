import { motion } from 'framer-motion';
import { useState } from 'react';
import { Globe, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

export const SignInPage = () => {
    const [language, setLanguage] = useState<'en' | 'hi'>('en');

    return (
        <div className="min-h-screen bg-[#faf7f2] dark:bg-[#0f1115] flex flex-col">
            {/* Header */}
            <motion.header
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="glass-strong border-b border-border"
            >
                <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                    {/* Back to Home */}
                    <Link to="/">
                        <Button variant="ghost" size="sm" className="gap-2">
                            <ArrowLeft className="h-4 w-4" />
                            {language === 'en' ? 'Back' : 'वापस'}
                        </Button>
                    </Link>

                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <img 
                            src="/national-emblem.png" 
                            alt="NYAYASHASTRA" 
                            className="h-10 w-10 object-contain"
                        />
                        <div className="hidden sm:block">
                            <h1 className="text-xl font-serif font-bold tracking-wide text-primary">NYAYASHASTRA</h1>
                            <p className="text-xs text-muted-foreground -mt-1 font-serif italic">
                                {language === 'en' ? "India's Legal Intelligence" : 'भारत की कानूनी बुद्धिमत्ता'}
                            </p>
                        </div>
                    </div>

                    {/* Language Toggle */}
                    <div className="flex items-center gap-1 glass rounded-full p-1">
                        <Button
                            variant={language === 'en' ? 'default' : 'ghost'}
                            size="sm"
                            className="h-7 px-3 rounded-full text-xs"
                            onClick={() => setLanguage('en')}
                        >
                            <Globe className="h-3 w-3 mr-1" />
                            EN
                        </Button>
                        <Button
                            variant={language === 'hi' ? 'default' : 'ghost'}
                            size="sm"
                            className="h-7 px-3 rounded-full text-xs text-hindi"
                            onClick={() => setLanguage('hi')}
                        >
                            हि
                        </Button>
                    </div>
                </div>
            </motion.header>

            {/* Main Content */}
            <div className="flex-1 flex items-center justify-center py-12 px-4">
                <div className="w-full max-w-lg">
                    {/* Welcome Text */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center mb-8"
                    >
                        <h2 className="text-3xl font-serif font-bold text-foreground mb-2">
                            {language === 'en' ? 'Welcome to NYAYASHASTRA' : 'NYAYASHASTRA में आपका स्वागत है'}
                        </h2>
                        <p className="text-muted-foreground">
                            {language === 'en' 
                                ? 'Sign up to jump straight into the dashboard' 
                                : 'डैशबोर्ड में सीधे जाने के लिए साइन अप करें'}
                        </p>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.1 }}
                        className="flex flex-col items-center gap-4"
                    >
                        <p className="text-center text-muted-foreground max-w-md">
                            {language === 'en'
                                ? 'Clerk authentication has been removed. Sign up to open the dashboard immediately.'
                                : 'क्लर्क प्रमाणीकरण हटा दिया गया है। डैशबोर्ड तुरंत खोलने के लिए साइन अप करें।'}
                        </p>
                        <Link to="/dashboard">
                            <Button className="rounded-full px-6">
                                {language === 'en' ? 'Sign Up' : 'साइन अप'}
                            </Button>
                        </Link>
                    </motion.div>

                    {/* Footer Note */}
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="text-center text-xs text-muted-foreground mt-8"
                    >
                        {language === 'en'
                            ? '⚖️ Demo mode is enabled for evaluation purposes'
                            : '⚖️ मूल्यांकन के लिए डेमो मोड सक्षम है'}
                    </motion.p>
                </div>
            </div>

            {/* Background Decoration */}
            <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] opacity-[0.02] pointer-events-none -z-10">
                <img 
                    src="/national-emblem.png" 
                    alt="" 
                    className="w-full h-full object-contain grayscale"
                />
            </div>
        </div>
    );
};

export default SignInPage;

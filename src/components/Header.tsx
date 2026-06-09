import { motion } from 'framer-motion';
import { Scale, Globe, Menu, MessageSquare, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { Link } from 'react-router-dom';


interface HeaderProps {
  language: 'en' | 'hi';
  onLanguageChange: (lang: 'en' | 'hi') => void;
  onMenuClick?: () => void;
  onLogoClick?: () => void;
}

export const Header = ({ language, onLanguageChange, onMenuClick, onLogoClick }: HeaderProps) => {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="glass-strong border-b border-border/50 sticky top-0 z-50"
    >
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo & Menu */}
        <div className="flex items-center gap-3">
          <Button 
            variant="ghost" 
            size="icon" 
            className="lg:hidden hover:bg-primary/10"
            onClick={onMenuClick}
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="flex items-center gap-2"
          >
            <Link 
              to="/" 
              className="flex items-center gap-2 group"
              onClick={() => onLogoClick?.()}
            >
              <div className="relative">
                <img 
                  src="/national-emblem.png" 
                  alt="NYAYASHASTRA Logo" 
                  className="h-10 w-10 object-contain transition-transform group-hover:scale-105"
                />
              </div>
              <div className="hidden sm:block text-left">
                <h1 className="text-xl font-serif font-bold tracking-wide">
                  <span className="text-foreground">NYAYA</span>
                  <span className="text-primary">SHASTRA</span>
                </h1>
                <p className="text-xs text-muted-foreground -mt-0.5 font-sans">
                  {language === 'en' ? "India's Legal Intelligence" : 'भारत की कानूनी बुद्धिमत्ता'}
                </p>
              </div>
            </Link>
          </motion.div>
        </div>

        {/* Center - Navigation */}
        <nav className="hidden lg:flex items-center gap-1">
          <Link to="/comparison">
            <Button variant="ghost" size="sm" className="gap-2 rounded-full hover:bg-primary/10">
              <Scale className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">
                {language === 'en' ? 'IPC vs BNS' : 'IPC बनाम BNS'}
              </span>
            </Button>
          </Link>
          <Link to="/documents">
            <Button variant="ghost" size="sm" className="gap-2 rounded-full hover:bg-primary/10">
              <FileText className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">
                {language === 'en' ? 'Documents' : 'दस्तावेज़'}
              </span>
            </Button>
          </Link>
          <Link to="/">
            <Button variant="ghost" size="sm" className="gap-2 rounded-full hover:bg-primary/10">
              <MessageSquare className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">
                {language === 'en' ? 'Legal Chat' : 'कानूनी चैट'}
              </span>
            </Button>
          </Link>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {/* Language Toggle */}
          <div className="flex items-center gap-1 bg-muted/50 rounded-full p-1">
            <Button
              variant={language === 'en' ? 'default' : 'ghost'}
              size="sm"
              className="h-7 px-3 rounded-full text-xs font-medium"
              onClick={() => onLanguageChange('en')}
            >
              <Globe className="h-3 w-3 mr-1" />
              EN
            </Button>
            <Button
              variant={language === 'hi' ? 'default' : 'ghost'}
              size="sm"
              className="h-7 px-3 rounded-full text-xs text-hindi font-medium"
              onClick={() => onLanguageChange('hi')}
            >
              हि
            </Button>
          </div>

          <div className="border-l border-border/50 pl-3">
            <span className="text-xs text-muted-foreground">
              {language === 'en' ? 'Demo Mode' : 'डेमो मोड'}
            </span>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

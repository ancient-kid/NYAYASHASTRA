import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { EnhancedIPCBNSComparison } from "@/components/EnhancedIPCBNSComparison";
import { motion } from "framer-motion";
import { getIPCBNSComparisons, IPCBNSMapping } from "@/services/api";
import { Loader2, Search, AlertCircle, Scale, BookOpen, ArrowLeftRight } from "lucide-react";
import { Input } from "@/components/ui/input";

interface ComparisonItem {
  id: string;
  ipcSection: string;
  ipcTitle: string;
  ipcContent: string;
  bnsSection: string;
  bnsTitle: string;
  bnsContent: string;
  changes: Array<{
    type: "added" | "removed" | "modified";
    description: string;
  }>;
  punishmentChange?: {
    old: string;
    new: string;
    increased: boolean;
  };
}

// Transform API data to component format
const transformMapping = (mapping: IPCBNSMapping): ComparisonItem => ({
  id: mapping.id,
  ipcSection: mapping.ipcSection,
  ipcTitle: mapping.ipcTitle,
  ipcContent: mapping.ipcContent,
  bnsSection: mapping.bnsSection,
  bnsTitle: mapping.bnsTitle,
  bnsContent: mapping.bnsContent,
  changes: mapping.changes.map((c) => ({
    type: c.type as "added" | "removed" | "modified",
    description: c.description,
  })),
  punishmentChange: mapping.punishmentChange,
});

export const Comparison = () => {
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [comparisons, setComparisons] = useState<ComparisonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [totalCount, setTotalCount] = useState(0);

  // Fetch comparisons from API with retry for Neon cold start
  useEffect(() => {
    const fetchComparisons = async (retries = 3) => {
      try {
        setLoading(true);
        setError(null);
        const data = await getIPCBNSComparisons(
          undefined,
          undefined,
          searchQuery || undefined,
        );
        setComparisons(data.comparisons.map(transformMapping));
        setTotalCount(data.total);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch comparisons:", err);
        if (retries > 0) {
          console.log(`Retrying... (${retries} attempts left)`);
          setTimeout(() => fetchComparisons(retries - 1), 2000);
          return;
        }
        // Don't show error, just show empty state
        setComparisons([]);
        setTotalCount(0);
      } finally {
        setLoading(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(fetchComparisons, searchQuery ? 300 : 0);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background to-muted/20">
      <Header language={language} onLanguageChange={setLanguage} />

      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 border-b border-primary/10">
        <div className="container mx-auto px-4 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-6xl mx-auto"
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              {/* Title Section */}
              <div className="flex items-start gap-4">
                <div className="p-4 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/20 hidden sm:block">
                  <ArrowLeftRight className="h-8 w-8 text-primary" />
                </div>
                <div>
                  <h1 className="text-3xl lg:text-4xl font-serif font-bold text-foreground mb-2">
                    {language === "en"
                      ? "IPC ↔ BNS Comparison"
                      : "IPC ↔ BNS तुलना"}
                  </h1>
                  <p className="text-muted-foreground max-w-xl">
                    {language === "en"
                      ? "Complete cross-reference guide from the Indian Penal Code (1860) to the new Bhartiya Nyaya Sanhita (2023). Track all changes, modifications, and punishments."
                      : "भारतीय दंड संहिता (1860) से नई भारतीय न्याय संहिता (2023) तक की संपूर्ण क्रॉस-रेफरेंस गाइड। सभी परिवर्तनों, संशोधनों और दंडों को ट्रैक करें।"}
                  </p>
                </div>
              </div>

              {/* Info Cards */}
              <div className="flex gap-3">
                <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-chart-1/10 border border-chart-1/20">
                  <BookOpen className="h-5 w-5 text-chart-1" />
                  <div>
                    <p className="text-xs text-muted-foreground">IPC 1860</p>
                    <p className="font-semibold text-chart-1">Old Law</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-chart-2/10 border border-chart-2/20">
                  <Scale className="h-5 w-5 text-chart-2" />
                  <div>
                    <p className="text-xs text-muted-foreground">BNS 2023</p>
                    <p className="font-semibold text-chart-2">New Law</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Search Bar */}
            <div className="mt-6 relative max-w-2xl">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder={
                  language === "en"
                    ? "Search by section number or title (e.g., '302', 'Murder', 'Theft')..."
                    : "खंड संख्या या शीर्षक द्वारा खोजें (जैसे, '302', 'हत्या', 'चोरी')..."
                }
                className="pl-12 h-14 text-lg rounded-2xl bg-background/80 backdrop-blur-sm border-primary/20 focus:border-primary shadow-lg"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="max-w-6xl mx-auto"
        >
          <div className="glass-strong rounded-[2rem] p-6 lg:p-8 shadow-2xl">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="relative mb-6">
                  <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl animate-pulse"></div>
                  <Loader2 className="h-12 w-12 text-primary animate-spin relative" />
                </div>
                <p className="text-foreground font-semibold text-lg mb-2">
                  {language === "en"
                    ? "Loading Comparisons..."
                    : "तुलना लोड हो रही है..."}
                </p>
                <p className="text-sm text-muted-foreground text-center max-w-md">
                  {language === "en"
                    ? "Fetching 213 IPC to BNS section mappings from the database. This may take a moment on first load."
                    : "डेटाबेस से 213 IPC से BNS सेक्शन मैपिंग प्राप्त कर रहा है। पहले लोड पर इसमें कुछ समय लग सकता है।"}
                </p>
              </div>
            ) : error ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="p-4 rounded-full bg-red-500/10 mb-4">
                    <AlertCircle className="h-10 w-10 text-red-500" />
                  </div>
                  <p className="text-center text-red-500 font-medium">{error}</p>
              </div>
            ) : (
              <EnhancedIPCBNSComparison
                comparisons={comparisons}
                language={language}
              />
            )}
          </div>
        </motion.div>
      </main>

      {/* Footer Note */}
      <div className="container mx-auto px-4 pb-8">
        <div className="max-w-6xl mx-auto">
          <p className="text-center text-xs text-muted-foreground">
            {language === "en"
              ? "Data sourced from official government publications. The Bhartiya Nyaya Sanhita (BNS) 2023 replaces the Indian Penal Code (IPC) 1860 effective July 1, 2024."
              : "आधिकारिक सरकारी प्रकाशनों से प्राप्त डेटा। भारतीय न्याय संहिता (BNS) 2023 भारतीय दंड संहिता (IPC) 1860 को 1 जुलाई 2024 से प्रभावी रूप से बदलती है।"}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Comparison;

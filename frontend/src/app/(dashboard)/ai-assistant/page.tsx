"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { examplePrompts, type ChatMessage } from "@/lib/chat-engine";
import { useLanguage } from "@/components/LanguageContext";
import * as motion from "motion/react-client";
import { Send, MessageSquare, Sparkles, Bot, User } from "lucide-react";

export default function AIAssistantPage() {
  const { t, lang } = useLanguage();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hello! I'm the CrimeRakshak AI Copilot. Ask me anything about Karnataka crime data. Try one of the suggestions below!", timestamp: new Date() },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const conversationId = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (query?: string) => {
    const q = query || input.trim();
    if (!q || loading) return;

    const userMsg: ChatMessage = { role: "user", content: q, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: q,
          conversation_id: conversationId.current,
          // UI language is "EN" | "KA"; backend expects "en" | "kn".
          language: lang === "KA" ? "kn" : "en",
        }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.detail || data?.error || `Request failed (${res.status})`);
      }

      conversationId.current = data.conversation_id ?? conversationId.current;
      let content: string = data.answer ?? "(no answer)";
      if (Array.isArray(data.sources) && data.sources.length > 0) {
        content += "\n\n---\n📎 Sources:\n" + data.sources.map((s: string) => `• ${s}`).join("\n");
      }
      const assistantMsg: ChatMessage = { role: "assistant", content, timestamp: new Date() };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: `⚠️ Could not reach the AI backend.\n${String(err)}\n\nMake sure the backend is running on http://localhost:8000.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 h-[calc(100vh-4rem)] flex flex-col">
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="mb-4">
        <h1 className="text-2xl md:text-3xl font-heading font-bold flex items-center gap-2">
          <Sparkles className="h-7 w-7 text-brand-purple" /> {t("AI Copilot Chat")}
        </h1>
        <p className="text-muted-foreground mt-1 text-sm">{t("Natural-language crime data analysis assistant")}</p>
      </motion.div>

      <Card className="glass-card flex-1 flex flex-col min-h-0 hover:!transform-none">
        {/* Messages */}
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-brand-purple to-brand-blue flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-brand-purple text-white rounded-br-md"
                  : "bg-muted/50 rounded-bl-md"
              }`}>
                {msg.content === "Hello! I'm the CrimeRakshak AI Copilot. Ask me anything about Karnataka crime data. Try one of the suggestions below!" ? t(msg.content) : msg.content}
              </div>
              {msg.role === "user" && (
                <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                  <User className="h-4 w-4" />
                </div>
              )}
            </motion.div>
          ))}
          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-brand-purple to-brand-blue flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="max-w-[80%] rounded-2xl px-4 py-3 text-sm bg-muted/50 rounded-bl-md text-muted-foreground animate-pulse">
                {t("Analyzing crime data...")}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>

        {/* Suggestions */}
        {messages.length <= 2 && (
          <div className="px-4 pb-2 flex flex-wrap gap-2">
            {examplePrompts.map((p) => (
              <button
                key={p}
                onClick={() => handleSend(p)}
                className="text-xs px-3 py-1.5 rounded-full border border-brand-purple/30 text-brand-purple hover:bg-brand-purple/10 transition-colors"
              >
                {t(p)}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-border">
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t("Ask about crime data...")}
              className="flex-1"
              disabled={loading}
            />
            <Button type="submit" size="icon" className="bg-gradient-to-r from-brand-purple to-brand-blue" disabled={!input.trim() || loading}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}

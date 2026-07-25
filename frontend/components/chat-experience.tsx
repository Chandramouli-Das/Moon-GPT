"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowUp,
  ArrowUpRight,
  BrainCircuit,
  BriefcaseBusiness,
  FileSearch,
  ChevronDown,
  Menu,
  Mail,
  Milestone,
  Moon,
  PanelLeftClose,
  RotateCcw,
  Sparkles,
  Sun,
  UsersRound,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { getProfile, sendChat } from "@/lib/api";
import type { Message, Profile } from "@/lib/types";
import { MessageBubble } from "./message-bubble";
import { ProfilePanel } from "./profile-panel";

const greeting: Message = {
  id: "welcome",
  role: "assistant",
  content:
    "Hello — I’m Chandramouli’s portfolio assistant. I can give you a focused view of his **AI leadership, production GenAI work, major projects, and technical depth**. What would you like to explore?",
};

const prompts = [
  { icon: BriefcaseBusiness, label: "Executive profile", text: "Summarize Chandramouli’s profile for a hiring leader." },
  { icon: FileSearch, label: "Relevant projects", text: "Which projects best demonstrate production GenAI and RAG expertise?" },
  { icon: UsersRound, label: "Leadership impact", text: "Tell me about his leadership and mentoring experience." },
  { icon: Milestone, label: "Career journey", text: "Walk me through Chandramouli’s career progression and biggest transitions." },
  { icon: BrainCircuit, label: "Technical depth", text: "Break down his strongest GenAI, data science, and agentic AI capabilities." },
  { icon: Mail, label: "Write an email", text: "Draft a professional recruiter outreach email to Chandramouli with placeholders for my details." },
];

function makeId() {
  return crypto.randomUUID();
}

export function ChatExperience() {
  const [messages, setMessages] = useState<Message[]>([greeting]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [dark, setDark] = useState(false);
  const [mobileProfile, setMobileProfile] = useState(false);
  const [nearBottom, setNearBottom] = useState(true);
  const [unread, setUnread] = useState(false);
  const [sessionId] = useState(() =>
    typeof window === "undefined" ? "pending-session" : makeId(),
  );
  const endRef = useRef<HTMLDivElement>(null);
  const conversationRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    getProfile(controller.signal).then(setProfile).catch(() => undefined);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);

  function scrollToLatest(behavior: ScrollBehavior = "smooth") {
    endRef.current?.scrollIntoView({ behavior, block: "end" });
    setNearBottom(true);
    setUnread(false);
  }

  function handleConversationScroll() {
    const element = conversationRef.current;
    if (!element) return;
    const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
    const isNearBottom = distance < 110;
    setNearBottom(isNearBottom);
    if (isNearBottom) setUnread(false);
  }

  useEffect(() => {
    if (nearBottom) {
      requestAnimationFrame(() => scrollToLatest("smooth"));
    } else if (!loading && messages.at(-1)?.role === "assistant") {
      setUnread(true);
    }
    // Scroll decisions intentionally run only when chat content changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, loading]);

  async function submit(text = input) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    const userMessage: Message = { id: makeId(), role: "user", content: trimmed };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    requestAnimationFrame(() => scrollToLatest("smooth"));

    try {
      const result = await sendChat(sessionId, nextMessages);
      setMessages((current) => [
        ...current,
        {
          id: makeId(),
          role: "assistant",
          content: result.answer,
          action: result.action,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: makeId(),
          role: "assistant",
          content: `I couldn’t complete that request. ${error instanceof Error ? error.message : "Please try again."}`,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void submit();
  }

  function reset() {
    setMessages([greeting]);
    setInput("");
  }

  return (
    <main className="app-shell">
      <div className="desktop-profile"><ProfilePanel profile={profile} /></div>

      <AnimatePresence>
        {mobileProfile && (
          <>
            <motion.button
              className="mobile-overlay"
              aria-label="Close profile"
              onClick={() => setMobileProfile(false)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
            <motion.div
              className="mobile-profile"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 34 }}
            >
              <button className="drawer-close" onClick={() => setMobileProfile(false)}>
                <X size={19} />
              </button>
              <ProfilePanel profile={profile} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <section className="chat-panel">
        <header className="chat-header">
          <div className="header-left">
            <button className="mobile-menu" onClick={() => setMobileProfile(true)} aria-label="Open profile">
              <Menu size={20} />
            </button>
            <div className="header-mark"><Sparkles size={18} /></div>
            <div>
              <h2>Ask MoonGPT</h2>
              <p><span /> Online <b>·</b> Résumé intelligence</p>
            </div>
          </div>
          <div className="header-actions">
            <button
              className="email-cta"
              onClick={() => void submit("Draft a professional recruiter outreach email")}
              title="Draft a recruiter email"
              disabled={loading}
            >
              <Mail size={16} /><span>Draft email</span>
            </button>
            <button className="new-chat" onClick={reset} title="New conversation">
              <RotateCcw size={17} /><span>New chat</span>
            </button>
            <button className="icon-action" onClick={() => setDark((value) => !value)} title="Change theme">
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button className="desktop-collapse icon-action" title="Profile panel"><PanelLeftClose size={18} /></button>
          </div>
        </header>

        <div
          className="conversation"
          ref={conversationRef}
          onScroll={handleConversationScroll}
        >
          <div className="conversation-inner">
            {messages.length === 1 && (
              <motion.section
                className="conversation-intro"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="intro-badge"><Sparkles size={13} /> The career lore, verified</div>
                <h3>Skip the résumé scroll.<br /><em>Meet the brain behind the builds.</em></h3>
                <p>No corporate word salad. Just the work, wins, and receipts—grounded in real career context.</p>
              </motion.section>
            )}

            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <MessageBubble message={message} onAction={(text) => void submit(text)} />
                </motion.div>
              ))}
            </AnimatePresence>

            {messages.length === 1 && (
              <div className="prompt-grid">
                {prompts.map(({ icon: Icon, label, text }) => (
                  <button key={label} onClick={() => void submit(text)}>
                    <div className="prompt-card-top">
                      <span><Icon size={18} /></span>
                      <ArrowUpRight size={15} />
                    </div>
                    <strong>{label}</strong>
                    <small>{text}</small>
                  </button>
                ))}
              </div>
            )}

            {loading && (
              <div className="message assistant">
                <div className="message-avatar"><Sparkles size={17} /></div>
                <div className="message-content">
                  <div className="message-meta"><span>MoonGPT</span></div>
                  <div className="bubble typing"><i /><i /><i /></div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        </div>

        <AnimatePresence>
          {!nearBottom && (
            <motion.button
              className="jump-to-latest"
              type="button"
              onClick={() => scrollToLatest()}
              initial={{ opacity: 0, y: 8, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.96 }}
              aria-label="Jump to the latest message"
            >
              <ChevronDown size={16} />
              <span>{unread ? "New response" : "Jump to latest"}</span>
              {unread && <i />}
            </motion.button>
          )}
        </AnimatePresence>

        <footer className="composer-wrap">
          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submit();
                }
              }}
              rows={1}
              placeholder="Ask about experience, projects, leadership, or skills…"
              aria-label="Message MoonGPT"
            />
            <span className="composer-hint">↵</span>
            <button disabled={!input.trim() || loading} aria-label="Send message">
              <ArrowUp size={19} />
            </button>
          </form>
          <p>MoonGPT answers from résumé data. Verify important details directly with Chandramouli.</p>
        </footer>
      </section>

    </main>
  );
}

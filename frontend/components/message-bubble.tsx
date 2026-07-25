"use client";

import { Bot, Check, Download, Send, UserRound } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "@/lib/types";
import { API_URL } from "@/lib/api";

export function MessageBubble({
  message,
  onAction,
}: {
  message: Message;
  onAction: (message: string) => void;
}) {
  const assistant = message.role === "assistant";

  return (
    <article className={`message ${message.role}`}>
      <div className="message-avatar">
        {assistant ? <Bot size={18} /> : <UserRound size={17} />}
      </div>
      <div className="message-content">
        <div className="message-meta">
          <span>{assistant ? "MoonGPT" : "You"}</span>
          {assistant && <span className="verified"><Check size={11} /> résumé-grounded</span>}
        </div>
        <div className="bubble">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </div>
        {message.action?.type === "resume_download" && (
          <a className="inline-action" href={`${API_URL}/api/resume`}>
            <Download size={16} /> {message.action.label}
          </a>
        )}
        {message.action?.type === "email_draft" && (
          <button className="inline-action" onClick={() => onAction("Ok send it")}>
            <Send size={16} /> {message.action.label}
          </button>
        )}
      </div>
    </article>
  );
}

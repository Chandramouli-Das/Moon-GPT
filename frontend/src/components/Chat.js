// src/components/Chat.js
import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import "./Chat.css";

const Chat = ({ messages }) => {
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div id="chat-history" ref={chatContainerRef}>
      {messages.map((msg, index) => (
        <div
          key={index}
          className={`chat-bubble ${msg.sender === "user" ? "user" : "assistant"}`}
        >
          <strong>{msg.sender === "user" ? "You:" : "Moon GPT:"}</strong>
          <ReactMarkdown>{msg.text}</ReactMarkdown>
        </div>
      ))}
    </div>
  );
};

export default Chat;
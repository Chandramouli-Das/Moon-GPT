// src/App.js
import React, { useState } from "react";
import axios from "axios";
import Chat from "./components/Chat";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Example FAQs (feel free to customize)
  const faqs = [
    "What is your highest qualification?",
    "Give me your contact details",
    "What is your name?",
    "What is your expertise?",
    "Tell me about the candidate",
  ];

  // Handle clicking on a FAQ to populate the input field
  const handleFAQClick = (faq) => {
    setUserInput(faq);
  };

  // Function to handle "Show My CV" button click
  const handleShowCVClick = async () => {
    const cvQuery = "Show me your resume";
    // Add this query to the chat history
    setMessages((prev) => [...prev, { sender: "user", text: cvQuery }]);
    try {
      setLoading(true);
      // Use axios with responseType 'blob' to handle the PDF file response
      const response = await axios.post(
        "http://localhost:8080/api/chat",
        { conversation: [{ role: "user", content: cvQuery }] },
        { responseType: "blob" }
      );
      // Create an object URL from the blob and open it in a new tab
      const file = new Blob([response.data], { type: "application/pdf" });
      const fileURL = URL.createObjectURL(file);
      window.open(fileURL, "_blank");
    } catch (error) {
      console.error("Error fetching CV:", error.response || error.message);
      setMessages((prev) => [
        ...prev,
        { sender: "assistant", text: "Error: Could not fetch CV." },
      ]);
    } finally {
      setLoading(false);
    }
    setUserInput("");
  };

  // Send a regular conversation message
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    // Add the user's new message to the chat history
    setMessages((prev) => [...prev, { sender: "user", text: userInput }]);

    // Build the conversation array
    const conversation = [
      {
        role: "system",
        content:
          "You are an expert assistant providing detailed and accurate information based on the document context. Please answer concisely, using bullet points for lists, and if more detail is needed, end with 'Do you want to know more?'.",
      },
      ...messages.map((msg) => ({
        role: msg.sender === "user" ? "user" : "assistant",
        content: msg.text,
      })),
      { role: "user", content: userInput },
    ];

    try {
      setLoading(true);
      const response = await axios.post("http://localhost:8080/api/chat", {
        conversation: conversation,
      });
      const reply = response.data.answer;
      setMessages((prev) => [...prev, { sender: "assistant", text: reply }]);
    } catch (error) {
      console.error("Error fetching reply:", error.response || error.message);
      setMessages((prev) => [
        ...prev,
        { sender: "assistant", text: "Error: Could not fetch reply." },
      ]);
    } finally {
      setLoading(false);
    }
    setUserInput("");
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    const lowerInput = userInput.toLowerCase();
    if (lowerInput.includes("cv") || lowerInput.includes("resume")) {
      await handleShowCVClick();
    } else {
      await sendMessage(e);
    }
  };

  return (
    <div className="main-content">
      {/* Left Side FAQ Panel */}
      <div className="faq-container">
        <h2>FAQ</h2>
        {faqs.map((faq, index) => (
          <div key={index} className="faq-item" onClick={() => handleFAQClick(faq)}>
            {faq}
          </div>
        ))}
      </div>

      {/* Right Side Chat Section */}
      <div className="chat-section">
        <h1>🌙 Moon GPT</h1>
        <div className="chat-window">
          <Chat messages={messages} />
        </div>
        <form className="chat-input" onSubmit={handleSubmit}>
          {/* CV button at the bottom left */}
          <button
            type="button"
            className="cv-button"
            onClick={handleShowCVClick}
          >
            Show My CV
          </button>

          <input
            type="text"
            placeholder="Type your message..."
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
          />
          <button type="submit">Send</button>
          {loading && <div className="spinner-inline" />}
        </form>
      </div>
    </div>
  );
}

export default App;
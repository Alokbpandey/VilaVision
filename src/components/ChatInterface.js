import React, { useState } from 'react';
import { ArrowRight, Globe, Copy } from 'lucide-react'; // Icons from lucide-react
import { FiUpload } from 'react-icons/fi'; // Upload icon
import axios from 'axios';

function ChatInterface({ onSubmit, chatHistory, isLoading, error, result }) {
  const [message, setMessage] = useState("");

  // Handle input field change
  const handleInputChange = (e) => {
    setMessage(e.target.value);
  };

  // Handle sending the message
  const handleSendMessage = async () => {
    if (message.trim()) {
      onSubmit(message);
      setMessage(""); // Clear message input after submitting
    }
  };

  // Render individual chat messages
  const renderMessages = () => {
    return chatHistory.map((msg, index) => (
      <div
        key={index}
        className={`message ${msg.sender === "user" ? "user-message" : "system-message"}`}
      >
        <div className="message-content">{msg.content}</div>
      </div>
    ));
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="logo">
          <Globe size={24} />
          VilaVision Chat
        </div>
      </div>
      
      {/* Chat Body (Message Area) */}
      <div className="chat-body">
        <div className="messages">
          {renderMessages()}
          {isLoading && (
            <div className="loading-message">Processing your request...</div>
          )}
          {error && (
            <div className="error-message">{error}</div>
          )}
          {result && (
            <div className="result-message">{result}</div>
          )}
        </div>
      </div>

      {/* Chat Input */}
      <div className="chat-footer">
        <input
          type="text"
          value={message}
          onChange={handleInputChange}
          className="chat-input"
          placeholder="Type a message..."
        />
        <button onClick={handleSendMessage} className="send-button">
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;

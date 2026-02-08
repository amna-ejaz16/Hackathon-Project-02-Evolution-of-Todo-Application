"use client";

import { useState, KeyboardEvent } from "react";
import { motion } from "framer-motion";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

/**
 * ChatInput - Message input area with send button
 *
 * Features:
 * - Dark themed input with purple focus glow
 * - Circular gradient send button
 * - Enter key to submit
 * - Auto-clear on send
 * - Disabled state handling
 */
export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [inputValue, setInputValue] = useState("");

  const handleSend = () => {
    const trimmed = inputValue.trim();
    if (!trimmed || disabled) return;

    onSend(trimmed);
    setInputValue("");
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isInputEmpty = inputValue.trim().length === 0;

  return (
    <div className="flex-shrink-0 px-4 py-3 glass-strong border-t border-purple-500/10">
      <div className="flex items-center gap-2">
        {/* Input field */}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          placeholder="Type a message..."
          className="flex-1 px-4 py-3 rounded-xl bg-gray-800/80 border border-gray-700 text-white placeholder-gray-500
                     focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20
                     transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            boxShadow: "0 0 0 0 rgba(168, 85, 247, 0)"
          }}
          onFocus={(e) => {
            e.target.style.boxShadow = "0 0 0 3px rgba(168, 85, 247, 0.1), 0 0 20px rgba(168, 85, 247, 0.1)";
          }}
          onBlur={(e) => {
            e.target.style.boxShadow = "0 0 0 0 rgba(168, 85, 247, 0)";
          }}
        />

        {/* Send button */}
        <motion.button
          onClick={handleSend}
          disabled={disabled || isInputEmpty}
          whileHover={!disabled && !isInputEmpty ? { scale: 1.05 } : {}}
          whileTap={!disabled && !isInputEmpty ? { scale: 0.95 } : {}}
          className="flex items-center justify-center w-11 h-11 rounded-full transition-all duration-300
                     disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: disabled || isInputEmpty
              ? "rgba(168, 85, 247, 0.3)"
              : "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)",
            boxShadow: disabled || isInputEmpty
              ? "none"
              : "0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(236, 72, 153, 0.2)"
          }}
          aria-label="Send message"
        >
          <svg
            className="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </motion.button>
      </div>
    </div>
  );
}

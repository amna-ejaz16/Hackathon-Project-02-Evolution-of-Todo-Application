"use client";

import { motion } from "framer-motion";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

/**
 * ChatMessage - Individual message bubble
 *
 * Features:
 * - Fade-in animation on mount
 * - User messages: right-aligned, gradient purple-to-pink background
 * - Assistant messages: left-aligned, glass background with purple border
 * - Rounded corners with distinctive tail (rounded-br-md for user, rounded-bl-md for assistant)
 * - Optional timestamp display
 */
export default function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const isUser = role === "user";

  // Format timestamp if provided
  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
      })
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col ${isUser ? "items-end" : "items-start"} mb-4`}
    >
      {/* Message bubble */}
      <div
        className={`max-w-[80%] px-4 py-3 ${
          isUser
            ? "ml-auto rounded-2xl rounded-br-md text-white"
            : "mr-auto rounded-2xl rounded-bl-md text-gray-200"
        }`}
        style={
          isUser
            ? {
                background: "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)",
                boxShadow: "0 2px 8px rgba(168, 85, 247, 0.3)",
              }
            : {
                background: "rgba(17, 17, 24, 0.85)",
                backdropFilter: "blur(20px)",
                WebkitBackdropFilter: "blur(20px)",
                border: "1px solid rgba(168, 85, 247, 0.2)",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.2)",
              }
        }
      >
        {/* Message content with word wrap */}
        <p className="text-sm leading-relaxed break-words whitespace-pre-wrap">
          {content}
        </p>
      </div>

      {/* Timestamp */}
      {formattedTime && (
        <span className="text-xs text-gray-500 mt-1 px-1">
          {formattedTime}
        </span>
      )}
    </motion.div>
  );
}

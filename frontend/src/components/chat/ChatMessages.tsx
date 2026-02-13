"use client";

import { useRef, useEffect } from "react";
import { Message } from "@/types/chat";
import ChatMessage from "./ChatMessage";
import TypingIndicator from "./TypingIndicator";

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

/**
 * ChatMessages - Scrollable messages container
 *
 * Features:
 * - Auto-scroll to bottom on new messages
 * - Custom dark-themed scrollbar
 * - Maps messages to ChatMessage components
 * - Shows typing indicator when loading
 * - Empty state when no messages
 */
export default function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change or loading state changes
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto px-4 py-3 scrollbar-thin scrollbar-track-gray-900 scrollbar-thumb-purple-500"
      style={{
        scrollbarWidth: "thin",
        scrollbarColor: "#a855f7 #0a0a0f",
      }}
    >
      {/* Empty state */}
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500 text-sm text-center px-4">
            No messages yet. Start a conversation!
          </p>
        </div>
      )}

      {/* Messages list */}
      {messages.map((message) => (
        <ChatMessage
          key={message.id}
          role={message.role as "user" | "assistant"}
          content={message.content}
          timestamp={message.created_at}
        />
      ))}

      {/* Typing indicator */}
      {isLoading && <TypingIndicator />}
    </div>
  );
}

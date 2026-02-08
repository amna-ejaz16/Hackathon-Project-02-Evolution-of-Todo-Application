"use client";

import { motion } from "framer-motion";

interface ChatHeaderProps {
  onClose: () => void;
}

/**
 * ChatHeader - Top bar of the chat widget
 *
 * Features:
 * - Gradient accent strip (purple-to-pink)
 * - AI assistant icon and title with text gradient
 * - Close button with hover effects
 * - Glass morphism background
 */
export default function ChatHeader({ onClose }: ChatHeaderProps) {
  return (
    <div className="flex-shrink-0">
      {/* Gradient accent strip */}
      <div
        className="h-[3px] w-full"
        style={{
          background: "linear-gradient(90deg, #a855f7 0%, #ec4899 100%)"
        }}
      />

      {/* Header content */}
      <div className="glass-strong flex items-center justify-between px-4 py-3 border-b border-purple-500/10">
        {/* Icon and title */}
        <div className="flex items-center gap-3">
          {/* AI Icon */}
          <motion.div
            initial={{ rotate: 0 }}
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg shadow-purple-500/50"
          >
            <span className="text-white text-lg">✨</span>
          </motion.div>

          {/* Title */}
          <h3 className="text-gradient font-semibold text-lg">
            Task Manager Assistant
          </h3>
        </div>

        {/* Close button */}
        <motion.button
          onClick={onClose}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-white/10 transition-colors group"
          aria-label="Close chat"
        >
          <svg
            className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </motion.button>
      </div>
    </div>
  );
}

// Chat.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User } from 'lucide-react';
import { sendChatMessage } from '@/lib/api';
import { ChatResponse } from '@/types';
import LoadingSpinner from './LoadingSpinner';

// >>> Markdown renderer
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type SourceItem =
  | string
  | {
      snippet?: string;
      score?: number;
      source?: string;
      [k: string]: any;
    };

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  sources?: SourceItem[];
}

interface ChatProps {
  fileId: string;
  filename: string;
}

export default function Chat({ fileId, filename }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: `Hi! I've analyzed your file "${filename}". You can ask me questions about the data, request analysis, or get insights. What would you like to know?`,
      sender: 'bot'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now().toString(), text: inputText, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await sendChatMessage({ message: userMessage.text, file_id: fileId });
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response ?? response.answer ?? 'OK',
        sources: response.sources as SourceItem[] | undefined,
        sender: 'bot'
      };
      setMessages(prev => [...prev, botMessage]);
    } catch {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: 'Sorry, I encountered an error processing your request. Please try again.', sender: 'bot' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const suggestedQuestions = [
    'What are the main insights from this data?',
    'Can you summarize the key statistics?',
    'What trends do you see in the data?',
    'Are there any anomalies or outliers?'
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 text-white">
          <h3 className="text-lg font-semibold">AI Data Assistant</h3>
          <p className="text-blue-100 text-sm">Chat about: {filename}</p>
        </div>

        {/* Messages */}
        <div className="h-96 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-3xl flex items-start space-x-2 ${m.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <div className={`p-2 rounded-full ${m.sender === 'user' ? 'bg-blue-500' : 'bg-gray-500'}`}>
                    {m.sender === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
                  </div>

                  <div className={`${m.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-800'} rounded-lg p-3`}>
                    {/* Markdown render: bold, list, table, dsb. */}
                    <div className="prose prose-sm max-w-none prose-headings:mt-2 prose-p:my-1">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {m.text}
                      </ReactMarkdown>
                    </div>

                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-300">
                        <p className="text-xs text-gray-600 mb-2">Sources:</p>
                        {m.sources.map((src, idx) => {
                          if (typeof src === 'string') {
                            return <div key={idx} className="text-xs bg-gray-50 p-2 rounded mb-1">{src}</div>;
                          }
                          const s = src as any;
                          return (
                            <div key={idx} className="text-xs bg-gray-50 p-2 rounded mb-1">
                              <div>{s.snippet ?? JSON.stringify(s)}</div>
                              {typeof s.score === 'number' && <div className="text-[10px] text-gray-500">score: {s.score.toFixed(3)}</div>}
                              {!!s.source && <div className="text-[10px] text-gray-500">source: {String(s.source)}</div>}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex justify-start">
              <div className="flex items-start space-x-2">
                <div className="p-2 rounded-full bg-gray-500"><Bot className="w-4 h-4 text-white" /></div>
                <div className="bg-gray-100 rounded-lg p-3"><LoadingSpinner /></div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Questions */}
        {messages.length === 1 && (
          <div className="p-4 border-t bg-gray-50">
            <p className="text-sm text-gray-600 mb-2">Try asking:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {suggestedQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => setInputText(q)}
                  className="text-left p-2 text-sm bg-white border border-gray-200 rounded hover:bg-blue-50 hover:border-blue-300 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t">
          <div className="flex space-x-2">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me anything about your data..."
              className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

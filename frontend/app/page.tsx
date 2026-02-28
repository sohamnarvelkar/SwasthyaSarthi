'use client';

import { useState, useEffect, useCallback } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Sidebar } from '@/components/Sidebar';
import { ChatWindow } from '@/components/ChatWindow';
import { StatusBar, AgentStatus } from '@/components/StatusBar';
import { OrderConfirmation, OrderDetails } from '@/components/OrderConfirmation';
import { useChat } from '@/hooks/useChat';
import { useVoiceAgent } from '@/hooks/useVoiceAgent';
import { useAuth } from '@/context/AuthContext';
import { ChatMessage } from '@/services/api';
import PrescriptionUploader from '@/components/PrescriptionUploader';

interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
}

function Dashboard() {
  const { user, logout } = useAuth();
  
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState('English');
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle');
  const [showOrderConfirmation, setShowOrderConfirmation] = useState(false);
  const [pendingOrder, setPendingOrder] = useState<OrderDetails | null>(null);
  const [showPrescriptionUploader, setShowPrescriptionUploader] = useState(false);

  const {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
  } = useChat({
    userId: user?.id?.toString() || 'default',
    userEmail: user?.email || 'user@example.com',
  });

  // Local state for managing messages (combines chat and voice)
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);

  // Sync local messages with useChat messages
  useEffect(() => {
    if (messages.length > 0) {
      setLocalMessages(messages);
    }
  }, [messages]);

  const {
    state: voiceState,
    transcript: voiceTranscript,
    isActive: isVoiceActive,
    startListening,
    stopListening,
    detectedLanguage,
  } = useVoiceAgent({
    userId: user?.id?.toString() || 'default',
    userEmail: user?.email || 'user@example.com',
    onMessage: (text, response) => {
      const assistantMessage: ChatMessage = {
        id: `voice-${Date.now()}`,
        role: 'assistant',
        content: response.text,
        language: response.language,
        timestamp: new Date(),
      };
      // Use functional update to add message
      setLocalMessages(prev => [...prev, assistantMessage]);
      
      if (response.requires_confirmation && response.pending_order) {
        setPendingOrder({
          order_id: `ORD-${Date.now()}`,
          medicine_name: response.pending_order.product_name,
          quantity: response.pending_order.quantity,
          unit_price: response.pending_order.unit_price,
          total_price: response.pending_order.total_price,
          status: 'confirmed',
          customer_email: user?.email,
        });
      }
    },
    onLanguageChange: (lang) => {
      setCurrentLanguage(lang);
    },
    onStateChange: (state) => {
      if (state === 'listening') setAgentStatus('thinking');
      else if (state === 'processing') setAgentStatus('checking_safety');
      else if (state === 'speaking') setAgentStatus('completed');
      else setAgentStatus('idle');
    },
  });

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const handleToggleVoiceMode = useCallback(() => {
    if (isVoiceMode) {
      stopListening();
    } else {
      startListening();
    }
    setIsVoiceMode(!isVoiceMode);
  }, [isVoiceMode, startListening, stopListening]);

  const handleToggleVoice = useCallback(() => {
    if (isVoiceActive) {
      stopListening();
      setIsVoiceMode(false);
    } else {
      startListening();
      setIsVoiceMode(true);
    }
  }, [isVoiceActive, startListening, stopListening]);

  const handleSendMessage = useCallback(async (content: string) => {
    setAgentStatus('thinking');
    await sendMessage(content);
    setAgentStatus('completed');
    setTimeout(() => setAgentStatus('idle'), 2000);
  }, [sendMessage]);

  const handleNewConversation = useCallback(() => {
    const newConv: Conversation = {
      id: `conv-${Date.now()}`,
      title: 'New Conversation',
      messages: [],
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
    clearMessages();
    setLocalMessages([]);
  }, [clearMessages]);

  const handleSelectConversation = useCallback((id: string) => {
    const conv = conversations.find(c => c.id === id);
    if (conv) {
      setActiveConversationId(id);
      setLocalMessages(conv.messages);
    }
  }, [conversations]);

  const handleDeleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeConversationId === id) {
      setActiveConversationId(null);
      clearMessages();
      setLocalMessages([]);
    }
  }, [activeConversationId, clearMessages]);

  const handleToggleDarkMode = useCallback(() => {
    setIsDarkMode(prev => !prev);
  }, []);

  const handleLanguageChange = useCallback((lang: string) => {
    setCurrentLanguage(lang);
  }, []);

  const handleLogout = useCallback(() => {
    logout();
  }, [logout]);

  // Handle tool button clicks - call APIs directly
  const handleToolClick = useCallback(async (tool: string) => {
    setAgentStatus('thinking');
    const userId = user?.id?.toString() || 'default';
    const userEmail = user?.email || 'user@example.com';
    
    try {
      let response;
      let messageContent = '';
      let toolData: any = null;
      
      switch (tool) {
        case 'medicines':
          // Get all medicines from database
          response = await fetch('/medicines');
          const medicines = await response.json();
          toolData = medicines;
          messageContent = `Here are all available medicines:\n\n${medicines.map((m: any) => 
            `• ${m.name} - ₹${m.price} (${m.in_stock ? 'In Stock' : 'Out of Stock'})`
          ).join('\n')}`;
          break;
          
        case 'orders':
          // Get order history for user
          response = await fetch(`/patients/${userId}/orders`);
          const orders = await response.json();
          toolData = orders;
          if (orders.length === 0) {
            messageContent = "You don't have any order history yet.";
          } else {
            messageContent = `Your order history:\n\n${orders.map((o: any) => 
              `• ${o.product_name} - Qty: ${o.quantity}, ₹${o.total_price} (${o.status}) - ${new Date(o.order_date).toLocaleDateString()}`
            ).join('\n')}`;
          }
          break;
          
        case 'refills':
          // Check for upcoming refills
          response = await fetch('/check-refills?days_ahead=7');
          const refillData = await response.json();
          toolData = refillData;
          if (refillData.alerts.length === 0) {
            messageContent = "You don't have any upcoming refills in the next 7 days.";
          } else {
            messageContent = `Upcoming medication refills:\n\n${refillData.alerts.map((a: any) => 
              `• ${a.product_name} - Refill in ${a.days_until_refill} days`
            ).join('\n')}`;
          }
          break;
          
        case 'profile':
          // Get patient profile
          response = await fetch(`/patients/${userId}`);
          const profile = await response.json();
          toolData = profile;
          if (profile.error) {
            messageContent = "Profile not found. Please complete your registration.";
          } else {
            messageContent = `Your Profile:\n\n` +
              `• Name: ${profile.name}\n` +
              `• Age: ${profile.age}\n` +
              `• Gender: ${profile.gender}\n` +
              `• Phone: ${profile.phone}\n` +
              `• Email: ${profile.email}\n` +
              `• Address: ${profile.address}\n` +
              `• Language: ${profile.language}`;
          }
          break;
          
        case 'prescription':
          // Show the prescription uploader
          setShowPrescriptionUploader(true);
          messageContent = "Please upload your prescription image (PNG, JPG, JPEG, or PDF).";
          break;
          
        default:
          messageContent = "Tool not implemented yet.";
      }
      
      // Add assistant response to chat
      const assistantMessage: ChatMessage = {
        id: `tool-${Date.now()}`,
        role: 'assistant',
        content: messageContent,
        language: currentLanguage,
        timestamp: new Date(),
      };
      setLocalMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Tool error:', error);
      const errorMessage: ChatMessage = {
        id: `tool-error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error while fetching data. Please try again.',
        language: currentLanguage,
        timestamp: new Date(),
      };
      setLocalMessages(prev => [...prev, errorMessage]);
    } finally {
      setAgentStatus('completed');
      setTimeout(() => setAgentStatus('idle'), 2000);
    }
  }, [user, currentLanguage, setShowPrescriptionUploader]);

  // Update conversation when local messages change
  useEffect(() => {
    if (activeConversationId && localMessages.length > 0) {
      setConversations(prev => prev.map(conv => {
        if (conv.id === activeConversationId) {
          return {
            ...conv,
            messages: localMessages,
            title: localMessages[0]?.content.slice(0, 30) || 'New Conversation',
          };
        }
        return conv;
      }));
    }
  }, [localMessages, activeConversationId]);

  // Initialize conversation on mount
  useEffect(() => {
    if (conversations.length === 0) {
      handleNewConversation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle pending orders
  useEffect(() => {
    if (pendingOrder && !showOrderConfirmation) {
      setShowOrderConfirmation(true);
      setAgentStatus('completed');
    }
  }, [pendingOrder, showOrderConfirmation]);

  return (
    <div className="flex h-screen bg-white dark:bg-slate-900">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isVoiceMode={isVoiceMode}
        onToggleVoiceMode={handleToggleVoiceMode}
        isDarkMode={isDarkMode}
        onToggleDarkMode={handleToggleDarkMode}
        userEmail={user?.email}
        onLogout={handleLogout}
      />

      <div className="flex-1 flex flex-col">
        <div className="px-6 pt-4">
          <StatusBar
            isVisible={agentStatus !== 'idle'}
            currentStatus={agentStatus}
          />
        </div>

        <ChatWindow
          messages={localMessages.length > 0 ? localMessages : messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
          isVoiceMode={isVoiceMode}
          voiceState={voiceState}
          voiceTranscript={voiceTranscript}
          voiceLanguage={detectedLanguage}
          onToggleVoice={handleToggleVoice}
          currentLanguage={currentLanguage}
          onLanguageChange={handleLanguageChange}
          onOpenTools={handleToolClick}
        />
      </div>

      {showOrderConfirmation && pendingOrder && (
        <OrderConfirmation
          order={pendingOrder}
          onClose={() => {
            setShowOrderConfirmation(false);
            setPendingOrder(null);
          }}
        />
      )}

      {showPrescriptionUploader && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-4 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Upload Prescription</h2>
              <button
                onClick={() => setShowPrescriptionUploader(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <PrescriptionUploader
              onMedicinesDetected={(medicines) => {
                console.log('Medicines detected:', medicines);
                setShowPrescriptionUploader(false);
              }}
              onError={(error) => {
                console.error('Prescription error:', error);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  );
}

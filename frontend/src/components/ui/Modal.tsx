"use client";

import { useEffect, ReactNode } from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  primaryAction?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "danger";
    loading?: boolean;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  primaryAction,
  secondaryAction,
}: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="bg-white rounded-2xl w-full max-w-md relative z-10 shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-5 border-b border-[#f8f3ee] flex items-center justify-between">
          <h3 className="text-lg font-bold text-[#1d1b19]">{title}</h3>
          <button 
            type="button"
            onClick={onClose}
            className="text-[#515f74] hover:text-[#1d1b19] transition-colors p-1"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
               <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6">
          {children}
        </div>
        
        <div className="px-6 py-4 bg-[#fdf8f3] border-t border-[#f8f3ee] flex gap-3 justify-end">
          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className="px-4 py-2 text-sm font-medium text-[#515f74] hover:bg-[#f8f3ee] rounded-lg transition-colors"
            >
              {secondaryAction.label}
            </button>
          )}
          {primaryAction && (
            <button
              type="button"
              onClick={primaryAction.onClick}
              disabled={primaryAction.loading}
              className={`px-4 py-2 text-sm font-semibold rounded-lg shadow-sm transition-all focus:ring-2 focus:ring-offset-2 ${
                primaryAction.variant === "danger"
                  ? "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500"
                  : "bg-[#3525cd] text-white hover:bg-[#4f46e5] focus:ring-[#3525cd]"
              } disabled:opacity-50`}
            >
              {primaryAction.loading ? "Processing..." : primaryAction.label}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shield, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAdminStore } from "@/lib/store/admin-store";

interface ZoiceAdminLayoutProps {
  children: React.ReactNode;
}

export default function ZoiceAdminLayout({ children }: ZoiceAdminLayoutProps) {
  const router = useRouter();
  const { isAdminMode, setAdminMode } = useAdminStore();

  // If not in admin mode, show access denied
  if (!isAdminMode) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-6">
        <div className="max-w-md text-center">
          <div className="mx-auto w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mb-6">
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
            Admin Access Required
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            You need to enable Admin Mode to access the Zoice Voice AI management features.
            Admin Mode can be toggled from the sidebar.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button variant="outline" onClick={() => router.push("/dashboard")}>
              Go to Dashboard
            </Button>
            <Button
              onClick={() => setAdminMode(true)}
              className="bg-purple-500 hover:bg-purple-600"
            >
              <Shield className="w-4 h-4 mr-2" />
              Enable Admin Mode
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Admin Mode Banner */}
      <div className="bg-purple-500 text-white px-4 py-2 text-sm flex items-center justify-center gap-2">
        <Shield className="w-4 h-4" />
        <span className="font-medium">Admin Mode Active</span>
        <span className="opacity-75">- Zoice Voice AI Management</span>
      </div>

      {/* Page Content */}
      <div className="bg-white dark:bg-gray-900 min-h-[calc(100vh-40px)]">
        {children}
      </div>
    </div>
  );
}

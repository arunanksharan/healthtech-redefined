"use client";

import { useRouter } from "next/navigation";
import { CallList } from "@/components/zoice-admin";
import { ZoiceCall } from "@/lib/store/admin-store";

export default function ZoiceCallsPage() {
  const router = useRouter();

  const handleCallSelect = (call: ZoiceCall) => {
    router.push(`/dashboard/admin/zoice/calls/${call.id}`);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Call History</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          View and analyze voice AI call records, transcripts, and recordings
        </p>
      </div>

      {/* Call List */}
      <CallList onCallSelect={handleCallSelect} />
    </div>
  );
}

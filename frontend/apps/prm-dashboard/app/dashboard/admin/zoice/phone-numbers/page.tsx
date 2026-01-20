"use client";

import { useRouter } from "next/navigation";
import { PhoneNumberList } from "@/components/zoice-admin";
import { ZoicePhoneNumber } from "@/lib/store/admin-store";

export default function ZoicePhoneNumbersPage() {
  const router = useRouter();

  const handlePhoneNumberSelect = (phoneNumber: ZoicePhoneNumber) => {
    // Could open a modal or navigate to detail page
    console.log("Selected phone number:", phoneNumber);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Phone Numbers</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Manage phone numbers and their pipeline assignments
        </p>
      </div>

      {/* Phone Number List */}
      <PhoneNumberList onPhoneNumberSelect={handlePhoneNumberSelect} />
    </div>
  );
}

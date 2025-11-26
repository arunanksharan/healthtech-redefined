"use client";

import * as React from "react";
import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Settings,
  Printer,
  MoreHorizontal,
  Calendar,
  Pill,
  FlaskConical,
  FileText,
  MessageSquare,
  Phone,
  FileOutput,
  ClipboardList,
  BarChart3,
  Search,
  Sparkles,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { patientsAPI } from "@/lib/api/patients";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePatientProfileStore } from "@/lib/store/patient-profile-store";
import {
  PatientHeader,
  HealthScoreWidget,
  AISummaryCard,
  PatientTimeline,
  CareGapsSection,
  CommunicationHistory,
  AskPatientData,
  AskPatientDataButton,
} from "@/components/patient-profile";

// ============================================================================
// Quick Actions Bar
// ============================================================================

interface QuickActionsBarProps {
  patientId: string;
  onAskData: () => void;
}

function QuickActionsBar({ patientId, onAskData }: QuickActionsBarProps) {
  const actions = [
    { icon: Calendar, label: "Book Appt", action: "book_appointment" },
    { icon: Pill, label: "Prescribe", action: "prescribe" },
    { icon: FlaskConical, label: "Order Lab", action: "order_lab" },
    { icon: FileText, label: "Add Note", action: "add_note" },
    { icon: MessageSquare, label: "Message", action: "message" },
    { icon: Phone, label: "Call", action: "call" },
    { icon: FileOutput, label: "Referral", action: "referral" },
    { icon: ClipboardList, label: "Care Plan", action: "care_plan" },
    { icon: BarChart3, label: "Reports", action: "reports" },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t p-4 z-40">
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 flex-wrap">
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={onAskData}
        >
          <Search className="h-4 w-4" />
          Ask Patient Data
        </Button>
        {actions.map((action) => (
          <Button
            key={action.action}
            variant="ghost"
            size="sm"
            className="gap-2"
          >
            <action.icon className="h-4 w-4" />
            {action.label}
          </Button>
        ))}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Export Summary</DropdownMenuItem>
            <DropdownMenuItem>Print Records</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Transfer Care</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function Patient360Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [askDataOpen, setAskDataOpen] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState("overview");

  // Patient profile store
  const {
    patient,
    alerts,
    healthScore,
    vitals,
    aiSummary,
    timelineEvents,
    careGaps,
    communications,
    communicationFilter,
    queryHistory,
    isLoadingPatient,
    isGeneratingSummary,
    isQueryLoading,
    loadPatient,
    regenerateSummary,
    setCommunicationFilter,
    submitQuery,
    updateCareGapStatus,
  } = usePatientProfileStore();

  // Load patient data on mount
  React.useEffect(() => {
    loadPatient(id);
  }, [id, loadPatient]);

  // Also fetch from API for server data (optional - can be used alongside mock data)
  const { data: apiData, isLoading: apiLoading } = useQuery({
    queryKey: ["patient-360", id],
    queryFn: async () => {
      const [data, error] = await patientsAPI.get360View(id);
      if (error) throw new Error(error.message);
      return data;
    },
    enabled: false, // Disable for now, using mock data from store
  });

  // Loading state
  if (isLoadingPatient) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Loading patient profile...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (!patient) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive mb-4">Patient not found</p>
        <Link href="/patients">
          <Button>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="pb-24">
      {/* Top navigation */}
      <div className="flex items-center justify-between mb-6">
        <Link href="/patients">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon">
            <Printer className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Patient Header with Alerts */}
      <PatientHeader
        patient={patient}
        alerts={alerts}
        onEdit={() => console.log("Edit patient")}
        onAction={(action) => console.log("Action:", action)}
        className="mb-6"
      />

      {/* View Mode Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList>
          <TabsTrigger value="overview">
            <Sparkles className="h-4 w-4 mr-2" />
            Story View
          </TabsTrigger>
          <TabsTrigger value="clinical">Clinical</TabsTrigger>
          <TabsTrigger value="engagement">Engagement</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Overview / Story View Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* AI Summary */}
              <AISummaryCard
                summary={aiSummary}
                isLoading={isGeneratingSummary}
                onRegenerate={regenerateSummary}
              />

              {/* Timeline */}
              <PatientTimeline
                events={timelineEvents}
                groupBy="day"
                isLoading={false}
                onEventClick={(event) => console.log("Event clicked:", event)}
                onLoadMore={() => console.log("Load more")}
                hasMore={true}
              />
            </div>

            {/* Right Column - Sidebar */}
            <div className="space-y-6">
              {/* Health Score */}
              {healthScore && (
                <HealthScoreWidget
                  score={healthScore.score}
                  trend={healthScore.trend}
                  label={healthScore.label}
                  components={healthScore.components}
                  lastUpdated={healthScore.lastUpdated}
                />
              )}

              {/* Care Gaps */}
              <CareGapsSection
                careGaps={careGaps}
                onAction={(gapId, action) => {
                  console.log("Care gap action:", gapId, action);
                }}
                onViewAll={() => setActiveTab("clinical")}
              />
            </div>
          </div>
        </TabsContent>

        {/* Clinical View Tab */}
        <TabsContent value="clinical" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Care Gaps - Full view */}
            <CareGapsSection
              careGaps={careGaps}
              onAction={(gapId, action) => {
                console.log("Care gap action:", gapId, action);
              }}
            />

            {/* Timeline - Clinical events only */}
            <PatientTimeline
              events={timelineEvents.filter(
                (e) => e.type === "encounter" || e.type === "lab" || e.type === "prescription"
              )}
              groupBy="episode"
              isLoading={false}
              onEventClick={(event) => console.log("Event clicked:", event)}
              onLoadMore={() => console.log("Load more")}
              hasMore={true}
            />
          </div>
        </TabsContent>

        {/* Engagement View Tab */}
        <TabsContent value="engagement" className="space-y-6 mt-6">
          <CommunicationHistory
            communications={communications}
            filter={communicationFilter}
            onFilterChange={setCommunicationFilter}
            onPlayRecording={(id) => console.log("Play recording:", id)}
            onViewTranscript={(id) => console.log("View transcript:", id)}
            onViewConversation={(id) => console.log("View conversation:", id)}
            hasMore={true}
          />
        </TabsContent>

        {/* Analytics View Tab */}
        <TabsContent value="analytics" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Health Score - Expanded */}
            {healthScore && (
              <HealthScoreWidget
                score={healthScore.score}
                trend={healthScore.trend}
                label={healthScore.label}
                components={healthScore.components}
                lastUpdated={healthScore.lastUpdated}
              />
            )}

            {/* Vitals trends placeholder */}
            <div className="p-6 border rounded-lg bg-card">
              <h3 className="font-medium mb-4">Vitals Trends</h3>
              <div className="h-48 flex items-center justify-center text-muted-foreground">
                <p className="text-sm">Charts will be displayed here</p>
              </div>
            </div>

            {/* Risk scores placeholder */}
            <div className="p-6 border rounded-lg bg-card">
              <h3 className="font-medium mb-4">Risk Predictions</h3>
              <div className="h-48 flex items-center justify-center text-muted-foreground">
                <p className="text-sm">Risk scores will be displayed here</p>
              </div>
            </div>

            {/* Population comparison placeholder */}
            <div className="p-6 border rounded-lg bg-card">
              <h3 className="font-medium mb-4">Population Comparison</h3>
              <div className="h-48 flex items-center justify-center text-muted-foreground">
                <p className="text-sm">Comparison charts will be displayed here</p>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Quick Actions Bar */}
      <QuickActionsBar
        patientId={id}
        onAskData={() => setAskDataOpen(true)}
      />

      {/* Ask Patient Data Dialog */}
      <AskPatientData
        isOpen={askDataOpen}
        onClose={() => setAskDataOpen(false)}
        patientId={id}
        patientName={patient.name}
        onQuery={submitQuery}
        queryHistory={queryHistory}
        isLoading={isQueryLoading}
      />
    </div>
  );
}

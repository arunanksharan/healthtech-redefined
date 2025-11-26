"use client";

// Health Records View
// EPIC-UX-011: Patient Self-Service Portal - Journey 11.1

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import {
  FileText, Activity, TestTube, Pill, Syringe, Download, Share2, ChevronRight,
  Circle, AlertTriangle, Check, Loader2, ClipboardList, Calendar,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  usePatientPortalStore,
  type HealthCondition,
  type Allergy,
  type LabReport,
  type LabResult,
  type VisitSummary,
  type Immunization,
} from "@/lib/store/patient-portal-store";

// Status indicator for lab results
function ResultStatus({ status }: { status: LabResult["status"] }) {
  const config = {
    normal: { color: "bg-green-500", label: "Normal" },
    abnormal: { color: "bg-amber-500", label: "Above/Below Target" },
    critical: { color: "bg-red-500", label: "Critical" },
  };
  const c = config[status];
  return (
    <div className="flex items-center gap-1.5">
      <div className={cn("h-2.5 w-2.5 rounded-full", c.color)} />
      <span className="text-xs text-muted-foreground">{c.label}</span>
    </div>
  );
}

// Health Summary Card
function HealthSummaryCard() {
  const { healthSummary, isLoadingHealth } = usePatientPortalStore();

  if (isLoadingHealth || !healthSummary) {
    return <div className="h-48 bg-muted animate-pulse rounded-lg" />;
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">HEALTH SUMMARY</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-6">
          {/* Conditions */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2">CONDITIONS</h4>
            <ul className="space-y-1">
              {healthSummary.conditions.map((condition) => (
                <li key={condition.id} className="flex items-center gap-2 text-sm">
                  <Circle className="h-1.5 w-1.5 fill-current" />
                  {condition.name}
                  {condition.status === "chronic" && (
                    <Badge variant="outline" className="text-xs">Chronic</Badge>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Allergies */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2">ALLERGIES</h4>
            <ul className="space-y-1">
              {healthSummary.allergies.map((allergy) => (
                <li key={allergy.id} className="flex items-center gap-2 text-sm">
                  <AlertTriangle className={cn(
                    "h-3 w-3",
                    allergy.severity === "severe" ? "text-red-500" : "text-amber-500"
                  )} />
                  {allergy.allergen}
                  {allergy.severity === "severe" && (
                    <Badge variant="destructive" className="text-xs">Severe</Badge>
                  )}
                </li>
              ))}
              {healthSummary.allergies.length === 0 && (
                <li className="text-sm text-muted-foreground">No known allergies</li>
              )}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Lab Results Card
interface LabResultsCardProps {
  lab: LabReport;
  onDownload: () => void;
  onShare: () => void;
}

function LabResultsCard({ lab, onDownload, onShare }: LabResultsCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">
            RECENT LAB RESULTS
            <span className="text-muted-foreground font-normal ml-2">
              {format(new Date(lab.date), "MMMM d, yyyy")}
            </span>
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onDownload}>
              <Download className="h-4 w-4 mr-1" />Download PDF
            </Button>
            <Button variant="outline" size="sm" onClick={onShare}>
              <Share2 className="h-4 w-4 mr-1" />Share
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr className="text-xs text-muted-foreground">
                <th className="text-left p-3">Test</th>
                <th className="text-left p-3">Result</th>
                <th className="text-left p-3">Normal Range</th>
                <th className="text-left p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {lab.results.map((result) => (
                <tr key={result.id} className="border-t">
                  <td className="p-3 text-sm font-medium">{result.testName}</td>
                  <td className="p-3 text-sm">
                    {result.result} {result.unit !== "%" && result.unit}
                  </td>
                  <td className="p-3 text-sm text-muted-foreground">{result.normalRange}</td>
                  <td className="p-3">
                    <ResultStatus status={result.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {lab.providerNote && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <span className="font-semibold">Dr. {lab.orderingProvider.split(" ").pop()}'s Note:</span>
              <br />
              "{lab.providerNote}"
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Visit Summary Card
interface VisitCardProps {
  visit: VisitSummary;
  onViewDetails: () => void;
}

function VisitCard({ visit, onViewDetails }: VisitCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={onViewDetails}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {format(new Date(visit.date), "MMMM d, yyyy")}
              </span>
            </div>
            <div>
              <p className="font-semibold">{visit.provider}</p>
              <p className="text-sm text-muted-foreground">{visit.specialty} - {visit.visitType}</p>
            </div>
            <p className="text-sm">{visit.chiefComplaint}</p>
            <div className="flex flex-wrap gap-1">
              {visit.diagnosis.map((dx, i) => (
                <Badge key={i} variant="outline" className="text-xs">{dx}</Badge>
              ))}
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

// Immunization Card
function ImmunizationCard({ immunization }: { immunization: Immunization }) {
  return (
    <div className="flex items-center justify-between p-3 border rounded-lg">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
          <Syringe className="h-5 w-5 text-green-600" />
        </div>
        <div>
          <p className="font-medium text-sm">{immunization.name}</p>
          <p className="text-xs text-muted-foreground">
            {format(new Date(immunization.date), "MMM d, yyyy")} - {immunization.administeredBy}
          </p>
        </div>
      </div>
      {immunization.nextDueDate && (
        <Badge variant="outline" className="text-xs">
          Next: {format(new Date(immunization.nextDueDate), "MMM yyyy")}
        </Badge>
      )}
    </div>
  );
}

// Main Health Records Component
export function HealthRecords() {
  const [activeTab, setActiveTab] = useState("summary");
  const { healthSummary, isLoadingHealth, fetchHealthSummary, downloadHealthRecord } = usePatientPortalStore();

  useEffect(() => { fetchHealthSummary(); }, [fetchHealthSummary]);

  if (isLoadingHealth) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <FileText className="h-6 w-6" />My Health Records
        </h1>
        <Button variant="outline" onClick={() => downloadHealthRecord("complete")}>
          <Download className="h-4 w-4 mr-2" />Download All Records
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary" className="gap-2">
            <ClipboardList className="h-4 w-4" />Summary
          </TabsTrigger>
          <TabsTrigger value="visits" className="gap-2">
            <Activity className="h-4 w-4" />Visits
          </TabsTrigger>
          <TabsTrigger value="labs" className="gap-2">
            <TestTube className="h-4 w-4" />Labs
          </TabsTrigger>
          <TabsTrigger value="medications" className="gap-2">
            <Pill className="h-4 w-4" />Medications
          </TabsTrigger>
          <TabsTrigger value="immunizations" className="gap-2">
            <Syringe className="h-4 w-4" />Immunizations
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="mt-6 space-y-6">
          <HealthSummaryCard />
          {healthSummary?.recentLabs[0] && (
            <LabResultsCard
              lab={healthSummary.recentLabs[0]}
              onDownload={() => downloadHealthRecord("labs")}
              onShare={() => {}}
            />
          )}
        </TabsContent>

        <TabsContent value="visits" className="mt-6 space-y-4">
          {healthSummary?.visits.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No visit history available
              </CardContent>
            </Card>
          ) : (
            healthSummary?.visits.map((visit) => (
              <VisitCard key={visit.id} visit={visit} onViewDetails={() => {}} />
            ))
          )}
        </TabsContent>

        <TabsContent value="labs" className="mt-6 space-y-4">
          {healthSummary?.recentLabs.map((lab) => (
            <LabResultsCard
              key={lab.id}
              lab={lab}
              onDownload={() => downloadHealthRecord("labs")}
              onShare={() => {}}
            />
          ))}
        </TabsContent>

        <TabsContent value="medications" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">MEDICATION HISTORY</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                View your current and past medications in the Medications section.
              </p>
              <Button variant="link" className="px-0 mt-2">
                Go to Medications <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="immunizations" className="mt-6 space-y-3">
          {healthSummary?.immunizations.map((imm) => (
            <ImmunizationCard key={imm.id} immunization={imm} />
          ))}
          {healthSummary?.immunizations.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No immunization records available
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default HealthRecords;

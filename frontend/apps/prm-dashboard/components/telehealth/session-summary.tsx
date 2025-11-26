"use client";

// Session Summary & Patient Feedback Components
// EPIC-UX-008: Telehealth Experience

import React, { useState, useCallback } from "react";
import { format } from "date-fns";
import {
  Check,
  Clock,
  FileText,
  Calendar,
  Edit,
  Copy,
  ChevronRight,
  Star,
  Loader2,
  Video,
  CheckCircle2,
  AlertCircle,
  Download,
  Sparkles,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useTelehealthStore,
  type SessionSummary,
  type PatientFeedback,
} from "@/lib/store/telehealth-store";

// ============================================================================
// Types
// ============================================================================

interface ProviderSessionSummaryProps {
  patientName: string;
  duration: number;
  recordingSaved: boolean;
  onStartDocumentation: () => void;
  onScheduleFollowUp: () => void;
  onDone: () => void;
}

interface PatientFeedbackFormProps {
  providerName: string;
  onSubmit: (feedback: Omit<PatientFeedback, "sessionId" | "submittedAt">) => void;
  onSkip: () => void;
}

// ============================================================================
// Provider Session Summary
// ============================================================================

export function ProviderSessionSummary({
  patientName,
  duration,
  recordingSaved,
  onStartDocumentation,
  onScheduleFollowUp,
  onDone,
}: ProviderSessionSummaryProps) {
  const [isEditing, setIsEditing] = useState(false);
  const { sessionSummary, isGeneratingSummary } = useTelehealthStore();

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} minute${mins !== 1 ? "s" : ""} ${secs} second${secs !== 1 ? "s" : ""}`;
  };

  // Next steps checklist
  const [nextSteps, setNextSteps] = useState({
    documentation: false,
    followUp: false,
    reviewLabs: false,
  });

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <CheckCircle2 className="h-8 w-8 text-green-600" />
        </div>
        <h1 className="text-2xl font-semibold mb-2">Session Complete</h1>
        <p className="text-muted-foreground">
          Telehealth session with {patientName} completed
        </p>
      </div>

      {/* Session Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Clock className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
            <p className="text-lg font-semibold">{formatDuration(duration)}</p>
            <p className="text-xs text-muted-foreground">Duration</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Video className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
            <p className="text-lg font-semibold">
              {recordingSaved ? "Saved" : "N/A"}
            </p>
            <p className="text-xs text-muted-foreground">Recording</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <FileText className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
            <p className="text-lg font-semibold">Available</p>
            <p className="text-xs text-muted-foreground">Transcription</p>
          </CardContent>
        </Card>
      </div>

      {/* AI-Generated Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-600" />
              AI-Generated Visit Summary
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
            >
              <Edit className="h-4 w-4 mr-1" />
              {isEditing ? "Done" : "Edit"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isGeneratingSummary ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>Generating summary...</span>
            </div>
          ) : sessionSummary ? (
            <>
              {/* Chief Complaint */}
              <div>
                <Label className="text-xs text-muted-foreground">
                  Chief Complaint
                </Label>
                {isEditing ? (
                  <Textarea
                    defaultValue={sessionSummary.chiefComplaint}
                    className="mt-1"
                  />
                ) : (
                  <p className="text-sm mt-1">{sessionSummary.chiefComplaint}</p>
                )}
              </div>

              {/* Key Points */}
              <div>
                <Label className="text-xs text-muted-foreground">
                  Key Points Discussed
                </Label>
                {isEditing ? (
                  <Textarea
                    defaultValue={sessionSummary.keyPoints.join("\n• ")}
                    className="mt-1"
                  />
                ) : (
                  <ul className="list-disc list-inside text-sm mt-1 space-y-1">
                    {sessionSummary.keyPoints.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Patient Education */}
              <div>
                <Label className="text-xs text-muted-foreground">
                  Patient Education
                </Label>
                {isEditing ? (
                  <Textarea
                    defaultValue={sessionSummary.patientEducation.join("\n• ")}
                    className="mt-1"
                  />
                ) : (
                  <ul className="list-disc list-inside text-sm mt-1 space-y-1">
                    {sessionSummary.patientEducation.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>

              {/* AI Notes */}
              <Separator />
              <div className="bg-muted/50 p-4 rounded-lg">
                <Label className="text-xs text-muted-foreground">
                  AI-Generated Clinical Note Draft
                </Label>
                {isEditing ? (
                  <Textarea
                    defaultValue={sessionSummary.aiGeneratedNotes}
                    className="mt-2 min-h-[100px]"
                  />
                ) : (
                  <p className="text-sm mt-2 whitespace-pre-wrap">
                    {sessionSummary.aiGeneratedNotes}
                  </p>
                )}
              </div>

              <Button className="w-full" onClick={onStartDocumentation}>
                <FileText className="h-4 w-4 mr-2" />
                Use for Clinical Note →
              </Button>
            </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>Summary not available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Next Steps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-3">
            <Checkbox
              id="documentation"
              checked={nextSteps.documentation}
              onCheckedChange={(c) =>
                setNextSteps({ ...nextSteps, documentation: !!c })
              }
            />
            <Label
              htmlFor="documentation"
              className={cn(
                "text-sm cursor-pointer",
                nextSteps.documentation && "line-through text-muted-foreground"
              )}
            >
              Complete clinical note (Required within 24 hours)
            </Label>
          </div>
          <div className="flex items-center gap-3">
            <Checkbox
              id="followUp"
              checked={nextSteps.followUp}
              onCheckedChange={(c) =>
                setNextSteps({ ...nextSteps, followUp: !!c })
              }
            />
            <Label
              htmlFor="followUp"
              className={cn(
                "text-sm cursor-pointer",
                nextSteps.followUp && "line-through text-muted-foreground"
              )}
            >
              Schedule follow-up appointment
            </Label>
          </div>
          <div className="flex items-center gap-3">
            <Checkbox
              id="reviewLabs"
              checked={nextSteps.reviewLabs}
              onCheckedChange={(c) =>
                setNextSteps({ ...nextSteps, reviewLabs: !!c })
              }
            />
            <Label
              htmlFor="reviewLabs"
              className={cn(
                "text-sm cursor-pointer",
                nextSteps.reviewLabs && "line-through text-muted-foreground"
              )}
            >
              Review lab results when available
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={onScheduleFollowUp}>
          <Calendar className="h-4 w-4 mr-2" />
          Schedule Follow-up
        </Button>
        <Button onClick={onDone}>
          Done
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Patient Feedback Form
// ============================================================================

export function PatientFeedbackForm({
  providerName,
  onSubmit,
  onSkip,
}: PatientFeedbackFormProps) {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [videoQuality, setVideoQuality] = useState<string>("");
  const [audioQuality, setAudioQuality] = useState<string>("");
  const [doctorExperience, setDoctorExperience] = useState<string>("");
  const [comments, setComments] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = useCallback(async () => {
    if (rating === 0) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        overallRating: rating,
        videoQuality: videoQuality as PatientFeedback["videoQuality"],
        audioQuality: audioQuality as PatientFeedback["audioQuality"],
        doctorExperience: doctorExperience as PatientFeedback["doctorExperience"],
        comments: comments || undefined,
      });
    } finally {
      setIsSubmitting(false);
    }
  }, [rating, videoQuality, audioQuality, doctorExperience, comments, onSubmit]);

  return (
    <div className="max-w-lg mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <Check className="h-8 w-8 text-green-600" />
        </div>
        <h1 className="text-2xl font-semibold mb-2">Your visit is complete</h1>
      </div>

      {/* Feedback Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-center">How was your visit?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Star Rating */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  className="p-1 transition-transform hover:scale-110"
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                >
                  <Star
                    className={cn(
                      "h-8 w-8 transition-colors",
                      (hoverRating || rating) >= star
                        ? "fill-amber-400 text-amber-400"
                        : "text-muted-foreground"
                    )}
                  />
                </button>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">
              {rating === 0
                ? "Tap to rate"
                : rating <= 2
                ? "We're sorry to hear that"
                : rating === 3
                ? "Thanks for your feedback"
                : rating === 4
                ? "Glad you had a good experience"
                : "Excellent! Thank you!"}
            </p>
          </div>

          {rating > 0 && (
            <>
              <Separator />

              {/* Quality Ratings */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm">Video Quality</Label>
                  <Select value={videoQuality} onValueChange={setVideoQuality}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select rating" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="excellent">Excellent</SelectItem>
                      <SelectItem value="good">Good</SelectItem>
                      <SelectItem value="fair">Fair</SelectItem>
                      <SelectItem value="poor">Poor</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm">Audio Quality</Label>
                  <Select value={audioQuality} onValueChange={setAudioQuality}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select rating" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="excellent">Excellent</SelectItem>
                      <SelectItem value="good">Good</SelectItem>
                      <SelectItem value="fair">Fair</SelectItem>
                      <SelectItem value="poor">Poor</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm">Doctor Experience</Label>
                  <Select value={doctorExperience} onValueChange={setDoctorExperience}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select rating" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="excellent">Excellent</SelectItem>
                      <SelectItem value="good">Good</SelectItem>
                      <SelectItem value="fair">Fair</SelectItem>
                      <SelectItem value="poor">Poor</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Comments */}
              <div className="space-y-2">
                <Label className="text-sm">Comments (optional)</Label>
                <Textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Tell us more about your experience..."
                  rows={3}
                />
              </div>
            </>
          )}

          {/* Submit Button */}
          <Button
            className="w-full"
            disabled={rating === 0 || isSubmitting}
            onClick={handleSubmit}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              "Submit Feedback"
            )}
          </Button>
        </CardContent>
      </Card>

      {/* What's Next */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">What's Next</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>• Your visit summary will be available in your patient portal</p>
          <p>• Any prescriptions will be sent to your pharmacy</p>
          <p>• Follow-up appointment: Dec 23, 2024 at 2:00 PM</p>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onSkip}>
          Skip
        </Button>
        <div className="flex gap-2">
          <Button variant="outline">View Visit Summary</Button>
          <Button variant="outline">Go to Patient Portal</Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Visit Complete Dialog (for quick dismissal)
// ============================================================================

interface VisitCompleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  providerName: string;
  followUpDate?: string;
  onViewSummary: () => void;
  onClose: () => void;
}

export function VisitCompleteDialog({
  open,
  onOpenChange,
  providerName,
  followUpDate,
  onViewSummary,
  onClose,
}: VisitCompleteDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-2">
            <Check className="h-6 w-6 text-green-600" />
          </div>
          <DialogTitle>Visit Complete</DialogTitle>
          <DialogDescription>
            Your telehealth visit with {providerName} has ended.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="p-4 bg-muted/50 rounded-lg space-y-2">
            <p className="text-sm">
              <strong>Visit summary</strong> will be available in your patient portal
            </p>
            {followUpDate && (
              <p className="text-sm">
                <strong>Follow-up:</strong> {followUpDate}
              </p>
            )}
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" className="flex-1" onClick={onViewSummary}>
            View Summary
          </Button>
          <Button className="flex-1" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Session Summary Skeleton
// ============================================================================

export function SessionSummarySkeleton() {
  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6 animate-pulse">
      <div className="text-center">
        <div className="w-16 h-16 bg-muted rounded-full mx-auto mb-4" />
        <div className="h-7 w-48 bg-muted rounded mx-auto mb-2" />
        <div className="h-5 w-64 bg-muted rounded mx-auto" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="border rounded-lg p-4">
            <div className="h-5 w-5 bg-muted rounded mx-auto mb-2" />
            <div className="h-6 w-16 bg-muted rounded mx-auto mb-1" />
            <div className="h-3 w-12 bg-muted rounded mx-auto" />
          </div>
        ))}
      </div>

      <div className="border rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-5 w-40 bg-muted rounded" />
          <div className="h-8 w-16 bg-muted rounded" />
        </div>
        <div className="space-y-3">
          <div className="h-4 w-24 bg-muted rounded" />
          <div className="h-4 w-full bg-muted rounded" />
          <div className="h-4 w-full bg-muted rounded" />
          <div className="h-4 w-3/4 bg-muted rounded" />
        </div>
      </div>
    </div>
  );
}

export default ProviderSessionSummary;

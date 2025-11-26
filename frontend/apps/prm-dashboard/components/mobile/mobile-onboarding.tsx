"use client";

// Mobile Onboarding Flow
// EPIC-UX-012: Mobile Applications - Journey 12.1

import React, { useState } from "react";
import {
  Building2, Lock, Bell, Heart, ChevronRight, ChevronLeft, Check, Fingerprint,
  Smartphone, Shield, Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useMobileStore } from "@/lib/store/mobile-store";

// Onboarding step interface
interface OnboardingStep {
  id: string;
  icon: typeof Building2;
  title: string;
  description: string;
  action?: string;
  skipText?: string;
  onAction?: () => Promise<void>;
  onSkip?: () => void;
}

// Step indicator dots
function StepIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="flex items-center justify-center gap-2">
      {Array.from({ length: totalSteps }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-2 w-2 rounded-full transition-colors",
            i === currentStep ? "bg-primary w-6" : i < currentStep ? "bg-primary/60" : "bg-muted"
          )}
        />
      ))}
    </div>
  );
}

// Welcome screen
function WelcomeScreen({ onGetStarted }: { onGetStarted: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center">
      <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-8">
        <Building2 className="h-12 w-12 text-primary" />
      </div>
      <h1 className="text-3xl font-bold mb-4">Your Health, Your Way</h1>
      <p className="text-muted-foreground max-w-sm mb-8">
        Access your health records, book appointments, and message your doctor - all from your phone
      </p>
      <StepIndicator currentStep={0} totalSteps={4} />
      <Button size="lg" className="mt-8 w-full max-w-xs" onClick={onGetStarted}>
        Get Started
        <ChevronRight className="h-5 w-5 ml-2" />
      </Button>
    </div>
  );
}

// Biometric setup screen
function BiometricScreen({ onEnable, onSkip }: { onEnable: () => void; onSkip: () => void }) {
  const [isEnabling, setIsEnabling] = useState(false);

  const handleEnable = async () => {
    setIsEnabling(true);
    // Simulate biometric setup
    await new Promise((r) => setTimeout(r, 1000));
    onEnable();
    setIsEnabling(false);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center">
      <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-8">
        <Fingerprint className="h-12 w-12 text-primary" />
      </div>
      <h1 className="text-2xl font-bold mb-4">Secure Access</h1>
      <p className="text-muted-foreground max-w-sm mb-8">
        Use Face ID or fingerprint for quick, secure access to your health data
      </p>
      <StepIndicator currentStep={1} totalSteps={4} />
      <div className="space-y-3 mt-8 w-full max-w-xs">
        <Button size="lg" className="w-full" onClick={handleEnable} disabled={isEnabling}>
          {isEnabling ? "Setting up..." : "Enable Face ID"}
        </Button>
        <Button variant="ghost" size="lg" className="w-full" onClick={onSkip}>
          Skip for now
        </Button>
      </div>
    </div>
  );
}

// Notification permission screen
function NotificationScreen({ onEnable, onSkip }: { onEnable: () => void; onSkip: () => void }) {
  const [isEnabling, setIsEnabling] = useState(false);

  const handleEnable = async () => {
    setIsEnabling(true);
    await new Promise((r) => setTimeout(r, 500));
    onEnable();
    setIsEnabling(false);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center">
      <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-8">
        <Bell className="h-12 w-12 text-primary" />
      </div>
      <h1 className="text-2xl font-bold mb-4">Stay Informed</h1>
      <p className="text-muted-foreground max-w-sm mb-4">
        Get reminders for appointments and important health updates
      </p>
      <div className="text-left max-w-xs space-y-2 mb-6">
        <div className="flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500" />
          <span>Appointment reminders</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500" />
          <span>Medication alerts</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500" />
          <span>Lab results ready</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-500" />
          <span>Messages from your doctor</span>
        </div>
      </div>
      <StepIndicator currentStep={2} totalSteps={4} />
      <div className="space-y-3 mt-8 w-full max-w-xs">
        <Button size="lg" className="w-full" onClick={handleEnable} disabled={isEnabling}>
          Enable Notifications
        </Button>
        <Button variant="ghost" size="lg" className="w-full" onClick={onSkip}>
          Not now
        </Button>
      </div>
    </div>
  );
}

// Health integration screen
function HealthScreen({ onEnable, onSkip }: { onEnable: () => void; onSkip: () => void }) {
  const [isEnabling, setIsEnabling] = useState(false);

  const handleEnable = async () => {
    setIsEnabling(true);
    await new Promise((r) => setTimeout(r, 1000));
    onEnable();
    setIsEnabling(false);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center">
      <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-8">
        <Activity className="h-12 w-12 text-primary" />
      </div>
      <h1 className="text-2xl font-bold mb-4">Connect Health Data</h1>
      <p className="text-muted-foreground max-w-sm mb-4">
        Share health data from your device to give your doctor a complete picture
      </p>
      <div className="text-left max-w-xs space-y-2 mb-6">
        <div className="flex items-center gap-2 text-sm">
          <Heart className="h-4 w-4 text-red-500" />
          <span>Heart rate & blood pressure</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Activity className="h-4 w-4 text-blue-500" />
          <span>Steps & activity</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Shield className="h-4 w-4 text-green-500" />
          <span>Your data stays private</span>
        </div>
      </div>
      <StepIndicator currentStep={3} totalSteps={4} />
      <div className="space-y-3 mt-8 w-full max-w-xs">
        <Button size="lg" className="w-full" onClick={handleEnable} disabled={isEnabling}>
          Connect Apple Health
        </Button>
        <Button variant="ghost" size="lg" className="w-full" onClick={onSkip}>
          Skip for now
        </Button>
      </div>
    </div>
  );
}

// Completion screen
function CompletionScreen({ onComplete }: { onComplete: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center">
      <div className="h-24 w-24 rounded-full bg-green-100 flex items-center justify-center mb-8">
        <Check className="h-12 w-12 text-green-600" />
      </div>
      <h1 className="text-2xl font-bold mb-4">You're All Set!</h1>
      <p className="text-muted-foreground max-w-sm mb-8">
        Your Surya Patient Portal is ready. Explore your health dashboard and stay connected with your care team.
      </p>
      <div className="grid grid-cols-2 gap-3 max-w-xs w-full mb-8">
        {[
          { icon: Smartphone, label: "View Records" },
          { icon: Bell, label: "Get Reminders" },
          { icon: Building2, label: "Book Visits" },
          { icon: Shield, label: "Stay Secure" },
        ].map((item, i) => (
          <Card key={i}>
            <CardContent className="p-3 text-center">
              <item.icon className="h-6 w-6 mx-auto mb-1 text-primary" />
              <span className="text-xs">{item.label}</span>
            </CardContent>
          </Card>
        ))}
      </div>
      <Button size="lg" className="w-full max-w-xs" onClick={onComplete}>
        Go to Dashboard
        <ChevronRight className="h-5 w-5 ml-2" />
      </Button>
    </div>
  );
}

// Main Onboarding Component
export function MobileOnboarding({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const {
    enableBiometrics,
    enablePushNotifications,
    setupHealthIntegration,
    completeOnboarding,
  } = useMobileStore();

  const handleComplete = () => {
    completeOnboarding();
    onComplete();
  };

  const screens = [
    <WelcomeScreen key="welcome" onGetStarted={() => setStep(1)} />,
    <BiometricScreen
      key="biometric"
      onEnable={() => {
        enableBiometrics(true);
        setStep(2);
      }}
      onSkip={() => setStep(2)}
    />,
    <NotificationScreen
      key="notification"
      onEnable={async () => {
        await enablePushNotifications(true);
        setStep(3);
      }}
      onSkip={() => setStep(3)}
    />,
    <HealthScreen
      key="health"
      onEnable={async () => {
        await setupHealthIntegration("apple_health");
        setStep(4);
      }}
      onSkip={() => setStep(4)}
    />,
    <CompletionScreen key="complete" onComplete={handleComplete} />,
  ];

  return (
    <div className="min-h-screen bg-background">
      {step > 0 && step < screens.length - 1 && (
        <div className="absolute top-4 left-4 z-10">
          <Button variant="ghost" size="icon" onClick={() => setStep(step - 1)}>
            <ChevronLeft className="h-5 w-5" />
          </Button>
        </div>
      )}
      {screens[step]}
    </div>
  );
}

// Provider onboarding (simplified)
export function ProviderMobileOnboarding({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const { enableBiometrics, enablePushNotifications, completeOnboarding } = useMobileStore();

  const handleComplete = () => {
    completeOnboarding();
    onComplete();
  };

  if (step === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center">
        <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-8">
          <Building2 className="h-12 w-12 text-primary" />
        </div>
        <h1 className="text-3xl font-bold mb-4">Surya Provider</h1>
        <p className="text-muted-foreground max-w-sm mb-8">
          Access your schedule, patient charts, and care team communications on the go
        </p>
        <Button size="lg" className="w-full max-w-xs" onClick={() => setStep(1)}>
          Get Started
          <ChevronRight className="h-5 w-5 ml-2" />
        </Button>
      </div>
    );
  }

  if (step === 1) {
    return (
      <BiometricScreen
        onEnable={() => {
          enableBiometrics(true);
          setStep(2);
        }}
        onSkip={() => setStep(2)}
      />
    );
  }

  if (step === 2) {
    return (
      <NotificationScreen
        onEnable={async () => {
          await enablePushNotifications(true);
          handleComplete();
        }}
        onSkip={handleComplete}
      />
    );
  }

  return null;
}

export default MobileOnboarding;

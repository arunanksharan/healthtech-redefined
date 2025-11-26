"use client";

import * as React from "react";
import {
  Activity,
  Heart,
  Thermometer,
  Wind,
  Droplets,
  Scale,
  Ruler,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Check,
  X,
  Clock,
  History,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import {
  useClinicalWorkflowsStore,
  type VitalSigns,
  type VitalAbnormalFlag,
} from "@/lib/store/clinical-workflows-store";
import { format } from "date-fns";

// ============================================================================
// Types
// ============================================================================

interface VitalsEntryProps {
  patientId: string;
  patientName: string;
  previousVitals?: VitalSigns;
  onSave: (vitals: VitalSigns) => void;
  onCancel: () => void;
  className?: string;
}

interface VitalFieldProps {
  label: string;
  value: string | number | undefined;
  onChange: (value: string) => void;
  unit: string;
  icon: React.ReactNode;
  status?: "normal" | "low" | "high" | "critical-low" | "critical-high";
  previousValue?: string | number;
  previousChange?: "up" | "down" | "same";
  changeAmount?: string;
  required?: boolean;
  type?: "number" | "text";
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
}

// ============================================================================
// Vital Field Component
// ============================================================================

function VitalField({
  label,
  value,
  onChange,
  unit,
  icon,
  status = "normal",
  previousValue,
  previousChange,
  changeAmount,
  required = false,
  type = "number",
  placeholder,
  min,
  max,
  step,
  className,
}: VitalFieldProps) {
  const statusColors = {
    normal: "",
    low: "border-blue-500 bg-blue-500/5",
    high: "border-amber-500 bg-amber-500/5",
    "critical-low": "border-red-500 bg-red-500/10",
    "critical-high": "border-red-500 bg-red-500/10",
  };

  const statusBadges = {
    normal: null,
    low: <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/30">Low</Badge>,
    high: <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/30">Elevated</Badge>,
    "critical-low": <Badge variant="destructive">Critical Low</Badge>,
    "critical-high": <Badge variant="destructive">Critical High</Badge>,
  };

  const changeIcons = {
    up: <TrendingUp className="h-3 w-3 text-amber-500" />,
    down: <TrendingDown className="h-3 w-3 text-emerald-500" />,
    same: <Minus className="h-3 w-3 text-muted-foreground" />,
  };

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <Label className="flex items-center gap-2">
          {icon}
          {label}
          {required && <span className="text-red-500">*</span>}
        </Label>
        {status !== "normal" && statusBadges[status]}
      </div>
      <div className="relative">
        <Input
          type={type}
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          min={min}
          max={max}
          step={step}
          className={cn(
            "pr-12",
            statusColors[status]
          )}
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
          {unit}
        </span>
      </div>
      {previousValue !== undefined && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Previous: {previousValue}</span>
          {previousChange && (
            <>
              <span>•</span>
              {changeIcons[previousChange]}
              <span className={cn(
                previousChange === "up" && "text-amber-500",
                previousChange === "down" && "text-emerald-500"
              )}>
                {changeAmount}
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Pain Scale Component
// ============================================================================

interface PainScaleProps {
  value: number;
  onChange: (value: number) => void;
  location?: string;
  onLocationChange?: (location: string) => void;
}

function PainScale({ value, onChange, location, onLocationChange }: PainScaleProps) {
  const painDescriptions = [
    { level: 0, label: "No Pain", color: "bg-emerald-500" },
    { level: 1, label: "Minimal", color: "bg-emerald-400" },
    { level: 2, label: "Mild", color: "bg-lime-400" },
    { level: 3, label: "Uncomfortable", color: "bg-yellow-400" },
    { level: 4, label: "Moderate", color: "bg-amber-400" },
    { level: 5, label: "Distracting", color: "bg-amber-500" },
    { level: 6, label: "Distressing", color: "bg-orange-400" },
    { level: 7, label: "Unmanageable", color: "bg-orange-500" },
    { level: 8, label: "Intense", color: "bg-red-400" },
    { level: 9, label: "Severe", color: "bg-red-500" },
    { level: 10, label: "Worst Possible", color: "bg-red-600" },
  ];

  const currentDescription = painDescriptions.find((p) => p.level === value);

  return (
    <div className="space-y-4">
      <Label className="flex items-center gap-2">
        Pain Level (0-10)
      </Label>
      <div className="flex gap-1">
        {painDescriptions.map((pain) => (
          <TooltipProvider key={pain.level}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  className={cn(
                    "w-8 h-8 rounded-full text-xs font-medium transition-all",
                    pain.color,
                    value === pain.level ? "ring-2 ring-offset-2 ring-primary scale-110" : "opacity-60 hover:opacity-100"
                  )}
                  onClick={() => onChange(pain.level)}
                >
                  {pain.level}
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{pain.label}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ))}
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm">
          Selected: <span className="font-medium">{value}</span> - {currentDescription?.label}
        </span>
        {value > 0 && onLocationChange && (
          <div className="flex-1">
            <Select value={location || ""} onValueChange={onLocationChange}>
              <SelectTrigger className="h-8">
                <SelectValue placeholder="Select pain location..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="head">Head</SelectItem>
                <SelectItem value="chest">Chest</SelectItem>
                <SelectItem value="abdomen">Abdomen</SelectItem>
                <SelectItem value="back">Back</SelectItem>
                <SelectItem value="neck">Neck</SelectItem>
                <SelectItem value="shoulder">Shoulder</SelectItem>
                <SelectItem value="arm">Arm</SelectItem>
                <SelectItem value="leg">Leg</SelectItem>
                <SelectItem value="knee">Knee</SelectItem>
                <SelectItem value="foot">Foot</SelectItem>
                <SelectItem value="generalized">Generalized</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Vitals Trends Component
// ============================================================================

interface VitalsTrendsProps {
  currentVitals: Partial<VitalSigns>;
  previousVitals?: VitalSigns;
}

function VitalsTrends({ currentVitals, previousVitals }: VitalsTrendsProps) {
  if (!previousVitals) return null;

  const trends = [];

  // Blood Pressure trend
  if (currentVitals.bloodPressure && previousVitals.bloodPressure) {
    const sysDiff = currentVitals.bloodPressure.systolic - previousVitals.bloodPressure.systolic;
    const diaDiff = currentVitals.bloodPressure.diastolic - previousVitals.bloodPressure.diastolic;
    trends.push({
      label: "BP",
      previous: `${previousVitals.bloodPressure.systolic}/${previousVitals.bloodPressure.diastolic}`,
      current: `${currentVitals.bloodPressure.systolic}/${currentVitals.bloodPressure.diastolic}`,
      change: sysDiff > 0 ? "up" : sysDiff < 0 ? "down" : "same",
      isGood: sysDiff <= 0,
    });
  }

  // Weight trend
  if (currentVitals.weight && previousVitals.weight) {
    const diff = currentVitals.weight.value - previousVitals.weight.value;
    trends.push({
      label: "Weight",
      previous: `${previousVitals.weight.value} ${previousVitals.weight.unit}`,
      current: `${currentVitals.weight.value} ${currentVitals.weight.unit}`,
      change: diff > 0 ? "up" : diff < 0 ? "down" : "same",
      changeAmount: diff !== 0 ? `${diff > 0 ? "+" : ""}${diff.toFixed(1)} ${currentVitals.weight.unit}` : "",
      isGood: diff <= 0, // Generally, weight gain is a concern
    });
  }

  // BMI trend
  if (currentVitals.bmi && previousVitals.bmi) {
    const diff = currentVitals.bmi - previousVitals.bmi;
    trends.push({
      label: "BMI",
      previous: previousVitals.bmi.toFixed(1),
      current: currentVitals.bmi.toFixed(1),
      change: diff > 0 ? "up" : diff < 0 ? "down" : "same",
      changeAmount: diff !== 0 ? `${diff > 0 ? "+" : ""}${diff.toFixed(1)}` : "",
      isGood: diff <= 0,
    });
  }

  if (trends.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <History className="h-4 w-4" />
          Trends vs Previous Visit
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          {trends.map((trend, index) => (
            <div key={index} className="text-center p-2 bg-muted/50 rounded-lg">
              <p className="text-xs text-muted-foreground">{trend.label}</p>
              <div className="flex items-center justify-center gap-1 mt-1">
                <span className="text-sm">{trend.previous}</span>
                <span className="text-muted-foreground">→</span>
                <span className="text-sm font-medium">{trend.current}</span>
              </div>
              {trend.changeAmount && (
                <p className={cn(
                  "text-xs mt-1",
                  trend.isGood ? "text-emerald-500" : "text-amber-500"
                )}>
                  {trend.change === "up" ? <TrendingUp className="h-3 w-3 inline mr-1" /> : trend.change === "down" ? <TrendingDown className="h-3 w-3 inline mr-1" /> : null}
                  {trend.changeAmount}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Vitals Entry Component
// ============================================================================

export function VitalsEntry({
  patientId,
  patientName,
  previousVitals,
  onSave,
  onCancel,
  className,
}: VitalsEntryProps) {
  const { validateVitals, recordVitals } = useClinicalWorkflowsStore();

  // Form state
  const [bpSystolic, setBpSystolic] = React.useState("");
  const [bpDiastolic, setBpDiastolic] = React.useState("");
  const [bpPosition, setBpPosition] = React.useState<"sitting" | "standing" | "supine">("sitting");
  const [bpArm, setBpArm] = React.useState<"left" | "right">("left");
  const [heartRate, setHeartRate] = React.useState("");
  const [respiratoryRate, setRespiratoryRate] = React.useState("");
  const [temperature, setTemperature] = React.useState("");
  const [tempUnit, setTempUnit] = React.useState<"F" | "C">("F");
  const [tempLocation, setTempLocation] = React.useState<"oral" | "axillary" | "tympanic" | "rectal" | "temporal">("oral");
  const [oxygenSaturation, setOxygenSaturation] = React.useState("");
  const [weight, setWeight] = React.useState("");
  const [weightUnit, setWeightUnit] = React.useState<"lbs" | "kg">("lbs");
  const [height, setHeight] = React.useState("");
  const [heightUnit, setHeightUnit] = React.useState<"ft-in" | "cm">("ft-in");
  const [painLevel, setPainLevel] = React.useState(0);
  const [painLocation, setPainLocation] = React.useState("");
  const [bloodGlucose, setBloodGlucose] = React.useState("");
  const [glucoseTiming, setGlucoseTiming] = React.useState<"fasting" | "random" | "post-meal">("random");
  const [notes, setNotes] = React.useState("");

  // Calculated values
  const [bmi, setBmi] = React.useState<number | null>(null);
  const [abnormalFlags, setAbnormalFlags] = React.useState<VitalAbnormalFlag[]>([]);

  // Calculate BMI when weight or height changes
  React.useEffect(() => {
    if (weight && height) {
      let weightKg = parseFloat(weight);
      let heightM: number;

      if (weightUnit === "lbs") {
        weightKg = weightKg * 0.453592;
      }

      if (heightUnit === "ft-in") {
        // Parse "5'10" format
        const parts = height.match(/(\d+)'?(\d+)?/);
        if (parts) {
          const feet = parseInt(parts[1]);
          const inches = parseInt(parts[2] || "0");
          heightM = ((feet * 12) + inches) * 0.0254;
        } else {
          heightM = 0;
        }
      } else {
        heightM = parseFloat(height) / 100;
      }

      if (weightKg > 0 && heightM > 0) {
        const calculatedBmi = weightKg / (heightM * heightM);
        setBmi(Math.round(calculatedBmi * 10) / 10);
      }
    }
  }, [weight, weightUnit, height, heightUnit]);

  // Build vitals object and validate
  const buildVitals = (): Partial<VitalSigns> => {
    const vitals: Partial<VitalSigns> = {
      patientId,
      recordedById: "current-user",
    };

    if (bpSystolic && bpDiastolic) {
      vitals.bloodPressure = {
        systolic: parseInt(bpSystolic),
        diastolic: parseInt(bpDiastolic),
        position: bpPosition,
        arm: bpArm,
      };
    }

    if (heartRate) vitals.heartRate = parseInt(heartRate);
    if (respiratoryRate) vitals.respiratoryRate = parseInt(respiratoryRate);

    if (temperature) {
      vitals.temperature = {
        value: parseFloat(temperature),
        unit: tempUnit,
        location: tempLocation,
      };
    }

    if (oxygenSaturation) vitals.oxygenSaturation = parseInt(oxygenSaturation);

    if (weight) {
      vitals.weight = {
        value: parseFloat(weight),
        unit: weightUnit,
      };
    }

    if (height) {
      vitals.height = {
        value: height,
        unit: heightUnit,
      };
    }

    if (bmi) vitals.bmi = bmi;
    if (painLevel > 0) {
      vitals.painLevel = painLevel;
      vitals.painLocation = painLocation;
    }

    if (bloodGlucose) {
      vitals.bloodGlucose = {
        value: parseInt(bloodGlucose),
        timing: glucoseTiming,
      };
    }

    if (notes) vitals.notes = notes;

    return vitals;
  };

  // Validate on change
  React.useEffect(() => {
    const vitals = buildVitals();
    const flags = validateVitals(vitals);
    setAbnormalFlags(flags);
  }, [bpSystolic, bpDiastolic, heartRate, respiratoryRate, temperature, oxygenSaturation]);

  // Get status for a vital
  const getVitalStatus = (vitalName: string): "normal" | "low" | "high" | "critical-low" | "critical-high" => {
    const flag = abnormalFlags.find((f) => f.vital.toLowerCase().includes(vitalName.toLowerCase()));
    return flag?.status || "normal";
  };

  // Handle save
  const handleSave = () => {
    const vitals = buildVitals();
    vitals.abnormalFlags = abnormalFlags;
    recordVitals(vitals);
    onSave(vitals as VitalSigns);
  };

  // Get previous value with comparison
  const getPreviousComparison = (currentValue: number | undefined, previousValue: number | undefined) => {
    if (!currentValue || !previousValue) return { change: "same" as const, amount: "" };
    const diff = currentValue - previousValue;
    if (diff > 0) return { change: "up" as const, amount: `+${diff}` };
    if (diff < 0) return { change: "down" as const, amount: String(diff) };
    return { change: "same" as const, amount: "" };
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Record Vital Signs</CardTitle>
              <CardDescription>Patient: {patientName}</CardDescription>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{format(new Date(), "PPp")}</span>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Abnormal Flags Alert */}
      {abnormalFlags.length > 0 && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
              <div>
                <p className="font-medium text-amber-600 dark:text-amber-400">Abnormal Values Detected</p>
                <ul className="mt-2 space-y-1">
                  {abnormalFlags.map((flag, index) => (
                    <li key={index} className="text-sm text-muted-foreground">
                      {flag.vital}: {flag.value} - {flag.message}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Vitals Form */}
      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Blood Pressure */}
          <div className="space-y-4">
            <Label className="flex items-center gap-2 text-base font-medium">
              <Activity className="h-5 w-5 text-red-500" />
              Blood Pressure
            </Label>
            <div className="grid grid-cols-2 gap-4">
              <VitalField
                label="Systolic"
                value={bpSystolic}
                onChange={setBpSystolic}
                unit="mmHg"
                icon={<></>}
                status={getVitalStatus("systolic")}
                previousValue={previousVitals?.bloodPressure?.systolic}
                placeholder="120"
                min={60}
                max={250}
              />
              <VitalField
                label="Diastolic"
                value={bpDiastolic}
                onChange={setBpDiastolic}
                unit="mmHg"
                icon={<></>}
                status={getVitalStatus("diastolic")}
                previousValue={previousVitals?.bloodPressure?.diastolic}
                placeholder="80"
                min={40}
                max={150}
              />
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <Label className="text-sm">Position</Label>
                <Select value={bpPosition} onValueChange={(v) => setBpPosition(v as any)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sitting">Sitting</SelectItem>
                    <SelectItem value="standing">Standing</SelectItem>
                    <SelectItem value="supine">Supine</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <Label className="text-sm">Arm</Label>
                <Select value={bpArm} onValueChange={(v) => setBpArm(v as any)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="left">Left</SelectItem>
                    <SelectItem value="right">Right</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator />

          {/* Heart Rate, Temperature, Respiratory Rate */}
          <div className="grid grid-cols-3 gap-6">
            <VitalField
              label="Heart Rate"
              value={heartRate}
              onChange={setHeartRate}
              unit="bpm"
              icon={<Heart className="h-4 w-4 text-red-400" />}
              status={getVitalStatus("heart")}
              previousValue={previousVitals?.heartRate}
              placeholder="72"
              min={30}
              max={220}
            />
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Thermometer className="h-4 w-4 text-orange-400" />
                Temperature
              </Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  placeholder="98.6"
                  step="0.1"
                  className="flex-1"
                />
                <Select value={tempUnit} onValueChange={(v) => setTempUnit(v as any)}>
                  <SelectTrigger className="w-16">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="F">°F</SelectItem>
                    <SelectItem value="C">°C</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <VitalField
              label="Respiratory Rate"
              value={respiratoryRate}
              onChange={setRespiratoryRate}
              unit="/min"
              icon={<Wind className="h-4 w-4 text-blue-400" />}
              placeholder="16"
              min={8}
              max={40}
            />
          </div>

          <Separator />

          {/* Weight, Height, SpO2 */}
          <div className="grid grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Scale className="h-4 w-4 text-purple-400" />
                Weight
              </Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  placeholder="165"
                  step="0.1"
                  className="flex-1"
                />
                <Select value={weightUnit} onValueChange={(v) => setWeightUnit(v as any)}>
                  <SelectTrigger className="w-16">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lbs">lbs</SelectItem>
                    <SelectItem value="kg">kg</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {previousVitals?.weight && (
                <p className="text-xs text-muted-foreground">
                  Previous: {previousVitals.weight.value} {previousVitals.weight.unit}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Ruler className="h-4 w-4 text-teal-400" />
                Height
              </Label>
              <div className="flex gap-2">
                <Input
                  type="text"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  placeholder={heightUnit === "ft-in" ? "5'10" : "178"}
                  className="flex-1"
                />
                <Select value={heightUnit} onValueChange={(v) => setHeightUnit(v as any)}>
                  <SelectTrigger className="w-16">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ft-in">ft-in</SelectItem>
                    <SelectItem value="cm">cm</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {bmi && (
                <p className="text-xs text-muted-foreground">
                  BMI: <span className="font-medium">{bmi}</span> kg/m²
                  {bmi < 18.5 && " (Underweight)"}
                  {bmi >= 18.5 && bmi < 25 && " (Normal)"}
                  {bmi >= 25 && bmi < 30 && " (Overweight)"}
                  {bmi >= 30 && " (Obese)"}
                </p>
              )}
            </div>
            <VitalField
              label="SpO2"
              value={oxygenSaturation}
              onChange={setOxygenSaturation}
              unit="%"
              icon={<Droplets className="h-4 w-4 text-cyan-400" />}
              status={getVitalStatus("spo2")}
              previousValue={previousVitals?.oxygenSaturation}
              placeholder="98"
              min={70}
              max={100}
            />
          </div>

          <Separator />

          {/* Pain Level */}
          <PainScale
            value={painLevel}
            onChange={setPainLevel}
            location={painLocation}
            onLocationChange={setPainLocation}
          />

          <Separator />

          {/* Blood Glucose (Optional) */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Droplets className="h-4 w-4 text-rose-400" />
              Blood Glucose (Optional)
            </Label>
            <div className="flex gap-4">
              <Input
                type="number"
                value={bloodGlucose}
                onChange={(e) => setBloodGlucose(e.target.value)}
                placeholder="100"
                className="w-24"
              />
              <span className="flex items-center text-sm text-muted-foreground">mg/dL</span>
              <Select value={glucoseTiming} onValueChange={(v) => setGlucoseTiming(v as any)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fasting">Fasting</SelectItem>
                  <SelectItem value="random">Random</SelectItem>
                  <SelectItem value="post-meal">Post-meal</SelectItem>
                </SelectContent>
              </Select>
              {bloodGlucose && parseInt(bloodGlucose) > 140 && (
                <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/30">
                  Monitor
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trends */}
      <VitalsTrends
        currentVitals={buildVitals()}
        previousVitals={previousVitals}
      />

      {/* Actions */}
      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave}>
          <Check className="h-4 w-4 mr-2" />
          Save Vitals
        </Button>
      </div>
    </div>
  );
}

export default VitalsEntry;

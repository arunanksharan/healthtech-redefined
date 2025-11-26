// Telehealth Store
// EPIC-UX-008: Telehealth Experience

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// ============================================================================
// Types
// ============================================================================

export type DeviceType = "camera" | "microphone" | "speaker";
export type SessionStatus = "scheduled" | "waiting" | "in_progress" | "completed" | "cancelled";
export type NetworkQuality = "excellent" | "good" | "fair" | "poor";
export type ParticipantRole = "provider" | "patient";
export type RecordingStatus = "inactive" | "recording" | "paused" | "stopped";

export interface DeviceInfo {
  deviceId: string;
  label: string;
  kind: MediaDeviceKind;
}

export interface DeviceStatus {
  camera: {
    available: boolean;
    selected: DeviceInfo | null;
    stream: MediaStream | null;
    error: string | null;
  };
  microphone: {
    available: boolean;
    selected: DeviceInfo | null;
    stream: MediaStream | null;
    error: string | null;
    level: number; // Audio level 0-100
  };
  speaker: {
    available: boolean;
    selected: DeviceInfo | null;
    tested: boolean;
    error: string | null;
  };
  network: {
    quality: NetworkQuality;
    downloadSpeed: number; // Mbps
    uploadSpeed: number; // Mbps
    latency: number; // ms
    tested: boolean;
  };
}

export interface TelehealthSession {
  id: string;
  appointmentId: string;
  patient: {
    id: string;
    name: string;
    mrn: string;
    dob: string;
    photo?: string;
  };
  provider: {
    id: string;
    name: string;
    specialty: string;
    photo?: string;
  };
  appointmentTime: string;
  reason: string;
  status: SessionStatus;
  deviceCheckPassed: boolean;
  consentObtained: boolean;
  recordingEnabled: boolean;
  transcriptionEnabled: boolean;
  joinedAt?: string;
  endedAt?: string;
  duration?: number; // seconds
  waitingTime?: number; // seconds
}

export interface WaitingRoomPatient {
  sessionId: string;
  patient: {
    id: string;
    name: string;
    photo?: string;
  };
  appointmentTime: string;
  reason: string;
  waitingSince: string;
  waitingDuration: number; // seconds
  deviceCheckPassed: boolean;
  position: number;
}

export interface Participant {
  id: string;
  name: string;
  role: ParticipantRole;
  videoEnabled: boolean;
  audioEnabled: boolean;
  isScreenSharing: boolean;
  isSpeaking: boolean;
  networkQuality: NetworkQuality;
}

export interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: string;
  type: "text" | "system";
}

export interface TranscriptionEntry {
  id: string;
  speakerId: string;
  speakerName: string;
  speakerRole: ParticipantRole;
  content: string;
  timestamp: string;
  confidence: number;
}

export interface AISuggestion {
  id: string;
  type: "note" | "alert" | "action";
  content: string;
  source: string; // e.g., "Based on transcription"
  timestamp: string;
  accepted?: boolean;
}

export interface SessionSummary {
  sessionId: string;
  duration: number;
  chiefComplaint: string;
  keyPoints: string[];
  patientEducation: string[];
  aiGeneratedNotes: string;
  followUpRecommendations: string[];
  generatedAt: string;
}

export interface PatientFeedback {
  sessionId: string;
  overallRating: number; // 1-5
  videoQuality: "poor" | "fair" | "good" | "excellent";
  audioQuality: "poor" | "fair" | "good" | "excellent";
  doctorExperience: "poor" | "fair" | "good" | "excellent";
  comments?: string;
  submittedAt: string;
}

export interface Recording {
  id: string;
  sessionId: string;
  status: RecordingStatus;
  startedAt?: string;
  duration: number;
  url?: string;
  consentObtained: boolean;
}

// ============================================================================
// State Interface
// ============================================================================

interface TelehealthState {
  // Sessions
  sessions: TelehealthSession[];
  activeSession: TelehealthSession | null;
  todaySessions: TelehealthSession[];

  // Waiting Room
  waitingRoom: WaitingRoomPatient[];
  patientWaitingStatus: {
    isWaiting: boolean;
    position: number;
    estimatedWait: number;
  } | null;

  // Device Status
  deviceStatus: DeviceStatus;
  availableDevices: {
    cameras: DeviceInfo[];
    microphones: DeviceInfo[];
    speakers: DeviceInfo[];
  };

  // Call State
  isInCall: boolean;
  participants: Participant[];
  localParticipant: Participant | null;
  remoteParticipant: Participant | null;

  // Recording
  recording: Recording | null;

  // Chat & Transcription
  chatMessages: ChatMessage[];
  transcription: TranscriptionEntry[];
  aiSuggestions: AISuggestion[];

  // Session Summary
  sessionSummary: SessionSummary | null;

  // UI State
  showPatientChart: boolean;
  showTranscription: boolean;
  showChat: boolean;
  isScreenSharing: boolean;
  isPictureInPicture: boolean;

  // Loading States
  isLoadingSessions: boolean;
  isJoiningSession: boolean;
  isEndingSession: boolean;
  isGeneratingSummary: boolean;

  // LiveKit
  livekitUrl: string | null;
  livekitToken: string | null;

  // Actions
  fetchTodaySessions: () => Promise<void>;
  fetchWaitingRoom: () => Promise<void>;
  startDeviceCheck: () => Promise<void>;
  selectDevice: (type: DeviceType, deviceId: string) => Promise<void>;
  testSpeakers: () => Promise<void>;
  testNetwork: () => Promise<void>;
  joinWaitingRoom: (sessionId: string) => Promise<void>;
  leaveWaitingRoom: () => Promise<void>;
  startSession: (sessionId: string) => Promise<void>;
  joinSession: (sessionId: string, role: ParticipantRole) => Promise<void>;
  endSession: () => Promise<void>;
  toggleVideo: () => void;
  toggleAudio: () => void;
  startScreenShare: () => Promise<void>;
  stopScreenShare: () => void;
  sendChatMessage: (content: string) => void;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  togglePatientChart: () => void;
  toggleTranscription: () => void;
  toggleChat: () => void;
  acceptAISuggestion: (suggestionId: string) => void;
  rejectAISuggestion: (suggestionId: string) => void;
  generateSessionSummary: () => Promise<void>;
  submitFeedback: (feedback: Omit<PatientFeedback, "sessionId" | "submittedAt">) => Promise<void>;
  setConsentObtained: (sessionId: string, consent: boolean) => void;
  setRecordingEnabled: (enabled: boolean) => void;
  setTranscriptionEnabled: (enabled: boolean) => void;
  resetCallState: () => void;
}

// ============================================================================
// Mock Data Generators
// ============================================================================

function generateMockSessions(): TelehealthSession[] {
  const now = new Date();
  const baseDate = new Date(now);
  baseDate.setHours(14, 0, 0, 0);

  const patients = [
    { id: "pat-1", name: "John Doe", mrn: "12345", dob: "1965-03-15" },
    { id: "pat-2", name: "Jane Smith", mrn: "12346", dob: "1978-07-22" },
    { id: "pat-3", name: "Bob Wilson", mrn: "12347", dob: "1982-11-08" },
    { id: "pat-4", name: "Mary Johnson", mrn: "12348", dob: "1955-05-30" },
    { id: "pat-5", name: "David Lee", mrn: "12349", dob: "1990-01-12" },
  ];

  const reasons = [
    "Cardiology Follow-up",
    "Diabetes Consult",
    "Initial Consult",
    "Medication Review",
    "Urgent - Chest Pain",
  ];

  return patients.map((patient, i) => {
    const appointmentTime = new Date(baseDate);
    appointmentTime.setMinutes(i * 30);

    let status: SessionStatus = "scheduled";
    if (i === 0) status = "waiting";
    if (i === 1) status = "waiting";

    return {
      id: `session-${i + 1}`,
      appointmentId: `appt-${i + 1}`,
      patient,
      provider: {
        id: "prov-1",
        name: "Dr. Rohit Sharma",
        specialty: "Cardiology",
      },
      appointmentTime: appointmentTime.toISOString(),
      reason: reasons[i],
      status,
      deviceCheckPassed: status === "waiting",
      consentObtained: status === "waiting",
      recordingEnabled: true,
      transcriptionEnabled: true,
    };
  });
}

function generateMockWaitingRoom(): WaitingRoomPatient[] {
  const now = new Date();

  return [
    {
      sessionId: "session-1",
      patient: { id: "pat-1", name: "John Doe" },
      appointmentTime: new Date(now.getTime() - 5 * 60000).toISOString(),
      reason: "Cardiology Follow-up",
      waitingSince: new Date(now.getTime() - 5 * 60000).toISOString(),
      waitingDuration: 300,
      deviceCheckPassed: true,
      position: 1,
    },
    {
      sessionId: "session-2",
      patient: { id: "pat-2", name: "Jane Smith" },
      appointmentTime: new Date(now.getTime() + 25 * 60000).toISOString(),
      reason: "Diabetes Consult",
      waitingSince: new Date(now.getTime() - 2 * 60000).toISOString(),
      waitingDuration: 120,
      deviceCheckPassed: false,
      position: 2,
    },
  ];
}

// ============================================================================
// Initial State
// ============================================================================

const initialDeviceStatus: DeviceStatus = {
  camera: {
    available: false,
    selected: null,
    stream: null,
    error: null,
  },
  microphone: {
    available: false,
    selected: null,
    stream: null,
    error: null,
    level: 0,
  },
  speaker: {
    available: false,
    selected: null,
    tested: false,
    error: null,
  },
  network: {
    quality: "good",
    downloadSpeed: 0,
    uploadSpeed: 0,
    latency: 0,
    tested: false,
  },
};

// ============================================================================
// Store
// ============================================================================

export const useTelehealthStore = create<TelehealthState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial State
      sessions: [],
      activeSession: null,
      todaySessions: [],
      waitingRoom: [],
      patientWaitingStatus: null,
      deviceStatus: initialDeviceStatus,
      availableDevices: {
        cameras: [],
        microphones: [],
        speakers: [],
      },
      isInCall: false,
      participants: [],
      localParticipant: null,
      remoteParticipant: null,
      recording: null,
      chatMessages: [],
      transcription: [],
      aiSuggestions: [],
      sessionSummary: null,
      showPatientChart: true,
      showTranscription: true,
      showChat: false,
      isScreenSharing: false,
      isPictureInPicture: false,
      isLoadingSessions: false,
      isJoiningSession: false,
      isEndingSession: false,
      isGeneratingSummary: false,
      livekitUrl: null,
      livekitToken: null,

      // Actions
      fetchTodaySessions: async () => {
        set({ isLoadingSessions: true });
        try {
          // Simulate API call
          await new Promise((resolve) => setTimeout(resolve, 500));
          const sessions = generateMockSessions();
          set({
            sessions,
            todaySessions: sessions,
            isLoadingSessions: false,
          });
        } catch (error) {
          set({ isLoadingSessions: false });
          throw error;
        }
      },

      fetchWaitingRoom: async () => {
        try {
          await new Promise((resolve) => setTimeout(resolve, 300));
          const waitingRoom = generateMockWaitingRoom();
          set({ waitingRoom });
        } catch (error) {
          console.error("Failed to fetch waiting room:", error);
        }
      },

      startDeviceCheck: async () => {
        try {
          // Request permissions and enumerate devices
          const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true,
          });

          const devices = await navigator.mediaDevices.enumerateDevices();

          const cameras = devices
            .filter((d) => d.kind === "videoinput")
            .map((d) => ({
              deviceId: d.deviceId,
              label: d.label || `Camera ${d.deviceId.slice(0, 8)}`,
              kind: d.kind,
            }));

          const microphones = devices
            .filter((d) => d.kind === "audioinput")
            .map((d) => ({
              deviceId: d.deviceId,
              label: d.label || `Microphone ${d.deviceId.slice(0, 8)}`,
              kind: d.kind,
            }));

          const speakers = devices
            .filter((d) => d.kind === "audiooutput")
            .map((d) => ({
              deviceId: d.deviceId,
              label: d.label || `Speaker ${d.deviceId.slice(0, 8)}`,
              kind: d.kind,
            }));

          set({
            availableDevices: { cameras, microphones, speakers },
            deviceStatus: {
              camera: {
                available: cameras.length > 0,
                selected: cameras[0] || null,
                stream,
                error: null,
              },
              microphone: {
                available: microphones.length > 0,
                selected: microphones[0] || null,
                stream,
                error: null,
                level: 50,
              },
              speaker: {
                available: speakers.length > 0,
                selected: speakers[0] || null,
                tested: false,
                error: null,
              },
              network: {
                quality: "good",
                downloadSpeed: 45,
                uploadSpeed: 20,
                latency: 35,
                tested: false,
              },
            },
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : "Device access denied";
          set((state) => ({
            deviceStatus: {
              ...state.deviceStatus,
              camera: { ...state.deviceStatus.camera, error: errorMessage },
              microphone: { ...state.deviceStatus.microphone, error: errorMessage },
            },
          }));
        }
      },

      selectDevice: async (type, deviceId) => {
        const { availableDevices, deviceStatus } = get();

        if (type === "camera") {
          const device = availableDevices.cameras.find((d) => d.deviceId === deviceId);
          if (device) {
            // Stop existing stream
            deviceStatus.camera.stream?.getTracks().forEach((t) => t.stop());

            try {
              const stream = await navigator.mediaDevices.getUserMedia({
                video: { deviceId: { exact: deviceId } },
              });
              set((state) => ({
                deviceStatus: {
                  ...state.deviceStatus,
                  camera: {
                    ...state.deviceStatus.camera,
                    selected: device,
                    stream,
                    error: null,
                  },
                },
              }));
            } catch (error) {
              set((state) => ({
                deviceStatus: {
                  ...state.deviceStatus,
                  camera: {
                    ...state.deviceStatus.camera,
                    error: "Failed to switch camera",
                  },
                },
              }));
            }
          }
        } else if (type === "microphone") {
          const device = availableDevices.microphones.find((d) => d.deviceId === deviceId);
          if (device) {
            try {
              const stream = await navigator.mediaDevices.getUserMedia({
                audio: { deviceId: { exact: deviceId } },
              });
              set((state) => ({
                deviceStatus: {
                  ...state.deviceStatus,
                  microphone: {
                    ...state.deviceStatus.microphone,
                    selected: device,
                    stream,
                    error: null,
                  },
                },
              }));
            } catch (error) {
              set((state) => ({
                deviceStatus: {
                  ...state.deviceStatus,
                  microphone: {
                    ...state.deviceStatus.microphone,
                    error: "Failed to switch microphone",
                  },
                },
              }));
            }
          }
        } else if (type === "speaker") {
          const device = availableDevices.speakers.find((d) => d.deviceId === deviceId);
          if (device) {
            set((state) => ({
              deviceStatus: {
                ...state.deviceStatus,
                speaker: {
                  ...state.deviceStatus.speaker,
                  selected: device,
                  tested: false,
                },
              },
            }));
          }
        }
      },

      testSpeakers: async () => {
        // Play test sound
        const audioContext = new AudioContext();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        gainNode.gain.value = 0.1;
        oscillator.frequency.value = 440;
        oscillator.type = "sine";

        oscillator.start();
        setTimeout(() => {
          oscillator.stop();
          audioContext.close();
        }, 500);

        set((state) => ({
          deviceStatus: {
            ...state.deviceStatus,
            speaker: {
              ...state.deviceStatus.speaker,
              tested: true,
            },
          },
        }));
      },

      testNetwork: async () => {
        // Simulate network test
        await new Promise((resolve) => setTimeout(resolve, 2000));

        const downloadSpeed = Math.floor(Math.random() * 50) + 20;
        const uploadSpeed = Math.floor(Math.random() * 30) + 10;
        const latency = Math.floor(Math.random() * 50) + 20;

        let quality: NetworkQuality = "excellent";
        if (downloadSpeed < 10 || latency > 150) quality = "poor";
        else if (downloadSpeed < 25 || latency > 100) quality = "fair";
        else if (downloadSpeed < 40 || latency > 50) quality = "good";

        set((state) => ({
          deviceStatus: {
            ...state.deviceStatus,
            network: {
              quality,
              downloadSpeed,
              uploadSpeed,
              latency,
              tested: true,
            },
          },
        }));
      },

      joinWaitingRoom: async (sessionId) => {
        set({ isJoiningSession: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));

          const session = get().sessions.find((s) => s.id === sessionId);
          if (session) {
            set({
              activeSession: { ...session, status: "waiting" },
              patientWaitingStatus: {
                isWaiting: true,
                position: 1,
                estimatedWait: 300, // 5 minutes
              },
              isJoiningSession: false,
            });
          }
        } catch (error) {
          set({ isJoiningSession: false });
          throw error;
        }
      },

      leaveWaitingRoom: async () => {
        set({
          activeSession: null,
          patientWaitingStatus: null,
        });
      },

      startSession: async (sessionId) => {
        set({ isJoiningSession: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));

          const session = get().sessions.find((s) => s.id === sessionId);
          if (session) {
            // Generate mock LiveKit credentials
            const livekitUrl = "wss://demo.livekit.cloud";
            const livekitToken = `mock-token-${sessionId}`;

            set({
              activeSession: {
                ...session,
                status: "in_progress",
                joinedAt: new Date().toISOString(),
              },
              isInCall: true,
              livekitUrl,
              livekitToken,
              localParticipant: {
                id: session.provider.id,
                name: session.provider.name,
                role: "provider",
                videoEnabled: true,
                audioEnabled: true,
                isScreenSharing: false,
                isSpeaking: false,
                networkQuality: "good",
              },
              remoteParticipant: {
                id: session.patient.id,
                name: session.patient.name,
                role: "patient",
                videoEnabled: true,
                audioEnabled: true,
                isScreenSharing: false,
                isSpeaking: false,
                networkQuality: "good",
              },
              recording: session.recordingEnabled
                ? {
                    id: `rec-${sessionId}`,
                    sessionId,
                    status: "recording",
                    startedAt: new Date().toISOString(),
                    duration: 0,
                    consentObtained: session.consentObtained,
                  }
                : null,
              isJoiningSession: false,
            });

            // Start mock transcription
            if (session.transcriptionEnabled) {
              get().startMockTranscription();
            }
          }
        } catch (error) {
          set({ isJoiningSession: false });
          throw error;
        }
      },

      joinSession: async (sessionId, role) => {
        set({ isJoiningSession: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));

          const session = get().sessions.find((s) => s.id === sessionId);
          if (session) {
            const livekitUrl = "wss://demo.livekit.cloud";
            const livekitToken = `mock-token-${sessionId}-${role}`;

            const participant = role === "provider" ? session.provider : session.patient;

            set({
              activeSession: {
                ...session,
                status: "in_progress",
                joinedAt: new Date().toISOString(),
              },
              isInCall: true,
              livekitUrl,
              livekitToken,
              localParticipant: {
                id: participant.id,
                name: participant.name,
                role,
                videoEnabled: true,
                audioEnabled: true,
                isScreenSharing: false,
                isSpeaking: false,
                networkQuality: "good",
              },
              isJoiningSession: false,
            });
          }
        } catch (error) {
          set({ isJoiningSession: false });
          throw error;
        }
      },

      endSession: async () => {
        set({ isEndingSession: true });
        try {
          const { activeSession, recording } = get();

          // Stop recording if active
          if (recording?.status === "recording") {
            set((state) => ({
              recording: state.recording
                ? { ...state.recording, status: "stopped" }
                : null,
            }));
          }

          // Stop device streams
          const { deviceStatus } = get();
          deviceStatus.camera.stream?.getTracks().forEach((t) => t.stop());
          deviceStatus.microphone.stream?.getTracks().forEach((t) => t.stop());

          // Generate summary
          if (activeSession) {
            await get().generateSessionSummary();
          }

          set({
            activeSession: activeSession
              ? {
                  ...activeSession,
                  status: "completed",
                  endedAt: new Date().toISOString(),
                }
              : null,
            isInCall: false,
            isEndingSession: false,
          });
        } catch (error) {
          set({ isEndingSession: false });
          throw error;
        }
      },

      toggleVideo: () => {
        set((state) => ({
          localParticipant: state.localParticipant
            ? {
                ...state.localParticipant,
                videoEnabled: !state.localParticipant.videoEnabled,
              }
            : null,
        }));
      },

      toggleAudio: () => {
        set((state) => ({
          localParticipant: state.localParticipant
            ? {
                ...state.localParticipant,
                audioEnabled: !state.localParticipant.audioEnabled,
              }
            : null,
        }));
      },

      startScreenShare: async () => {
        try {
          await navigator.mediaDevices.getDisplayMedia({ video: true });
          set((state) => ({
            isScreenSharing: true,
            localParticipant: state.localParticipant
              ? { ...state.localParticipant, isScreenSharing: true }
              : null,
          }));
        } catch (error) {
          console.error("Screen share failed:", error);
        }
      },

      stopScreenShare: () => {
        set((state) => ({
          isScreenSharing: false,
          localParticipant: state.localParticipant
            ? { ...state.localParticipant, isScreenSharing: false }
            : null,
        }));
      },

      sendChatMessage: (content) => {
        const { localParticipant } = get();
        if (!localParticipant) return;

        const message: ChatMessage = {
          id: `msg-${Date.now()}`,
          senderId: localParticipant.id,
          senderName: localParticipant.name,
          content,
          timestamp: new Date().toISOString(),
          type: "text",
        };

        set((state) => ({
          chatMessages: [...state.chatMessages, message],
        }));
      },

      startRecording: async () => {
        const { activeSession } = get();
        if (!activeSession) return;

        set({
          recording: {
            id: `rec-${Date.now()}`,
            sessionId: activeSession.id,
            status: "recording",
            startedAt: new Date().toISOString(),
            duration: 0,
            consentObtained: activeSession.consentObtained,
          },
        });
      },

      stopRecording: async () => {
        set((state) => ({
          recording: state.recording
            ? { ...state.recording, status: "stopped" }
            : null,
        }));
      },

      togglePatientChart: () => {
        set((state) => ({ showPatientChart: !state.showPatientChart }));
      },

      toggleTranscription: () => {
        set((state) => ({ showTranscription: !state.showTranscription }));
      },

      toggleChat: () => {
        set((state) => ({ showChat: !state.showChat }));
      },

      acceptAISuggestion: (suggestionId) => {
        set((state) => ({
          aiSuggestions: state.aiSuggestions.map((s) =>
            s.id === suggestionId ? { ...s, accepted: true } : s
          ),
        }));
      },

      rejectAISuggestion: (suggestionId) => {
        set((state) => ({
          aiSuggestions: state.aiSuggestions.filter((s) => s.id !== suggestionId),
        }));
      },

      generateSessionSummary: async () => {
        const { activeSession, transcription } = get();
        if (!activeSession) return;

        set({ isGeneratingSummary: true });

        try {
          await new Promise((resolve) => setTimeout(resolve, 2000));

          const summary: SessionSummary = {
            sessionId: activeSession.id,
            duration: Math.floor(
              (Date.now() - new Date(activeSession.joinedAt || Date.now()).getTime()) / 1000
            ),
            chiefComplaint: activeSession.reason,
            keyPoints: [
              "Patient reports improvement with current medication",
              "Persistent GI side effects discussed",
              "Blood pressure control requires monitoring",
            ],
            patientEducation: [
              "Take Metformin with breakfast to reduce GI effects",
              "Maintain low sodium diet for BP management",
              "Regular home BP monitoring recommended",
            ],
            aiGeneratedNotes: `${activeSession.patient.name} presents for ${activeSession.reason.toLowerCase()}. Patient reports general improvement but continues to experience occasional GI upset with current medication regimen. Discussed importance of taking medication with food. Blood pressure remains slightly elevated. Recommended continued home monitoring and dietary modifications. Follow-up scheduled in 3 months.`,
            followUpRecommendations: [
              "Schedule follow-up in 3 months",
              "Review A1C results when available",
              "Consider medication adjustment if GI symptoms persist",
            ],
            generatedAt: new Date().toISOString(),
          };

          set({ sessionSummary: summary, isGeneratingSummary: false });
        } catch (error) {
          set({ isGeneratingSummary: false });
          throw error;
        }
      },

      submitFeedback: async (feedback) => {
        const { activeSession } = get();
        if (!activeSession) return;

        const fullFeedback: PatientFeedback = {
          ...feedback,
          sessionId: activeSession.id,
          submittedAt: new Date().toISOString(),
        };

        // In production, this would be an API call
        console.log("Feedback submitted:", fullFeedback);
      },

      setConsentObtained: (sessionId, consent) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId ? { ...s, consentObtained: consent } : s
          ),
          activeSession:
            state.activeSession?.id === sessionId
              ? { ...state.activeSession, consentObtained: consent }
              : state.activeSession,
        }));
      },

      setRecordingEnabled: (enabled) => {
        set((state) => ({
          activeSession: state.activeSession
            ? { ...state.activeSession, recordingEnabled: enabled }
            : null,
        }));
      },

      setTranscriptionEnabled: (enabled) => {
        set((state) => ({
          activeSession: state.activeSession
            ? { ...state.activeSession, transcriptionEnabled: enabled }
            : null,
        }));
      },

      resetCallState: () => {
        set({
          activeSession: null,
          isInCall: false,
          participants: [],
          localParticipant: null,
          remoteParticipant: null,
          recording: null,
          chatMessages: [],
          transcription: [],
          aiSuggestions: [],
          sessionSummary: null,
          livekitUrl: null,
          livekitToken: null,
        });
      },

      // Mock transcription generator (internal)
      startMockTranscription: () => {
        const mockDialogue = [
          { role: "provider" as const, text: "Hello John, how have you been feeling since our last visit?" },
          { role: "patient" as const, text: "Hi Doctor. The new medication is helping, but I'm still getting some stomach upset, especially in the morning." },
          { role: "provider" as const, text: "I see. Are you taking it with food?" },
          { role: "patient" as const, text: "Sometimes I forget to eat breakfast before taking it." },
          { role: "provider" as const, text: "That's likely the cause. The medication works best when taken with a meal. It helps reduce those GI side effects significantly." },
        ];

        let index = 0;
        const interval = setInterval(() => {
          if (index >= mockDialogue.length || !get().isInCall) {
            clearInterval(interval);
            return;
          }

          const { activeSession } = get();
          if (!activeSession) {
            clearInterval(interval);
            return;
          }

          const entry: TranscriptionEntry = {
            id: `trans-${Date.now()}`,
            speakerId: mockDialogue[index].role === "provider" ? activeSession.provider.id : activeSession.patient.id,
            speakerName: mockDialogue[index].role === "provider" ? activeSession.provider.name : activeSession.patient.name,
            speakerRole: mockDialogue[index].role,
            content: mockDialogue[index].text,
            timestamp: new Date().toISOString(),
            confidence: 0.95,
          };

          set((state) => ({
            transcription: [...state.transcription, entry],
          }));

          // Generate AI suggestion after specific entries
          if (index === 3) {
            const suggestion: AISuggestion = {
              id: `ai-${Date.now()}`,
              type: "note",
              content: "Patient reports improvement but persistent GI side effects. Medication not consistently taken with food.",
              source: "Based on transcription",
              timestamp: new Date().toISOString(),
            };
            set((state) => ({
              aiSuggestions: [...state.aiSuggestions, suggestion],
            }));
          }

          index++;
        }, 4000);
      },
    })),
    { name: "telehealth-store" }
  )
);

// ============================================================================
// Selectors
// ============================================================================

export const selectWaitingPatients = (state: TelehealthState) =>
  state.waitingRoom.filter((w) => w.deviceCheckPassed);

export const selectUpcomingSessions = (state: TelehealthState) =>
  state.todaySessions.filter((s) => s.status === "scheduled");

export const selectDeviceCheckPassed = (state: TelehealthState) =>
  state.deviceStatus.camera.available &&
  state.deviceStatus.microphone.available &&
  !state.deviceStatus.camera.error &&
  !state.deviceStatus.microphone.error;

export const selectNetworkQualityIcon = (quality: NetworkQuality) => {
  switch (quality) {
    case "excellent":
      return "📶";
    case "good":
      return "📶";
    case "fair":
      return "📶";
    case "poor":
      return "📵";
  }
};

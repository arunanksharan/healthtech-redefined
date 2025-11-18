'use client';

import React, { useState, useEffect } from 'react';
import { format, formatDuration, intervalToDuration } from 'date-fns';
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  PhoneMissed,
  Play,
  Pause,
  Download,
  FileText,
  Clock,
  Calendar,
  User,
  MapPin,
  AlertCircle,
  CheckCircle,
  XCircle,
  ArrowRight,
  Volume2,
  Filter,
  Search,
} from 'lucide-react';

// ==================== Types ====================

interface VoiceCall {
  id: string;
  patientId?: string;
  patientName?: string;
  patientPhone: string;
  callType: 'inbound' | 'outbound';
  callStatus: 'scheduled' | 'in_progress' | 'completed' | 'failed' | 'no_answer';
  startedAt?: string;
  endedAt?: string;
  durationSeconds?: number;
  detectedIntent?: string;
  callOutcome?: string;
  confidenceScore?: number;
  transcriptId?: string;
  recordingId?: string;
  appointmentId?: string;
}

interface CallTranscript {
  id: string;
  fullTranscript: string;
  turns: Array<{
    speaker: 'agent' | 'patient';
    text: string;
    timestamp: string;
  }>;
  provider: string;
  confidenceScore?: number;
  wordCount?: number;
}

interface CallRecording {
  id: string;
  recordingUrl: string;
  format: string;
  durationSeconds?: number;
  fileSizeBytes?: number;
}

interface CallHistoryProps {
  patientId?: string;
  onCallSelect?: (call: VoiceCall) => void;
}

// ==================== Helper Components ====================

const CallStatusBadge = ({ status }: { status: string }) => {
  const config = {
    completed: { color: 'green', icon: CheckCircle, label: 'Completed' },
    failed: { color: 'red', icon: XCircle, label: 'Failed' },
    no_answer: { color: 'yellow', icon: PhoneMissed, label: 'No Answer' },
    in_progress: { color: 'blue', icon: Phone, label: 'In Progress' },
    scheduled: { color: 'gray', icon: Calendar, label: 'Scheduled' },
  };

  const { color, icon: Icon, label } = config[status as keyof typeof config] || config.completed;

  return (
    <span className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800`}>
      <Icon className="w-3 h-3" />
      <span>{label}</span>
    </span>
  );
};

const CallTypeIcon = ({ type }: { type: 'inbound' | 'outbound' }) => {
  return type === 'inbound' ? (
    <PhoneIncoming className="w-5 h-5 text-blue-600" />
  ) : (
    <PhoneOutgoing className="w-5 h-5 text-green-600" />
  );
};

const AudioPlayer = ({ recording }: { recording: CallRecording }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Volume2 className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-900">Call Recording</span>
        </div>
        <a
          href={recording.recordingUrl}
          download
          className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
        >
          <Download className="w-4 h-4" />
          <span>Download</span>
        </a>
      </div>

      <div className="flex items-center space-x-3">
        <button
          onClick={togglePlay}
          className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700"
        >
          {isPlaying ? (
            <Pause className="w-4 h-4" />
          ) : (
            <Play className="w-4 h-4" />
          )}
        </button>

        <div className="flex-1">
          <audio
            ref={audioRef}
            src={recording.recordingUrl}
            onTimeUpdate={handleTimeUpdate}
            onEnded={() => setIsPlaying(false)}
            className="w-full"
          />
          <input
            type="range"
            min="0"
            max={recording.durationSeconds || 0}
            value={currentTime}
            onChange={(e) => {
              const time = Number(e.target.value);
              setCurrentTime(time);
              if (audioRef.current) {
                audioRef.current.currentTime = time;
              }
            }}
            className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        <span className="text-sm text-gray-600 font-mono">
          {formatTime(currentTime)} / {formatTime(recording.durationSeconds || 0)}
        </span>
      </div>
    </div>
  );
};

const TranscriptViewer = ({ transcript }: { transcript: CallTranscript }) => {
  const [showFullTranscript, setShowFullTranscript] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-900">Transcript</span>
        </div>
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <span>{transcript.wordCount} words</span>
          <span>•</span>
          <span>{Math.round((transcript.confidenceScore || 0) * 100)}% confidence</span>
        </div>
      </div>

      {/* Turn-by-turn transcript */}
      {transcript.turns && transcript.turns.length > 0 ? (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {transcript.turns.map((turn, index) => (
            <div key={index} className="flex space-x-3">
              <div className={`flex-shrink-0 w-20 text-xs font-medium ${
                turn.speaker === 'agent' ? 'text-blue-600' : 'text-green-600'
              }`}>
                {turn.speaker === 'agent' ? 'Agent' : 'Patient'}
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">{turn.text}</p>
                {turn.timestamp && (
                  <span className="text-xs text-gray-500">
                    {format(new Date(turn.timestamp), 'HH:mm:ss')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Full transcript fallback */
        <div className="prose prose-sm max-w-none">
          <p className={`text-sm text-gray-700 ${!showFullTranscript && 'line-clamp-4'}`}>
            {transcript.fullTranscript}
          </p>
          {transcript.fullTranscript.length > 200 && (
            <button
              onClick={() => setShowFullTranscript(!showFullTranscript)}
              className="text-sm text-blue-600 hover:text-blue-700 mt-2"
            >
              {showFullTranscript ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// ==================== Main Component ====================

export default function CallHistory({ patientId, onCallSelect }: CallHistoryProps) {
  const [calls, setCalls] = useState<VoiceCall[]>([]);
  const [selectedCall, setSelectedCall] = useState<VoiceCall | null>(null);
  const [transcript, setTranscript] = useState<CallTranscript | null>(null);
  const [recording, setRecording] = useState<CallRecording | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    loadCalls();
  }, [patientId]);

  useEffect(() => {
    if (selectedCall) {
      loadCallDetails(selectedCall);
    }
  }, [selectedCall]);

  const loadCalls = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      const url = patientId
        ? `/api/v1/voice-calls?patient_id=${patientId}`
        : '/api/v1/voice-calls';
      const response = await fetch(url);
      const data = await response.json();
      setCalls(data.calls || []);
    } catch (error) {
      console.error('Failed to load calls:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCallDetails = async (call: VoiceCall) => {
    try {
      if (call.transcriptId) {
        const transcriptResponse = await fetch(
          `/api/v1/voice-calls/${call.id}/transcript`
        );
        const transcriptData = await transcriptResponse.json();
        setTranscript(transcriptData);
      }

      if (call.recordingId) {
        const recordingResponse = await fetch(
          `/api/v1/voice-calls/${call.id}/recording`
        );
        const recordingData = await recordingResponse.json();
        setRecording(recordingData);
      }
    } catch (error) {
      console.error('Failed to load call details:', error);
    }
  };

  const handleCallClick = (call: VoiceCall) => {
    setSelectedCall(call);
    if (onCallSelect) {
      onCallSelect(call);
    }
  };

  const formatCallDuration = (seconds?: number) => {
    if (!seconds) return '0:00';
    const duration = intervalToDuration({ start: 0, end: seconds * 1000 });
    return formatDuration(duration, { format: ['minutes', 'seconds'] });
  };

  const filteredCalls = calls.filter((call) => {
    const matchesSearch =
      !searchQuery ||
      call.patientName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      call.patientPhone.includes(searchQuery);

    const matchesStatus =
      statusFilter === 'all' || call.callStatus === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* Call List */}
      <div className="lg:col-span-1 bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Call History</h2>

          {/* Search */}
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search calls..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="no_answer">No Answer</option>
          </select>
        </div>

        {/* Call List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredCalls.length === 0 ? (
            <div className="flex flex-col justify-center items-center h-32 text-gray-500">
              <Phone className="w-8 h-8 mb-2" />
              <p className="text-sm">No calls found</p>
            </div>
          ) : (
            filteredCalls.map((call) => (
              <button
                key={call.id}
                onClick={() => handleCallClick(call)}
                className={`w-full p-4 border-b border-gray-200 hover:bg-gray-50 text-left transition-colors ${
                  selectedCall?.id === call.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <CallTypeIcon type={call.callType} />
                    <div>
                      <p className="font-medium text-gray-900">
                        {call.patientName || 'Unknown'}
                      </p>
                      <p className="text-sm text-gray-500">{call.patientPhone}</p>
                    </div>
                  </div>
                  <CallStatusBadge status={call.callStatus} />
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-4">
                    {call.startedAt && (
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{format(new Date(call.startedAt), 'MMM d, HH:mm')}</span>
                      </span>
                    )}
                    {call.durationSeconds && (
                      <span className="flex items-center space-x-1">
                        <Phone className="w-3 h-3" />
                        <span>{formatCallDuration(call.durationSeconds)}</span>
                      </span>
                    )}
                  </div>
                </div>

                {call.detectedIntent && (
                  <div className="mt-2">
                    <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
                      {call.detectedIntent}
                    </span>
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Call Details */}
      <div className="lg:col-span-2 space-y-4">
        {selectedCall ? (
          <>
            {/* Call Info Card */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    {selectedCall.patientName || 'Unknown Patient'}
                  </h3>
                  <p className="text-gray-600">{selectedCall.patientPhone}</p>
                </div>
                <CallStatusBadge status={selectedCall.callStatus} />
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Call Type:</span>
                  <p className="font-medium capitalize">{selectedCall.callType}</p>
                </div>
                <div>
                  <span className="text-gray-500">Duration:</span>
                  <p className="font-medium">
                    {formatCallDuration(selectedCall.durationSeconds)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Started:</span>
                  <p className="font-medium">
                    {selectedCall.startedAt
                      ? format(new Date(selectedCall.startedAt), 'PPp')
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Ended:</span>
                  <p className="font-medium">
                    {selectedCall.endedAt
                      ? format(new Date(selectedCall.endedAt), 'PPp')
                      : 'N/A'}
                  </p>
                </div>
                {selectedCall.detectedIntent && (
                  <div>
                    <span className="text-gray-500">Intent:</span>
                    <p className="font-medium capitalize">
                      {selectedCall.detectedIntent}
                    </p>
                  </div>
                )}
                {selectedCall.callOutcome && (
                  <div>
                    <span className="text-gray-500">Outcome:</span>
                    <p className="font-medium capitalize">
                      {selectedCall.callOutcome}
                    </p>
                  </div>
                )}
              </div>

              {selectedCall.appointmentId && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-green-800">
                      Appointment booked from this call
                    </span>
                    <button className="text-sm text-green-600 hover:text-green-700 flex items-center space-x-1">
                      <span>View Appointment</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Audio Player */}
            {recording && <AudioPlayer recording={recording} />}

            {/* Transcript */}
            {transcript && <TranscriptViewer transcript={transcript} />}
          </>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-12 flex flex-col items-center justify-center text-gray-500">
            <Phone className="w-16 h-16 mb-4" />
            <p className="text-lg font-medium">Select a call to view details</p>
            <p className="text-sm">Click on any call from the list to see transcript and recording</p>
          </div>
        )}
      </div>
    </div>
  );
}

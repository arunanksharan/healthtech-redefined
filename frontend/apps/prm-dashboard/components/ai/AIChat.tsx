'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Sparkles, Bot, User, Paperclip } from 'lucide-react';
import { initializeAISystem, processUserInput, executeConfirmedPlan } from '@/lib/ai';
import { useToast } from '@/hooks/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils/cn';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    agentsUsed?: string[];
    executionTime?: number;
    requiresConfirmation?: boolean;
    plan?: any;
    showSmsButton?: boolean;
    smsData?: {
      phone: string;
      patientName: string;
      doctorName: string;
      time: string;
      department: string;
    };
    smsSent?: boolean;
  };
}

interface AIChatProps {
  userId: string;
  orgId: string;
  sessionId: string;
  permissions?: string[];
  onConfirmationRequired?: (plan: any) => void;
}

export function AIChat({
  userId,
  orgId,
  sessionId,
  permissions = [],
  onConfirmationRequired,
}: AIChatProps) {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hi! I'm your Clinical Assistant. I can help you with scheduling, patient records, and workflow automation. How can I assist you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      initializeAISystem(process.env.NEXT_PUBLIC_OPENAI_API_KEY);
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize AI system:', error);
      toast({ title: 'Error', description: 'Failed to initialize AI assistant', variant: 'destructive' });
    }
  }, [toast]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Demo mode - hardcoded responses for showcase
  const getDemoResponse = (userInput: string): { message: string; agentsUsed: string[]; showSmsButton?: boolean; smsData?: any } | null => {
    const input = userInput.toLowerCase();

    // Demo patient database
    const demoPatients: Record<string, { mrn: string; name: string; dob: string; age: number; gender: string; phone: string; email: string; doctor: string; lastVisit: string; nextAppt: string; status: string; activities: string[] }> = {
      // By MRN
      '2026309037': {
        mrn: 'MRN-2026309037',
        name: 'Arunank Sharan',
        dob: 'July 10, 1990',
        age: 35,
        gender: 'Male',
        phone: '+91 98441 11173',
        email: 'arunanksharan@gmail.com',
        doctor: 'Dr. Sarah Mitchell',
        lastVisit: 'January 28, 2026',
        nextAppt: 'February 5, 2026 at 10:30 AM',
        status: '✅ Active Patient',
        activities: ['Lab results uploaded (Jan 28)', 'Prescription renewed (Jan 25)', 'Follow-up scheduled (Jan 20)']
      },
      '2026260887': {
        mrn: 'MRN-2026260887',
        name: 'Priya Sharma',
        dob: 'March 15, 1985',
        age: 40,
        gender: 'Female',
        phone: '+91 98765 43210',
        email: 'priya.sharma@email.com',
        doctor: 'Dr. Rajesh Kapoor',
        lastVisit: 'January 25, 2026',
        nextAppt: 'February 8, 2026 at 2:00 PM',
        status: '✅ Active Patient',
        activities: ['Annual checkup completed (Jan 25)', 'Mammogram scheduled (Feb 10)', 'Vitamins prescribed (Jan 25)']
      },
      '2026184523': {
        mrn: 'MRN-2026184523',
        name: 'Rahul Verma',
        dob: 'November 22, 1978',
        age: 47,
        gender: 'Male',
        phone: '+91 87654 32109',
        email: 'rahul.verma@email.com',
        doctor: 'Dr. Anita Desai',
        lastVisit: 'January 20, 2026',
        nextAppt: 'February 3, 2026 at 11:00 AM',
        status: '⚠️ Requires Follow-up',
        activities: ['Blood sugar monitoring (ongoing)', 'Diet consultation (Jan 20)', 'HbA1c test due (Feb 3)']
      },
      '2026372841': {
        mrn: 'MRN-2026372841',
        name: 'Meera Krishnan',
        dob: 'August 5, 1992',
        age: 33,
        gender: 'Female',
        phone: '+91 99887 76655',
        email: 'meera.k@email.com',
        doctor: 'Dr. Sarah Mitchell',
        lastVisit: 'January 29, 2026',
        nextAppt: 'March 1, 2026 at 9:30 AM',
        status: '✅ Active Patient',
        activities: ['Prenatal checkup (Jan 29)', 'Ultrasound scheduled (Feb 15)', 'Prenatal vitamins prescribed (Jan 29)']
      }
    };

    // Phone to MRN mapping
    const phoneToMrn: Record<string, string> = {
      '9844111173': '2026309037',
      '98441111173': '2026309037',
      '919844111173': '2026309037',
      '9876543210': '2026260887',
      '98765432109': '2026260887',
      '8765432109': '2026184523',
      '87654321099': '2026184523',
    };

    // BOOKING WITH SPECIFIC DETAILS - Check this FIRST before phone lookup
    // Handles: "book 10 AM for phone 9844111173 with Dr. Sarah Mitchell"
    if ((input.includes('book') || input.includes('schedule')) &&
        (input.includes('am') || input.includes('pm')) &&
        userInput.match(/\d{10}/) &&
        (input.includes('dr') || input.includes('doctor') || input.includes('anita') || input.includes('sarah') || input.includes('rajesh'))) {

      // Extract details
      const timeMatch = input.match(/(\d{1,2})\s*(am|pm)/i);
      const phoneMatchBooking = userInput.match(/(\d{10})/);
      const time = timeMatch ? `${timeMatch[1]}:00 ${timeMatch[2].toUpperCase()}` : '10:00 AM';
      const phone = phoneMatchBooking ? phoneMatchBooking[1] : '9844111173';

      // Find doctor name
      let doctorName = 'Dr. Anita Desai';
      let department = 'Cardiology';
      let room = 'Heart Center, Room 105';
      if (input.includes('sarah') || input.includes('mitchell')) {
        doctorName = 'Dr. Sarah Mitchell';
        department = 'General Medicine';
        room = 'Main Building, Room 204';
      } else if (input.includes('rajesh') || input.includes('kapoor')) {
        doctorName = 'Dr. Rajesh Kapoor';
        department = 'General Medicine';
        room = 'Main Building, Room 210';
      }

      // Find patient from phone
      const patientName = phone === '9844111173' ? 'Arunank Sharan' :
                          phone === '9876543210' ? 'Priya Sharma' :
                          phone === '8765432109' ? 'Rahul Verma' : 'Patient';

      const bookingRef = `APT-2026-${Math.floor(Math.random() * 9000) + 1000}`;

      return {
        message: `✅ **Appointment Confirmed!**\n\n**Booking Reference:** ${bookingRef}\n\n**📋 Appointment Details:**\n• **Patient:** ${patientName}\n• **Phone:** +91 ${phone}\n• **Doctor:** ${doctorName}\n• **Department:** ${department}\n• **Date:** Monday, February 3, 2026\n• **Time:** ${time}\n• **Location:** ${room}\n\n---\n\n**📝 Pre-Visit Instructions:**\n\n1. Please arrive 15 minutes before your appointment\n2. Bring a valid photo ID and insurance card\n3. Bring any previous medical reports or prescriptions\n4. Fast for 8 hours if blood work is required\n5. Wear comfortable, loose-fitting clothing\n\n**📎 Pre-Visit Form:**\nhttps://healthtech.clinic/previt/${bookingRef}\n\n---\n\n**📍 Directions:**\nhttps://maps.google.com/healthtech-clinic\n\n**📞 For queries:** +91 1800-123-4567`,
        agentsUsed: ['AppointmentAgent', 'SchedulingAgent', 'NotificationAgent'],
        showSmsButton: true,
        smsData: { phone, patientName, doctorName, time, department }
      };
    }

    // Phone number lookup (only if NOT a booking request)
    const phoneMatch = userInput.match(/(\d{10,12})/);
    if (phoneMatch && !input.includes('book') && !input.includes('schedule')) {
      const phoneDigits = phoneMatch[1];
      const mrnKey = phoneToMrn[phoneDigits];
      if (mrnKey && demoPatients[mrnKey]) {
        const patient = demoPatients[mrnKey];
        return {
          message: `📱 **Patient Found by Phone Number**\n\n**MRN:** ${patient.mrn}\n**Name:** ${patient.name}\n**DOB:** ${patient.dob} (Age: ${patient.age})\n**Gender:** ${patient.gender}\n**Phone:** ${patient.phone}\n**Email:** ${patient.email}\n\n**Status:** ${patient.status}\n**Primary Care:** ${patient.doctor}\n**Last Visit:** ${patient.lastVisit}\n**Next Appointment:** ${patient.nextAppt}\n\n**Recent Activity:**\n• ${patient.activities.join('\n• ')}\n\nWould you like me to schedule an appointment, view lab results, or send a message to this patient?`,
          agentsUsed: ['PatientAgent', 'SearchAgent']
        };
      }
    }

    // MRN lookup patterns
    const mrnMatch = userInput.match(/MRN[-\s]?(\d+)/i);
    if (mrnMatch) {
      const mrnNumber = mrnMatch[1];
      const patient = demoPatients[mrnNumber] || demoPatients['2026309037'];

      return {
        message: `📋 **Patient Record Found**\n\n**MRN:** ${patient.mrn}\n**Name:** ${patient.name}\n**DOB:** ${patient.dob} (Age: ${patient.age})\n**Gender:** ${patient.gender}\n**Phone:** ${patient.phone}\n**Email:** ${patient.email}\n\n**Status:** ${patient.status}\n**Primary Care:** ${patient.doctor}\n**Last Visit:** ${patient.lastVisit}\n**Next Appointment:** ${patient.nextAppt}\n\n**Recent Activity:**\n• ${patient.activities.join('\n• ')}\n\nWould you like me to schedule an appointment, view lab results, or send a message to this patient?`,
        agentsUsed: ['PatientAgent', 'RecordsAgent']
      };
    }

    // Patient details / medical records
    if (input.includes('patient detail') || input.includes('medical record') || input.includes('health record')) {
      return {
        message: `📊 **Medical Records Summary**\n\n**Patient:** Arunank Sharan (MRN-2026309037)\n\n**Vitals (Last Recorded - Jan 28, 2026):**\n• Blood Pressure: 120/80 mmHg ✅\n• Heart Rate: 72 bpm ✅\n• Temperature: 98.6°F ✅\n• SpO2: 98% ✅\n• Weight: 75 kg\n\n**Active Conditions:**\n• Seasonal allergies (managed)\n• Mild hypertension (controlled)\n\n**Current Medications:**\n• Lisinopril 10mg - Daily\n• Cetirizine 10mg - As needed\n• Vitamin D3 1000 IU - Daily\n\n**Recent Lab Results (Jan 28, 2026):**\n• HbA1c: 5.4% ✅ Normal\n• Cholesterol: 185 mg/dL ✅ Normal\n• CBC: All values within range ✅\n\n**Upcoming:**\n• Annual physical - Feb 5, 2026\n• Flu shot due - March 2026\n\nWould you like to view detailed lab reports, schedule a follow-up, or print a summary?`,
        agentsUsed: ['RecordsAgent', 'LabAgent']
      };
    }

    // Practitioner / Doctor queries
    if (input.includes('doctor') || input.includes('practitioner') || input.includes('physician') || input.includes('dr.') || input.includes('dr ')) {
      // Check for specific doctors
      if (input.includes('sarah') || input.includes('mitchell')) {
        return {
          message: `👩‍⚕️ **Dr. Sarah Mitchell**\n\n**Specialty:** General Medicine & Internal Medicine\n**Experience:** 15 years\n**Languages:** English, Hindi\n**Rating:** ⭐ 4.9 (324 reviews)\n\n**🏥 Department:** General Medicine\n**📍 Location:** Main Building, Room 204\n\n**📅 Available Time Slots (This Week):**\n\n**Today (Thu, Jan 30):**\n• 3:30 PM - 4:00 PM ✅\n• 4:30 PM - 5:00 PM ✅\n\n**Friday, Jan 31:**\n• 9:00 AM - 9:30 AM ✅\n• 10:00 AM - 10:30 AM ✅\n• 11:00 AM - 11:30 AM ✅\n• 2:00 PM - 2:30 PM ✅\n\n**Monday, Feb 3:**\n• 9:00 AM - 12:00 PM (Multiple slots)\n• 2:00 PM - 5:00 PM (Multiple slots)\n\n**Consultation Fee:** ₹800\n**Follow-up Fee:** ₹500\n\nWould you like to book an appointment with Dr. Mitchell?`,
          agentsUsed: ['PractitionerAgent', 'SchedulingAgent']
        };
      }
      if (input.includes('rajesh') || input.includes('kapoor')) {
        return {
          message: `👨‍⚕️ **Dr. Rajesh Kapoor**\n\n**Specialty:** General Medicine & Diabetology\n**Experience:** 20 years\n**Languages:** English, Hindi, Marathi\n**Rating:** ⭐ 4.8 (456 reviews)\n\n**🏥 Department:** General Medicine\n**📍 Location:** Main Building, Room 210\n\n**📅 Available Time Slots (This Week):**\n\n**Today (Thu, Jan 30):**\n• 4:00 PM - 4:30 PM ✅\n• 5:00 PM - 5:30 PM ✅\n\n**Saturday, Feb 1:**\n• 10:00 AM - 10:30 AM ✅\n• 11:00 AM - 11:30 AM ✅\n• 12:00 PM - 12:30 PM ✅\n• 3:00 PM - 3:30 PM ✅\n\n**Tuesday, Feb 4:**\n• 10:00 AM - 6:00 PM (Multiple slots)\n\n**Consultation Fee:** ₹1,000\n**Follow-up Fee:** ₹600\n\nWould you like to book an appointment with Dr. Kapoor?`,
          agentsUsed: ['PractitionerAgent', 'SchedulingAgent']
        };
      }
      if (input.includes('anita') || input.includes('desai')) {
        return {
          message: `👩‍⚕️ **Dr. Anita Desai**\n\n**Specialty:** Cardiology & Interventional Cardiology\n**Experience:** 18 years\n**Languages:** English, Hindi, Gujarati\n**Rating:** ⭐ 4.9 (289 reviews)\n\n**🏥 Department:** Cardiology\n**📍 Location:** Heart Center, Room 105\n\n**📅 Available Time Slots (This Week):**\n\n**Today (Thu, Jan 30):**\n• Fully booked ❌\n\n**Monday, Feb 3:**\n• 9:00 AM - 9:30 AM ✅\n• 10:00 AM - 10:30 AM ✅\n• 11:00 AM - 11:30 AM ✅\n\n**Wednesday, Feb 5:**\n• 9:00 AM - 1:00 PM (Multiple slots)\n\n**Consultation Fee:** ₹1,500\n**Follow-up Fee:** ₹800\n\n**Special Procedures:**\n• ECG Interpretation\n• Stress Test\n• Echo Review\n\nWould you like to book an appointment with Dr. Desai?`,
          agentsUsed: ['PractitionerAgent', 'SchedulingAgent']
        };
      }
      // General doctor list
      return {
        message: `👨‍⚕️ **Our Practitioners**\n\n**General Medicine:**\n\n• **Dr. Sarah Mitchell** ⭐ 4.9\n  Mon, Wed, Fri | 9 AM - 5 PM\n  Next available: Today 3:30 PM\n  Fee: ₹800\n\n• **Dr. Rajesh Kapoor** ⭐ 4.8\n  Tue, Thu, Sat | 10 AM - 6 PM\n  Next available: Today 4:00 PM\n  Fee: ₹1,000\n\n**Cardiology:**\n\n• **Dr. Anita Desai** ⭐ 4.9\n  Mon, Wed | 9 AM - 1 PM\n  Next available: Feb 3, 9:00 AM\n  Fee: ₹1,500\n\n• **Dr. Vikram Singh** ⭐ 4.7\n  Tue, Thu, Fri | 2 PM - 7 PM\n  Next available: Tomorrow 2:00 PM\n  Fee: ₹1,200\n\n**Orthopedics:**\n\n• **Dr. Suresh Menon** ⭐ 4.8\n  Mon-Fri | 10 AM - 4 PM\n  Next available: Tomorrow 10:00 AM\n  Fee: ₹1,000\n\n**Dermatology:**\n\n• **Dr. Priya Nair** ⭐ 4.9\n  Mon, Wed, Fri | 11 AM - 3 PM\n  Next available: Friday 11:00 AM\n  Fee: ₹900\n\nSay "Dr. [name]" for detailed availability, or "book with Dr. [name]" to schedule.`,
        agentsUsed: ['PractitionerAgent']
      };
    }

    // Time slots query
    if (input.includes('time slot') || input.includes('timeslot') || input.includes('availability') || input.includes('available slot') || input.includes('when is') || input.includes('free slot')) {
      return {
        message: `🕐 **Available Time Slots - Today & This Week**\n\n**Today (Thursday, Jan 30):**\n\n🟢 **General Medicine:**\n• 3:30 PM - Dr. Sarah Mitchell\n• 4:00 PM - Dr. Rajesh Kapoor\n• 4:30 PM - Dr. Sarah Mitchell\n• 5:00 PM - Dr. Rajesh Kapoor\n\n🔴 **Cardiology:**\n• Fully booked today\n\n🟢 **Orthopedics:**\n• 2:00 PM - Dr. Suresh Menon\n• 3:00 PM - Dr. Suresh Menon\n\n---\n\n**Tomorrow (Friday, Jan 31):**\n\n🟢 **General Medicine:**\n• 9:00 AM - 12:00 PM (Dr. Mitchell)\n• 2:00 PM - 5:00 PM (Dr. Mitchell)\n\n🟢 **Cardiology:**\n• 2:00 PM - Dr. Vikram Singh\n• 3:30 PM - Dr. Vikram Singh\n• 5:00 PM - Dr. Vikram Singh\n\n🟢 **Dermatology:**\n• 11:00 AM - Dr. Priya Nair\n• 12:00 PM - Dr. Priya Nair\n• 1:00 PM - Dr. Priya Nair\n\n---\n\n**Quick Book:**\nTell me the patient name and preferred time, and I'll book it for you!`,
        agentsUsed: ['SchedulingAgent', 'AvailabilityAgent']
      };
    }

    // Medication queries
    if (input.includes('medication') || input.includes('medicine') || input.includes('prescription') || input.includes('drug')) {
      return {
        message: `💊 **Medication Management**\n\n**Active Prescriptions for Arunank Sharan:**\n\n**1. Lisinopril 10mg**\n   • Dosage: 1 tablet daily (morning)\n   • Purpose: Blood pressure management\n   • Refills remaining: 3\n   • Next refill: February 15, 2026\n\n**2. Cetirizine 10mg**\n   • Dosage: 1 tablet as needed\n   • Purpose: Allergy relief\n   • Refills remaining: 5\n   • Status: PRN (as needed)\n\n**3. Vitamin D3 1000 IU**\n   • Dosage: 1 capsule daily\n   • Purpose: Vitamin supplementation\n   • Refills remaining: 2\n   • Next refill: March 1, 2026\n\n**⚠️ Alerts:**\n• No drug interactions detected\n• All medications within therapeutic range\n\n**Quick Actions:**\n• "Refill prescription for [medication]"\n• "Add new medication"\n• "Check drug interactions"\n• "Send prescription to pharmacy"\n\nWhat would you like me to do?`,
        agentsUsed: ['MedicationAgent', 'PharmacyAgent']
      };
    }

    // View today's appointments (check this BEFORE general booking)
    if (input.includes('today') || input.includes('schedule today') || input.includes('today\'s')) {
      return {
        message: `📅 **Today's Schedule (Jan 30, 2026)**\n\n✅ 9:00 AM - Completed\n   John Smith - Follow-up\n   Dr. Sarah Mitchell | General Medicine\n\n🔵 10:30 AM - In Progress\n   Maria Garcia - Annual Physical\n   Dr. Rajesh Kapoor | General Medicine\n\n⏳ 11:30 AM - Upcoming\n   David Chen - Lab Review\n   Dr. Anita Desai | Cardiology\n\n⏳ 2:00 PM - Upcoming\n   Sarah Johnson - New Patient\n   Dr. Sarah Mitchell | General Medicine\n\n⏳ 3:30 PM - Upcoming\n   Arunank Sharan - Consultation\n   Dr. Vikram Singh | Cardiology\n\n**Summary:**\n• Total: 5 appointments\n• Completed: 1\n• In Progress: 1\n• Upcoming: 3\n\nWould you like to reschedule any appointment or send reminders?`,
        agentsUsed: ['AppointmentAgent']
      };
    }

    // Appointment booking - ask for doctor/department
    if (input.includes('book') || input.includes('schedule') || input.includes('appointment')) {
      return {
        message: `📅 **Schedule New Appointment**\n\nI'd be happy to help you book an appointment! Please select from the following:\n\n**🏥 Department:**\n• General Medicine\n• Cardiology\n• Orthopedics\n• Dermatology\n• Gynecology\n• Pediatrics\n• ENT\n• Ophthalmology\n\n**👨‍⚕️ Available Doctors:**\n\n**General Medicine:**\n• Dr. Sarah Mitchell - Mon, Wed, Fri (9 AM - 5 PM)\n• Dr. Rajesh Kapoor - Tue, Thu, Sat (10 AM - 6 PM)\n\n**Cardiology:**\n• Dr. Anita Desai - Mon, Wed (9 AM - 1 PM)\n• Dr. Vikram Singh - Tue, Thu, Fri (2 PM - 7 PM)\n\n**Orthopedics:**\n• Dr. Suresh Menon - Mon-Fri (10 AM - 4 PM)\n\n**Next Available Slots:**\n• Today 3:30 PM - Dr. Sarah Mitchell\n• Tomorrow 10:00 AM - Dr. Rajesh Kapoor\n• Tomorrow 2:30 PM - Dr. Anita Desai\n\nPlease tell me:\n1. Which department or doctor?\n2. Preferred date and time?\n3. Patient name or MRN?`,
        agentsUsed: ['AppointmentAgent', 'SchedulingAgent']
      };
    }

    // Communication / messaging
    if (input.includes('send') || input.includes('message') || input.includes('whatsapp') || input.includes('sms') || input.includes('email') || input.includes('notify')) {
      return {
        message: `📨 **Communication Center**\n\nI can help you send messages via:\n• 📱 WhatsApp\n• 💬 SMS\n• 📧 Email\n\n**Recent Messages Sent:**\n• WhatsApp to Maria Garcia - Appointment reminder (2h ago)\n• SMS to 5 patients - Lab results ready (Today)\n• Email to David Chen - Pre-visit instructions (Yesterday)\n\n**Quick Templates Available:**\n• Appointment Reminder\n• Lab Results Ready\n• Prescription Renewal\n• Follow-up Reminder\n• General Health Tips\n\nTry: "Send WhatsApp to Arunank about his upcoming appointment"`,
        agentsUsed: ['CommunicationAgent']
      };
    }

    // Status query
    if (input.includes('status') || input === 'status') {
      return {
        message: `✅ **System Status - All Services Operational**\n\n**AI Agents Online:**\n• 🤖 PatientAgent - Ready\n• 📅 AppointmentAgent - Ready\n• 📨 CommunicationAgent - Ready\n• 🎫 TicketAgent - Ready\n• 🗺️ JourneyAgent - Ready\n\n**Integrations:**\n• 🏥 EHR System - Connected\n• 📞 Zoice Voice AI - Active\n• 💬 WhatsApp Business - Connected\n• 📊 Analytics - Real-time\n\n**Today's Metrics:**\n• 47 patients processed\n• 23 appointments completed\n• 156 messages sent\n• 98.7% satisfaction score\n\nAll systems operating normally. How can I assist you?`,
        agentsUsed: ['SystemAgent']
      };
    }

    // Default - return null to use real AI
    return null;
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || !isInitialized) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    // Check for demo response first
    const demoResponse = getDemoResponse(currentInput);
    if (demoResponse) {
      // Simulate thinking delay for realism
      await new Promise(resolve => setTimeout(resolve, 1200));

      const assistantMessage: Message = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: demoResponse.message,
        timestamp: new Date(),
        metadata: {
          agentsUsed: demoResponse.agentsUsed,
          executionTime: 1.2,
          showSmsButton: demoResponse.showSmsButton,
          smsData: demoResponse.smsData,
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
      return;
    }

    try {
      const result = await processUserInput(
        currentInput,
        userId,
        orgId,
        sessionId,
        permissions
      );

      if (result.results?.[0]?.data?.requiresConfirmation) {
        const confirmationMessage: Message = {
          id: `msg_${Date.now()}_confirm`,
          role: 'assistant',
          content: result.message,
          timestamp: new Date(),
          metadata: {
            requiresConfirmation: true,
            plan: result.results[0].data.plan,
            agentsUsed: result.agentsUsed,
          },
        };

        setMessages((prev) => [...prev, confirmationMessage]);

        if (onConfirmationRequired) {
          onConfirmationRequired(result.results[0].data.plan);
        }
      } else if (result.metadata?.requiresClarification) {
        // Handle clarification requests - show the questions
        const clarifications = result.metadata.clarifications as string[] || [];
        const clarificationText = clarifications.length > 0
          ? `${result.message}\n\n${clarifications.map((q, i) => `${i + 1}. ${q}`).join('\n')}`
          : result.message;

        const clarificationMessage: Message = {
          id: `msg_${Date.now()}_clarify`,
          role: 'assistant',
          content: clarificationText,
          timestamp: new Date(),
          metadata: {
            agentsUsed: result.agentsUsed,
          },
        };

        setMessages((prev) => [...prev, clarificationMessage]);
      } else {
        const assistantMessage: Message = {
          id: `msg_${Date.now()}_assistant`,
          role: 'assistant',
          content: result.message,
          timestamp: new Date(),
          metadata: {
            agentsUsed: result.agentsUsed,
            executionTime: result.metadata?.executionTime,
          },
        };

        setMessages((prev) => [...prev, assistantMessage]);

        if (!result.success) {
          toast({ title: 'Error', description: 'Action failed: ' + result.error?.message, variant: 'destructive' });
        }
      }
    } catch (error: any) {
      console.error('Chat error:', error);

      const errorMessage: Message = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: `I encountered an error: ${error.message}. Please try again.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      toast({ title: 'Error', description: 'Failed to process your request', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg overflow-hidden border-2 border-gray-100 dark:border-gray-800">
      {/* Header - Flat solid blue */}
      <div className="flex items-center gap-4 px-6 py-5 bg-blue-500 text-white shrink-0">
        <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center transition-all duration-200 hover:scale-105">
          <Sparkles className="w-6 h-6 text-blue-500" />
        </div>
        <div>
          <h2 className="font-heading text-lg text-white leading-tight">Clinical Assistant</h2>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={cn("w-2 h-2 rounded-full", isInitialized ? "bg-emerald-400" : "bg-gray-300")} />
            <p className="text-xs text-blue-100 font-medium">
              {isInitialized ? 'Online & Ready' : 'Initializing...'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 bg-gray-50 dark:bg-gray-800/50">
        <div className="px-6 py-6 space-y-6 min-h-full">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'} group`}
            >
              {/* Avatar */}
              <Avatar className={cn(
                "w-9 h-9 mt-1 rounded-lg",
                message.role === 'assistant'
                  ? "bg-blue-100 dark:bg-blue-900/30"
                  : "bg-gray-100 dark:bg-gray-700"
              )}>
                {message.role === 'assistant' ? (
                  <AvatarFallback className="bg-blue-500 text-white rounded-lg"><Bot className="w-5 h-5" /></AvatarFallback>
                ) : (
                  <AvatarFallback className="bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-lg"><User className="w-5 h-5" /></AvatarFallback>
                )}
              </Avatar>

              {/* Message Bubble - Flat, no shadows */}
              <div className="flex flex-col max-w-[80%]">
                <div className={cn(
                  "rounded-lg px-5 py-3.5 text-sm leading-relaxed transition-all duration-200",
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white dark:bg-gray-800 border-2 border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-200'
                )}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>

                {/* Metadata & Timestamp */}
                <div className={cn(
                  "flex items-center gap-2 mt-1.5 px-1 opacity-0 group-hover:opacity-100 transition-opacity text-[10px]",
                  message.role === 'user' ? "justify-end text-gray-400" : "justify-start text-gray-400"
                )}>
                  <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  {message.role === 'assistant' && message.metadata && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        {message.metadata.agentsUsed?.length ? 'Multi-Agent' : 'AI'}
                      </span>
                    </>
                  )}
                </div>

                {/* Actions (Assistant Only) */}
                {message.metadata && message.role === 'assistant' && (
                  <div className="mt-2 text-xs space-y-2">
                    {message.metadata.showSmsButton && !message.metadata.smsSent && (
                      <div className="flex gap-2 mt-3">
                        <button
                          className="flat-btn-primary text-sm py-2 px-4 flex items-center gap-2"
                          onClick={async () => {
                            // Show sending state
                            const sendingMsg: Message = {
                              id: `msg_${Date.now()}_sending`,
                              role: 'assistant',
                              content: '📤 Sending SMS confirmation...',
                              timestamp: new Date(),
                            };
                            setMessages(prev => [...prev, sendingMsg]);

                            // Simulate SMS sending delay
                            await new Promise(resolve => setTimeout(resolve, 1500));

                            // Mark SMS as sent on original message
                            setMessages(prev => prev.map(m =>
                              m.id === message.id
                                ? { ...m, metadata: { ...m.metadata, smsSent: true, showSmsButton: false } }
                                : m
                            ));

                            // Remove sending message and add success
                            const smsData = message.metadata?.smsData;
                            const successMsg: Message = {
                              id: `msg_${Date.now()}_sms_sent`,
                              role: 'assistant',
                              content: `✅ **SMS Sent Successfully!**\n\n**To:** +91 ${smsData?.phone || '9844111173'}\n**Patient:** ${smsData?.patientName || 'Patient'}\n\n**Message Preview:**\n"Dear ${smsData?.patientName || 'Patient'}, your appointment with ${smsData?.doctorName || 'Doctor'} is confirmed for ${smsData?.time || '10:00 AM'} on Feb 3, 2026. Pre-visit form: https://healthtech.clinic/previt/APT-2026. Reply CONFIRM to confirm or CANCEL to reschedule. - HealthTech Clinic"\n\n📱 SMS delivered at ${new Date().toLocaleTimeString()}`,
                              timestamp: new Date(),
                              metadata: {
                                agentsUsed: ['SMSAgent', 'NotificationAgent']
                              }
                            };
                            setMessages(prev => [...prev.filter(m => m.id !== sendingMsg.id), successMsg]);
                            toast({ title: 'SMS Sent', description: `Confirmation sent to +91 ${smsData?.phone}` });
                          }}
                        >
                          📱 Send SMS Confirmation
                        </button>
                        <button
                          className="text-sm py-2 px-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 flex items-center gap-2"
                          onClick={() => {
                            toast({ title: 'WhatsApp', description: 'WhatsApp confirmation coming soon!' });
                          }}
                        >
                          💬 Send WhatsApp
                        </button>
                      </div>
                    )}
                    {message.metadata.smsSent && (
                      <div className="flex items-center gap-2 mt-3 text-emerald-600 dark:text-emerald-400">
                        <span>✓ SMS confirmation sent</span>
                      </div>
                    )}
                    {message.metadata.requiresConfirmation && (
                      <div className="flex gap-2">
                        <button
                          className="flat-btn-primary text-sm py-2 px-4"
                          onClick={async () => {
                            // Mark this message as confirmed (remove the button)
                            setMessages(prev => prev.map(m =>
                              m.id === message.id
                                ? { ...m, metadata: { ...m.metadata, requiresConfirmation: false } }
                                : m
                            ));

                            // Add processing message
                            const processingMsg: Message = {
                              id: `msg_${Date.now()}_processing`,
                              role: 'assistant',
                              content: '⏳ Processing your request...',
                              timestamp: new Date(),
                            };
                            setMessages(prev => [...prev, processingMsg]);

                            try {
                              // Get the plan and agent from the message metadata
                              const plan = message.metadata?.plan;
                              const agentName = message.metadata?.agentsUsed?.[0] || 'AppointmentAgent';

                              if (!plan) {
                                throw new Error('No plan found to execute');
                              }

                              // Execute the confirmed plan
                              const result = await executeConfirmedPlan(
                                plan,
                                agentName,
                                userId,
                                orgId,
                                sessionId,
                                permissions
                              );

                              // Add result message
                              const resultMsg: Message = {
                                id: `msg_${Date.now()}_result`,
                                role: 'assistant',
                                content: result.success
                                  ? `✅ ${result.message}`
                                  : `❌ ${result.message || 'Action failed'}`,
                                timestamp: new Date(),
                              };
                              setMessages(prev => [...prev.filter(m => m.id !== processingMsg.id), resultMsg]);

                              if (result.success) {
                                toast({ title: 'Success', description: 'Your action has been completed!' });
                              } else {
                                toast({ title: 'Error', description: result.message, variant: 'destructive' });
                              }
                            } catch (error: any) {
                              const errorMsg: Message = {
                                id: `msg_${Date.now()}_error`,
                                role: 'assistant',
                                content: `❌ Error: ${error.message}`,
                                timestamp: new Date(),
                              };
                              setMessages(prev => [...prev.filter(m => m.id !== processingMsg.id), errorMsg]);
                              toast({ title: 'Error', description: error.message, variant: 'destructive' });
                            }
                          }}
                        >
                          Confirm Action
                        </button>
                        <button
                          className="text-sm py-2 px-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200"
                          onClick={() => {
                            setMessages(prev => prev.map(m =>
                              m.id === message.id
                                ? { ...m, metadata: { ...m.metadata, requiresConfirmation: false } }
                                : m
                            ));
                            const cancelMsg: Message = {
                              id: `msg_${Date.now()}_cancelled`,
                              role: 'assistant',
                              content: '❌ Action cancelled. Let me know if you need anything else.',
                              timestamp: new Date(),
                            };
                            setMessages(prev => [...prev, cancelMsg]);
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Thinking Indicator */}
          {isLoading && (
            <div className="flex gap-4">
              <Avatar className="w-9 h-9 mt-1 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <AvatarFallback className="bg-blue-500 text-white rounded-lg"><Bot className="w-5 h-5" /></AvatarFallback>
              </Avatar>
              <div className="bg-white dark:bg-gray-800 border-2 border-gray-100 dark:border-gray-700 rounded-lg px-6 py-4 flex items-center gap-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                </div>
                <span className="text-xs text-gray-500 font-medium">Analyzing...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area - Flat */}
      <div className="p-4 bg-white dark:bg-gray-900 border-t-2 border-gray-100 dark:border-gray-800 shrink-0">
        <div className="relative rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 focus-within:border-blue-500 focus-within:bg-white dark:focus-within:bg-gray-900 transition-all duration-200">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your task or ask a question..."
            className="min-h-[70px] max-h-[180px] w-full resize-none border-0 bg-transparent py-4 pl-5 pr-28 placeholder:text-gray-400 text-gray-900 dark:text-white focus-visible:ring-0 font-medium"
          />

          <div className="absolute bottom-2.5 right-2.5 flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105"
              onClick={() => toast({ title: 'Coming Soon', description: 'Attachments coming soon!' })}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105"
              onClick={() => toast({ title: 'Coming Soon', description: 'Voice input coming soon!' })}
            >
              <Mic className="h-4 w-4" />
            </Button>
            <div className="w-0.5 h-5 bg-gray-200 dark:bg-gray-600 mx-1" />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading || !isInitialized}
              size="icon"
              className="h-9 w-9 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-all duration-200 hover:scale-105"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 px-2">
          <div className="flex gap-2">
            {['Summarize Visits', 'Check Alerts'].map(s => (
              <button
                key={s}
                className="text-[10px] sm:text-xs font-semibold bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-3 py-1.5 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 hover:text-blue-500 transition-all duration-200 hover:scale-105"
                onClick={() => setInput(s)}
              >
                {s}
              </button>
            ))}
          </div>
          <p className="text-[10px] text-gray-400 hidden sm:block">
            Powering clinical workflows securely
          </p>
        </div>
      </div>
    </div>
  );
}

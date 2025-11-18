import Link from "next/link";
import { ArrowRight, Bot, Calendar, MessageSquare, Users } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Bot className="w-4 h-4" />
            AI-Native Healthcare Platform
          </div>

          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            PRM Dashboard
          </h1>

          <p className="text-2xl text-gray-600 mb-4">
            Revolutionary Agent-Native Patient Relationship Management
          </p>

          <p className="text-lg text-gray-500 mb-12 max-w-2xl mx-auto">
            Work at the speed of thought with AI assistants. No menus, no forms.
            Just natural language commands that execute complex workflows instantly.
          </p>

          <div className="flex gap-4 justify-center">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors"
            >
              Open Dashboard
              <ArrowRight className="w-5 h-5" />
            </Link>

            <Link
              href="/login"
              className="inline-flex items-center gap-2 bg-white hover:bg-gray-50 text-gray-900 px-8 py-4 rounded-lg font-semibold text-lg border-2 border-gray-200 transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-20 max-w-5xl mx-auto">
          <FeatureCard
            icon={<Bot className="w-8 h-8 text-blue-600" />}
            title="AI-First Interface"
            description="Talk to specialized agents using natural language. No clicking through menus."
          />
          <FeatureCard
            icon={<Calendar className="w-8 h-8 text-purple-600" />}
            title="Smart Scheduling"
            description="Book appointments, reschedule, and send reminders with a single command."
          />
          <FeatureCard
            icon={<MessageSquare className="w-8 h-8 text-green-600" />}
            title="Unified Communications"
            description="WhatsApp, SMS, Email - all managed through one AI assistant."
          />
        </div>

        {/* Example Commands */}
        <div className="mt-20 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8 text-gray-900">
            Example Commands
          </h2>
          <div className="bg-gray-900 rounded-xl p-8 text-green-400 font-mono space-y-4">
            <CommandExample command='Schedule callback for patient arunank tomorrow at 2pm' />
            <CommandExample command='Send reminder to all patients with appointments today' />
            <CommandExample command='Complete billing for patient 9844111173' />
            <CommandExample command='Show me patients who missed appointments this week' />
          </div>
        </div>

        {/* Stats */}
        <div className="mt-20 grid md:grid-cols-4 gap-6 max-w-4xl mx-auto">
          <StatCard number="95%" label="Intent Accuracy" />
          <StatCard number="<2s" label="Response Time" />
          <StatCard number="90%" label="Success Rate" />
          <StatCard number="10x" label="Faster Workflows" />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="bg-white p-6 rounded-xl border-2 border-gray-100 hover:border-blue-200 transition-colors">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 text-gray-900">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function CommandExample({ command }: { command: string }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-gray-500">$</span>
      <span>{command}</span>
    </div>
  );
}

function StatCard({ number, label }: { number: string; label: string }) {
  return (
    <div className="bg-white p-6 rounded-xl border-2 border-gray-100 text-center">
      <div className="text-3xl font-bold text-blue-600 mb-1">{number}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  );
}

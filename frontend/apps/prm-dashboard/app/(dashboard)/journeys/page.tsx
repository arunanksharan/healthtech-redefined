'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Route,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  Calendar,
  User,
  MoreVertical,
  Play,
  Pause,
  XCircle,
  ChevronRight,
  Activity,
} from 'lucide-react';
import { journeysAPI } from '@/lib/api/journeys';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { formatDate, formatSmartDate } from '@/lib/utils/date';
import { cn } from '@/lib/utils/cn';
import toast from 'react-hot-toast';

export default function JourneysPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedJourney, setSelectedJourney] = useState<any>(null);

  // Fetch all journeys
  const { data: journeysData, isLoading, error } = useQuery({
    queryKey: ['journeys', statusFilter],
    queryFn: async () => {
      const [data, error] = await journeysAPI.getAll({
        status: statusFilter === 'all' ? undefined : statusFilter,
      });
      if (error) throw new Error(error.message);
      return data;
    },
  });

  const journeys = journeysData?.items || [];
  const filteredJourneys = journeys.filter(journey =>
    searchQuery === '' ||
    journey.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    journey.patient?.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stats = {
    total: journeys.length,
    active: journeys.filter(j => j.status === 'active').length,
    completed: journeys.filter(j => j.status === 'completed').length,
    paused: journeys.filter(j => j.status === 'paused').length,
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'completed': return 'secondary';
      case 'paused': return 'warning';
      case 'cancelled': return 'destructive';
      default: return 'default';
    }
  };

  const getJourneyTypeColor = (type: string) => {
    switch (type) {
      case 'post_surgery': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'chronic_disease': return 'bg-red-100 text-red-700 border-red-200';
      case 'wellness': return 'bg-green-100 text-green-700 border-green-200';
      case 'pregnancy': return 'bg-pink-100 text-pink-700 border-pink-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getProgressPercentage = (journey: any) => {
    if (!journey.steps || journey.steps.length === 0) return 0;
    const completedSteps = journey.steps.filter((s: any) => s.status === 'completed').length;
    return Math.round((completedSteps / journey.steps.length) * 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Care Journeys</h1>
          <p className="text-gray-500 mt-1">Manage patient care pathways and recovery plans</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Journey
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Total Journeys</CardDescription>
              <Route className="w-4 h-4 text-gray-400" />
            </div>
            <CardTitle className="text-3xl">{stats.total}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Active</CardDescription>
              <Activity className="w-4 h-4 text-green-600" />
            </div>
            <CardTitle className="text-3xl text-green-600">{stats.active}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Completed</CardDescription>
              <CheckCircle2 className="w-4 h-4 text-blue-600" />
            </div>
            <CardTitle className="text-3xl text-blue-600">{stats.completed}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Paused</CardDescription>
              <Pause className="w-4 h-4 text-yellow-600" />
            </div>
            <CardTitle className="text-3xl text-yellow-600">{stats.paused}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Search & Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search journeys or patients..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="paused">Paused</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <Button variant="outline">
              <Filter className="w-4 h-4 mr-2" />
              More Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Journeys List */}
      {isLoading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-red-600">
              Error loading journeys: {(error as Error).message}
            </div>
          </CardContent>
        </Card>
      ) : filteredJourneys.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-gray-500">
              <Route className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No journeys found</p>
              {searchQuery && (
                <p className="text-sm mt-2">Try adjusting your search or filters</p>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {filteredJourneys.map((journey) => (
            <Card key={journey.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  {/* Journey Info */}
                  <div className="flex-1">
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center",
                        getJourneyTypeColor(journey.journey_type || 'default')
                      )}>
                        <Route className="w-6 h-6" />
                      </div>

                      {/* Details */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="text-lg font-semibold text-gray-900">
                              {journey.title || 'Untitled Journey'}
                            </h3>
                            <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                              <div className="flex items-center gap-1">
                                <User className="w-4 h-4" />
                                {journey.patient?.name || 'Unknown Patient'}
                              </div>
                              <div className="flex items-center gap-1">
                                <Calendar className="w-4 h-4" />
                                Started {formatSmartDate(journey.created_at || new Date().toISOString())}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={getStatusColor(journey.status)}>
                              {journey.status}
                            </Badge>
                            <Badge variant="outline" className={getJourneyTypeColor(journey.journey_type || 'default')}>
                              {journey.journey_type?.replace('_', ' ') || 'General'}
                            </Badge>
                          </div>
                        </div>

                        {/* Description */}
                        {journey.description && (
                          <p className="text-sm text-gray-600 mb-4">
                            {journey.description}
                          </p>
                        )}

                        {/* Progress Bar */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">
                              Progress: {journey.steps?.filter((s: any) => s.status === 'completed').length || 0} of {journey.steps?.length || 0} steps
                            </span>
                            <span className="font-medium text-gray-900">
                              {getProgressPercentage(journey)}%
                            </span>
                          </div>
                          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-300"
                              style={{ width: `${getProgressPercentage(journey)}%` }}
                            />
                          </div>
                        </div>

                        {/* Steps Preview */}
                        {journey.steps && journey.steps.length > 0 && (
                          <div className="mt-4 space-y-2">
                            <div className="text-sm font-medium text-gray-700">Recent Steps:</div>
                            <div className="space-y-1">
                              {journey.steps.slice(0, 3).map((step: any, index: number) => (
                                <div
                                  key={step.id || index}
                                  className="flex items-center gap-3 text-sm"
                                >
                                  {step.status === 'completed' ? (
                                    <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                                  ) : step.status === 'in_progress' ? (
                                    <Clock className="w-4 h-4 text-blue-600 flex-shrink-0" />
                                  ) : (
                                    <div className="w-4 h-4 border-2 border-gray-300 rounded-full flex-shrink-0" />
                                  )}
                                  <span className={cn(
                                    "flex-1",
                                    step.status === 'completed' ? 'text-gray-500 line-through' : 'text-gray-900'
                                  )}>
                                    {step.title || `Step ${index + 1}`}
                                  </span>
                                  {step.due_date && (
                                    <span className="text-xs text-gray-500">
                                      Due {formatSmartDate(step.due_date)}
                                    </span>
                                  )}
                                </div>
                              ))}
                              {journey.steps.length > 3 && (
                                <button className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
                                  View all {journey.steps.length} steps
                                  <ChevronRight className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

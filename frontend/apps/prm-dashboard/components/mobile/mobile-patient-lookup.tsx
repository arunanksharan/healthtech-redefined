"use client";

// Mobile Patient Lookup - Quick Patient Search for Providers
// EPIC-UX-012: Mobile Applications - Journey 12.4

import React, { useState, useEffect, useCallback } from "react";
import { format } from "date-fns";
import {
  Search, X, Clock, User, AlertTriangle, Heart, Pill, FileText,
  ChevronRight, Scan, Mic, Loader2, History, Star, StarOff,
  Phone, Calendar, Activity, Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMobileStore, type QuickPatient } from "@/lib/store/mobile-store";

// Patient search result card
interface PatientResultCardProps {
  patient: QuickPatient;
  onSelect: () => void;
  isFavorite?: boolean;
  onToggleFavorite?: () => void;
}

function PatientResultCard({ patient, onSelect, isFavorite, onToggleFavorite }: PatientResultCardProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors">
      <button onClick={onSelect} className="flex items-center gap-3 flex-1 text-left">
        <Avatar className="h-12 w-12">
          <AvatarFallback className="text-sm">
            {patient.name.split(" ").map(n => n[0]).join("")}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium truncate">{patient.name}</p>
            {patient.hasActiveAlerts && (
              <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            MRN: {patient.mrn} • {patient.age}y {patient.gender}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            {patient.allergies.length > 0 && (
              <Badge variant="outline" className="text-[10px] text-red-600 border-red-200">
                <AlertTriangle className="h-2 w-2 mr-1" />
                {patient.allergies.length} Allergies
              </Badge>
            )}
            {patient.conditions.slice(0, 2).map((cond, i) => (
              <Badge key={i} variant="secondary" className="text-[10px]">
                {cond}
              </Badge>
            ))}
          </div>
        </div>
        <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0" />
      </button>
      {onToggleFavorite && (
        <button
          onClick={(e) => { e.stopPropagation(); onToggleFavorite(); }}
          className="p-2 hover:bg-muted rounded-full transition-colors"
        >
          {isFavorite ? (
            <Star className="h-5 w-5 text-amber-500 fill-amber-500" />
          ) : (
            <StarOff className="h-5 w-5 text-muted-foreground" />
          )}
        </button>
      )}
    </div>
  );
}

// Patient quick view card
interface PatientQuickViewProps {
  patient: QuickPatient;
  onViewChart: () => void;
  onClose: () => void;
}

function PatientQuickView({ patient, onViewChart, onClose }: PatientQuickViewProps) {
  return (
    <Card className="border-2 border-primary">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-14 w-14">
              <AvatarFallback>{patient.name.split(" ").map(n => n[0]).join("")}</AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-lg">{patient.name}</CardTitle>
              <p className="text-sm text-muted-foreground">
                MRN: {patient.mrn} • {patient.age}y {patient.gender}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Allergies */}
        {patient.allergies.length > 0 && (
          <div className="p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <span className="font-medium text-red-900">Allergies</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {patient.allergies.map((allergy, i) => (
                <Badge key={i} variant="outline" className="bg-red-100 text-red-700 border-red-200">
                  {allergy}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Active Conditions */}
        <div>
          <p className="text-sm font-medium mb-2">Active Conditions</p>
          <div className="flex flex-wrap gap-2">
            {patient.conditions.map((cond, i) => (
              <Badge key={i} variant="secondary">{cond}</Badge>
            ))}
          </div>
        </div>

        {/* Quick Info */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="p-2 bg-muted/50 rounded">
            <p className="text-muted-foreground">Last Visit</p>
            <p className="font-medium">{format(new Date(patient.lastVisit), "MMM d, yyyy")}</p>
          </div>
          <div className="p-2 bg-muted/50 rounded">
            <p className="text-muted-foreground">Status</p>
            <p className="font-medium flex items-center gap-1">
              {patient.hasActiveAlerts ? (
                <><AlertTriangle className="h-3 w-3 text-amber-500" /> Has Alerts</>
              ) : (
                <><Shield className="h-3 w-3 text-green-500" /> No Alerts</>
              )}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button className="flex-1" onClick={onViewChart}>
            <FileText className="h-4 w-4 mr-2" /> View Chart
          </Button>
          <Button variant="outline" size="icon">
            <Phone className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <Calendar className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Recent search item
interface RecentSearchItemProps {
  query: string;
  timestamp: string;
  onSelect: () => void;
  onRemove: () => void;
}

function RecentSearchItem({ query, timestamp, onSelect, onRemove }: RecentSearchItemProps) {
  return (
    <div className="flex items-center gap-3 p-2 rounded hover:bg-muted/50 transition-colors">
      <button onClick={onSelect} className="flex items-center gap-3 flex-1 text-left">
        <History className="h-4 w-4 text-muted-foreground" />
        <div className="flex-1 min-w-0">
          <p className="text-sm truncate">{query}</p>
          <p className="text-xs text-muted-foreground">{timestamp}</p>
        </div>
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onRemove(); }}
        className="p-1 hover:bg-muted rounded"
      >
        <X className="h-4 w-4 text-muted-foreground" />
      </button>
    </div>
  );
}

// Main Mobile Patient Lookup Component
export function MobilePatientLookup() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("search");
  const [selectedPatient, setSelectedPatient] = useState<QuickPatient | null>(null);
  const [favoritePatients, setFavoritePatients] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<Array<{ query: string; timestamp: string }>>([
    { query: "John Doe", timestamp: "2 hours ago" },
    { query: "12345", timestamp: "Yesterday" },
    { query: "Mary", timestamp: "2 days ago" },
  ]);

  const {
    recentPatients,
    searchResults,
    isSearching,
    searchPatients,
    addToRecentPatients,
    clearRecentPatients,
  } = useMobileStore();

  // Debounced search
  useEffect(() => {
    if (searchQuery.length >= 2) {
      const timer = setTimeout(() => {
        searchPatients(searchQuery);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [searchQuery, searchPatients]);

  const handleSelectPatient = (patient: QuickPatient) => {
    setSelectedPatient(patient);
    addToRecentPatients(patient);
    // Add to recent searches
    if (searchQuery && !recentSearches.find(s => s.query === searchQuery)) {
      setRecentSearches([
        { query: searchQuery, timestamp: "Just now" },
        ...recentSearches.slice(0, 9),
      ]);
    }
  };

  const toggleFavorite = (patientId: string) => {
    setFavoritePatients(prev =>
      prev.includes(patientId)
        ? prev.filter(id => id !== patientId)
        : [...prev, patientId]
    );
  };

  const clearSearch = () => {
    setSearchQuery("");
    setSelectedPatient(null);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Search Header */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="p-4">
          <div className="relative flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, MRN, or DOB..."
                className="pl-9 pr-9"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoFocus
              />
              {searchQuery && (
                <button
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              )}
            </div>
            <Button variant="outline" size="icon">
              <Scan className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Mic className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Quick View Card */}
        {selectedPatient && (
          <div className="mb-4">
            <PatientQuickView
              patient={selectedPatient}
              onViewChart={() => {}}
              onClose={() => setSelectedPatient(null)}
            />
          </div>
        )}

        {/* Search Results */}
        {searchQuery.length >= 2 ? (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              {isSearching ? "Searching..." : `${searchResults.length} results for "${searchQuery}"`}
            </p>
            {isSearching ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : searchResults.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <User className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">No patients found</p>
                  <p className="text-xs text-muted-foreground mt-1">Try a different search term</p>
                </CardContent>
              </Card>
            ) : (
              <div className="divide-y">
                {searchResults.map((patient) => (
                  <PatientResultCard
                    key={patient.id}
                    patient={patient}
                    onSelect={() => handleSelectPatient(patient)}
                    isFavorite={favoritePatients.includes(patient.id)}
                    onToggleFavorite={() => toggleFavorite(patient.id)}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          // Empty state with tabs
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="search">Recent</TabsTrigger>
              <TabsTrigger value="patients">Patients</TabsTrigger>
              <TabsTrigger value="favorites">Favorites</TabsTrigger>
            </TabsList>

            <TabsContent value="search" className="mt-4 space-y-4">
              {/* Recent Searches */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium">Recent Searches</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setRecentSearches([])}
                    className="text-xs"
                  >
                    Clear
                  </Button>
                </div>
                {recentSearches.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No recent searches</p>
                ) : (
                  <div className="space-y-1">
                    {recentSearches.map((search, i) => (
                      <RecentSearchItem
                        key={i}
                        query={search.query}
                        timestamp={search.timestamp}
                        onSelect={() => setSearchQuery(search.query)}
                        onRemove={() => setRecentSearches(recentSearches.filter((_, idx) => idx !== i))}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Quick Access Suggestions */}
              <div>
                <p className="text-sm font-medium mb-2">Quick Search</p>
                <div className="flex flex-wrap gap-2">
                  {["Today's Patients", "Checked In", "Pending Labs", "Follow-ups"].map((tag) => (
                    <Button key={tag} variant="outline" size="sm" className="text-xs">
                      {tag}
                    </Button>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="patients" className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium">Recently Viewed</p>
                <Button variant="ghost" size="sm" onClick={clearRecentPatients} className="text-xs">
                  Clear
                </Button>
              </div>
              {recentPatients.length === 0 ? (
                <Card>
                  <CardContent className="py-8 text-center">
                    <Clock className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">No recently viewed patients</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="divide-y">
                  {recentPatients.map((patient) => (
                    <PatientResultCard
                      key={patient.id}
                      patient={patient}
                      onSelect={() => handleSelectPatient(patient)}
                      isFavorite={favoritePatients.includes(patient.id)}
                      onToggleFavorite={() => toggleFavorite(patient.id)}
                    />
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="favorites" className="mt-4">
              {favoritePatients.length === 0 ? (
                <Card>
                  <CardContent className="py-8 text-center">
                    <Star className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">No favorite patients</p>
                    <p className="text-xs text-muted-foreground mt-1">Star patients for quick access</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="divide-y">
                  {recentPatients
                    .filter(p => favoritePatients.includes(p.id))
                    .map((patient) => (
                      <PatientResultCard
                        key={patient.id}
                        patient={patient}
                        onSelect={() => handleSelectPatient(patient)}
                        isFavorite={true}
                        onToggleFavorite={() => toggleFavorite(patient.id)}
                      />
                    ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}

// Compact search widget
export function PatientSearchWidget({ onPatientSelect }: { onPatientSelect: (patient: QuickPatient) => void }) {
  const [query, setQuery] = useState("");
  const { searchResults, isSearching, searchPatients } = useMobileStore();

  useEffect(() => {
    if (query.length >= 2) {
      const timer = setTimeout(() => searchPatients(query), 300);
      return () => clearTimeout(timer);
    }
  }, [query, searchPatients]);

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search patients..."
          className="pl-9"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {query.length >= 2 && (
        <div className="max-h-48 overflow-y-auto border rounded-lg">
          {isSearching ? (
            <div className="p-4 text-center">
              <Loader2 className="h-4 w-4 animate-spin mx-auto" />
            </div>
          ) : searchResults.length === 0 ? (
            <p className="p-4 text-center text-sm text-muted-foreground">No results</p>
          ) : (
            searchResults.map((patient) => (
              <button
                key={patient.id}
                onClick={() => { onPatientSelect(patient); setQuery(""); }}
                className="w-full p-2 text-left hover:bg-muted transition-colors"
              >
                <p className="text-sm font-medium">{patient.name}</p>
                <p className="text-xs text-muted-foreground">MRN: {patient.mrn}</p>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default MobilePatientLookup;

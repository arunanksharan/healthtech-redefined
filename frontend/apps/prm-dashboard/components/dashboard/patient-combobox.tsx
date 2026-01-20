"use client"

import * as React from "react"
import { Check, ChevronsUpDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { Patient } from "@/lib/types"

interface PatientComboboxProps {
    value: string
    onChange: (value: string) => void
    patients: Patient[]
    error?: boolean
}

export function PatientCombobox({ value, onChange, patients, error }: PatientComboboxProps) {
    const [open, setOpen] = React.useState(false)

    // Find selected patient object to display name
    const selectedPatient = patients.find((p) => p.id === value)

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    className={cn(
                        "w-full justify-between h-11 rounded-xl bg-background px-3 font-normal",
                        !value && "text-muted-foreground",
                        error && "border-red-500 hover:border-red-500 focus:ring-red-500"
                    )}
                >
                    {selectedPatient
                        ? `${selectedPatient.first_name} ${selectedPatient.last_name} (MRN: ${selectedPatient.mrn})`
                        : "Select patient..."}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0 rounded-xl" align="start">
                <Command>
                    <CommandInput placeholder="Search patient name or MRN..." />
                    <CommandList>
                        <CommandEmpty>No patient found.</CommandEmpty>
                        <CommandGroup>
                            {patients.map((patient) => (
                                <CommandItem
                                    key={patient.id}
                                    value={`${patient.first_name} ${patient.last_name} ${patient.mrn}`} // Make everything searchable
                                    onSelect={() => {
                                        onChange(patient.id === value ? "" : patient.id)
                                        setOpen(false)
                                    }}
                                    className="cursor-pointer"
                                >
                                    <Check
                                        className={cn(
                                            "mr-2 h-4 w-4",
                                            value === patient.id ? "opacity-100" : "opacity-0"
                                        )}
                                    />
                                    <div className="flex flex-col">
                                        <span className="font-medium">
                                            {patient.first_name} {patient.last_name}
                                        </span>
                                        <span className="text-xs text-muted-foreground">
                                            MRN: {patient.mrn}
                                        </span>
                                    </div>
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    )
}

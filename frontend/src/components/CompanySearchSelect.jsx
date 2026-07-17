import { useState, useEffect, useRef } from "react"
import { Check, ChevronsUpDown, Building2 } from "lucide-react"
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
import { API_URL } from "../config"

export function CompanySearchSelect({
    value,
    onValueChange,
    onCompanySelect,
    onCreateNew,
    variant = "light", // "light" or "dark"
    compact = false,    // compact mode for topbar
    placeholder        // optional override for placeholder text
}) {
    const [open, setOpen] = useState(false)
    const [companies, setCompanies] = useState([])
    const [loading, setLoading] = useState(false)
    const [inputValue, setInputValue] = useState("")
    const companiesCache = useRef(null) // Cache für Firmen-Liste

    const isDark = variant === "dark"

    // Fetch all companies only once (cached)
    useEffect(() => {
        if (open && !companiesCache.current) {
            fetchAllCompanies()
        } else if (open && companiesCache.current) {
            // Benutze Cache
            setCompanies(companiesCache.current)
        }
    }, [open])

    // Sync input value with external value
    useEffect(() => {
        setInputValue(value || "")
    }, [value])

    const fetchAllCompanies = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${API_URL}/companies`)
            if (!res.ok) throw new Error('Failed to fetch companies')
            const data = await res.json()
            const companiesList = Array.isArray(data) ? data : []
            setCompanies(companiesList)
            companiesCache.current = companiesList // Cache speichern
        } catch (error) {
            console.error('Error fetching companies:', error)
            setCompanies([])
        } finally {
            setLoading(false)
        }
    }

    const handleSelect = (company) => {
        onValueChange(company.name)
        onCompanySelect(company)
        setOpen(false)
    }

    const handleInputChange = (newValue) => {
        setInputValue(newValue)
        onValueChange(newValue)
        // Reset company selection when user types something different
        onCompanySelect(null)
    }

    // Filter companies based on input
    const filteredCompanies = companies.filter((company) =>
        company.name.toLowerCase().includes(inputValue.toLowerCase())
    )

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    className={cn(
                        "w-full justify-between text-left font-normal",
                        compact
                            ? "h-7 px-2.5 text-[12px] rounded-md border-slate-300 bg-white hover:bg-slate-50"
                            : "h-auto",
                        !compact && (isDark
                            ? "rounded-lg border-slate-600 bg-slate-800 px-4 py-2 text-white placeholder-slate-400 hover:bg-slate-700 focus:ring-2 focus:ring-blue-400"
                            : "rounded-xl border-slate-300 bg-white px-4 py-3 hover:bg-slate-50")
                    )}
                >
                    <span className={cn(
                        "truncate",
                        value
                            ? (compact ? "text-slate-900" : (isDark ? "text-white" : "text-slate-900"))
                            : "text-slate-400"
                    )}>
                        {value || placeholder || (compact ? "Firma wählen…" : "Firmenname eingeben oder auswählen...")}
                    </span>
                    <ChevronsUpDown className={cn(
                        "ml-2 shrink-0",
                        compact ? "h-3.5 w-3.5 opacity-60" : "h-4 w-4",
                        !compact && (isDark ? "text-white opacity-70" : "opacity-50")
                    )} />
                </Button>
            </PopoverTrigger>
            <PopoverContent 
                className={cn(
                    "w-[var(--radix-popover-trigger-width)] p-0",
                    isDark && "bg-slate-800 border-slate-600"
                )} 
                align="start"
            >
                <Command 
                    shouldFilter={false}
                    className={cn(
                        isDark && "bg-slate-800 [&_[cmdk-input-wrapper]_svg]:text-white [&_[cmdk-input]]:text-white"
                    )}
                >
                    <CommandInput
                        placeholder="Firma suchen..."
                        value={inputValue}
                        onValueChange={handleInputChange}
                        className={cn(isDark && "text-white placeholder:text-slate-400")}
                    />
                    <CommandList className={cn(isDark && "bg-slate-800")}>
                        {loading ? (
                            <div className={cn(
                                "py-6 text-center text-sm",
                                isDark ? "text-slate-400" : "text-slate-500"
                            )}>
                                <div className="flex items-center justify-center gap-2">
                                    <div className={cn(
                                        "h-4 w-4 border-2 rounded-full animate-spin",
                                        isDark 
                                            ? "border-slate-600 border-t-blue-400" 
                                            : "border-slate-300 border-t-blue-500"
                                    )} />
                                    Lädt Firmen...
                                </div>
                            </div>
                        ) : filteredCompanies.length === 0 ? (
                            <CommandEmpty>
                                <div className="flex flex-col items-center gap-2 py-2">
                                    <Building2 className={cn(
                                        "h-8 w-8",
                                        isDark ? "text-slate-600" : "text-slate-300"
                                    )} />
                                    <p className={isDark ? "text-slate-400" : "text-slate-500"}>
                                        Keine Firma gefunden.
                                    </p>
                                    {inputValue && onCreateNew && (
                                        <button
                                            onClick={() => {
                                                onCreateNew(inputValue)
                                                setOpen(false)
                                            }}
                                            className={cn(
                                                "mt-2 px-4 py-2 rounded-lg font-medium text-sm transition-all cursor-pointer active:scale-95",
                                                isDark 
                                                    ? "bg-blue-600 hover:bg-blue-700 text-white" 
                                                    : "bg-blue-500 hover:bg-blue-600 text-white"
                                            )}
                                        >
                                            + Neue Firma analysieren
                                        </button>
                                    )}
                                </div>
                            </CommandEmpty>
                        ) : (
                            <CommandGroup 
                                heading="Verfügbare Firmen"
                                className={cn(isDark && "[&_[cmdk-group-heading]]:text-slate-400")}
                            >
                                {filteredCompanies.map((company) => (
                                    <CommandItem
                                        key={company.id}
                                        value={company.name}
                                        onSelect={() => handleSelect(company)}
                                        className={cn(
                                            "cursor-pointer",
                                            isDark && "text-white data-[selected=true]:bg-blue-700 data-[selected=true]:text-white hover:bg-slate-700"
                                        )}
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                value === company.name ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        <Building2 className={cn(
                                            "mr-2 h-4 w-4",
                                            isDark ? "text-slate-500" : "text-slate-400"
                                        )} />
                                        <span style={{ flex: 1 }}>{company.name}</span>
                                        {company.review_count != null && (
                                            <span style={{
                                                marginLeft: 8,
                                                fontSize: 11,
                                                color: isDark ? "var(--slate-400)" : "var(--slate-500)",
                                                whiteSpace: "nowrap",
                                            }}>
                                                {company.review_count} Bew.
                                            </span>
                                        )}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        )}
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    )
}

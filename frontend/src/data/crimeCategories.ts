// Extensible crime category list for the Predictive Hotspots feature.
// New categories can be added here without touching any component code.

export interface CrimeCategory {
  id: string;
  label: string;
  group: "all" | "person" | "property" | "financial" | "special";
}

export const CRIME_CATEGORIES: CrimeCategory[] = [
  { id: "all",                label: "All Crimes",             group: "all" },
  // Person crimes
  { id: "murder",             label: "Murder",                 group: "person" },
  { id: "attempt-murder",     label: "Attempt to Murder",      group: "person" },
  { id: "assault",            label: "Assault",                group: "person" },
  { id: "kidnapping",         label: "Kidnapping",             group: "person" },
  { id: "robbery",            label: "Robbery",                group: "person" },
  { id: "dacoity",            label: "Dacoity",                group: "person" },
  // Property crimes
  { id: "theft",              label: "Theft",                  group: "property" },
  { id: "burglary",           label: "Burglary",               group: "property" },
  { id: "vehicle-theft",      label: "Vehicle Theft",          group: "property" },
  { id: "property-crime",     label: "Property Crime",         group: "property" },
  // Financial crimes
  { id: "fraud",              label: "Fraud",                  group: "financial" },
  { id: "cyber-crime",        label: "Cyber Crime",            group: "financial" },
  { id: "counterfeiting",     label: "Counterfeiting",         group: "financial" },
  // Special categories
  { id: "crimes-women",       label: "Crimes Against Women",   group: "special" },
  { id: "crimes-children",    label: "Crimes Against Children",group: "special" },
  { id: "drug-related",       label: "Drug-Related (NDPS)",    group: "special" },
  { id: "road-accidents",     label: "Road Accidents",         group: "special" },
];

export function getCategoryLabel(id: string): string {
  return CRIME_CATEGORIES.find((c) => c.id === id)?.label ?? id;
}

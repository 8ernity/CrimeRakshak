

// ─── Criminal Network Data ───────────────────────────────────────────

export interface NetworkNode {
  id: string;
  name: string;
  type: "accused" | "victim" | "location" | "account";
  group: number; // cluster id
  firCount: number;
  risk: "high" | "medium" | "low";
}

export interface NetworkEdge {
  source: string;
  target: string;
  type: "co-accused" | "shared-location" | "transaction" | "victim-link";
  weight: number;
}

export const networkNodes: NetworkNode[] = [
  { id: "A1", name: "Rajesh Kumar", type: "accused", group: 1, firCount: 7, risk: "high" },
  { id: "A2", name: "Suresh Patil", type: "accused", group: 1, firCount: 5, risk: "high" },
  { id: "A3", name: "Mohan Rao", type: "accused", group: 1, firCount: 3, risk: "medium" },
  { id: "A4", name: "Anil Gowda", type: "accused", group: 2, firCount: 6, risk: "high" },
  { id: "A5", name: "Prakash Shetty", type: "accused", group: 2, firCount: 4, risk: "medium" },
  { id: "A6", name: "Naveen Reddy", type: "accused", group: 2, firCount: 2, risk: "low" },
  { id: "A7", name: "Farhan Sheikh", type: "accused", group: 3, firCount: 8, risk: "high" },
  { id: "A8", name: "Kiran Das", type: "accused", group: 3, firCount: 3, risk: "medium" },
  { id: "A9", name: "Deepak Jain", type: "accused", group: 4, firCount: 2, risk: "low" },
  { id: "A10", name: "Vikram Singh", type: "accused", group: 4, firCount: 1, risk: "low" },
  { id: "V1", name: "Meera Devi", type: "victim", group: 1, firCount: 2, risk: "low" },
  { id: "V2", name: "Lakshmi Bai", type: "victim", group: 2, firCount: 1, risk: "low" },
  { id: "V3", name: "Fatima Begum", type: "victim", group: 3, firCount: 1, risk: "low" },
  { id: "L1", name: "Majestic Area", type: "location", group: 1, firCount: 12, risk: "high" },
  { id: "L2", name: "KR Puram", type: "location", group: 2, firCount: 8, risk: "medium" },
  { id: "L3", name: "Whitefield", type: "location", group: 3, firCount: 6, risk: "medium" },
  { id: "L4", name: "Jayanagar", type: "location", group: 4, firCount: 3, risk: "low" },
  { id: "B1", name: "HDFC-****4521", type: "account", group: 1, firCount: 3, risk: "high" },
  { id: "B2", name: "SBI-****8832", type: "account", group: 2, firCount: 2, risk: "medium" },
  { id: "B3", name: "ICICI-****1190", type: "account", group: 3, firCount: 4, risk: "high" },
];

export const networkEdges: NetworkEdge[] = [
  { source: "A1", target: "A2", type: "co-accused", weight: 5 },
  { source: "A1", target: "A3", type: "co-accused", weight: 3 },
  { source: "A2", target: "A3", type: "co-accused", weight: 2 },
  { source: "A1", target: "L1", type: "shared-location", weight: 7 },
  { source: "A2", target: "L1", type: "shared-location", weight: 4 },
  { source: "A3", target: "L1", type: "shared-location", weight: 2 },
  { source: "A1", target: "B1", type: "transaction", weight: 3 },
  { source: "A2", target: "B1", type: "transaction", weight: 2 },
  { source: "A1", target: "V1", type: "victim-link", weight: 2 },
  { source: "A4", target: "A5", type: "co-accused", weight: 4 },
  { source: "A4", target: "A6", type: "co-accused", weight: 2 },
  { source: "A5", target: "A6", type: "co-accused", weight: 1 },
  { source: "A4", target: "L2", type: "shared-location", weight: 5 },
  { source: "A5", target: "L2", type: "shared-location", weight: 3 },
  { source: "A4", target: "B2", type: "transaction", weight: 2 },
  { source: "A4", target: "V2", type: "victim-link", weight: 1 },
  { source: "A7", target: "A8", type: "co-accused", weight: 6 },
  { source: "A7", target: "L3", type: "shared-location", weight: 5 },
  { source: "A8", target: "L3", type: "shared-location", weight: 3 },
  { source: "A7", target: "B3", type: "transaction", weight: 4 },
  { source: "A8", target: "B3", type: "transaction", weight: 2 },
  { source: "A7", target: "V3", type: "victim-link", weight: 1 },
  { source: "A9", target: "A10", type: "co-accused", weight: 1 },
  { source: "A9", target: "L4", type: "shared-location", weight: 2 },
  { source: "A10", target: "L4", type: "shared-location", weight: 1 },
  // Cross-cluster links
  { source: "A3", target: "A6", type: "co-accused", weight: 1 },
  { source: "A7", target: "L1", type: "shared-location", weight: 1 },
];

// ─── Offender Profiling Data ─────────────────────────────────────────

export interface Offender {
  id: string;
  name: string;
  age: number;
  photo: string;
  alias: string[];
  gender: "male" | "female";
  height: string;
  weight: string;
  scars: string[];
  lastKnownAddress: string;
  district: string;
  associates: string[];
  paroleOfficer: string | null;
  convictions: number;
  acquittals: number;
  pendingCases: number;
  fingerprint: string;
  nationalId: string;
  totalFIRs: number;
  crimeTypes: string[];
  riskScore: number;
  isHabitual: boolean;
  modusOperandi: string[];
  lastOffense: string;
  status: "active" | "jailed" | "absconding" | "on-bail";
  timeline: { date: string; crime: string; location: string }[];
  // Phase 2 fields
  bloodGroup: string;
  languages: string[];
  occupation: string;
  education: string;
  fatherName: string;
  phoneNumber: string;
  aiBehavioralNote: string;
  personalityTraits: { trait: string; score: number }[];
  courtDates: { date: string; court: string; caseRef: string; outcome: "pending" | "convicted" | "acquitted" | "adjourned" }[];
  linkedFIRs: { firNumber: string; date: string; crime: string; section: string; status: string }[];
  victimCount: number;
  estimatedLoss: string;
  frequencyByYear: { year: string; count: number }[];
}

export const offenders: Offender[] = [
  {
    id: "OFF-001", name: "Rajesh Kumar", age: 34,
    photo: "/offenders/off-001.png",
    alias: ["Raju Bhai", "RK"],
    gender: "male", height: "5'10\"", weight: "78 kg",
    scars: ["Scar on left forearm", "Tattoo on right shoulder — snake"],
    lastKnownAddress: "42, 3rd Cross, Gandhinagar, Majestic, Bengaluru - 560009",
    district: "Bengaluru Central",
    associates: ["Suresh Patil", "Mohan Rao"],
    paroleOfficer: "SI Raghavendra K.",
    convictions: 3, acquittals: 1, pendingCases: 2,
    fingerprint: "Whorl — Right Thumb",
    nationalId: "XXXX-XXXX-4521",
    totalFIRs: 7, crimeTypes: ["Robbery", "Assault", "Extortion"],
    riskScore: 92, isHabitual: true, modusOperandi: ["Armed robbery", "Vehicle theft at night", "Extortion via threats"],
    lastOffense: "2025-03-15", status: "on-bail",
    timeline: [
      { date: "2019-06-12", crime: "Petty Theft", location: "Majestic" },
      { date: "2020-01-23", crime: "Robbery", location: "Majestic" },
      { date: "2020-11-08", crime: "Assault", location: "KR Puram" },
      { date: "2021-07-19", crime: "Armed Robbery", location: "Jayanagar" },
      { date: "2022-03-02", crime: "Extortion", location: "Whitefield" },
      { date: "2023-08-14", crime: "Armed Robbery", location: "Majestic" },
      { date: "2025-03-15", crime: "Extortion", location: "KR Puram" },
    ],
    bloodGroup: "B+", languages: ["Kannada", "Hindi", "Telugu"], occupation: "Auto Rickshaw Driver (Claimed)", education: "10th Pass",
    fatherName: "Ramesh Kumar", phoneNumber: "XXXXX-XX890",
    aiBehavioralNote: "Displays escalating pattern of violence with each offense. Subject transitions from petty theft to armed confrontations, suggesting growing confidence and desensitization. High recidivism risk — reoffends within 8–14 months of release. Territorial attachment to Majestic area indicates a comfort zone for operations.",
    personalityTraits: [
      { trait: "Aggression", score: 88 }, { trait: "Manipulation", score: 55 }, { trait: "Impulsivity", score: 78 },
      { trait: "Social Deviance", score: 82 }, { trait: "Criminal Sophistication", score: 65 },
    ],
    courtDates: [
      { date: "2020-04-15", court: "3rd ACMM, Bengaluru", caseRef: "CC-1204/2020", outcome: "convicted" },
      { date: "2021-11-20", court: "Sessions Court, Bengaluru", caseRef: "SC-892/2021", outcome: "convicted" },
      { date: "2023-02-10", court: "3rd ACMM, Bengaluru", caseRef: "CC-3341/2023", outcome: "acquitted" },
      { date: "2024-01-18", court: "Sessions Court, Bengaluru", caseRef: "SC-114/2024", outcome: "convicted" },
      { date: "2025-06-22", court: "Sessions Court, Bengaluru", caseRef: "SC-501/2025", outcome: "pending" },
      { date: "2025-09-10", court: "3rd ACMM, Bengaluru", caseRef: "CC-778/2025", outcome: "pending" },
    ],
    linkedFIRs: [
      { firNumber: "FIR-2019-BLR-0312", date: "2019-06-12", crime: "Petty Theft", section: "IPC 379", status: "convicted" },
      { firNumber: "FIR-2020-BLR-0145", date: "2020-01-23", crime: "Robbery", section: "IPC 392", status: "convicted" },
      { firNumber: "FIR-2020-BLR-0891", date: "2020-11-08", crime: "Assault", section: "IPC 323, 324", status: "convicted" },
      { firNumber: "FIR-2021-BLR-0673", date: "2021-07-19", crime: "Armed Robbery", section: "IPC 392, 397", status: "acquitted" },
      { firNumber: "FIR-2022-BLR-0234", date: "2022-03-02", crime: "Extortion", section: "IPC 384, 506", status: "charge-sheeted" },
      { firNumber: "FIR-2023-BLR-0412", date: "2023-08-14", crime: "Armed Robbery", section: "IPC 392, 397, 34", status: "convicted" },
      { firNumber: "FIR-2025-BLR-0847", date: "2025-03-15", crime: "Extortion", section: "IPC 384, 506", status: "under-investigation" },
    ],
    victimCount: 14, estimatedLoss: "₹18.2 Lakh",
    frequencyByYear: [
      { year: "2019", count: 1 }, { year: "2020", count: 2 }, { year: "2021", count: 1 },
      { year: "2022", count: 1 }, { year: "2023", count: 1 }, { year: "2024", count: 0 }, { year: "2025", count: 1 },
    ],
  },
  {
    id: "OFF-002", name: "Farhan Sheikh", age: 29,
    photo: "/offenders/off-002.png",
    alias: ["Phantom", "FS Cyber"],
    gender: "male", height: "5'7\"", weight: "65 kg",
    scars: ["No visible scars"],
    lastKnownAddress: "Flat 12B, Prestige Tower, Whitefield, Bengaluru - 560066",
    district: "Bengaluru East",
    associates: ["Kiran Das"],
    paroleOfficer: null,
    convictions: 2, acquittals: 2, pendingCases: 3,
    fingerprint: "Loop — Left Index",
    nationalId: "XXXX-XXXX-8817",
    totalFIRs: 8, crimeTypes: ["Cybercrime", "Fraud", "Identity Theft"],
    riskScore: 88, isHabitual: true, modusOperandi: ["Phishing attacks", "SIM swap fraud", "Fake KYC scams"],
    lastOffense: "2025-05-20", status: "absconding",
    timeline: [
      { date: "2020-02-11", crime: "Online Fraud", location: "Whitefield" },
      { date: "2020-09-17", crime: "Identity Theft", location: "Electronic City" },
      { date: "2021-03-05", crime: "Phishing", location: "Whitefield" },
      { date: "2021-11-22", crime: "SIM Swap Fraud", location: "Koramangala" },
      { date: "2022-06-08", crime: "Bank Fraud", location: "MG Road" },
      { date: "2023-01-14", crime: "Cybercrime", location: "Whitefield" },
      { date: "2024-04-30", crime: "KYC Scam", location: "HSR Layout" },
      { date: "2025-05-20", crime: "Wire Fraud", location: "Whitefield" },
    ],
    bloodGroup: "O+", languages: ["Hindi", "English", "Urdu"], occupation: "Self-Employed IT Consultant (Claimed)", education: "B.Tech (Dropout)",
    fatherName: "Mohammed Sheikh", phoneNumber: "XXXXX-XX234",
    aiBehavioralNote: "Highly sophisticated digital criminal with above-average intelligence. Displays classic traits of a social engineer — calm under pressure, articulate, and technically proficient. Avoids physical confrontation entirely. Flight risk is extremely high — has used multiple identities and may have international connections. Operates through proxy networks making digital forensics challenging.",
    personalityTraits: [
      { trait: "Aggression", score: 15 }, { trait: "Manipulation", score: 95 }, { trait: "Impulsivity", score: 30 },
      { trait: "Social Deviance", score: 70 }, { trait: "Criminal Sophistication", score: 92 },
    ],
    courtDates: [
      { date: "2021-06-15", court: "Cyber Crime Court, Bengaluru", caseRef: "CYB-201/2021", outcome: "convicted" },
      { date: "2022-02-20", court: "Cyber Crime Court, Bengaluru", caseRef: "CYB-445/2022", outcome: "acquitted" },
      { date: "2023-05-12", court: "Sessions Court, Bengaluru", caseRef: "SC-667/2023", outcome: "acquitted" },
      { date: "2024-08-30", court: "Cyber Crime Court, Bengaluru", caseRef: "CYB-112/2024", outcome: "convicted" },
      { date: "2025-07-15", court: "Sessions Court, Bengaluru", caseRef: "SC-330/2025", outcome: "pending" },
    ],
    linkedFIRs: [
      { firNumber: "FIR-2020-BLR-0221", date: "2020-02-11", crime: "Online Fraud", section: "IT Act 66C", status: "convicted" },
      { firNumber: "FIR-2020-BLR-0678", date: "2020-09-17", crime: "Identity Theft", section: "IT Act 66C, 66D", status: "convicted" },
      { firNumber: "FIR-2021-BLR-0189", date: "2021-03-05", crime: "Phishing", section: "IT Act 66D, IPC 420", status: "acquitted" },
      { firNumber: "FIR-2021-BLR-0901", date: "2021-11-22", crime: "SIM Swap Fraud", section: "IT Act 66C", status: "acquitted" },
      { firNumber: "FIR-2022-BLR-0445", date: "2022-06-08", crime: "Bank Fraud", section: "IPC 420, IT Act 66D", status: "charge-sheeted" },
      { firNumber: "FIR-2023-BLR-0112", date: "2023-01-14", crime: "Cybercrime", section: "IT Act 43, 66", status: "charge-sheeted" },
      { firNumber: "FIR-2024-BLR-0891", date: "2024-04-30", crime: "KYC Scam", section: "IPC 468, 471", status: "convicted" },
      { firNumber: "FIR-2025-BLR-1234", date: "2025-05-20", crime: "Wire Fraud", section: "IT Act 66C, 66D", status: "under-investigation" },
    ],
    victimCount: 47, estimatedLoss: "₹1.2 Crore",
    frequencyByYear: [
      { year: "2020", count: 2 }, { year: "2021", count: 2 }, { year: "2022", count: 1 },
      { year: "2023", count: 1 }, { year: "2024", count: 1 }, { year: "2025", count: 1 },
    ],
  },
  {
    id: "OFF-003", name: "Anil Gowda", age: 41,
    photo: "/offenders/off-003.png",
    alias: ["AG", "Gowda Boss"],
    gender: "male", height: "5'9\"", weight: "88 kg",
    scars: ["Burn mark on left hand", "Tattoo on chest — eagle"],
    lastKnownAddress: "23, 7th Main, KR Puram, Bengaluru - 560036",
    district: "Bengaluru East",
    associates: ["Prakash Shetty", "Naveen Reddy"],
    paroleOfficer: null,
    convictions: 4, acquittals: 0, pendingCases: 1,
    fingerprint: "Arch — Right Index",
    nationalId: "XXXX-XXXX-3309",
    totalFIRs: 6, crimeTypes: ["Narcotics", "Smuggling", "Assault"],
    riskScore: 85, isHabitual: true, modusOperandi: ["Drug distribution network", "Interstate smuggling", "Intimidation"],
    lastOffense: "2024-12-01", status: "jailed",
    timeline: [
      { date: "2018-04-20", crime: "Drug Possession", location: "KR Puram" },
      { date: "2019-10-15", crime: "Narcotics Distribution", location: "Majestic" },
      { date: "2020-08-03", crime: "Assault", location: "KR Puram" },
      { date: "2022-01-12", crime: "Smuggling", location: "Mangalore" },
      { date: "2023-06-28", crime: "Drug Trafficking", location: "KR Puram" },
      { date: "2024-12-01", crime: "Narcotics Possession", location: "Whitefield" },
    ],
    bloodGroup: "A+", languages: ["Kannada", "Hindi"], occupation: "Transport Business (Front)", education: "8th Pass",
    fatherName: "Basavanna Gowda", phoneNumber: "XXXXX-XX567",
    aiBehavioralNote: "Classic organized crime profile with hierarchical network control. Uses fear and loyalty to maintain subordinate compliance. Has a pattern of using legitimate businesses as fronts for narcotics distribution. Subject is methodical and patient — avoids impulsive actions. In custody, shows compliance but remains influential through outside associates.",
    personalityTraits: [
      { trait: "Aggression", score: 72 }, { trait: "Manipulation", score: 80 }, { trait: "Impulsivity", score: 35 },
      { trait: "Social Deviance", score: 88 }, { trait: "Criminal Sophistication", score: 78 },
    ],
    courtDates: [
      { date: "2019-01-10", court: "NDPS Court, Bengaluru", caseRef: "NDPS-78/2019", outcome: "convicted" },
      { date: "2020-05-22", court: "NDPS Court, Bengaluru", caseRef: "NDPS-201/2020", outcome: "convicted" },
      { date: "2021-03-14", court: "3rd ACMM, Bengaluru", caseRef: "CC-567/2021", outcome: "convicted" },
      { date: "2022-09-08", court: "Sessions Court, Mangalore", caseRef: "SC-340/2022", outcome: "convicted" },
      { date: "2025-03-20", court: "NDPS Court, Bengaluru", caseRef: "NDPS-45/2025", outcome: "pending" },
    ],
    linkedFIRs: [
      { firNumber: "FIR-2018-BLR-0456", date: "2018-04-20", crime: "Drug Possession", section: "NDPS 20", status: "convicted" },
      { firNumber: "FIR-2019-BLR-0789", date: "2019-10-15", crime: "Narcotics Distribution", section: "NDPS 21, 22", status: "convicted" },
      { firNumber: "FIR-2020-BLR-0612", date: "2020-08-03", crime: "Assault", section: "IPC 323, 506", status: "convicted" },
      { firNumber: "FIR-2022-MNG-0234", date: "2022-01-12", crime: "Smuggling", section: "NDPS 21, 29", status: "convicted" },
      { firNumber: "FIR-2023-BLR-0782", date: "2023-06-28", crime: "Drug Trafficking", section: "NDPS 21, 22, 29", status: "charge-sheeted" },
      { firNumber: "FIR-2024-BLR-0965", date: "2024-12-01", crime: "Narcotics Possession", section: "NDPS 21, 22", status: "under-investigation" },
    ],
    victimCount: 3, estimatedLoss: "₹85 Lakh (seized contraband)",
    frequencyByYear: [
      { year: "2018", count: 1 }, { year: "2019", count: 1 }, { year: "2020", count: 1 },
      { year: "2021", count: 0 }, { year: "2022", count: 1 }, { year: "2023", count: 1 }, { year: "2024", count: 1 },
    ],
  },
  {
    id: "OFF-004", name: "Suresh Patil", age: 37,
    photo: "/offenders/off-004.png",
    alias: ["Shadow", "SP"],
    gender: "male", height: "5'11\"", weight: "75 kg",
    scars: ["Knife scar on right cheek"],
    lastKnownAddress: "118, 2nd Stage, Jayanagar, Bengaluru - 560011",
    district: "Bengaluru South",
    associates: ["Rajesh Kumar"],
    paroleOfficer: null,
    convictions: 2, acquittals: 1, pendingCases: 2,
    fingerprint: "Whorl — Left Thumb",
    nationalId: "XXXX-XXXX-6644",
    totalFIRs: 5, crimeTypes: ["Burglary", "Theft", "Robbery"],
    riskScore: 74, isHabitual: true, modusOperandi: ["Night-time burglary", "Lock picking", "Residential targeting"],
    lastOffense: "2025-01-10", status: "active",
    timeline: [
      { date: "2020-03-15", crime: "Burglary", location: "Jayanagar" },
      { date: "2021-07-22", crime: "Theft", location: "Indiranagar" },
      { date: "2022-11-08", crime: "Burglary", location: "Koramangala" },
      { date: "2023-09-14", crime: "Robbery", location: "Majestic" },
      { date: "2025-01-10", crime: "Burglary", location: "HSR Layout" },
    ],
    bloodGroup: "AB-", languages: ["Kannada", "Marathi", "Hindi"], occupation: "Daily Wage Laborer (Claimed)", education: "7th Pass",
    fatherName: "Hanumant Patil", phoneNumber: "XXXXX-XX112",
    aiBehavioralNote: "Stealthy and methodical burglar who operates exclusively at night (11 PM–3 AM window). Shows strong pattern recognition — targets affluent residential areas during weekdays when occupancy is low. Avoids confrontation but carries weapons as deterrent. Operates solo or with one accomplice. Post-release surveillance recommended during festive seasons (historically peak activity).",
    personalityTraits: [
      { trait: "Aggression", score: 45 }, { trait: "Manipulation", score: 40 }, { trait: "Impulsivity", score: 50 },
      { trait: "Social Deviance", score: 68 }, { trait: "Criminal Sophistication", score: 60 },
    ],
    courtDates: [
      { date: "2020-10-20", court: "JMFC, Bengaluru", caseRef: "CC-2210/2020", outcome: "convicted" },
      { date: "2022-04-12", court: "JMFC, Bengaluru", caseRef: "CC-889/2022", outcome: "acquitted" },
      { date: "2023-07-05", court: "Sessions Court, Bengaluru", caseRef: "SC-445/2023", outcome: "convicted" },
      { date: "2025-04-18", court: "JMFC, Bengaluru", caseRef: "CC-301/2025", outcome: "pending" },
      { date: "2025-08-22", court: "Sessions Court, Bengaluru", caseRef: "SC-201/2025", outcome: "pending" },
    ],
    linkedFIRs: [
      { firNumber: "FIR-2020-BLR-0234", date: "2020-03-15", crime: "Burglary", section: "IPC 454, 380", status: "convicted" },
      { firNumber: "FIR-2021-BLR-0567", date: "2021-07-22", crime: "Theft", section: "IPC 379", status: "acquitted" },
      { firNumber: "FIR-2022-BLR-1105", date: "2022-11-08", crime: "Burglary", section: "IPC 454, 457", status: "convicted" },
      { firNumber: "FIR-2023-BLR-0890", date: "2023-09-14", crime: "Robbery", section: "IPC 392", status: "charge-sheeted" },
      { firNumber: "FIR-2025-BLR-0089", date: "2025-01-10", crime: "Burglary", section: "IPC 454, 380", status: "under-investigation" },
    ],
    victimCount: 9, estimatedLoss: "₹6.8 Lakh",
    frequencyByYear: [
      { year: "2020", count: 1 }, { year: "2021", count: 1 }, { year: "2022", count: 1 },
      { year: "2023", count: 1 }, { year: "2024", count: 0 }, { year: "2025", count: 1 },
    ],
  },
  {
    id: "OFF-005", name: "Prakash Shetty", age: 26,
    photo: "/offenders/off-005.png",
    alias: ["PK"],
    gender: "male", height: "5'8\"", weight: "70 kg",
    scars: ["Tattoo on left wrist — skull"],
    lastKnownAddress: "56, Old Airport Road, KR Puram, Bengaluru - 560036",
    district: "Bengaluru East",
    associates: ["Anil Gowda"],
    paroleOfficer: "ASI Manjunath B.",
    convictions: 1, acquittals: 1, pendingCases: 1,
    fingerprint: "Loop — Right Middle",
    nationalId: "XXXX-XXXX-2290",
    totalFIRs: 4, crimeTypes: ["Assault", "Vandalism"],
    riskScore: 58, isHabitual: false, modusOperandi: ["Street fights", "Property damage", "Road rage"],
    lastOffense: "2024-09-22", status: "on-bail",
    timeline: [
      { date: "2022-04-10", crime: "Assault", location: "KR Puram" },
      { date: "2023-01-18", crime: "Vandalism", location: "Majestic" },
      { date: "2023-08-05", crime: "Road Rage Assault", location: "Hebbal" },
      { date: "2024-09-22", crime: "Assault", location: "KR Puram" },
    ],
    bloodGroup: "O-", languages: ["Kannada", "Tulu"], occupation: "Unemployed", education: "PUC (Dropout)",
    fatherName: "Ganesh Shetty", phoneNumber: "XXXXX-XX445",
    aiBehavioralNote: "Reactive aggression profile — crimes are driven by situational triggers (alcohol, road rage, personal disputes) rather than premeditation. Low criminal sophistication but escalating frequency is concerning. Association with Anil Gowda's network may indicate recruitment into organized crime. Anger management intervention recommended as part of bail conditions.",
    personalityTraits: [
      { trait: "Aggression", score: 75 }, { trait: "Manipulation", score: 20 }, { trait: "Impulsivity", score: 85 },
      { trait: "Social Deviance", score: 52 }, { trait: "Criminal Sophistication", score: 22 },
    ],
    courtDates: [
      { date: "2022-11-14", court: "JMFC, Bengaluru", caseRef: "CC-1890/2022", outcome: "convicted" },
      { date: "2023-06-20", court: "JMFC, Bengaluru", caseRef: "CC-445/2023", outcome: "acquitted" },
      { date: "2025-01-28", court: "JMFC, Bengaluru", caseRef: "CC-112/2025", outcome: "pending" },
    ],
    linkedFIRs: [
      { firNumber: "FIR-2022-BLR-0334", date: "2022-04-10", crime: "Assault", section: "IPC 323, 324", status: "convicted" },
      { firNumber: "FIR-2023-BLR-0078", date: "2023-01-18", crime: "Vandalism", section: "IPC 427", status: "acquitted" },
      { firNumber: "FIR-2023-BLR-0601", date: "2023-08-05", crime: "Road Rage Assault", section: "IPC 323, 341", status: "charge-sheeted" },
      { firNumber: "FIR-2024-BLR-0812", date: "2024-09-22", crime: "Assault", section: "IPC 324, 506", status: "under-investigation" },
    ],
    victimCount: 5, estimatedLoss: "₹1.2 Lakh",
    frequencyByYear: [
      { year: "2022", count: 1 }, { year: "2023", count: 2 }, { year: "2024", count: 1 },
    ],
  },
  {
    id: "OFF-006", name: "Deepak Jain", age: 45,
    photo: "/offenders/off-006.png",
    alias: ["DJ"],
    gender: "male", height: "5'6\"", weight: "82 kg",
    scars: ["No visible scars"],
    lastKnownAddress: "203, Diamond District, Domlur, Bengaluru - 560071",
    district: "Bengaluru Central",
    associates: ["Vikram Singh"],
    paroleOfficer: "SI Priya Sharma",
    convictions: 0, acquittals: 1, pendingCases: 1,
    fingerprint: "Whorl — Right Ring",
    nationalId: "XXXX-XXXX-1178",
    totalFIRs: 2, crimeTypes: ["White Collar Crime", "Fraud"],
    riskScore: 42, isHabitual: false, modusOperandi: ["Document forgery", "Real estate fraud"],
    lastOffense: "2024-06-15", status: "on-bail",
    timeline: [
      { date: "2023-02-28", crime: "Document Forgery", location: "MG Road" },
      { date: "2024-06-15", crime: "Real Estate Fraud", location: "Whitefield" },
    ],
    bloodGroup: "A-", languages: ["Hindi", "English", "Gujarati"], occupation: "Real Estate Developer", education: "MBA (Finance)",
    fatherName: "Ramkishan Jain", phoneNumber: "XXXXX-XX778",
    aiBehavioralNote: "White-collar criminal with high social standing and connections. Uses legitimate business operations to mask fraudulent activities. Articulate and composed — unlikely to exhibit visible stress. Leverages legal expertise to exploit procedural delays. Financial trail analysis suggests significantly larger unreported fraud network. Low physical threat but high economic damage potential.",
    personalityTraits: [
      { trait: "Aggression", score: 10 }, { trait: "Manipulation", score: 82 }, { trait: "Impulsivity", score: 18 },
      { trait: "Social Deviance", score: 45 }, { trait: "Criminal Sophistication", score: 88 },
    ],
    courtDates: [
      { date: "2023-09-15", court: "Sessions Court, Bengaluru", caseRef: "SC-780/2023", outcome: "acquitted" },
      { date: "2025-02-10", court: "Sessions Court, Bengaluru", caseRef: "SC-89/2025", outcome: "pending" },
    ],
    linkedFIRs: [
      { firNumber: "FIR-2023-BLR-0201", date: "2023-02-28", crime: "Document Forgery", section: "IPC 467, 468, 471", status: "acquitted" },
      { firNumber: "FIR-2024-BLR-0512", date: "2024-06-15", crime: "Real Estate Fraud", section: "IPC 420, 467", status: "under-investigation" },
    ],
    victimCount: 3, estimatedLoss: "₹2.4 Crore",
    frequencyByYear: [
      { year: "2023", count: 1 }, { year: "2024", count: 1 },
    ],
  },
];




// ─── Case Intelligence Data ──────────────────────────────────────────

export interface CaseRecord {
  firNumber: string;
  date: string;
  crimeType: string;
  section: string;
  accused: string[];
  victim: string;
  location: string;
  status: "under-investigation" | "charge-sheeted" | "court-pending" | "convicted" | "closed";
  summary: string;
  timeline: { date: string; event: string }[];
  similarCases: string[];
  leads: string[];
  // Phase 2 Fields
  solvabilityScore: number;
  investigatingOfficer: string;
  witnessCount: number;
  evidence: { type: string; displayTitle?: string; description: string; status: "collected" | "at-forensics" | "processed" }[];
  recoveredAssets: string;
  nextHearingDate: string | null;
  priority: "critical" | "high" | "medium" | "low";
  aiAnalysis: string;
}

export const cases: CaseRecord[] = [
  {
    firNumber: "FIR-2025-BLR-0847",
    date: "2025-03-15",
    crimeType: "Armed Robbery",
    section: "IPC 392, 397",
    accused: ["Rajesh Kumar", "Unknown"],
    victim: "Meera Devi",
    location: "Majestic Area, Bengaluru",
    status: "under-investigation",
    summary: "Armed robbery at a jewelry store in Majestic area at approximately 9:45 PM. Two suspects, one identified as Rajesh Kumar (repeat offender, 7 prior FIRs), entered the store with concealed weapons. Approximately ₹12.5 lakh worth of gold jewelry was stolen. CCTV footage partially captured the incident.",
    timeline: [
      { date: "2025-03-15", event: "FIR Filed at Upparpet PS" },
      { date: "2025-03-16", event: "CCTV footage reviewed — 1 suspect identified" },
      { date: "2025-03-18", event: "Rajesh Kumar identified via facial recognition" },
      { date: "2025-03-20", event: "Arrest warrant issued" },
      { date: "2025-03-25", event: "Rajesh Kumar arrested at Whitefield hideout" },
    ],
    similarCases: ["FIR-2023-BLR-0412", "FIR-2022-BLR-1105", "FIR-2021-BLR-0673"],
    leads: ["Cross-reference HDFC-****4521 for recent large deposits", "Check CCTV at MG Road metro for second suspect", "Interview jewelry store employees for insider information"],
    solvabilityScore: 82,
    investigatingOfficer: "Insp. Vikram Patil",
    witnessCount: 3,
    evidence: [
      { type: "CCTV Footage", description: "Exterior street camera capturing getaway vehicle", status: "processed" },
      { type: "Weapon", description: "Discarded 9mm handgun found 2km from scene", status: "at-forensics" },
      { type: "Fingerprint", displayTitle: "Fingerprint Lift", description: "Partial print from display case glass", status: "processed" }
    ],
    recoveredAssets: "₹4.2 Lakh (Partial)",
    nextHearingDate: null,
    priority: "critical",
    aiAnalysis: "Pattern matches three previous armed robberies in the Majestic area within the last 24 months. High likelihood of insider collusion given the precise targeting of the highest-value display case within a 3-minute window. The second suspect is likely a new recruit, showing signs of hesitation in the CCTV footage."
  },
  {
    firNumber: "FIR-2025-BLR-1234",
    date: "2025-05-20",
    crimeType: "Cybercrime - Wire Fraud",
    section: "IT Act 66C, 66D",
    accused: ["Farhan Sheikh"],
    victim: "Multiple (12 complainants)",
    location: "Whitefield, Bengaluru",
    status: "under-investigation",
    summary: "Sophisticated wire fraud scheme targeting senior citizens through fake bank customer care calls. Victims were tricked into revealing OTPs and transferring funds to mule accounts. Total estimated loss: ₹48.7 lakh across 12 victims. Suspect Farhan Sheikh has 7 prior cybercrime FIRs.",
    timeline: [
      { date: "2025-05-18", event: "First complaint received at Cyber Crime PS" },
      { date: "2025-05-19", event: "4 more victims identified through common phone number" },
      { date: "2025-05-20", event: "FIR registered; bank accounts frozen" },
      { date: "2025-05-22", event: "SIM card traced to Farhan Sheikh" },
      { date: "2025-05-25", event: "Lookout circular issued — suspect absconding" },
    ],
    similarCases: ["FIR-2024-BLR-0891", "FIR-2023-BLR-1567"],
    leads: ["Trace ICICI-****1190 withdrawal locations", "Check mule account KYC documents for accomplices", "Coordinate with Telecom provider for call detail records"],
    solvabilityScore: 65,
    investigatingOfficer: "ACP Neha Sharma",
    witnessCount: 12,
    evidence: [
      { type: "Digital Logs", description: "IP access logs for the mule accounts", status: "processed" },
      { type: "Call Records", description: "CDR of the primary spoofed number", status: "collected" },
      { type: "Financial", description: "Frozen bank statements from 4 mule accounts", status: "processed" }
    ],
    recoveredAssets: "₹18.5 Lakh (Frozen)",
    nextHearingDate: null,
    priority: "high",
    aiAnalysis: "The structured nature of the withdrawals (keeping amounts under ₹50k to avoid automated flagging) indicates a highly organized operation. The suspect is likely part of a larger syndicate operating out of Jamtara or a similar hub, using local operatives for cash withdrawals."
  },
  {
    firNumber: "FIR-2024-BLR-0965",
    date: "2024-12-01",
    crimeType: "Narcotics Possession",
    section: "NDPS Act 21, 22",
    accused: ["Anil Gowda"],
    victim: "State",
    location: "KR Puram, Bengaluru",
    status: "court-pending",
    summary: "Narcotics raid at a warehouse in KR Puram led to the seizure of 2.5 kg of methamphetamine and 500g of MDMA. Accused Anil Gowda was apprehended at the scene. Investigation revealed links to an interstate drug trafficking network operating across Karnataka and Tamil Nadu.",
    timeline: [
      { date: "2024-11-28", event: "Intelligence tip received from informant" },
      { date: "2024-11-30", event: "Surveillance operation initiated" },
      { date: "2024-12-01", event: "Raid conducted; Anil Gowda arrested with contraband" },
      { date: "2024-12-05", event: "Charge sheet filed" },
      { date: "2025-01-15", event: "Case referred to NDPS Court" },
    ],
    similarCases: ["FIR-2023-BLR-0782", "FIR-2022-MNG-0234"],
    leads: ["Investigate supply chain from Tamil Nadu border", "Check SBI-****8832 for hawala transactions", "Interview warehouse owner for rental agreement details"],
    solvabilityScore: 95,
    investigatingOfficer: "DCP Rajesh Menon",
    witnessCount: 4,
    evidence: [
      { type: "Contraband", description: "2.5kg Meth, 500g MDMA seized at scene", status: "processed" },
      { type: "Mobile Device", description: "Burner phone recovered from accused", status: "at-forensics" },
      { type: "Document", description: "Warehouse lease agreement", status: "processed" }
    ],
    recoveredAssets: "₹35 Lakh (Contraband Value)",
    nextHearingDate: "2026-08-14",
    priority: "medium",
    aiAnalysis: "The scale of the seizure suggests this location was a primary distribution node for East Bengaluru. Communication logs from the recovered burner phone, once decrypted, will likely expose the interstate supply chain route originating from Chennai."
  },
];

// ─── Financial Trails Data ───────────────────────────────────────────

export interface SuspiciousTransaction {
  id: string;
  fromAccount: string;
  toAccount: string;
  amount: number;
  date: string;
  type: "deposit" | "withdrawal" | "transfer";
  flag: "amount-anomaly" | "frequency-anomaly" | "cross-border" | "structuring";
  severity: "critical" | "high" | "medium";
  linkedFIR: string;
  linkedAccused: string;
  status: "flagged" | "under-review" | "escalated" | "resolved";
}

export const suspiciousTransactions: SuspiciousTransaction[] = [
  { id: "TXN-001", fromAccount: "HDFC-****4521", toAccount: "CASH", amount: 495000, date: "2025-03-16", type: "withdrawal", flag: "structuring", severity: "critical", linkedFIR: "FIR-2025-BLR-0847", linkedAccused: "Rajesh Kumar", status: "under-review" },
  { id: "TXN-002", fromAccount: "HDFC-****4521", toAccount: "SBI-****2211", amount: 250000, date: "2025-03-17", type: "transfer", flag: "amount-anomaly", severity: "high", linkedFIR: "FIR-2025-BLR-0847", linkedAccused: "Rajesh Kumar", status: "flagged" },
  { id: "TXN-003", fromAccount: "ICICI-****1190", toAccount: "CASH", amount: 180000, date: "2025-05-21", type: "withdrawal", flag: "frequency-anomaly", severity: "critical", linkedFIR: "FIR-2025-BLR-1234", linkedAccused: "Farhan Sheikh", status: "escalated" },
  { id: "TXN-004", fromAccount: "Multiple Victims", toAccount: "ICICI-****1190", amount: 487000, date: "2025-05-20", type: "transfer", flag: "amount-anomaly", severity: "critical", linkedFIR: "FIR-2025-BLR-1234", linkedAccused: "Farhan Sheikh", status: "under-review" },
  { id: "TXN-005", fromAccount: "SBI-****8832", toAccount: "UNKNOWN INTL", amount: 750000, date: "2024-11-29", type: "transfer", flag: "cross-border", severity: "critical", linkedFIR: "FIR-2024-BLR-0965", linkedAccused: "Anil Gowda", status: "escalated" },
  { id: "TXN-006", fromAccount: "SBI-****8832", toAccount: "CASH", amount: 49000, date: "2024-11-28", type: "withdrawal", flag: "structuring", severity: "high", linkedFIR: "FIR-2024-BLR-0965", linkedAccused: "Anil Gowda", status: "flagged" },
  { id: "TXN-007", fromAccount: "SBI-****8832", toAccount: "CASH", amount: 48500, date: "2024-11-27", type: "withdrawal", flag: "structuring", severity: "high", linkedFIR: "FIR-2024-BLR-0965", linkedAccused: "Anil Gowda", status: "flagged" },
  { id: "TXN-008", fromAccount: "HDFC-****4521", toAccount: "Axis-****7730", amount: 120000, date: "2025-02-10", type: "transfer", flag: "frequency-anomaly", severity: "medium", linkedFIR: "FIR-2025-BLR-0847", linkedAccused: "Suresh Patil", status: "resolved" },
];

export const flowData = [
  { from: "Victims (12)", to: "ICICI-****1190", amount: 487000 },
  { from: "ICICI-****1190", to: "Cash Withdrawal", amount: 180000 },
  { from: "ICICI-****1190", to: "Mule Account 1", amount: 150000 },
  { from: "ICICI-****1190", to: "Mule Account 2", amount: 157000 },
  { from: "HDFC-****4521", to: "Cash Withdrawal", amount: 495000 },
  { from: "HDFC-****4521", to: "SBI-****2211", amount: 250000 },
  { from: "SBI-****8832", to: "International Transfer", amount: 750000 },
  { from: "SBI-****8832", to: "Cash (Structured)", amount: 97500 },
];

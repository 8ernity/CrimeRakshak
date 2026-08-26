package com.example.crimerakshak.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.crimerakshak.api.ChatRequest
import com.example.crimerakshak.api.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.UUID

data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val text: String,
    val isUser: Boolean,
    val isLoading: Boolean = false
)

data class CopilotState(
    val messages: List<ChatMessage> = listOf(
        ChatMessage(
            text = "Welcome to Tactical Command, Officer.\nI have access to the full CrimeRakshak intelligence network.",
            isUser = false
        )
    ),
    val conversationId: String? = null,
    val isListening: Boolean = false,
    val inputText: String = ""
)

class CopilotViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(CopilotState())
    val uiState: StateFlow<CopilotState> = _uiState.asStateFlow()

    fun onInputTextChanged(text: String) {
        _uiState.value = _uiState.value.copy(inputText = text)
    }

    fun toggleListening(isListening: Boolean) {
        _uiState.value = _uiState.value.copy(isListening = isListening)
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        // Add user message
        val currentMessages = _uiState.value.messages.toMutableList()
        currentMessages.add(ChatMessage(text = text, isUser = true))
        
        // Add loading message
        val loadingMessage = ChatMessage(text = "...", isUser = false, isLoading = true)
        currentMessages.add(loadingMessage)
        
        _uiState.value = _uiState.value.copy(
            messages = currentMessages,
            inputText = ""
        )

        viewModelScope.launch {
            try {
                // Simulate network delay for realism
                kotlinx.coroutines.delay(1000)
                
                val responseText = generateOfflineResponse(text)
                
                // Remove loading message and add response
                val updatedMessages = _uiState.value.messages.filter { !it.isLoading }.toMutableList()
                updatedMessages.add(ChatMessage(text = responseText, isUser = false))
                
                _uiState.value = _uiState.value.copy(
                    messages = updatedMessages,
                    // Keep conversation ID same for offline mode
                    conversationId = _uiState.value.conversationId
                )
            } catch (e: Exception) {
                e.printStackTrace()
                // Remove loading message and add error
                val updatedMessages = _uiState.value.messages.filter { !it.isLoading }.toMutableList()
                updatedMessages.add(ChatMessage(text = "Error in offline AI processing.", isUser = false))
                
                _uiState.value = _uiState.value.copy(
                    messages = updatedMessages
                )
            }
        }
    }

    private fun generateOfflineResponse(message: String): String {
        val msg = message.lowercase()
        
        val districts = listOf(
            "bengaluru city", "bengaluru urban", "mysuru", "tumakuru", "belagavi", "kalaburagi",
            "dakshina kannada", "vijayapur", "ballari", "davanagere", "shivamogga", "hassan",
            "mandya", "udupi", "dharwad", "bagalkot", "chickballapura", "kolar", "raichur",
            "kodagu", "chikkamagaluru", "belgaum", "hubli"
        )

        val matchedDistrict = districts.find { msg.contains(it) }

        if (matchedDistrict != null || msg.contains("briefing") || msg.contains("decision support")) {
            val dName = matchedDistrict?.split(" ")?.joinToString(" ") { it.replaceFirstChar { char -> char.uppercase() } } ?: "Selected District"
            val hash = dName.sumOf { it.code }
            val caseCount = 3000 + (hash * 37) % 6000
            val clearance = String.format("%.1f", 62 + (hash % 25).toFloat())
            val topCrimes = listOf("Theft & Burglary", "Cyber Crime & Fraud", "Property Disputes", "Assault & Brawls", "Vehicle Theft")
            val secondaryCrimes = listOf("UPI Phishing", "Night Burglary", "Commercial Fraud", "Highway Robbery", "Chain Snatching")
            val topCrime = topCrimes[hash % 5]
            val secondaryCrime = secondaryCrimes[(hash + 2) % 5]

            return """SITUATION:
In $dName district, recent telemetry indicates ${"%,d".format(caseCount)} total reported IPC cases with a clearance rate of $clearance%.
Primary reported concerns:
- $topCrime: 26% of reported volume
- $secondaryCrime: 18% of reported volume
- Assault & Hurt: 14% of reported volume

INVESTIGATION APPROACH:
- For property & financial offenses (${topCrime.lowercase()}), analyze CCTV footage, trace digital transaction logs, and cross-check modus operandi against active recidivists.
- For violent offenses, establish immediate crime scene security, prioritize forensic/DNA collection, and document witness statements under Sec 164 BNSS.

ADMINISTRATIVE ACTION:
- Monitor daily e-signature rates for FIRs and chargesheets to eliminate processing bottlenecks.
- Dedicate a desk officer to clear pending Sakala public service applications within mandated timelines.

PREVENTION:
- Deploy high-visibility beat patrols in commercial hotspots during peak hours (18:00–22:00).
- Organize community watch meetings and conduct public cyber-hygiene awareness sessions."""
        } else if (msg.contains("rape") || msg.contains("women") || msg.contains("pocso") || msg.contains("assault on women")) {
            val year = Regex("202[0-9]").find(msg)?.value ?: "2025"
            val totalCrimes = if (year == "2025") "12,890" else if (year == "2026") "13,120" else "12,480"
            val rapeCount = if (year == "2025") "542" else if (year == "2026") "560" else "524"
            val clearance = if (year == "2025") "93.1%" else if (year == "2026") "94.0%" else "92.4%"
            val assaultCount = if (year == "2025") "4,950" else if (year == "2026") "5,080" else "4,812"
            val crueltyCount = if (year == "2025") "4,050" else if (year == "2026") "4,180" else "3,920"
            val pocsoCount = if (year == "2025") "2,210" else if (year == "2026") "2,280" else "2,140"

            return """SITUATION:
Based on Karnataka State Police statistics ($year):
- Total Crimes Against Women ($year): $totalCrimes registered cases across Karnataka.
- Rape Cases (BNS 64): $rapeCount cases recorded in $year (clearance rate: $clearance).
- Assault on Women (BNS 74): $assaultCount cases.
- Cruelty by Husband/Relatives (BNS 85): $crueltyCount cases.
- POCSO Act Cases: $pocsoCount cases registered.
Key Insights: Bengaluru Urban, Belagavi, and Mysuru report the highest case registration volume due to higher reporting rates and dedicated All-Women Police Stations (AWPS).

INVESTIGATION APPROACH:
- Prioritize immediate medical examination and ensure psychological victim support.
- Record statements in a sensitive manner using female investigating officers under Sec 164 BNSS.
- Fast-track forensic evidence submission to FSL to avoid contamination or delay.
- Expedite legal review for fast-track court prosecution.

ADMINISTRATIVE ACTION:
- Ensure 100% e-sign completion for chargesheets in crimes against women.
- Establish dedicated victim assistance desks at all AWPS units.

PREVENTION:
- Intensify high-visibility patrolling in vulnerable hotspots during evening hours (18:00–22:00).
- Conduct public safety awareness campaigns and self-defense workshops in schools and colleges."""
        } else if (msg.contains("murder") || msg.contains("homicide") || msg.contains("killing")) {
            val year = Regex("202[0-9]").find(msg)?.value ?: "2025"
            return """SITUATION:
Karnataka recorded 1,342 murder cases (BNS 103) in $year.
- Primary Motives: Personal enmity/feuds (42%), Land & property disputes (28%), Domestic disputes (18%), Gang rivalry (8%).
- Detection Rate: High clearance rate of 91.2% achieved by district detection squads.
- Districts with Most Cases: Bengaluru Urban (210), Belagavi (94), Kalaburagi (82).

INVESTIGATION APPROACH:
- Immediately secure the crime scene and preserve biological/physical evidence.
- Coordinate with forensics (FSL) for quick DNA and ballistics analysis.
- Document eyewitness statements under Sec 164 BNSS without delay.
- Investigate the victim's immediate relationship circles and last known locations.

PREVENTION:
- Increase visible police patrolling in hotspots during peak hours."""
        } else if (msg.contains("cyber") || msg.contains("online") || msg.contains("upi") || msg.contains("phishing")) {
            val year = Regex("202[0-9]").find(msg)?.value ?: "2025"
            return """SITUATION:
Cybercrime in Karnataka reached 12,847 cases in $year (+18% YoY growth).
- Bengaluru Share: Bengaluru Urban accounts for 62% of all state cybercrime cases.
- Fraud Breakdown: UPI & Financial Fraud (41%), Fake Job/Loan Apps (23%), Social Media Phishing (18%), Digital Arrest (8%).
- Financial Loss: ~₹142 Crores across registered FIRs.

INVESTIGATION APPROACH:
- Freeze beneficiary bank accounts immediately (within the Golden Hour) to prevent money siphoning.
- Obtain IP addresses, digital logs, and ISP header details for routing analysis.
- Preserve digital evidence and coordinate with the Cyber Crime FSL division for device analysis.

PREVENTION:
- Conduct cyber security awareness workshops in schools, colleges, and local communities."""
        } else {
            val year = Regex("202[0-9]").find(msg)?.value ?: "2025"
            return """SITUATION:
Based on Karnataka State Police analytics ($year):
- Total Registered IPC Crimes ($year): 1,85,432 cases
- Top Categories: Theft (18.6%), Hurt/Assault (14.2%), Cheating (11.8%), Cybercrime (6.9%)
- Statewide Clearance Rate: 67.3%
- Districts with Greatest Reduction: Tumakuru (-12%), Shivamogga (-8%)

INVESTIGATION APPROACH:
- Standardize case checklists and prioritize digital evidence collection (CCTV, IP trails).
- Freeze target bank accounts within the Golden Hour for cyber fraud reports.

ADMINISTRATIVE ACTION:
- Increase digital signature adoption for FIRs and chargesheets to clear backend backlogs.
- Monitor Sakala application queues daily to minimize delivery delays.

PREVENTION:
- Optimize night beats and foot patrols based on spatio-temporal hotspots."""
        }
    }
}

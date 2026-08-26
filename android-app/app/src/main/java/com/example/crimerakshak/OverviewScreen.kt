package com.example.crimerakshak

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.clickable
import com.example.crimerakshak.viewmodel.OverviewViewModel

val Primary = Color(0xFFb5ea4d)
val PrimaryContainer = Color(0xFF9acd32)
val OnPrimaryContainer = Color(0xFF273500)
val OnPrimary = Color(0xFF263500)
val BackgroundDark = Color(0xFF11150b)
val SurfaceDark = Color(0xFF1a1d14)
val SurfaceContainer = Color(0xFF1d2116)
val TextLight = Color(0xFFe1e4d3)
val TextMuted = Color(0xFF8c9383)
val OutlineVariant = Color(0xFF434937)

@Composable
fun OverviewScreen(
    modifier: Modifier = Modifier,
    viewModel: OverviewViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    val context = androidx.compose.ui.platform.LocalContext.current
    var selectedChipIndex by androidx.compose.runtime.remember { androidx.compose.runtime.mutableIntStateOf(0) }
    
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(BackgroundDark)
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Top Bar (Profile + Name)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(SurfaceDark),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.Person, contentDescription = "Profile", tint = TextMuted)
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("TACTICAL COMMAND", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                Text("Welcome, Officer Miller", color = TextLight, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            }
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(PrimaryContainer),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.Warning, contentDescription = "Emergency", tint = OnPrimaryContainer, modifier = Modifier.size(20.dp))
            }
        }

        // Header
        Text("Executive Snapshot", color = TextLight, fontSize = 24.sp, fontWeight = FontWeight.Bold)
        Text("Real-time jurisdictional overview", color = TextMuted, fontSize = 14.sp, modifier = Modifier.padding(bottom = 16.dp))

        // Chips Row
        if (state.isLoading) {
            CircularProgressIndicator(color = Primary, modifier = Modifier.padding(bottom = 16.dp))
        } else {
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.padding(bottom = 16.dp)
            ) {
                val ranges = listOf("All Karnataka", "Bengaluru Commissionerate", "Southern Range", "Coastal Range", "North Karnataka Range")
                items(ranges.size) { index ->
                    val rangeName = ranges[index]
                    val isSelected = rangeName == state.selectedRange
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(16.dp))
                            .background(if (isSelected) PrimaryContainer else SurfaceContainer)
                            .clickable { 
                                viewModel.selectRange(rangeName)
                            }
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                    ) {
                        Text(
                            text = rangeName, 
                            color = if (isSelected) OnPrimaryContainer else TextLight, 
                            fontSize = 12.sp, 
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }
        }

        // Predictive Alert Card
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFF161d0f)),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp)
                .border(1.dp, Primary.copy(alpha = 0.2f), RoundedCornerShape(12.dp))
        ) {
            Row(modifier = Modifier.fillMaxWidth()) {
                Box(modifier = Modifier.width(4.dp).height(120.dp).background(Primary))
                Column(modifier = Modifier.padding(16.dp).weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 8.dp)) {
                        Icon(Icons.Filled.Warning, contentDescription = null, tint = Primary, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("AI PREDICTIVE ALERT", color = Primary, fontSize = 12.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                        Spacer(modifier = Modifier.width(8.dp))
                        Box(modifier = Modifier.background(Primary.copy(alpha = 0.2f), RoundedCornerShape(4.dp)).padding(horizontal = 4.dp, vertical = 2.dp)) {
                            Text("ACTIVE", color = Primary, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                    Text("Projected +14.2% Property Theft anomaly.", color = TextLight, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text("Action: Pre-deploy units & step up screening.", color = TextMuted, fontSize = 12.sp, modifier = Modifier.padding(bottom = 8.dp, top = 4.dp))
                }
            }
        }

        // Governance SLA Card
        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 12.dp)) {
                    Icon(Icons.Filled.AdminPanelSettings, contentDescription = null, tint = TextMuted, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("DIGITAL POLICING SLA", color = TextMuted, fontSize = 12.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    Spacer(modifier = Modifier.width(8.dp))
                    Box(
                        modifier = Modifier
                            .border(1.dp, Primary.copy(alpha = 0.5f), RoundedCornerShape(4.dp))
                            .background(Color(0xFF161d0f))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Filled.CheckCircle, contentDescription = null, tint = Primary, modifier = Modifier.size(10.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("VERIFIED", color = Primary, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
                Text("eSign FIR Compliance: 98.4% | Service Disposal: 96.8%.", color = TextLight, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(bottom = 4.dp))
                Text("All records backed by immutable audit logs.", color = TextMuted, fontSize = 11.sp, modifier = Modifier.padding(bottom = 12.dp))
            }
        }

        // Dynamic KPI calculations
        val (displayTotalCrimes, displayIpc, displaySll, displayDistrictCount) = when (state.selectedRange) {
            "All Karnataka" -> listOf(220308, 152876, 67432, 37)
            "Bengaluru Commissionerate" -> listOf(69833, 48554, 21279, 2)
            "Southern Range" -> listOf(27119, 19096, 8023, 5)
            "Coastal Range" -> listOf(13529, 9368, 4161, 3)
            "North Karnataka Range" -> listOf(16876, 11692, 5184, 3)
            else -> listOf(220308, 152876, 67432, 37)
        }
        val isAll = state.selectedRange == "All Karnataka"
        val displayResRate = if (isAll) 68.4 else 88.4
        val yoyChange = if (isAll) "-3.2%" else "-2.4%"
        val share = if (displayTotalCrimes > 0) (displayIpc * 100 / displayTotalCrimes) else 70

        // 2x2 Grid Stats
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
            // Total Crimes
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.weight(1f).aspectRatio(1.2f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("Total Crimes", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    Text(String.format("%,d", displayTotalCrimes), color = TextLight, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.ArrowDownward, contentDescription = null, tint = Color(0xFFF43F5E), modifier = Modifier.size(12.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("↘ $yoyChange vs 2024", color = Color(0xFFF43F5E), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
            // IPC Cases
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.weight(1f).aspectRatio(1.2f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("IPC Cases", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    Text(String.format("%,d", displayIpc), color = TextLight, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Column {
                        Text("+ SLL: ${String.format("%,d", displaySll)}", color = Primary, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        Text("~ $share% of total", color = Primary, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
            // Resolution Rate
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.weight(1f).aspectRatio(1.2f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("Resolution Rate", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    Text("$displayResRate%", color = TextLight, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Text("~ +2.1% statutory clearance", color = Primary, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
            }
            // Jurisdictions
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.weight(1f).aspectRatio(1.2f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("Monitored Jurisdictions", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    Text("$displayDistrictCount", color = TextLight, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    val displayLabel = if (isAll) "All Karnataka" else state.selectedRange
                    Text("~ $displayLabel active sector", color = Primary, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 0.5.sp)
                }
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Dynamic SQL-powered Charts
        DashboardCharts(state)
        
        Spacer(modifier = Modifier.height(32.dp))
    }
}
